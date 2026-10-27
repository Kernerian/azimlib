"""Thematic drawing on the existing physical scene; no parallel renderer."""
import math
from dataclasses import replace
from .scene import Path,Text
from .styles import path_style,text_style
from .typography import POINT
from .bodies import UnsupportedBodyOperation


def symbol_scene(definition,point,size,style,scene,clip,*,anchor=(.5,.5),offset=(0,0),rotation=None):
    notice=dict(kind='cartographic_symbol',name=definition.name,origin=definition.source.origin,license=definition.source.license,credit=definition.source.credit,sha256=definition.source.sha256)
    if notice not in scene._material_notices:scene._material_notices.append(notice)
    from .scene import Scene
    target_scene=scene;scene=Scene(scene.width,scene.height);size*=style.get('icon_scale',1)
    if size>256*POINT:raise ValueError('Scaled icon exceeds256pt visual budget')
    x0,y0,w,h=definition.viewbox;scale=size/max(w,h)
    angle=math.radians(-style.get('rotation',0) if rotation is None else -rotation);c,s=math.cos(angle),math.sin(angle)
    ox,oy=point[0]+offset[0]*POINT,point[1]+offset[1]*POINT
    if definition.kind=='png':
        from ._raster_icons import rotated
        from .scene import RasterIcon
        pw,ph,data,factor=rotated(definition.raster,size,style.get('rotation',0) if rotation is None else rotation)
        u=(.5-anchor[0])*w*scale;v=(.5-anchor[1])*h*scale;cx=ox+c*u-s*v;cy=oy+s*u+c*v
        scene.add(RasterIcon(cx-pw*factor/2,cy-ph*factor/2,pw*factor,ph*factor,pw,ph,data,dict(opacity=style.get('alpha',1)),clip))
        return _emit_icon(scene.items,target_scene,style)
    for part in definition.parts:
        appearance=dict(part.style)
        current=style.get('facecolor',style.get('color','#245d71'))
        if 'facecolor' not in appearance:appearance['facecolor']=current
        for key in ('facecolor','edgecolor'):
            if appearance.get(key)=='currentColor':appearance[key]=current
        if 'icon_stroke_width' in style:appearance['linewidth']=style['icon_stroke_width']
        if 'linewidth' in appearance:appearance['linewidth']*=scale/POINT
        for key in ('alpha','linewidth','linestyle','hatch','hatch_color','hatch_spacing','hatch_linewidth'):
            if key in style:
                appearance[key]=style[key]*appearance.get(key,1) if key=='alpha' else style[key]
        appearance.setdefault('edgecolor','none');appearance.setdefault('linewidth',0)
        paths=[]
        for ring in part.paths:
            points=[]
            for x,y in ring:
                u=(x-x0-anchor[0]*w)*scale;v=(y-y0-anchor[1]*h)*scale
                points.append((ox+c*u-s*v,oy+s*u+c*v))
            paths.append(points)
        scene.add(Path(paths,part.closed,path_style(appearance,part.closed),clip))
    return _emit_icon(scene.items,target_scene,style)


def _emit_icon(items,scene,style):
    from .icon_effects import add_effects
    add_effects(items,scene,style.get('icon_halo'),style.get('icon_shadow'))
    first=len(scene.items)
    for item in items:scene.add(item)
    return first,len(scene.items)


def render_thematic(layer,vp,scene):
    from .render_map import _geometry,_text
    start=len(scene.items);clip=vp.box if layer.get_clip_on() else None
    if layer.kind=='thematic_symbols':
        for i in sorted(range(len(layer.data)),key=lambda i:(layer.priorities[i],i)):
            p=vp.project(*layer.data[i])
            if p is None:continue
            size=layer._size*POINT
            if layer.size_unit=='m':
                from .surfaces import BodySurface
                surface=BodySurface(layer.get_context())
                if layer._size>surface.a*.1:raise UnsupportedBodyOperation('Map-size symbol exceeds local scale domain')
                lon,lat=layer.data[i];a=surface.direct((lon,lat),270,layer._size/2);b=surface.direct((lon,lat),90,layer._size/2)
                pa,pb=vp.project(*a),vp.project(*b)
                if pa is None or pb is None:raise UnsupportedBodyOperation('Map-size symbol footprint crosses projection horizon')
                size=math.dist(pa,pb)
            first=len(scene.items)
            first,_=symbol_scene(layer.symbol,p,size,layer.style,scene,clip,anchor=layer.anchor,offset=layer.offset)
            if layer.labels[i]:
                labelstyle=text_style(dict(color=layer.style.get('labelcolor','#23313c'),fontsize=layer.style.get('fontsize',9),ha='left',va='center',halo='white',halo_width=1))
                _text(scene,p[0]+layer.offset[0]*POINT+size*.65,p[1]+layer.offset[1]*POINT,layer.labels[i],labelstyle,clip)
            scene._pick_records.append((layer,i,first,len(scene.items)))
    elif layer.kind=='thematic_region':
        style=dict(layer.style)
        if layer.gradient:
            first=len(scene.items)
            for geometry,color in layer.slices:_geometry(geometry,dict(style,facecolor=color,edgecolor='none',linewidth=0,hatch=None,antialiased=False),vp,scene)
            for i in range(first,len(scene.items)):
                item=scene.items[i];scene.items[i]=replace(item,style=dict(item.style,_thematic_gradient=first))
            if style.get('edgecolor') not in (None,'none'):_geometry(layer.definition.geometry,dict(style,facecolor='none',hatch=None),vp,scene)
        else:_geometry(layer.definition.geometry,style,vp,scene)
        # Shared clipping can be disabled only for screen bounds, never domain/horizon.
        if clip is None:
            for i in range(start,len(scene.items)):scene.items[i]=replace(scene.items[i],clip=None)
        scene._pick_records.append((layer,0,start,len(scene.items)))
    else:
        _geometry(layer.definition.geometry,dict(layer.style),vp,scene)
        line_end=len(scene.items)
        if layer.path_symbol:
            used=0
            for item in tuple(scene.items[start:line_end]):
                if not isinstance(item,Path) or item.closed:continue
                for part in item.paths:
                    remaining=layer.spacing*POINT*.5
                    for a,b in zip(part,part[1:]):
                        length=math.dist(a,b)
                        if not length:continue
                        distance=remaining
                        while distance<length:
                            used+=1
                            if used>2048:raise ValueError('Path-symbol instance budget exceeded')
                            p=tuple(x+(y-x)*distance/length for x,y in zip(a,b));angle=-math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
                            symbol_scene(layer.path_symbol,p,layer.symbol_size*POINT,layer.style,scene,clip,rotation=angle)
                            distance+=layer.spacing*POINT
                        remaining=distance-length
        if clip is None:
            for i in range(start,len(scene.items)):scene.items[i]=replace(scene.items[i],clip=None)
        scene._pick_records.append((layer,0,start,len(scene.items)))


def apply_group_clip(layer,scene,start,box):
    group=getattr(layer,'_group',None)
    if group is None:return
    rect=group.effective_clip_box(box)
    if rect is None:return
    for i in range(start,len(scene.items)):
        item=scene.items[i];clip=rect
        if item.clip is not None:
            x,y,w,h=clip;a,b,c,d=item.clip;right=min(x+w,a+c);bottom=min(y+h,b+d);x,y=max(x,a),max(y,b)
            clip=(x,y,max(0,right-x),max(0,bottom-y))
        scene.items[i]=replace(item,clip=clip)
