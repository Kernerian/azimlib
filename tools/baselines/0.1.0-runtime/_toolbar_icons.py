"""Azimlib's original toolbar geometry, shared by desktop and offline SVG.

All coordinates are authored here on a 24-unit canvas. No downloaded glyphs,
font outlines, SVG paths or bitmap assets are used to construct these icons.
Operations paint/erase a mask, so transparent counters stay identical in both
renderers. Pillow is imported only for the optional desktop bitmap.
"""
from __future__ import annotations
from xml.sax.saxutils import escape


NAMES = ('home', 'back', 'forward', 'move', 'zoom_to_rect', 'subplots', 'filesave')


def _geometry(name):
    # Each operation: primitive, coordinates, paint (True) or erase (False).
    if name == 'home':
        return [('polygon', ((2,10),(12,2),(22,10),(20,12),(12,5.5),(4,12)), True),
                ('polygon', ((5,11),(12,5.5),(19,11),(19,21),(14,21),(14,14),(10,14),(10,21),(5,21)), True)]
    if name in ('back', 'forward'):
        points=((2,12),(10.5,3.5),(13,6),(9,10),(22,10),(22,14),(9,14),(13,18),(10.5,20.5))
        if name == 'forward': points=tuple((24-x,y) for x,y in points)
        return [('polygon', points, True)]
    if name == 'move':
        return [('polygon', ((12,1),(17,6),(14,6),(14,10),(18,10),(18,7),(23,12),
                             (18,17),(18,14),(14,14),(14,18),(17,18),(12,23),
                             (7,18),(10,18),(10,14),(6,14),(6,17),(1,12),(6,7),
                             (6,10),(10,10),(10,6),(7,6)), True)]
    if name == 'zoom_to_rect':
        return [('ellipse', (2.5,2.5,17.5,17.5), True),
                ('ellipse', (5,5,15,15), False),
                ('polygon', ((15,13),(22,20),(20,22),(13,15)), True)]
    if name == 'subplots':
        operations=[]
        for x,y in ((7,5),(17,12),(10,19)):
            operations.extend([('rect',(2,y-1,22,y+1),True),
                               ('roundrect',(x-1.75,y-3.5,x+1.75,y+3.5,.65),True)])
        return operations
    if name == 'filesave':
        return [('polygon',((3,3),(18,3),(21,6),(21,21),(3,21)),True),
                ('polygon',((5,5),(17,5),(19,7),(19,19),(5,19)),False),
                ('rect',(7,3,17,10),True), ('rect',(9,5,15,8),False),
                ('rect',(7,13,17,21),True), ('rect',(9,15,15,19),False)]
    raise ValueError(f'Unknown toolbar icon {name!r}')


def icon_svg(name):
    """Serialize original vector geometry without external assets or libraries."""
    shapes=[]
    for kind,coordinates,paint in _geometry(name):
        color='white' if paint else 'black'
        style=f'fill="{color}" stroke="none"'
        if kind == 'polygon':
            points=' '.join(f'{x:g},{y:g}' for x,y in coordinates)
            shapes.append(f'<polygon points="{points}" {style}/>')
        else:
            x0,y0,x1,y1=coordinates[:4]
            if kind == 'ellipse':
                shapes.append(f'<ellipse cx="{(x0+x1)/2:g}" cy="{(y0+y1)/2:g}" rx="{(x1-x0)/2:g}" ry="{(y1-y0)/2:g}" {style}/>')
            else:
                radius=f' rx="{coordinates[4]:g}"' if kind=='roundrect' else ''
                shapes.append(f'<rect x="{x0:g}" y="{y0:g}" width="{x1-x0:g}" height="{y1-y0:g}"{radius} {style}/>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">'
            f'<title>Azimlib {escape(name)} icon</title><defs>'
            '<mask id="shape" maskUnits="userSpaceOnUse" x="0" y="0" width="24" height="24">'
            '<rect width="24" height="24" fill="black"/>'+''.join(shapes)+
            '</mask></defs><rect width="24" height="24" fill="#111111" stroke="none" mask="url(#shape)"/></svg>')


def icon_image(name, size=24):
    """Rasterize the same original geometry, with eightfold edge sampling."""
    from PIL import Image, ImageDraw
    if not isinstance(size,int) or size<1: raise ValueError('Icon size must be a positive integer.')
    sample=8; scale=size*sample/24
    mask=Image.new('L',(size*sample,size*sample),0)
    draw=ImageDraw.Draw(mask)
    for kind,coordinates,paint in _geometry(name):
        fill=255 if paint else 0
        if kind=='polygon':
            draw.polygon([(x*scale,y*scale) for x,y in coordinates],fill=fill)
        else:
            box=tuple(value*scale for value in coordinates[:4])
            if kind=='ellipse': draw.ellipse(box,fill=fill)
            elif kind=='roundrect': draw.rounded_rectangle(box,radius=coordinates[4]*scale,fill=fill)
            else: draw.rectangle(box,fill=fill)
    alpha=mask.resize((size,size),Image.Resampling.LANCZOS)
    mask.close()
    image=Image.new('RGBA',(size,size),'#111111'); image.putalpha(alpha); alpha.close()
    return image
