"""Optional complex text: ICU itemization, HarfBuzz shaping, own composition.

Runs and glyph positions are immutable, in em units, with logical code-point
clusters. Renderers consume the same outlines; they never shape independently.
No fonts are discovered, downloaded, substituted or uploaded automatically.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, replace
from functools import lru_cache
from functools import wraps
import hashlib
import io
import math
from pathlib import Path
import re
from threading import RLock
import unicodedata
from urllib.parse import urlsplit


class TextEngineError(ValueError):pass
class MissingGlyphError(TextEngineError):pass
class FontPermissionError(TextEngineError):pass

_defaults = ContextVar('azimlib_text_defaults', default={})
_lock = RLock()
_fonts = {}; _families = {}; _registered_bytes = 0
MAX_TEXT = 4096
MAX_FONT_BYTES = 32*1024*1024
MAX_REGISTRY_BYTES = 128*1024*1024


def text_options(options):
    """Validate the public opt-in controls without loading optional engines."""
    result=dict(options)
    if result.get('textengine','basic') not in ('basic','harfbuzz','tex'):
        raise TextEngineError('textengine must be basic, harfbuzz or tex')
    if result.get('direction','auto') not in ('auto','ltr','rtl'):
        raise TextEngineError('direction must be auto, ltr or rtl')
    language=result.get('language','und')
    if not isinstance(language,str) or not re.fullmatch(r'[A-Za-z]{2,8}(?:-[A-Za-z0-9]{1,8})*',language):
        raise TextEngineError('language must be a BCP-47-style language tag')
    fallback=result.get('fontfallback',())
    if isinstance(fallback,str):fallback=(fallback,)
    if not isinstance(fallback,(tuple,list)) or any(not isinstance(f,str) or not f.strip() for f in fallback):
        raise TextEngineError('fontfallback must contain registered family names')
    if len(fallback)>16:raise TextEngineError('At most 16 fallback families are accepted')
    if 'fontfallback' in result:result['fontfallback']=tuple(fallback)
    features=result.get('fontfeatures',())
    if isinstance(features,dict):features=tuple(sorted(features.items()))
    try:
        if len(features)>64 or any(not re.fullmatch(r'[A-Za-z0-9]{4}',tag) or not isinstance(value,(bool,int)) or not 0<=value<=65535 for tag,value in features):
            raise TextEngineError('fontfeatures requires four-character OpenType tags and nonnegative integer values')
    except (TypeError,ValueError) as exc:raise TextEngineError('Invalid fontfeatures') from exc
    if 'fontfeatures' in result:result['fontfeatures']=tuple(features)
    if result.get('textengine')=='basic' and any(result.get(k) not in (None,(),{},'auto','und') for k in ('fontfallback','fontfeatures','direction','language')):
        raise TextEngineError('Direction, language, fallback and features require textengine="harfbuzz"')
    if result.get('textengine')=='tex':
        from .tex import TexConfig
        if not isinstance(result.get('texconfig'),TexConfig):raise TextEngineError('textengine="tex" requires texconfig=TexConfig(...)')
        if any(result.get(k) not in (None,(),{},'auto','und') for k in ('fontfallback','fontfeatures','direction','language')):
            raise TextEngineError('HarfBuzz controls do not apply to the TeX engine')
    elif 'texconfig' in result:raise TextEngineError('texconfig requires textengine="tex"')
    return result


@contextmanager
def text_context(*, engine='harfbuzz', direction='auto', language='und', fallback=(), features=()):
    """Defaults captured by newly composed Artists; reset on exit, thread-local.

    Existing primitives retain their controls after this context exits.
    This does not change the published version or legacy typography defaults.
    """
    options=text_options(dict(textengine=engine,direction=direction,language=language,fontfallback=fallback,fontfeatures=features))
    token=_defaults.set(options)
    try:yield
    finally:_defaults.reset(token)


def scene_options(style):
    keys=('textengine','direction','language','fontfallback','fontfeatures','texconfig')
    values=dict(_defaults.get());values.update({k:style[k] for k in keys if k in style})
    if style.get('textengine') in ('basic','harfbuzz'):values.pop('texconfig',None)
    if style.get('textengine')=='tex':
        for key in ('direction','language','fontfallback','fontfeatures'):
            if key not in style:values.pop(key,None)
    return text_options(values) if values else {}


def is_shaped(style):return style.get('textengine')=='harfbuzz'


def current_defaults():return dict(_defaults.get())


def figure_defaults(method):
    """Recompose auto-generated components with the figure's captured controls."""
    @wraps(method)
    def compose(figure,*args,**kwargs):
        values={**getattr(figure,'_text_defaults',{}),**_defaults.get()}
        token=_defaults.set(values)
        try:
            from .tex import composition_resources
            with composition_resources():return method(figure,*args,**kwargs)
        finally:_defaults.reset(token)
    return compose


@dataclass(frozen=True)
class FontRecord:
    family:str
    sha256:str
    source:str
    license_id:str
    license_text:str
    copyright:str
    coverage:tuple

    @property
    def key(self):
        return hashlib.sha256(repr((self.sha256,self.family,self.source,self.license_id,self.license_text,self.copyright)).encode('utf8')).hexdigest()

    def notice(self):
        return dict(kind='font',font_id=self.key,family=self.family,sha256=self.sha256,source=self.source,
                    license=self.license_id,license_text=self.license_text,copyright=self.copyright)


def _load_font(raw, family, source, license_id, license_text):
    try:
        from fontTools.ttLib import TTFont
    except ImportError as exc:raise ImportError('Install azimlib[text] for complex typography') from exc
    if not 0<len(raw)<=MAX_FONT_BYTES:raise TextEngineError('Font exceeds the 32 MiB limit')
    if raw[:4] not in (b'\x00\x01\x00\x00',b'OTTO',b'true'):
        raise TextEngineError('Use a standalone static TTF or OTF font; collections/WOFF are unsupported')
    font=TTFont(io.BytesIO(raw),lazy=False)
    if 'fvar' in font:raise TextEngineError('Instantiate variable fonts explicitly before registration')
    if not any(tag in font for tag in ('glyf','CFF ')):
        raise TextEngineError('Only monochrome TrueType/CFF outlines are supported')
    if any(tag in font for tag in ('COLR','SVG ','CBDT','sbix')):
        raise TextEngineError('Color/bitmap fonts are outside the outline renderer contract')
    flags=getattr(font.get('OS/2'),'fsType',0)
    if flags & (0x0002|0x0200):raise FontPermissionError('Font embedding restrictions prohibit this export path')
    cmap=font.getBestCmap() or {}
    copyright='; '.join(sorted({n.toUnicode() for n in font['name'].names if n.nameID==0})) if 'name' in font else ''
    record=FontRecord(family,hashlib.sha256(raw).hexdigest(),source,license_id,license_text,copyright,tuple(sorted(cmap)))
    return record,dict(raw=raw,font=font,cmap=cmap,order=font.getGlyphOrder(),units=font['head'].unitsPerEm,
                       ascent=font['hhea'].ascent,font_descent=font['hhea'].descent)


def register_font(path, *, family, source, license_id, license_text, allow_outlines=False):
    """Register an immutable font snapshot with explicit redistribution provenance.

    allow_outlines is the caller's confirmation of permission, not a legal
    inference from a filename, SPDX label or OpenType embedding flag.
    Local filesystem paths are never included in exported notices.
    """
    global _registered_bytes
    if not isinstance(family,str) or not re.fullmatch(r'[\w .-]{1,80}',family):raise TextEngineError('Invalid family name')
    if family.lower().replace(' ','') in ('dejavusans','sans-serif'):raise TextEngineError('Bundled family names are reserved')
    if not isinstance(source,str):raise TextEngineError('A public HTTPS source URL is required')
    url=urlsplit(source)
    if url.scheme!='https' or not url.hostname or url.username or url.password or url.query or url.fragment or '\\' in source:
        raise TextEngineError('Use a public HTTPS source without credentials, query parameters or fragment')
    if not isinstance(license_id,str) or not re.fullmatch(r'[A-Za-z0-9.+-]{1,80}',license_id):raise TextEngineError('A license identifier is required')
    if not isinstance(license_text,str) or not 30<=len(license_text)<=1024*1024:raise TextEngineError('Supply the complete font license text')
    if allow_outlines is not True:raise FontPermissionError('Confirm permission for outline exports with allow_outlines=True')
    path=Path(path)
    if path.stat().st_size>MAX_FONT_BYTES:raise TextEngineError('Font exceeds the 32 MiB limit')
    with path.open('rb') as stream:raw=stream.read(MAX_FONT_BYTES+1)
    record,face=_load_font(raw,family,source,license_id,license_text)
    with _lock:
        if family in _families:
            old=_fonts[_families[family]][0]
            if old!=record:raise TextEngineError('A registered family cannot be replaced')
            return old
        if _registered_bytes+len(raw)>MAX_REGISTRY_BYTES:raise TextEngineError('Font registry exceeds 128 MiB')
        _families[family]=record.key;_fonts[record.key]=(record,face);_registered_bytes+=len(raw)
    return record


def _face(family, style):
    from .typography import font_path,FONTS
    if family.lower().replace(' ','') in ('dejavusans','sans-serif'):
        path=font_path(style); key=path.name
        with _lock:
            if key not in _families:
                record,face=_load_font(path.read_bytes(),'DejaVu Sans','https://dejavu-fonts.github.io/',
                                      'LicenseRef-DejaVu',(FONTS/'LICENSE_DEJAVU').read_text('utf8'))
                _families[key]=record.key;_fonts[record.key]=(record,face)
            return _fonts[_families[key]]
    with _lock:
        if family not in _families:raise TextEngineError('Unregistered font family: '+family)
        return _fonts[_families[family]]


@dataclass(frozen=True)
class Glyph:
    font:str
    glyph:int
    start:int
    end:int
    x:float
    y:float
    advance:float
    outline:tuple
    ink:tuple | None


@dataclass(frozen=True)
class TextRun:
    start:int
    end:int
    direction:str
    script:str
    font:str
    glyph_start:int
    glyph_end:int


@dataclass(frozen=True)
class ShapedLine:
    text:str
    glyphs:tuple
    runs:tuple
    width:float
    ascent:float
    descent:float
    ink:tuple
    engines:tuple
    notices:tuple
    signature:tuple


def _ignored(char):
    return unicodedata.category(char)=='Cf' or ord(char) in range(0xfe00,0xfe10) or ord(char) in range(0xe0100,0xe01f0)


def shape_text(text, style):
    options=text_options({k:style[k] for k in ('textengine','direction','language','fontfallback','fontfeatures') if k in style})
    signature=(style.get('font_family','DejaVu Sans'),str(style.get('font_weight','normal')),style.get('font_style','normal'),
               options.get('direction','auto'),options.get('language','und'),tuple(options.get('fontfallback',())),tuple(options.get('fontfeatures',())))
    if isinstance(text,ClusterText) and text.layout.signature==signature:return text.layout
    text=str(text)
    if len(text)>MAX_TEXT:raise TextEngineError('A shaped line is limited to 4096 code points')
    if any(c in text for c in '\r\n\t\u2028\u2029') or any(unicodedata.category(c)=='Cs' for c in text):
        raise TextEngineError('Shape one Unicode line at a time; tabs, paragraph separators and surrogates are unsupported')
    return _shape(text,*signature)


@lru_cache(maxsize=128)
def _shape(text,family,weight,slant,direction,language,fallback,features):
    try:import uharfbuzz as hb
    except ImportError as exc:raise ImportError('Install azimlib[text] for HarfBuzz shaping') from exc
    from ._unicode_icu import graphemes,visual_runs,script,unicode_version,unicode_data_version
    style=dict(font_family=family,font_weight=weight,font_style=slant)
    faces=[_face(f,dict(style,font_family=f)) for f in (family,*fallback)]
    spans=[]
    for start,end in graphemes(text):
        chars=text[start:end]
        face=next((f for f in faces if all(ord(c) in f[1]['cmap'] or _ignored(c) for c in chars)),None)
        if face is None:
            missing=','.join(f'U+{ord(c):04X}' for c in chars if not _ignored(c))
            raise MissingGlyphError('No configured font covers grapheme '+missing)
        tag=next((script(c) for c in chars if script(c) not in ('Zyyy','Zinh','Zzzz')),'Zyyy')
        spans.append((start,end,face,tag))
    glyphs=[]; runs=[]; cursor=0.; ascent=descent=0.
    for lo,hi,rtl in visual_runs(text,direction):
        parts=[];previous=None
        # Resolve Common/Inherited script inside each directional run, so
        # spaces/marks preserve contextual shaping instead of splitting words.
        selected=[(max(a,lo),min(b,hi),f,s) for a,b,f,s in spans if a<hi and b>lo]
        strong=next((s for a,b,f,s in selected if s!='Zyyy'),'Latn')
        for a,b,face,tag in selected:
            if tag=='Zyyy':tag=previous or strong
            else:previous=tag
            key=(face[0].key,tag)
            if parts and parts[-1][2]==key:parts[-1]=(parts[-1][0],b,key,face)
            else:parts.append((a,b,key,face))
        if rtl=='rtl':parts.reverse()
        for a,b,(font_id,tag),(record,face) in parts:
            units=face['units'];font=hb.Font(hb.Face(face['raw']));font.scale=(units,units);hb.ot_font_set_funcs(font)
            buf=hb.Buffer();buf.add_codepoints([ord(c) for c in text],a,b-a)
            buf.direction=rtl;buf.script=tag;buf.language=language
            hb.shape(font,buf,dict(features))
            infos,positions=buf.glyph_infos,buf.glyph_positions
            ends=sorted(set(info.cluster for info in infos)|{b})
            end_by_start=dict(zip(ends,ends[1:]));first=len(glyphs)
            for info,pos in zip(infos,positions):
                if info.codepoint==0 and not all(_ignored(c) for c in text[info.cluster:end_by_start.get(info.cluster,b)]):
                    raise MissingGlyphError('The shaping engine produced a missing glyph')
                glyphs.append(Glyph(font_id,info.codepoint,info.cluster,end_by_start.get(info.cluster,b),
                                    cursor+pos.x_offset/units,-pos.y_offset/units,pos.x_advance/units,
                                    glyph_commands(font_id,info.codepoint),glyph_bounds(font_id,info.codepoint)))
                cursor+=pos.x_advance/units
            if len(glyphs)>MAX_TEXT*4:raise TextEngineError('Shaped glyph count exceeds resource limit')
            runs.append(TextRun(a,b,rtl,tag,font_id,first,len(glyphs)))
            ascent=max(ascent,face['ascent']/units);descent=max(descent,-face['font_descent']/units)
    if not spans:
        face=faces[0][1];ascent=face['ascent']/face['units'];descent=-face['font_descent']/face['units']
    boxes=[]
    for g in glyphs:
        bounds=g.ink
        if bounds:
            x0,y0,x1,y1=bounds;boxes.append((g.x+x0,g.y-y1,g.x+x1,g.y-y0))
    ink=(min(v[0] for v in boxes),min(v[1] for v in boxes),max(v[2] for v in boxes),max(v[3] for v in boxes)) if boxes else (0.,0.,0.,0.)
    notices=tuple(tuple(sorted(_fonts[key][0].notice().items())) for key in sorted({g.font for g in glyphs}))
    return ShapedLine(text,tuple(glyphs),tuple(runs),cursor,max(ascent,-ink[1]),max(descent,ink[3]),ink,
                      (('Bidi','Azimlib-UAX9-r51'),('HarfBuzz',hb.version_string()),('ICU',unicode_version()),('Unicode',unicode_data_version())),notices,
                      (family,weight,slant,direction,language,fallback,features))


@lru_cache(maxsize=2048)
def glyph_bounds(font_id,glyph):
    from fontTools.pens.boundsPen import BoundsPen
    with _lock:
        record,face=_fonts[font_id];gs=face['font'].getGlyphSet();pen=BoundsPen(gs)
        gs[face['order'][glyph]].draw(pen)
        return tuple(v/face['units'] for v in pen.bounds) if pen.bounds else None


@lru_cache(maxsize=2048)
def glyph_commands(font_id,glyph):
    from fontTools.pens.basePen import BasePen
    class Pen(BasePen):
        def __init__(self,gs):super().__init__(gs);self.commands=[]
        def _moveTo(self,p):self.commands.append(('M',p))
        def _lineTo(self,p):self.commands.append(('L',p))
        def _curveToOne(self,a,b,c):self.commands.append(('C',a,b,c))
        def _qCurveToOne(self,a,b):self.commands.append(('Q',a,b))
        def _closePath(self):self.commands.append(('Z',))
        def _endPath(self):self.commands.append(('Z',))
    with _lock:
        record,face=_fonts[font_id];gs=face['font'].getGlyphSet();pen=Pen(gs)
        gs[face['order'][glyph]].draw(pen)
        if len(pen.commands)>16384:raise TextEngineError('Glyph outline exceeds resource limit')
        return tuple((cmd[0],*(tuple(v/face['units'] for v in p) for p in cmd[1:])) for cmd in pen.commands)


def text_commands(item):
    from .typography import text_baseline_offset
    layout=shape_text(item.text,item.style);size=item.style.get('font_size',12)
    left=-{'start':0,'middle':.5,'end':1}[item.style.get('anchor','start')]*layout.width*size
    base=text_baseline_offset(item.text,item.style)
    angle=math.radians(item.style.get('rotation',0));c,s=math.cos(angle),math.sin(angle)
    for g in layout.glyphs:
        for cmd in g.outline:
            points=[]
            for px,py in cmd[1:]:
                x=left+(g.x+px)*size;y=base+(g.y-py)*size
                points.append((item.x+x*c-y*s,item.y+x*s+y*c))
            yield (cmd[0],*points)


def with_text_notices(scene):
    """Return a shallow scene view with deduplicated font provenance; no paths."""
    from .scene import Text
    notices=list(scene._material_notices);seen={n.get('font_id') for n in notices if n.get('kind')=='font'}
    for item in scene.items:
        if isinstance(item,Text) and item.style.get('textengine')=='tex':
            from .tex import tex_layout
            for pairs in tex_layout(item.text,item.style).notices:
                notice=dict(pairs)
                if notice not in notices:notices.append(notice)
        if isinstance(item,Text) and is_shaped(item.style):
            for pairs in shape_text(item.text,item.style).notices:
                notice=dict(pairs)
                if notice['font_id'] not in seen:
                    notices.append(notice);seen.add(notice['font_id'])
    return replace(scene,_material_notices=notices) if notices!=scene._material_notices else scene


class ClusterText(str):
    """Internal curved-label slice; retains whole-word shaping and mark offsets."""
    def __new__(cls,text,layout):
        value=super().__new__(cls,text);value.layout=layout;return value
    def split(self,sep=None,maxsplit=-1):
        return [self] if sep=='\n' and '\n' not in self else super().split(sep,maxsplit)
    def replace(self,old,new,count=-1):
        return self if old not in self else super().replace(old,new,count)
    def __reduce__(self):return ClusterText,(str(self),self.layout)


def cluster_units(text,style):
    layout=shape_text(text,style);groups=[]
    for g in layout.glyphs:
        if groups and groups[-1][0]==(g.font,g.start,g.end):groups[-1][1].append(g)
        else:groups.append(((g.font,g.start,g.end),[g]))
    cursor=0.
    for (_,start,end),glyphs in groups:
        width=sum(g.advance for g in glyphs)
        subset=tuple(replace(g,x=g.x-cursor) for g in glyphs)
        boxes=[]
        for g in subset:
            bounds=g.ink
            if bounds:
                x0,y0,x1,y1=bounds;boxes.append((g.x+x0,g.y-y1,g.x+x1,g.y-y0))
        ink=(min(v[0] for v in boxes),min(v[1] for v in boxes),max(v[2] for v in boxes),max(v[3] for v in boxes)) if boxes else (0.,0.,0.,0.)
        sliced=replace(layout,text=layout.text[start:end],glyphs=subset,runs=(),width=width,ink=ink)
        yield ClusterText(sliced.text,sliced),width*style.get('font_size',12),0.
        cursor+=width


def cache_token(text,style):
    if style.get('textengine')=='tex':
        from .tex import tex_layout
        return tex_layout(text,style).identity
    if not is_shaped(style):return None
    line=shape_text(text,style)
    return line.engines,tuple((g.font,g.glyph,g.start,g.end,g.x,g.y,g.advance) for g in line.glyphs)
