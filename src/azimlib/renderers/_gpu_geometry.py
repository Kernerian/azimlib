"""Owned bounded screen meshes; no geographic interpretation or foreign tessellator."""
import math
import hashlib
from functools import lru_cache
from array import array
from dataclasses import dataclass
from ..scene import Path, Circle, Rect, Text, Raster3D


@dataclass(frozen=True)
class Draw:
    vertices: tuple
    color: tuple
    rule: int  # 0 union, 1 even-odd, 2 nonzero
    clip: tuple | None


@dataclass(frozen=True)
class PreparedDraws:
    items: tuple
    signature: bytes
    def __iter__(self):return iter(self.items)
    def __len__(self):return len(self.items)
    def __getitem__(self,index):return self.items[index]


class PackedBytes(bytes):
    """Immutable buffer payload with a once-computed content digest."""
    def __new__(cls,value):
        result=super().__new__(cls,value);result.sha256=hashlib.sha256(result).digest();return result


def fan(rings, *, signed=False):
    output=[]
    for ring in rings:
        if len(ring)<3:continue
        a=ring[0]
        for b,c in zip(ring[1:-1],ring[2:]):
            cross=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
            if not cross:continue
            weight=(-1. if cross<0 else 1.) if signed else 1.
            output.extend((x,y,weight) for x,y in (a,b,c))
            if len(output)>2000000:raise ValueError('GPU mesh exceeds two million vertices')
    return tuple(output)


@lru_cache(maxsize=128)
def unit_circle(count):
    return tuple((math.cos(i*2*math.pi/count),math.sin(i*2*math.pi/count)) for i in range(count))


def circle(x,y,rx,ry):
    count=max(16,min(2048,math.ceil(math.pi*math.sqrt(max(rx,ry)*8))))
    return tuple((x+rx*a,y+ry*b) for a,b in unit_circle(count))


class StrokeMesh:
    def __init__(self):self.rings=[];self.points=0
    def polygon(self,points,**kwargs):
        points=tuple(points);self.points+=len(points)
        if self.points>700000:raise ValueError('GPU stroke mesh budget exceeded')
        self.rings.append(points)
    def ellipse(self,box,**kwargs):
        x,y,r,b=box;self.polygon(circle((x+r)/2,(y+b)/2,(r-x)/2,(b-y)/2))


def outlines(commands):
    from ..path import Path as CurvePath
    vertices=[];codes=[]
    for cmd in commands:
        tag=cmd[0]
        if tag=='Z':vertices.append((0,0));codes.append(CurvePath.CLOSEPOLY)
        else:
            code={'M':1,'L':2,'Q':3,'C':4}[tag]
            vertices.extend(cmd[1:]);codes.extend([code]*len(cmd[1:]))
        if len(vertices)>200000:raise ValueError('GPU outline input budget exceeded')
    return tuple(p for p,closed in CurvePath(vertices,codes).to_polylines(tolerance=.08) if p)


def drawing(item):
    """Fill and stroke meshes with the CPU renderer's original dash/cap/join rules."""
    from ..colors import to_rgba
    from .pillow import _stroke,_dash_parts
    s=item.style;glyph=isinstance(item,Text)
    if isinstance(item,Raster3D):return (item,)
    if glyph:
        from ..font_outline import text_commands
        rings=outlines(text_commands(item))
    elif isinstance(item,Path):rings=tuple(tuple(p) for p in item.paths)
    elif isinstance(item,Circle):rings=(circle(item.x,item.y,item.r,item.r),) if item.r else ()
    else:rings=(((item.x,item.y),(item.x+item.width,item.y),(item.x+item.width,item.y+item.height),(item.x,item.y+item.height)),) if item.width and item.height else ()
    result=[]
    def add(vertices,color,rule,opacity):
        if not len(vertices) or color in (None,'none'):return
        rgba=to_rgba(color);rgba=(*rgba[:3],rgba[3]*s.get('opacity',1)*opacity)
        if rgba[3]:result.append(Draw(vertices,rgba,rule,item.clip))
    if glyph and s.get('background'):
        from ._shaped_text import _background
        add(fan((_background(item),)),s['background'],0,1)
    def stroke():
        if not s.get('dash') and s.get('linejoin','round')=='round':
            from ._gpu_stroke import round_stroke
            vertices=round_stroke(rings,s.get('stroke_width',1),s.get('linecap','butt'),glyph or not isinstance(item,Path) or item.closed)
            if vertices is not None:
                add(vertices,s.get('stroke'),0,s.get('stroke_opacity',1));return
        mesh=StrokeMesh()
        for ring in rings:
            closed=glyph or not isinstance(item,Path) or item.closed
            points=list(ring)
            if closed and points and points[-1]!=points[0]:points.append(points[0])
            for part in _dash_parts(points,s.get('dash')):
                _stroke(mesh,part,s.get('stroke_width',1),s.get('linecap','butt'),s.get('linejoin','round'),closed and not s.get('dash'))
        add(fan(mesh.rings),s.get('stroke'),0,s.get('stroke_opacity',1))
    # Text halos precede the ink; ordinary paths paint stroke after filling.
    if glyph and s.get('stroke') not in (None,'none'):stroke()
    add(fan(rings,signed=glyph),s.get('fill','#172b38' if glyph else 'none'),2 if glyph else 1,s.get('fill_opacity',1))
    if not glyph and s.get('stroke') not in (None,'none'):stroke()
    return tuple(result)


def packed(vertices):
    """Keep translation out of a float32 VBO; no rounding of physical coordinates."""
    x,y=vertices[0][:2]
    if hasattr(vertices,'dtype'):
        import numpy as np
        values=np.empty(vertices.shape,dtype='f4')
        np.subtract(vertices[:,0],x,out=values[:,0]);np.subtract(vertices[:,1],y,out=values[:,1]);values[:,2]=vertices[:,2]
        return PackedBytes(values.tobytes()),(float(x),float(y))
    values=array('f',(v for a,b,w in vertices for v in (a-x,b-y,w)))
    return PackedBytes(values.tobytes()),(x,y)


class PreparationCache:
    """Exact geometry/content keys, bounded packed payload; translations stay uniforms."""
    def __init__(self,max_bytes):
        from collections import OrderedDict
        self.entries=OrderedDict();self.bytes=0;self.limit=max_bytes;self.hits=0;self.misses=0
    def get(self,item):
        from copy import copy
        from ..text_engine import cache_token
        import hashlib
        if isinstance(item,Raster3D):return (item,), (0,0)
        if isinstance(item,Path):
            anchor=next((p[0] for p in item.paths if len(p)),(0.,0.))
            x,y=anchor
            parts=tuple(tuple((a-x,b-y) for a,b in part) for part in item.paths)
            geometry=(item.closed,tuple(len(p) for p in parts),hashlib.sha256(array('d',(v for part in parts for p in part for v in p)).tobytes()).digest())
        else:
            anchor=(item.x,item.y)
            geometry=(str(item.text),cache_token(item.text,item.style)) if isinstance(item,Text) else (item.r,) if isinstance(item,Circle) else (item.width,item.height)
        key=(type(item),geometry,repr(sorted((k,v) for k,v in item.style.items() if k!='texconfig')))
        if key in self.entries:
            value,size=self.entries.pop(key);self.entries[key]=(value,size);self.hits+=1;return value,anchor
        # Resolved Text must not be shaped or aligned a second time. Construct
        # local geometry only on misses; hits already own immutable packets.
        local=copy(item);object.__setattr__(local,'clip',None)
        if isinstance(item,Path):object.__setattr__(local,'paths',parts)
        else:
            object.__setattr__(local,'x',0);object.__setattr__(local,'y',0)
        self.misses+=1;value=[];size=0
        for draw in drawing(local):
            raw,origin=packed(draw.vertices)
            if hasattr(draw.vertices,'dtype'):
                v=draw.vertices
                bounds=tuple(map(float,(v[:,0].min(),v[:,1].min(),v[:,0].max(),v[:,1].max())))
            else:
                bounds=(min(p[0] for p in draw.vertices),min(p[1] for p in draw.vertices),max(p[0] for p in draw.vertices),max(p[1] for p in draw.vertices))
            value.append((raw,origin,bounds,draw.color,draw.rule,len(draw.vertices)))
            size+=len(raw)+256
        # A resolved-surface signature must not keep evicted mesh payload alive.
        # Hash each immutable packet once, with unambiguous length delimiters.
        digest=hashlib.sha256()
        for packet in value:
            raw=packet[0];metadata=repr(packet[1:]).encode('utf8')
            digest.update(len(raw).to_bytes(8,'little'));digest.update(raw.sha256)
            digest.update(len(metadata).to_bytes(8,'little'));digest.update(metadata)
        size+=len(repr(key).encode('utf8'))+32;value=PreparedDraws(tuple(value),digest.digest())
        if size<=self.limit:
            while self.entries and (self.bytes+size>self.limit or len(self.entries)>=2048):
                _,(_,old)=self.entries.popitem(last=False);self.bytes-=old
            self.entries[key]=(value,size);self.bytes+=size
        return value,anchor
    def clear(self):self.entries.clear();self.bytes=0
