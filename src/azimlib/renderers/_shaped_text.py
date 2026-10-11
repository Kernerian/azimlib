"""Paint shared positioned outlines; no backend-specific text layout."""
import math
from html import escape
from ..font_outline import text_commands
from ..text_engine import TextEngineError
from ..typography import text_bounds
from ._common import number as n


def _background(item):
    x,y,w,h=text_bounds(item.text,item.style)
    angle=math.radians(item.style.get('rotation',0));c,s=math.cos(angle),math.sin(angle)
    return [(item.x+u*c-v*s,item.y+u*s+v*c) for u,v in ((x-3,y-3),(x+w+3,y-3),(x+w+3,y+h+3),(x-3,y+h+3))]


def svg_text(item,clip):
    from .svg import _paint,_attr
    commands=' '.join(cmd[0]+(' '+' '.join(n(v) for p in cmd[1:] for v in p) if len(cmd)>1 else '') for cmd in text_commands(item))
    # One root node per primitive preserves the browser's navigation indexes.
    out=[f'<g{clip} data-azimlib-shaped="true" data-anchor-x="{n(item.x)}" data-anchor-y="{n(item.y)}" role="img" aria-label="{escape(str(item.text),quote=True)}">',
         '<desc>'+escape(str(item.text))+'</desc>']
    if item.style.get('background'):
        points=' '.join(n(v) for p in _background(item) for v in p)
        out.append(f'<polygon points="{points}"{_attr("fill",item.style["background"])}{_attr("opacity",n(item.style.get("opacity",1)))}/>')
    out.append(f'<path d="{commands}" fill-rule="nonzero" paint-order="stroke fill"{_paint(item.style,text=True)}/></g>')
    return ''.join(out)


def raster_text(item,factor):
    """Cubic/quadratic glyph contours in one supersampled, bounded RGBA tile."""
    try:import aggdraw
    except ImportError as exc:raise ImportError('Install azimlib[text] for shaped PNG/viewer rendering') from exc
    from PIL import Image
    from ..colors import to_rgba
    commands=tuple(text_commands(item));points=[p for cmd in commands for p in cmd[1:]]
    if item.style.get('background'):points+=_background(item)
    if not points:return Image.new('RGBA',(1,1)),(round(item.x*factor),round(item.y*factor))
    margin=(item.style.get('stroke_width',0)/2+2)*factor
    left=math.floor(min(p[0] for p in points)*factor-margin);top=math.floor(min(p[1] for p in points)*factor-margin)
    right=math.ceil(max(p[0] for p in points)*factor+margin);bottom=math.ceil(max(p[1] for p in points)*factor+margin)
    if (right-left)*(bottom-top)>16*1024*1024:raise TextEngineError('Shaped text raster tile exceeds 16 megapixels')
    tile=Image.new('RGBA',(max(1,right-left),max(1,bottom-top)))
    def pos(p):return p[0]*factor-left,p[1]*factor-top
    def rgba(color,opacity=1):
        r,g,b,a=to_rgba(color);return (round(r*255),round(g*255),round(b*255),round(a*opacity*255))
    if item.style.get('background'):
        path=aggdraw.Path();corners=_background(item);path.moveto(*pos(corners[0]))
        for point in corners[1:]:path.lineto(*pos(point))
        path.close();draw=aggdraw.Draw(tile);draw.path(path,None,aggdraw.Brush(rgba(item.style['background'])));draw.flush()
    path=aggdraw.Path();current=None
    for cmd in commands:
        if cmd[0]=='M':current=pos(cmd[1]);path.moveto(*current)
        elif cmd[0]=='L':current=pos(cmd[1]);path.lineto(*current)
        elif cmd[0]=='Q':
            control,end=map(pos,cmd[1:]);a=tuple(current[i]+2*(control[i]-current[i])/3 for i in range(2));b=tuple(end[i]+2*(control[i]-end[i])/3 for i in range(2))
            path.curveto(*a,*b,*end);current=end
        elif cmd[0]=='C':
            a,b,end=map(pos,cmd[1:]);path.curveto(*a,*b,*end);current=end
        else:path.close()
    s=item.style;draw=aggdraw.Draw(tile)
    if s.get('stroke') not in (None,'none') and s.get('stroke_width',0)>0:
        draw.path(path,aggdraw.Pen(rgba(s['stroke'],s.get('stroke_opacity',1)),s['stroke_width']*factor))
    if s.get('fill','black') not in (None,'none'):
        draw.path(path,None,aggdraw.Brush(rgba(s.get('fill','black'),s.get('fill_opacity',1))))
    draw.flush()
    return tile,(left,top)
