"""Immutable bounded cartographic symbols; own geometry and strict SVG subset."""
from dataclasses import dataclass
import hashlib,io,math,re,xml.etree.ElementTree as ET
from pathlib import Path as FilePath
from .geometry import _number
from .colors import to_rgba
from .path import Path

@dataclass(frozen=True)
class AssetSource:
    origin:str
    license:str
    credit:str
    sha256:str=''
    def __post_init__(self):
        if any(not isinstance(v,str) or not v.strip() for v in (self.origin,self.license,self.credit)):raise ValueError('Declare asset origin, license and credit')
        if not isinstance(self.sha256,str):raise ValueError('Asset SHA must be a string')
        if self.sha256 and not re.fullmatch('[a-f0-9]{64}',self.sha256):raise ValueError('Invalid asset SHA-256')

@dataclass(frozen=True)
class SymbolPart:
    paths:tuple
    closed:bool=True
    style:tuple=()
    def __post_init__(self):
        paths=tuple(tuple(tuple(_number(v) for v in p) for p in ring) for ring in self.paths)
        if not paths or any(len(p)!=2 for r in paths for p in r) or sum(map(len,paths))>16384:raise ValueError('Invalid symbol paths/budget')
        styles=tuple(tuple(p) for p in self.style)
        if any(len(p)!=2 for p in styles) or len(dict(styles))!=len(styles):raise ValueError('Invalid symbol style')
        from .styles import style_dict
        style_dict(dict(styles))
        object.__setattr__(self,'paths',paths);object.__setattr__(self,'style',styles)

@dataclass(frozen=True)
class SymbolDefinition:
    name:str
    viewbox:tuple
    parts:tuple
    source:AssetSource
    kind:str='vector'
    raster:tuple | None=None
    def __post_init__(self):
        b=tuple(_number(v) for v in self.viewbox)
        if len(b)!=4 or min(b[2:])<=0 or not isinstance(self.source,AssetSource):raise ValueError('Require positive viewBox and provenance')
        parts=tuple(self.parts)
        if not isinstance(self.name,str) or not self.name or not parts or len(parts)>4096 or any(not isinstance(p,SymbolPart) for p in parts) or sum(len(r) for p in parts for r in p.paths)>16384:raise ValueError('Symbol complexity exceeds limits')
        if self.kind not in ('vector','svg','png'):raise ValueError('Unknown symbol kind')
        if self.kind=='png':
            if self.raster is None or len(self.raster)!=3:raise ValueError('PNG definition needs immutable pixel data')
            w,h,data=self.raster
            if type(w) is not int or type(h) is not int or not 0<w<=128 or not 0<h<=128 or not isinstance(data,bytes) or len(data)!=w*h*4:raise ValueError('PNG definition pixel budget exceeded')
            object.__setattr__(self,'raster',(w,h,data))
        elif self.raster is not None:raise ValueError('Vector symbol cannot carry a hidden raster')
        object.__setattr__(self,'viewbox',b);object.__setattr__(self,'parts',parts)
    @classmethod
    def from_paths(cls,name,paths,*,source,viewbox=(0,0,1,1),closed=True):
        return cls(name,viewbox,(SymbolPart(paths,closed),),source)
    @classmethod
    def from_svg(cls,path,*,source):
        raw=_read(path,source,262144)
        return parse_svg(raw,name=FilePath(path).stem,source=AssetSource(source.origin,source.license,source.credit,hashlib.sha256(raw).hexdigest()))
    @classmethod
    def from_png(cls,path,*,source):
        raw=_read(path,source,1048576)
        import struct
        if not raw.startswith(b'\x89PNG\r\n\x1a\n') or len(raw)<33:raise ValueError('Malformed PNG header')
        w,h=struct.unpack('>II',raw[16:24])
        if not 0<w<=128 or not 0<h<=128:raise ValueError('PNG limited to 128x128')
        from PIL import Image
        try:
            with Image.open(io.BytesIO(raw)) as image:
                if image.format!='PNG' or getattr(image,'n_frames',1)!=1:raise ValueError('Require a single-frame PNG')
                with image.convert('RGBA') as rgba:width,height=rgba.size;pixels=rgba.tobytes()
        except OSError as ex:raise ValueError('Malformed PNG') from ex
        if not any(pixels[3::4]):raise ValueError('PNG contains no visible pixels')
        part=SymbolPart((((0,0),(width,0),(width,height),(0,height)),))
        return cls(FilePath(path).stem,(0,0,width,height),(part,),AssetSource(source.origin,source.license,source.credit,hashlib.sha256(raw).hexdigest()),'png',(width,height,pixels))

def _read(path,source,limit):
    if not isinstance(source,AssetSource):raise TypeError('Declare AssetSource before reading')
    p=FilePath(path)
    if p.stat().st_size>limit:raise ValueError('Asset file budget exceeded')
    with p.open('rb') as f:raw=f.read(limit+1)
    if len(raw)>limit or source.sha256 and hashlib.sha256(raw).hexdigest()!=source.sha256:raise ValueError('Asset budget/hash mismatch')
    return raw

_NUM=r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?'
def _numbers(s):
    if len(s)>262144 or re.sub(_NUM+'|[ ,\t\n\r]','',s):raise ValueError('Malformed numeric SVG data')
    v=tuple(float(x) for x in re.findall(_NUM,s))
    if any(not math.isfinite(x) or abs(x)>1e7 for x in v):raise ValueError('SVG coordinate budget exceeded')
    return v

def _svg_path(s):
    tokens=re.findall(_NUM+'|[A-Za-z]',s)
    if re.sub(_NUM+'|[A-Za-z]|[ ,\t\r\n]','',s):raise ValueError('Invalid SVG path syntax')
    vertices=[];codes=[];i=0;command=None;current=(0.,0.);start=current
    counts={'M':2,'L':2,'H':1,'V':1,'Q':4,'C':6,'S':4,'T':2,'A':7,'Z':0}
    previous=None;control=None
    while i<len(tokens):
        if tokens[i].isalpha():command=tokens[i];i+=1
        if command is None or command.upper() not in counts:raise ValueError('SVG supports M/L/H/V/Q/C/S/T/A/Z only')
        key=command.upper();n=counts[key];relative=command.islower()
        if key=='Z':
            vertices.append(start);codes.append(Path.CLOSEPOLY);current=start;command=None;previous='Z';control=None;continue
        if key=='A':
            # SVG flags may be adjacent to each other or the following coordinate.
            for flag in (i+3,i+4):
                if flag<len(tokens) and len(tokens[flag])>1 and tokens[flag][0] in '01':tokens[flag:flag+1]=[tokens[flag][0],tokens[flag][1:]]
        if i+n>len(tokens) or any(t.isalpha() for t in tokens[i:i+n]):raise ValueError('Incomplete SVG path')
        values=[float(v) for v in tokens[i:i+n]];i+=n
        if any(not math.isfinite(v) or abs(v)>1e7 for v in values):raise ValueError('Invalid SVG coordinate')
        if key=='H':values=[values[0]+current[0] if relative else values[0],current[1]];key='L';relative=False
        if key=='V':values=[current[0],values[0]+current[1] if relative else values[0]];key='L';relative=False
        if key=='A':
            rx,ry,angle,large,sweep,x,y=values
            if large not in (0,1) or sweep not in (0,1):raise ValueError('SVG arc flags must be 0 or 1')
            end=(x+current[0],y+current[1]) if relative else (x,y)
            for point in _arc_points(current,end,rx,ry,angle,large,sweep):vertices.append(point);codes.append(Path.LINETO)
            current=end;previous='A';control=None
            if len(vertices)>4096:raise ValueError('SVG arc vertex budget exceeded')
            continue
        points=[tuple(values[j:j+2]) for j in range(0,len(values),2)]
        if relative:points=[(x+current[0],y+current[1]) for x,y in points]
        if key in ('S','T'):
            reflected=tuple(2*a-b for a,b in zip(current,control)) if control is not None and previous in (('C','S') if key=='S' else ('Q','T')) else current
            points=[reflected,*points];key='C' if key=='S' else 'Q'
        previous=key;control=points[-2] if key in ('C','Q') else None
        if key=='M':start=points[0];code=Path.MOVETO
        else:code={'L':Path.LINETO,'Q':Path.CURVE3,'C':Path.CURVE4}[key]
        vertices.extend(points);codes.extend([code]*len(points));current=points[-1]
        if command.upper()=='M':command='l' if relative else 'L'
        if len(vertices)>4096:raise ValueError('SVG path budget exceeded')
    if not vertices or codes[0]!=Path.MOVETO:raise ValueError('SVG path must begin with move')
    return Path(vertices,codes).to_polylines(steps=24)

def _arc_points(start,end,rx,ry,angle,large,sweep):
    """Own bounded endpoint-to-center geometry from SVG2 Appendix B equations.

    Mathematical SVG convention, not third-party implementation code.
    """
    if start==end:return ()
    rx,ry=abs(rx),abs(ry)
    if not rx or not ry:return (end,)
    phi=math.radians(angle%360);c,s=math.cos(phi),math.sin(phi)
    dx,dy=((a-b)/2 for a,b in zip(start,end));x=c*dx+s*dy;y=-s*dx+c*dy
    factor=max(1.,math.sqrt((x/rx)**2+(y/ry)**2));rx*=factor;ry*=factor
    denominator=(rx*y)**2+(ry*x)**2
    coef=math.sqrt(max(0.,((rx*ry)**2-denominator)/denominator)) if denominator else 0.
    if large==sweep:coef=-coef
    cx,cy=coef*rx*y/ry,-coef*ry*x/rx
    ox=c*cx-s*cy+(start[0]+end[0])/2;oy=s*cx+c*cy+(start[1]+end[1])/2
    first=math.atan2((y-cy)/ry,(x-cx)/rx);last=math.atan2((-y-cy)/ry,(-x-cx)/rx);span=(last-first)%math.tau
    if not sweep:span=span-math.tau if span else 0.
    n=max(2,math.ceil(abs(span)*24/math.pi));result=[]
    for i in range(1,n+1):
        theta=first+span*i/n;u,v=rx*math.cos(theta),ry*math.sin(theta);result.append((ox+c*u-s*v,oy+s*u+c*v))
    result[-1]=end;return tuple(result)

def _transform(s):
    result=(1.,0.,0.,1.,0.,0.)
    if not s:return result
    groups=re.findall(r'(matrix|translate|scale|rotate)\s*\(([^()]*)\)',s)
    residue=re.sub(r'(matrix|translate|scale|rotate)\s*\([^()]*\)|[ ,\t\r\n]','',s)
    if residue or len(groups)>16:raise ValueError('Unsupported SVG transform')
    for name,raw in groups:
        v=_numbers(raw)
        if name=='matrix' and len(v)==6:q=v
        elif name=='translate' and len(v) in (1,2):q=(1,0,0,1,v[0],v[1] if len(v)==2 else 0)
        elif name=='scale' and len(v) in (1,2):q=(v[0],0,0,v[-1],0,0)
        elif name=='rotate' and len(v)==1:
            a=math.radians(v[0]);q=(math.cos(a),math.sin(a),-math.sin(a),math.cos(a),0,0)
        else:raise ValueError('Invalid SVG transform arguments')
        result=_multiply(result,q)
    return result

def _multiply(a,b):
    x,y,z,w,u,v=a;A,B,C,D,E,F=b
    return (x*A+z*B,y*A+w*B,x*C+z*D,y*C+w*D,x*E+z*F+u,y*E+w*F+v)

def parse_svg(raw,*,name,source):
    if not isinstance(raw,bytes) or b'\0' in raw or len(raw)>262144 or any(t in raw.lower() for t in (b'<!doctype',b'<!entity',b'<?xml-stylesheet')):raise ValueError('Unsafe/oversized SVG')
    try:raw.decode('utf-8-sig')
    except UnicodeDecodeError as ex:raise ValueError('SVG must be UTF-8') from ex
    try:root=ET.fromstring(raw)
    except ET.ParseError as ex:raise ValueError('Malformed SVG') from ex
    if root.tag not in ('svg','{http://www.w3.org/2000/svg}svg'):raise ValueError('Require SVG root')
    view=_numbers(root.attrib.get('viewBox',''))
    if len(view)!=4 or min(view[2:])<=0:raise ValueError('Explicit positive SVG viewBox required')
    parts=[];nodes=0
    paint={'fill':'facecolor','stroke':'edgecolor','stroke-width':'linewidth','opacity':'alpha','fill-opacity':'fill_alpha','stroke-opacity':'edge_alpha','stroke-linecap':'linecap','stroke-linejoin':'linejoin'}
    def visit(el,parent_style,matrix,depth,evenodd=False):
        nonlocal nodes
        nodes+=1
        if nodes>256 or depth>8:raise ValueError('SVG node/depth budget exceeded')
        tag=el.tag.removeprefix('{http://www.w3.org/2000/svg}')
        allowed={'svg':{'viewBox','width','height','version','preserveAspectRatio'},'g':set(),'path':{'d'},'rect':{'x','y','width','height','rx','ry'},'circle':{'cx','cy','r'},'ellipse':{'cx','cy','rx','ry'},'line':{'x1','y1','x2','y2'},'polyline':{'points'},'polygon':{'points'}}
        if tag not in allowed or set(el.attrib)-(allowed[tag]|set(paint)|{'style','transform','id','fill-rule'}):raise ValueError('Unsupported SVG element/attribute: '+tag)
        if (el.text and el.text.strip()) or el.tail and el.tail.strip():raise ValueError('SVG text content is not supported')
        attrs=dict(el.attrib)
        if 'style' in attrs:
            for declaration in attrs.pop('style').split(';'):
                if declaration.strip():
                    pair=declaration.split(':')
                    if len(pair)!=2 or pair[0].strip() not in set(paint)|{'fill-rule'}:raise ValueError('Unsupported SVG CSS')
                    attrs[pair[0].strip()]=pair[1].strip()
        evenodd=evenodd or attrs.get('fill-rule')=='evenodd'
        if attrs.get('fill-rule','evenodd')!='evenodd':raise ValueError('SVG subset uses evenodd fill only')
        if 'preserveAspectRatio' in attrs and attrs['preserveAspectRatio'] not in ('xMidYMid meet',):raise ValueError('Only aspect-preserving SVG supported')
        style=dict(parent_style)
        for k,dest in paint.items():
            if k in attrs:
                value=attrs[k]
                if k in ('fill','stroke'):
                    if value!='currentColor':to_rgba(value)
                    style[dest]=value
                elif dest in ('linecap','linejoin'):style[dest]=value
                else:
                    vals=_numbers(value)
                    if len(vals)!=1:raise ValueError('Invalid SVG paint number')
                    if k=='opacity' and tag in ('svg','g') and vals[0]!=1:raise ValueError('SVG group compositing opacity requires offscreen semantics; apply alpha on the Artist instead')
                    style[dest]=vals[0]
        from .styles import style_dict
        style_dict(style)
        matrix=_multiply(matrix,_transform(attrs.get('transform','')))
        def num(key,default=0):
            v=_numbers(attrs.get(key,str(default)))
            if len(v)!=1:raise ValueError('SVG length must be numeric user units')
            return v[0]
        shapes=[]
        if tag=='path':shapes=list(_svg_path(attrs.get('d','')))
        elif tag in ('polygon','polyline'):
            v=_numbers(attrs.get('points',''))
            if len(v)<4 or len(v)%2:raise ValueError('Invalid polygon/polyline')
            shapes=[(tuple(zip(v[::2],v[1::2])),tag=='polygon')]
        elif tag=='rect':
            x,y,w,h=num('x'),num('y'),num('width'),num('height')
            if min(w,h)<=0:raise ValueError('Invalid SVG rect')
            rx=num('rx',num('ry',0));ry=num('ry',rx)
            if min(rx,ry)<0:raise ValueError('Invalid SVG corner radius')
            rx,ry=min(rx,w/2),min(ry,h/2)
            if rx and ry:
                points=[]
                for cx,cy,angle in ((x+w-rx,y+ry,-90),(x+w-rx,y+h-ry,0),(x+rx,y+h-ry,90),(x+rx,y+ry,180)):
                    points.extend((cx+rx*math.cos(math.radians(angle+90*i/12)),cy+ry*math.sin(math.radians(angle+90*i/12))) for i in range(13))
                shapes=[(tuple(points),True)]
            else:shapes=[(((x,y),(x+w,y),(x+w,y+h),(x,y+h)),True)]
        elif tag in ('circle','ellipse'):
            x,y=num('cx'),num('cy');rx=num('r') if tag=='circle' else num('rx');ry=rx if tag=='circle' else num('ry')
            if min(rx,ry)<=0:raise ValueError('Invalid SVG ellipse')
            shapes=[(tuple((x+rx*math.cos(i*math.tau/64),y+ry*math.sin(i*math.tau/64)) for i in range(64)),True)]
        elif tag=='line':shapes=[(((num('x1'),num('y1')),(num('x2'),num('y2'))),False)]
        # Preserve subpath parity for holes; never fill separate rings independently.
        closed=[p for p,c in shapes if c];opened=[p for p,c in shapes if not c]
        if len(closed)>1 and not evenodd:raise ValueError('Multipart SVG paths require explicit evenodd fill rule')
        if opened and any(len(p)>2 for p in opened) and style.get('facecolor')!='none':raise ValueError('Open SVG curves/polylines require explicit fill=none')
        def mapped(p):
            a,b,c,d,e,f=matrix;return tuple((a*x+c*y+e,b*x+d*y+f) for x,y in p)
        part_style=dict(style)
        a,b,c,d,e,f=matrix
        if abs(a*d-b*c)<1e-15:raise ValueError('Singular SVG affine transform')
        if style.get('edgecolor','none')!='none' and style.get('linewidth',0)>0:
            first=a*a+b*b;second=c*c+d*d
            if abs(first-second)>1e-10*max(first,second) or abs(a*c+b*d)>1e-10*max(first,second):raise ValueError('Non-uniform SVG stroke transform is outside the subset')
            part_style['linewidth']*=math.sqrt(first)
        if closed:parts.append(SymbolPart(tuple(mapped(p) for p in closed),True,tuple(part_style.items())))
        for p in opened:parts.append(SymbolPart((mapped(p),),False,tuple(part_style.items())))
        if tag not in ('svg','g') and len(el):raise ValueError('SVG shape cannot contain children')
        for child in el:visit(child,style,matrix,depth+1,evenodd)
    visit(root,{'facecolor':'currentColor','edgecolor':'none','linewidth':0},(1,0,0,1,0,0),0)
    if any(not (view[0]-1e-9<=x<=view[0]+view[2]+1e-9 and view[1]-1e-9<=y<=view[1]+view[3]+1e-9) for part in parts for ring in part.paths for x,y in ring):raise ValueError('SVG geometry outside its viewBox requires explicit source clipping')
    return SymbolDefinition(name,view,tuple(parts),source,'svg')

# All catalog strokes/polygons below are original programmatic illustrations.
def _part(points,closed=True,**style):return SymbolPart((tuple(points),),closed,tuple(style.items()))
def _circle(x,y,r,n=24):return tuple((x+r*math.cos(i*math.tau/n),y+r*math.sin(i*math.tau/n)) for i in range(n))
def _catalog():
    box=((.15,.85),(.15,.35),(.5,.08),(.85,.35),(.85,.85))
    ring=_part(_circle(.5,.5,.36));line=lambda p:_part(p,False,edgecolor='currentColor',facecolor='none',linewidth=.07)
    icons={
      'city':(ring,_part(_circle(.5,.5,.14),facecolor='white')),
      'village':(_part(_circle(.5,.5,.22)),),
      'port':(line(((.5,.08),(.5,.82))),line(((.15,.56),(.3,.79),(.5,.88),(.7,.79),(.85,.56))),line(((.3,.3),(.7,.3)))),
      'gold':(_part(((.12,.7),(.27,.25),(.7,.25),(.9,.7))),line(((.12,.7),(.9,.7))),line(((.27,.25),(.36,.7)))),
      'salt':(_part(((.12,.8),(.5,.1),(.88,.8))),line(((.5,.1),(.5,.8)))),
      'ivory':(line(((.22,.15),(.25,.5),(.4,.8),(.66,.88),(.8,.76),(.8,.52))),),
      'fortress':(_part(((.12,.86),(.12,.15),(.28,.15),(.28,.32),(.42,.32),(.42,.15),(.58,.15),(.58,.32),(.72,.32),(.72,.15),(.88,.15),(.88,.86))),),
      'mine':(line(((.15,.8),(.75,.15))),line(((.12,.35),(.38,.2),(.65,.22),(.88,.4))),line(((.3,.2),(.85,.83)))),
      'monument':(_part(((.25,.86),(.4,.12),(.6,.12),(.75,.86))),line(((.1,.9),(.9,.9)))),
      'landing':(line(((.1,.78),(.9,.78))),_part(((.5,.1),(.73,.5),(.27,.5))),line(((.32,.48),(.2,.78))),line(((.68,.48),(.8,.78)))),
      'rover':(_part(((.16,.3),(.78,.3),(.88,.65),(.12,.65))),_part(_circle(.26,.76,.14)),_part(_circle(.73,.76,.14)),line(((.62,.3),(.62,.1),(.9,.1)))),
      'probe':(_part(((.5,.18),(.72,.48),(.5,.8),(.28,.48))),_part(((.02,.3),(.25,.3),(.25,.65),(.02,.65))),_part(((.75,.3),(.98,.3),(.98,.65),(.75,.65)))),
      'instrument':(ring,line(((.5,.1),(.5,.9))),line(((.1,.5),(.9,.5)))),
      'battle':(line(((.15,.15),(.85,.85))),line(((.85,.15),(.15,.85)))),
      'temple':(_part(((.08,.3),(.5,.03),(.92,.3))),_part(((.15,.4),(.3,.4),(.3,.8),(.15,.8))),_part(((.7,.4),(.85,.4),(.85,.8),(.7,.8))),line(((.08,.9),(.92,.9)))),
      'base':(_part(box),line(((.5,.35),(.5,.85))),line(((.3,.55),(.7,.55)))),
      'scientific-point':(ring,line(((.25,.5),(.75,.5)))),
      'arrow':(_part(((.05,.35),(.55,.35),(.55,.1),(.95,.5),(.55,.9),(.55,.65),(.05,.65))),)}
    return {name:SymbolDefinition(name,(0,0,1,1),parts,AssetSource('azimlib:programmatic-catalog','BSD-3-Clause','Copyright (c) 2026 Kernerian')) for name,parts in icons.items()}
_CATALOG=_catalog()
def symbol_catalog(catalog='lucide'):
    if catalog=='original':return dict(_CATALOG)
    if catalog!='lucide':raise ValueError('Catalog must be lucide or original')
    from .lucide import lucide_catalog
    return lucide_catalog()
def get_symbol(symbol):
    if isinstance(symbol,SymbolDefinition):return symbol
    if not isinstance(symbol,str):raise TypeError('Require symbol name or SymbolDefinition')
    if symbol.startswith('original:'):
        name=symbol.split(':',1)[1]
        if name not in _CATALOG:raise ValueError('Unknown original symbol')
        return _CATALOG[name]
    from .lucide import lucide_catalog,CARTOGRAPHIC_ALIASES
    catalog=lucide_catalog();name=CARTOGRAPHIC_ALIASES.get(symbol,symbol.removeprefix('lucide:'))
    if name.startswith('original:'):return _CATALOG[name.split(':',1)[1]]
    if name not in catalog:raise ValueError('Unknown cartographic symbol: '+symbol)
    return catalog[name]
