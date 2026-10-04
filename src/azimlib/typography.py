"""Bundled, licensed DejaVu fonts and dependency-free advance metrics."""
from functools import lru_cache
import json
from pathlib import Path
from collections import OrderedDict
from copy import deepcopy
from threading import RLock

FONTS=Path(__file__).with_name('fonts')
POINT=100/72

def font_path(style):
    family=style.get('font_family','DejaVu Sans').lower().replace(' ','')
    if family not in ('dejavusans','sans-serif'):return None
    weight=str(style.get('font_weight','normal'))
    bold=weight=='bold' or weight.isdigit() and int(weight)>=600
    italic=style.get('font_style','normal')!='normal'
    suffix='-BoldOblique' if bold and italic else '-Bold' if bold else '-Oblique' if italic else ''
    return FONTS/f'DejaVuSans{suffix}.ttf'

@lru_cache(maxsize=1)
def _metrics():return json.loads((FONTS/'metrics.json').read_text(encoding='utf-8'))

def text_width(text,style):
    """Advance width in scene units; Latin kerning, no complex-script shaping."""
    path=font_path(style)
    size=style.get('font_size',10*POINT)
    if path is None:return max((len(line)*size*.62 for line in str(text).splitlines()),default=0)
    metrics=_metrics()[path.stem]
    def width(line):
        total=0;previous=None
        for char in line:
            glyph,advance=metrics['chars'].get(char,metrics['chars']['?'])
            total+=advance+metrics['kern'].get(f'{previous},{glyph}',0)
            previous=glyph
        return total*size/metrics['units']
    return max(map(width,str(text).split('\n')),default=0)


_portable_subsets=OrderedDict()
_portable_lock=RLock()


def _export_metrics(characters, style):
    """Small serializable subset of our font metrics for portable components."""
    path=font_path(style)
    if path is None:return None
    metrics=_metrics()[path.stem]
    characters=''.join(sorted(set(characters+'?')))
    key=(path,characters)
    with _portable_lock:
        entry=_portable_subsets.get(key)
        if entry is not None and entry[0] is metrics:
            _portable_subsets.move_to_end(key)
            return deepcopy(entry[1])
    chars={c:metrics['chars'].get(c,metrics['chars']['?']) for c in sorted(set(characters+'?'))}
    glyphs={str(value[0]) for value in chars.values()}
    result=dict(units=metrics['units'],chars=chars,vertical=_font_vertical_metrics(path),
                kern={k:v for k,v in metrics['kern'].items() if all(g in glyphs for g in k.split(','))},
                bounds={c:metrics['bounds'].get(c,[0,metrics['units']*.75]) for c in chars})
    with _portable_lock:
        if key not in _portable_subsets and len(_portable_subsets)>=64:_portable_subsets.popitem(last=False)
        _portable_subsets[key]=(metrics,result)
    return deepcopy(result)

def text_vertical_bounds(text,style):
    """Ink bounds above the alphabetic baseline, in scene units."""
    size=style.get('font_size',10*POINT)
    path=font_path(style)
    if path is None:return (-.2*size,.8*size)
    metrics=_metrics()[path.stem]
    bounds=[metrics['bounds'].get(c,[0,metrics['units']*.75]) for c in str(text) if not c.isspace()]
    if not bounds:return (0,0)
    return min(b[0] for b in bounds)*size/metrics['units'],max(b[1] for b in bounds)*size/metrics['units']

@lru_cache(maxsize=4)
def _font_vertical_metrics(path):
    """Read standard TrueType line metrics with the Python standard library."""
    import struct
    raw=path.read_bytes();count=struct.unpack_from('>H',raw,4)[0]
    tables={raw[12+16*i:16+16*i]:struct.unpack_from('>II',raw,20+16*i) for i in range(count)}
    units=struct.unpack_from('>H',raw,tables[b'head'][0]+18)[0]
    tag=b'OS/2' if b'OS/2' in tables else b'hhea'
    position=tables[tag][0]+(68 if tag==b'OS/2' else 4)
    ascent,descent,gap=struct.unpack_from('>hhh',raw,position)
    return ascent/units,-descent/units,gap/units

def text_line_metrics(text,style,*,multiline=False):
    """Font line box including accents/descenders beyond the standard metrics."""
    size=style.get('font_size',10*POINT);path=font_path(style)
    a,d,g=_font_vertical_metrics(path) if path is not None else (.8,.2,.2)
    low,high=text_vertical_bounds(text,style)
    halfgap=g*size/2 if multiline or style.get('multiline',False) else 0
    return max(a*size,high)+halfgap,max(d*size,-low)+halfgap

def text_baseline_offset(text,style):
    ascent,descent=text_line_metrics(text,style)
    return {'top':ascent,'middle':(ascent-descent)/2,'bottom':-descent,'alphabetic':0}[style.get('baseline','alphabetic')]

def text_line_layout(text,style):
    """Baselines of a whole block; baseline alignment anchors the last line."""
    lines=str(text).replace('\r\n','\n').replace('\r','\n').split('\n')
    metrics=[text_line_metrics(line,style,multiline=len(lines)>1) for line in lines]
    total=sum(a+d for a,d in metrics);first=metrics[0][0];last=metrics[-1][1]
    origin={'top':first,'middle':first-total/2,'bottom':first-total,'alphabetic':first-total+last}[style.get('baseline','alphabetic')]
    rows=[];cursor=origin
    for i,(line,(ascent,descent)) in enumerate(zip(lines,metrics)):
        if i:cursor+=metrics[i-1][1]+ascent
        rows.append((line,cursor,ascent,descent))
    return rows

def text_bounds(text,style):
    """Unrotated advance/font line box relative to the anchor, including lines."""
    boxes=[]
    for line,y,ascent,descent in text_line_layout(text,style):
        width=text_width(line,style)
        left=-{'start':0,'middle':.5,'end':1}[style.get('anchor','start')]*width
        boxes.append((left,y-ascent,left+width,y+descent))
    x0=min(b[0] for b in boxes);y0=min(b[1] for b in boxes)
    return x0,y0,max(b[2] for b in boxes)-x0,max(b[3] for b in boxes)-y0


def text_rotation_offset(text,style):
    """Own alignment of the rotated line box around a requested text anchor.

    Public default aligns after rotation; anchor aligns before rotation.
    Low-level primitives without a mode retain their already-baked anchor.
    """
    import math
    mode=style.get('rotation_mode','anchor');angle=style.get('rotation',0)
    if mode=='anchor' or (not angle and mode=='default'):return (0.,0.)
    bx,by,w,h=text_bounds(text,style);a=math.radians(angle);c,s=math.cos(a),math.sin(a)
    points=[(x*c-y*s,x*s+y*c) for x,y in ((bx,by),(bx+w,by),(bx+w,by+h),(bx,by+h))]
    left=min(p[0] for p in points);right=max(p[0] for p in points)
    top=min(p[1] for p in points);bottom=max(p[1] for p in points)
    ha=style.get('anchor','start');va=style.get('baseline','alphabetic');public=(-angle)%360
    if mode=='xtick':
        central=public<=10 or 85<=public<=95 or public>=350 or 170<=public<=190 or 265<=public<=275
        first=10<public<85 or 190<public<265
        ha='middle' if central else ('start' if va=='bottom' else 'end') if first else ('end' if va=='bottom' else 'start')
    elif mode=='ytick':
        central=public<=10 or public>=350 or 170<=public<=190 or 80<=public<=100 or 260<=public<=280
        first=190<public<260 or 10<public<80
        va='middle' if central else ('alphabetic' if ha=='start' else 'top') if first else ('top' if ha=='start' else 'alphabetic')
    dx=-{'start':left,'middle':(left+right)/2,'end':right}[ha]
    descent=text_line_metrics(str(text).split('\n')[-1],style,multiline='\n' in str(text))[1]
    dy=-{'top':top,'middle':(top+bottom)/2,'bottom':bottom,'alphabetic':bottom-descent}[va]
    return dx,dy
