"""Own TrueType outlines for the four bundled DejaVu faces, without hint execution.

Reads glyf/loca per the OpenType specification; no third-party parser code.
Only bundled static fonts are accepted. Unsupported composite attachment fails
explicitly rather than drawing a silently corrupted glyph.
"""
import struct
from functools import lru_cache
from .typography import font_path, _metrics, text_width, text_baseline_offset

@lru_cache(maxsize=4)
def _tables(path):
    raw=path.read_bytes();count=struct.unpack_from('>H',raw,4)[0]
    tables={raw[12+16*i:16+16*i]:struct.unpack_from('>II',raw,20+16*i) for i in range(count)}
    head=tables[b'head'][0];units=struct.unpack_from('>H',raw,head+18)[0]
    long=struct.unpack_from('>h',raw,head+50)[0]
    count=struct.unpack_from('>H',raw,tables[b'maxp'][0]+4)[0]
    offsets=struct.unpack_from('>'+('I' if long else 'H')*(count+1),raw,tables[b'loca'][0])
    return raw,tables[b'glyf'][0],units,tuple(v*(1 if long else 2) for v in offsets)

@lru_cache(maxsize=2048)
def contours(path,glyph,depth=0):
    if depth>16:raise ValueError('Composite glyph nesting exceeds 16')
    raw,base,units,offsets=_tables(path)
    if offsets[glyph]==offsets[glyph+1]:return ()
    pos=base+offsets[glyph];n=struct.unpack_from('>h',raw,pos)[0];pos+=10
    result=[]
    if n>=0:
        if not n:return ()
        ends=struct.unpack_from('>'+'H'*n,raw,pos);pos+=2*n
        skip=struct.unpack_from('>H',raw,pos)[0];pos+=2+skip
        flags=[]
        while len(flags)<=ends[-1]:
            flag=raw[pos];pos+=1;flags.append(flag)
            if flag&8:flags.extend([flag]*raw[pos]);pos+=1
        if len(flags)!=ends[-1]+1:raise ValueError('Invalid glyph flag count')
        coords=[]
        for short,same in ((2,16),(4,32)):
            values=[];value=0
            for flag in flags:
                if flag&short:
                    delta=raw[pos]*(1 if flag&same else -1);pos+=1
                elif flag&same:delta=0
                else:delta=struct.unpack_from('>h',raw,pos)[0];pos+=2
                value+=delta;values.append(value)
            coords.append(values)
        start=0
        for end in ends:
            result.append(tuple((coords[0][i],coords[1][i],bool(flags[i]&1)) for i in range(start,end+1)));start=end+1
    else:
        flags=32
        while flags&32:
            flags,child=struct.unpack_from('>HH',raw,pos);pos+=4
            fmt=('h' if flags&2 else 'H') if flags&1 else ('b' if flags&2 else 'B')
            a,b=struct.unpack_from('>'+fmt*2,raw,pos);pos+=4 if flags&1 else 2
            xx=yy=1.;xy=yx=0.
            count=4 if flags&128 else 2 if flags&64 else 1 if flags&8 else 0
            if count:
                values=tuple(v/16384 for v in struct.unpack_from('>'+'h'*count,raw,pos));pos+=2*count
                if count==1:xx=yy=values[0]
                elif count==2:xx,yy=values
                else:xx,yx,xy,yy=values
            child_contours=contours(path,child,depth+1)
            child_contours=[[(xx*x+xy*y,yx*x+yy*y,on) for x,y,on in ring] for ring in child_contours]
            if flags&2:
                if flags&2048:a,b=xx*a+xy*b,yx*a+yy*b
            else:
                parent_points=[p for ring in result for p in ring];child_points=[p for ring in child_contours for p in ring]
                if a>=len(parent_points) or b>=len(child_points):raise ValueError('Unsupported phantom point glyph attachment')
                a,b=parent_points[a][0]-child_points[b][0],parent_points[a][1]-child_points[b][1]
            result.extend(tuple((x+a,y+b,on) for x,y,on in ring) for ring in child_contours)
    return tuple(result)

def glyph_commands(ring):
    """M/L/Q/Z, preserving exact quadratic curves and implied on-curve points."""
    if not ring:return ()
    first,last=ring[0],ring[-1]
    if first[2]:start=first[:2];points=list(ring[1:])
    elif last[2]:start=last[:2];points=list(ring[:-1])
    else:start=((first[0]+last[0])/2,(first[1]+last[1])/2);points=list(ring)
    out=[('M',start)];points.append((*start,True));i=0
    while i<len(points):
        p=points[i]
        if p[2]:out.append(('L',p[:2]));i+=1
        else:
            q=points[i+1]
            end=q[:2] if q[2] else ((p[0]+q[0])/2,(p[1]+q[1])/2)
            out.append(('Q',p[:2],end));i+=2 if q[2] else 1
    out.append(('Z',));return tuple(out)

def text_commands(item):
    """Yield glyph outlines in screen coordinates, with bundled advances/kerning."""
    import math
    style=item.style;path=font_path(style)
    if path is None:raise ValueError('PDF vector text requires bundled DejaVu Sans')
    metrics=_metrics()[path.stem];factor=style.get('font_size',12)/metrics['units']
    x=-{'start':0,'middle':.5,'end':1}[style.get('anchor','start')]*text_width(item.text,style)
    y=text_baseline_offset(item.text,style);a=math.radians(style.get('rotation',0));c,s=math.cos(a),math.sin(a)
    def transform(p):
        dx=x+p[0]*factor;dy=y-p[1]*factor
        return item.x+dx*c-dy*s,item.y+dx*s+dy*c
    previous=None
    for char in str(item.text):
        if char not in metrics['chars']:raise ValueError(f'Glyph U+{ord(char):04X} is not in bundled metrics')
        glyph,advance=metrics['chars'][char];x+=metrics['kern'].get(f'{previous},{glyph}',0)*factor
        for ring in contours(path,glyph):
            for cmd in glyph_commands(ring):yield (cmd[0],*(transform(p) for p in cmd[1:]))
        previous=glyph;x+=advance*factor
