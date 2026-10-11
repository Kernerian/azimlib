"""Opt-in real LaTeX fragments, through explicit offline external tools.

Original integration code. Tectonic and pdftocairo are separate executables,
not bundled backends. TeX fonts/packages retain their own rights and notices.
This module never downloads anything and is not a sandbox for untrusted TeX.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from collections import OrderedDict,namedtuple
from dataclasses import dataclass, field, asdict
import hashlib
import math
from pathlib import Path
import re
import shutil
import sys
import tempfile
from threading import RLock
from urllib.parse import urlsplit


class TexError(ValueError): pass
class TexUnavailableError(TexError): pass
class TexResourceError(TexError): pass


@dataclass(frozen=True)
class TexConfig:
    """Explicit Tectonic + pdftocairo contract, with caller-owned resources.

    `cache_dir` must already contain a prepared Tectonic cache. Resource fonts
    require explicit public provenance and permission to export outlines.
    Tools, cache and temp paths are private and omitted from repr/exports.
    The guards sample RAM/disk; use an OS sandbox for adversarial input.
    """
    executable: str = field(default='tectonic', repr=False)
    converter: str = field(default='pdftocairo', repr=False)
    cache_dir: object = field(default=None, repr=False)
    temp_root: object = field(default=None, repr=False)
    preamble: str = field(default=r'\usepackage{amsmath}', repr=False)
    font_notices: tuple = field(default=(), repr=False)
    resource_files: tuple = field(default=(), repr=False)
    trusted: bool = False
    allow_outlines: bool = False
    timeout: float = 30
    max_memory_bytes: int = 1024**3
    max_temp_bytes: int = 64*1024**2
    max_cache_bytes: int = 256*1024**2
    fallback: object = None

    def __post_init__(self):
        from .patterns import Provenance
        if self.trusted is not True:
            raise TexError('Real TeX requires trusted=True; never compile untrusted input in this process')
        if self.allow_outlines is not True:
            raise TexError('Confirm font outline export permission with allow_outlines=True')
        if self.cache_dir is None:
            raise TexError('An explicitly prepared local TeX cache_dir is required')
        object.__setattr__(self, 'cache_dir', Path(self.cache_dir).resolve())
        if self.temp_root is not None:
            object.__setattr__(self, 'temp_root', Path(self.temp_root).resolve())
        if not isinstance(self.resource_files,(tuple,list)):
            raise TexError('resource_files must list explicitly used local fonts/resources')
        if len(self.resource_files)>128:raise TexError('At most 128 external TeX resource files are accepted')
        object.__setattr__(self,'resource_files',tuple(Path(p).resolve() for p in self.resource_files))
        if not isinstance(self.preamble, str) or len(self.preamble) > 8192:
            raise TexError('TeX preamble must contain at most 8192 characters')
        if not isinstance(self.font_notices, (tuple, list)) or not self.font_notices:
            raise TexError('Require provenance notices for the TeX fonts being exported')
        for notice in self.font_notices:
            if not isinstance(notice, Provenance) or not notice.license_text.strip():
                raise TexError('TeX fonts require Provenance with the full license text')
            url = urlsplit(notice.source)
            if url.scheme != 'https' or not url.netloc or url.username or url.password:
                raise TexError('TeX font provenance requires a public HTTPS source')
        object.__setattr__(self, 'font_notices', tuple(self.font_notices))
        for name, low, high in (('timeout', .05, 120), ('max_memory_bytes', 16*1024**2, 2*1024**3),
                               ('max_temp_bytes', 1024, 256*1024**2), ('max_cache_bytes', 1024, 512*1024**2)):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not low <= value <= high:
                raise TexError('Invalid TeX resource limit: '+name)
        if self.fallback not in (None, 'basic'):
            raise TexError('fallback must be None or explicitly "basic"')
        for name in ('executable', 'converter'):
            if not isinstance(getattr(self, name), (str, Path)) or not str(getattr(self, name)):
                raise TexError('TeX executables must be explicit names or paths')
            object.__setattr__(self, name, str(getattr(self, name)))


@contextmanager
def tex_context(config):
    """Capture real TeX defaults in new figures/Artists; reset on exit."""
    from .text_engine import _defaults
    if not isinstance(config, TexConfig): raise TypeError('Require TexConfig')
    token = _defaults.set(dict(textengine='tex', texconfig=config))
    try: yield
    finally: _defaults.reset(token)


@dataclass(frozen=True)
class TexLayout:
    width: float
    ascent: float
    descent: float
    commands: tuple
    notices: tuple
    identity: str
    metrics: tuple = ()
    engine: str = 'tectonic'


class TexText(str):
    """Prepared immutable outlines, portable to render workers without TeX."""
    def __new__(cls, text, layout):
        value = super().__new__(cls, text); value.tex_layout = layout; return value
    def __reduce__(self): return TexText, (str(self), self.tex_layout)
    def split(self, sep=None, maxsplit=-1):
        return [self] if sep == '\n' and '\n' not in self else super().split(sep, maxsplit)
    def replace(self, old, new, count=-1):
        return self if old not in self else super().replace(old, new, count)


_fingerprints = {}
_lock = RLock()
_snapshots = ContextVar('azimlib_tex_composition_resources',default=None)
_compiled = OrderedDict()
_cache_bytes = _cache_hits = _cache_misses = 0


@contextmanager
def composition_resources():
    """One verified tool/font snapshot per composition, never a time-based TTL."""
    if _snapshots.get() is not None:
        yield
        return
    snapshots={};token=_snapshots.set(snapshots)
    try:
        yield
        for config,(_,_,identity) in snapshots.items():
            if _resources(config)!=identity[2]:
                raise TexError('TeX resources changed during composition')
            if _tool(config.executable)[1]!=identity[0] or _tool(config.converter)[1]!=identity[1]:
                raise TexError('TeX tools changed during composition')
    finally:_snapshots.reset(token)


def _digest(path):
    stat = path.stat()
    key = (str(path), stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    with _lock:
        if key in _fingerprints: return _fingerprints[key]
    if stat.st_size > 64*1024**2: raise TexResourceError('TeX resource file exceeds 64 MiB')
    value = hashlib.sha256(path.read_bytes()).hexdigest()
    with _lock:
        if len(_fingerprints) >= 4096: _fingerprints.clear()
        _fingerprints[key] = value
    return value


def _tool(name):
    selected = shutil.which(name)
    if selected is None: raise TexUnavailableError('Configured TeX tool is unavailable; install/configure it explicitly')
    path = Path(selected).resolve()
    return str(path), _digest(path)


def _resources(config):
    from ._tex_process import tree_bytes
    root = config.cache_dir
    if not root.is_dir(): raise TexUnavailableError('Prepared local TeX cache is unavailable')
    try: tree_bytes(root, config.max_cache_bytes)
    except ValueError as exc: raise TexResourceError(str(exc)) from None
    files = sorted(p for p in root.rglob('*') if p.is_file())
    if not files: raise TexUnavailableError('Prepared local TeX cache is empty')
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path.relative_to(root)).replace('\\', '/').encode('utf8'))
        digest.update(bytes.fromhex(_digest(path)))
    for path in config.resource_files:
        if not path.is_file() or path.is_symlink():
            raise TexUnavailableError('Explicit TeX font/resource file is unavailable')
        digest.update(bytes.fromhex(_digest(path)))
    return digest.hexdigest()


def _document(text, size, style, preamble):
    # TeX owns the entire fragment, including $ delimiters and macros. The
    # internal mathtext parser is never involved in this path.
    weight_value=str(style.get('font_weight','normal'))
    weight = r'\bfseries ' if weight_value=='bold' or weight_value.isdigit() and int(weight_value)>=600 else ''
    slant = r'\itshape ' if style.get('font_style', 'normal') != 'normal' else ''
    return (r'\documentclass{article}'+'\n'+preamble+'\n'+r'''
\pagestyle{empty}
\begin{document}
\hoffset=-1in\voffset=-1in
\setbox0=\hbox{\fontsize{'''+format(size, '.8g')+r'bp}{'+format(size*1.2, '.8g')+
            r'bp}\selectfont '+weight+slant+text+r'''}
\typeout{AZIMLIB-METRICS:\the\wd0:\the\ht0:\the\dp0}
\dimen0=\wd0\advance\dimen0 by 4bp
\dimen2=\ht0\advance\dimen2 by \dp0\advance\dimen2 by 4bp
\shipout\vbox{\offinterlineskip\special{papersize=\the\dimen0,\the\dimen2}\kern2bp\hbox{\kern2bp\box0\kern2bp}\kern2bp}
\end{document}
''')


def _svg_commands(raw, width, height):
    """Bounded Cairo SVG subset, rejecting images/scripts/external references.

    fontTools only parses generic SVG path curves. Azimlib handles traversal,
    reference resolution, transforms, limits and integration independently.
    """
    from ._readers import xml_root
    import io
    from fontTools.svgLib.path import parse_path
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.misc.transform import Transform, Identity
    root = xml_root(io.BytesIO(raw))
    tag = lambda e: e.tag.rsplit('}', 1)[-1]
    if tag(root) != 'svg': raise TexError('Converter did not produce SVG')
    view = tuple(map(float, root.get('viewBox', '').split()))
    if len(view) != 4 or view[:2] != (0, 0) or abs(view[2]-width) > .1 or abs(view[3]-height) > .1:
        raise TexError('TeX page geometry does not match measured fragment')
    ids = {}
    for element in root.iter():
        if element.get('id'):
            if element.get('id') in ids: raise TexError('Duplicate TeX SVG identifier')
            ids[element.get('id')] = element
        if tag(element) not in ('svg', 'defs', 'g', 'path', 'use'):
            raise TexError('Unsupported TeX drawing: '+tag(element))
        if set(element.attrib)-{'id','style','d','transform','x','y','href',
              'fill','fill-opacity','fill-rule','stroke','stroke-width',
              'stroke-linecap','stroke-linejoin','stroke-opacity','stroke-miterlimit',
              '{http://www.w3.org/1999/xlink}href','viewBox','width','height','version'}:
            raise TexError('Unsupported attribute in TeX SVG')
    out = []
    expansions = 0
    def walk(element, transform=Identity, chain=()):
        nonlocal expansions
        expansions += 1
        if expansions>40000: raise TexResourceError('TeX SVG expansion limit exceeded')
        if len(chain) > 32: raise TexResourceError('TeX SVG reference nesting limit exceeded')
        kind = tag(element)
        if kind == 'defs': return
        style = element.get('style', '')
        properties = {k:v for k,v in element.attrib.items() if k in
            ('fill','fill-opacity','fill-rule','stroke','stroke-width','stroke-linecap',
             'stroke-linejoin','stroke-opacity','stroke-miterlimit')}
        # The caller controls a single Artist color/opacity. Colored graphics,
        # clipping and strokes are outside the monochrome fragment contract.
        for part in filter(None, style.split(';')):
            key, value = map(str.strip, part.split(':', 1))
            properties[key] = value
        black = lambda value: re.sub(r'\s+', '', value) in ('rgb(0%,0%,0%)','black','#000000')
        for key,value in properties.items():
            permitted = (key in ('fill','stroke') and (value=='none' or black(value)) or
                         key in ('fill-opacity','stroke-opacity') and value=='1' or
                         key=='fill-rule' and value=='nonzero' or
                         key=='stroke-linecap' and value=='butt' or
                         key=='stroke-linejoin' and value=='miter' or
                         key=='stroke-miterlimit' and value=='10' or
                         key=='stroke-width' and 0<float(value)<100)
            if not permitted: raise TexError('TeX SVG requires monochrome glyphs and straight rules')
        matrix = element.get('transform')
        if matrix:
            match = re.fullmatch(r'matrix\(\s*([^()]*)\s*\)', matrix)
            if not match: raise TexError('Unsupported TeX SVG transform')
            values = tuple(map(float, re.split(r'[ ,]+', match[1].strip())))
            if len(values) != 6 or not all(math.isfinite(v) for v in values): raise TexError('Invalid SVG matrix')
            transform = transform.transform(Transform(*values))
        if kind == 'use':
            href = element.get('href', element.get('{http://www.w3.org/1999/xlink}href',''))
            if not href.startswith('#') or href[1:] not in ids or href in chain:
                raise TexError('Invalid, external or cyclic TeX SVG reference')
            transform = transform.translate(float(element.get('x', 0)), float(element.get('y', 0)))
            walk(ids[href[1:]], transform, (*chain, href))
        elif kind == 'path':
            pen = RecordingPen()
            parse_path(element.get('d', ''), pen)
            if properties.get('stroke','none')!='none':
                # TeX fraction/radical rules are open straight segments. Turn
                # them into filled rectangles before the affine transform so
                # every backend uses identical physical widths.
                if properties.get('fill')!='none': raise TexError('Unsupported mixed TeX path painting')
                previous = None
                for operator,points in pen.value:
                    if operator=='moveTo': previous=points[0]
                    elif operator=='lineTo' and previous is not None:
                        end=points[0];dx,dy=end[0]-previous[0],end[1]-previous[1]
                        length=math.hypot(dx,dy)
                        if length:
                            half=float(properties['stroke-width'])/2
                            nx,ny=-dy*half/length,dx*half/length
                            ring=[(previous[0]+nx,previous[1]+ny),(end[0]+nx,end[1]+ny),
                                  (end[0]-nx,end[1]-ny),(previous[0]-nx,previous[1]-ny)]
                            out.extend((command,transform.transformPoint(point))
                                       for command,point in zip(('M','L','L','L'),ring))
                            out.append(('Z',))
                            if len(out)>20000: raise TexResourceError('TeX outline command limit exceeded')
                        previous=end
                    elif operator not in ('closePath','endPath'):
                        raise TexError('Only straight TeX rules are supported')
                return
            for operator, points in pen.value:
                command = dict(moveTo='M',lineTo='L',curveTo='C',qCurveTo='Q',closePath='Z',endPath='Z').get(operator)
                if command is None or any(p is None for p in points): raise TexError('Unsupported TeX outline')
                transformed = tuple(transform.transformPoint(p) for p in points)
                if any(not math.isfinite(v) or abs(v)>1e6 for p in transformed for v in p): raise TexResourceError('TeX coordinates exceed bounds')
                out.append((command, *transformed))
                if len(out) > 20000: raise TexResourceError('TeX outline command limit exceeded')
        else:
            for child in element: walk(child, transform, chain)
    walk(root)
    return tuple(out)


def _compile_uncached(text, point_size, weight, slant, config, executable, converter, identity):
    from ._tex_process import run_tool
    try:
        import fontTools.svgLib.path
        import psutil
    except ImportError as exc: raise ImportError('Install azimlib[tex] for real TeX rendering') from exc
    if config.temp_root is not None and not config.temp_root.is_dir():
        raise TexUnavailableError('Configured TeX temporary root is unavailable')
    with tempfile.TemporaryDirectory(prefix='azimlib-tex-', dir=config.temp_root) as temporary:
        job = Path(temporary)
        (job/'fragment.tex').write_text(_document(text, point_size,
            dict(font_weight=weight,font_style=slant), config.preamble), encoding='utf8', newline='\n')
        metrics = [run_tool([executable,'-X','compile','--untrusted','--only-cached',
            '--keep-logs','--outfmt','pdf','--reruns','0','fragment.tex'], job, config, 'engine-output.log')]
        if not (job/'fragment.log').is_file() or not (job/'fragment.pdf').is_file():
            raise TexError('TeX did not produce a complete fragment')
        log = (job/'fragment.log').read_text('utf8', errors='replace')
        if 'Missing character:' in log: raise TexError('TeX font does not cover a requested character')
        pages=re.findall(r'Output written on .*?\((\d+) pages?[,)]',log)
        if pages!=['1']:raise TexError('A TeX fragment must produce exactly one page')
        found = re.findall(r'AZIMLIB-METRICS:([\d.]+)pt:([\d.]+)pt:([\d.]+)pt', log)
        if len(found) != 1: raise TexError('TeX did not report one fragment metric record')
        w, a, d = (float(value)*72/72.27 for value in found[0])
        if not all(math.isfinite(v) and 0<=v<=10000 for v in (w,a,d)):
            raise TexResourceError('TeX fragment dimensions exceed bounds')
        metrics.append(run_tool([converter,'-svg','-f','1','-l','1','fragment.pdf','fragment.svg'],
                                job, config, 'converter-output.log'))
        raw = (job/'fragment.svg').read_bytes()
        if len(raw) > 8*1024**2: raise TexResourceError('TeX SVG exceeds eight MiB')
        commands = _svg_commands(raw, w+4, a+d+4)
        # The page has a two-bp gutter. Shift to the alphabetic baseline,
        # normalize to em; renderers can then rotate/scale exactly once.
        commands = tuple((cmd[0],*((x/point_size-2/point_size,
                                   (y-2-a)/point_size) for x,y in cmd[1:])) for cmd in commands)
        notices = tuple(tuple(sorted(dict(kind='tex-font',**asdict(n)).items())) for n in config.font_notices)
        notices += (tuple(sorted(dict(kind='tex-engine',engine='Tectonic',converter='pdftocairo',
            resources_sha256=identity[2],executable_sha256=identity[0],converter_sha256=identity[1]).items())),)
        if _resources(config)!=identity[2]:
            raise TexError('TeX resources changed during compilation; prepare a stable cache')
        return TexLayout(w/point_size,a/point_size,d/point_size,commands,notices,
            hashlib.sha256(repr((text,point_size,weight,slant,config.preamble,identity,notices)).encode('utf8')).hexdigest(),
            tuple(tuple(sorted(m.items())) for m in metrics))


def _compile(*args):
    """128 entries / 16 MiB measured immutable payload; no disk output cache."""
    global _cache_bytes,_cache_hits,_cache_misses
    with _lock:
        if args in _compiled:
            _cache_hits+=1;_compiled.move_to_end(args);return _compiled[args][0]
        _cache_misses+=1
    result=_compile_uncached(*args)
    def size(value):
        return sys.getsizeof(value)+(sum(size(v) for v in value) if isinstance(value,tuple) else 0)
    weight=size(result.commands)+size(result.notices)+size(result.identity)+len(args[0].encode('utf8'))
    if weight<=16*1024**2:
        with _lock:
            old=_compiled.pop(args,None)
            if old:_cache_bytes-=old[1]
            while _compiled and (len(_compiled)>=128 or _cache_bytes+weight>16*1024**2):
                _,entry=_compiled.popitem(last=False);_cache_bytes-=entry[1]
            _compiled[args]=(result,weight);_cache_bytes+=weight
    return result


def tex_cache_info():
    """Read prepared-fragment cache counts and measured retained payload."""
    with _lock:return dict(hits=_cache_hits,misses=_cache_misses,entries=len(_compiled),
                           payload_bytes=_cache_bytes,max_entries=128,max_payload_bytes=16*1024**2)


def tex_layout(text, style):
    if isinstance(text, TexText): return text.tex_layout
    config = style.get('texconfig')
    if not isinstance(config, TexConfig): raise TexError('Real TeX requires an explicit TexConfig or tex_context')
    if not isinstance(text, str) or len(text)>4096 or '\x00' in text or '\n' in text or '\r' in text:
        raise TexError('A TeX fragment must be one line of at most 4096 characters')
    try:
        snapshots=_snapshots.get()
        snapshot=snapshots.get(config) if snapshots is not None else None
        if snapshot is None:
            executable,a=_tool(config.executable);converter,b=_tool(config.converter)
            identity=(a,b,_resources(config));snapshot=(executable,converter,identity)
            if snapshots is not None:snapshots[config]=snapshot
        executable,converter,identity=snapshot
        result = _compile(text, style.get('font_size',12)*72/100, style.get('font_weight','normal'),
                          style.get('font_style','normal'), config, executable, converter, identity)
        return result
    except TexError:
        if config.fallback != 'basic': raise
        import warnings
        warnings.warn('Real TeX unavailable/failed; explicitly requested basic fallback is in use', RuntimeWarning, stacklevel=2)
        return None


def text_commands(item):
    from .typography import text_baseline_offset
    layout = tex_layout(item.text, item.style); size = item.style.get('font_size',12)
    left = -{'start':0,'middle':.5,'end':1}[item.style.get('anchor','start')]*layout.width*size
    base = text_baseline_offset(item.text,item.style)
    angle = math.radians(item.style.get('rotation',0)); c,s = math.cos(angle),math.sin(angle)
    for cmd in layout.commands:
        points = []
        for x,y in cmd[1:]:
            dx,dy = left+x*size,base+y*size
            points.append((item.x+dx*c-dy*s,item.y+dx*s+dy*c))
        yield (cmd[0],*points)


def clear_tex_cache():
    """Discard prepared fragments and force rehashing of tools/resources."""
    global _cache_bytes,_cache_hits,_cache_misses
    with _lock:
        _fingerprints.clear();_compiled.clear()
        _cache_bytes=_cache_hits=_cache_misses=0
