"""Cartographic scene construction. Backends never see geographic coordinates."""
from __future__ import annotations
import math
from functools import lru_cache
from dataclasses import asdict
from numbers import Real

from .geometry import split_antimeridian, clip_polygon_antimeridian, haversine
from .scene import Path, Text, Circle, Rect
from .styles import path_style, text_style, style_dict
from .viewport import Viewport, densify
from .typography import POINT,text_width
from .hatches import add_hatches


def render_axes(ax, scene, box, *, inset=False,measure_layout=False,cull=False):
    layout_start=len(scene.items)
    x,y,w,h = box
    # Like equal-aspect Matplotlib axes, shrink the axes box (not the content
    # inside a larger frame). Titles occupy the surrounding figure margin.
    title_height = len(ax._title[0].splitlines()) * ax._title[1].get("fontsize",12) * 100/72 * 1.2 if ax._title else 0
    subtitle_height = len(ax._subtitle[0].splitlines()) * ax._subtitle[1].get("fontsize",11) * 100/72 * 1.2 + 4 if ax._subtitle else 0
    bottom=0
    from .colorbar_render import colorbar_layout,render_colorbar
    mapbox,barbox=colorbar_layout(ax._colorbar,box) if ax._colorbar else (box,None)
    x,y,w,h=mapbox
    if mapbox[2] < 30 or mapbox[3] < 30:
        raise ValueError("Figure is too small for its titles, subplots, and color bars")
    vp = Viewport(ax.projection, ax._get_extent(), mapbox)
    px0,py0,px1,py1=vp.projected_bounds
    actual_w,actual_h=(px1-px0)*vp.scale,(py1-py0)*vp.scale
    mapbox=(x+(w-actual_w)/2,y+(h-bottom-actual_h)/2,actual_w,actual_h)
    vp=Viewport(ax.projection,ax._get_extent(),mapbox)
    x,y,w,h=mapbox
    scene.add(Rect(*mapbox, dict(fill=ax.facecolor)))
    metadata = dict(box=mapbox,start=len(scene.items),extent=vp.extent,
                    projected_bounds=vp.projected_bounds,ox=vp.ox,oy=vp.oy,scale=vp.scale,
                    projection=dict(asdict(ax.projection),name=ax.projection.name),
                    overview=getattr(ax,"_overview",False) or False,tick_indices=[],static_indices=[],grid_indices=[],grid_specs=[],
                    ticks=bool(ax._frame),inset=inset,pixel_ratio=1,degree_ticks=bool(ax._grid_format and ax._grid_format['labels']),
                    custom_ticks=any(a.locator_explicit or a.formatter_explicit or a.minor_locator_explicit or a.minor_formatter_explicit for a in (ax.xaxis,ax.yaxis)),
                    tick_settings={'major':ax._tick_params,'minor':ax._minor_tick_params},
                    major_locator_explicit={name:getattr(ax,name+'axis').locator_explicit for name in ('x','y')},
                    minor_remove_overlap={name:getattr(ax,name+'axis').remove_overlapping_locs for name in ('x','y')},
                    grid_format=ax._grid_format,
                    tick_rotation={name:ax._tick_params[name]['rotation'] for name in ('x','y')},
                    axes_index=ax.figure.axes.index(ax) if ax.figure and ax in ax.figure.axes else -1)
    scene.maps.append(metadata)
    if metadata['custom_ticks']:
        portable={name:getattr(ax,name+'axis')._export_ticks(metadata['degree_ticks']) for name in ('x','y')}
        if all(v is not None for v in portable.values()):metadata['portable_ticks']=portable
    minor={name:getattr(ax,name+'axis')._export_ticks(minor=True) for name in ('x','y')}
    if all(v is not None for v in minor.values()):metadata['portable_minor_ticks']=minor
    else:metadata['custom_ticks']=True;metadata.pop('portable_ticks',None)
    from .label_layout import plan_labels
    planned=plan_labels(ax,vp) if not measure_layout and any(l.kind=='labels' and l.visible for l in ax.layers) else {}
    for layer in (() if measure_layout else sorted(ax.layers, key=lambda a:a.zorder)):
        if not layer.visible:
            continue
        if layer.kind == "geometry":
            pixel_padding=2*max(1,100/ax.figure.dpi) if ax.figure else 2
            candidates=_geometry_candidates(layer,vp,pixel_padding) if cull else None
            features=enumerate(layer.data) if candidates is None else ((i,layer.data[i]) for i in candidates)
            for index, feature in features:
                if feature.geometry is None:
                    continue
                style = dict(layer.style)
                if "feature_styles" in layer.options:
                    style.update(layer.options["feature_styles"][index])
                if layer.options.get('mapped') and layer._array is not None:
                    style['facecolor']=layer.to_color(layer._array[index])
                if layer.options.get('contour'):
                    colors=layer.options.get('contour_colors')
                    style['color']=colors if isinstance(colors,str) else colors[layer.options['levels'].index(feature.properties['level'])%len(colors)] if colors else layer.to_color(layer._array[index])
                callback = layer.options.get("feature_style")
                if callback is not None:
                    style.update(style_dict(callback(feature)))
                _geometry(feature.geometry, style, vp, scene, cull=cull,
                          pixel_padding=pixel_padding)
        elif layer.kind == "scatter":
            for i, coordinate in enumerate(layer.data):
                size=layer._scatter_size(i)
                if size==0:continue
                p = vp.project(*coordinate)
                if p:
                    _marker(p, math.sqrt(size), layer._scatter_style(i), scene, mapbox)
        elif layer.kind == "grid":
            first = len(scene.items)
            metadata['grid_specs'].extend(_grid(layer, vp, scene))
            metadata['grid_indices'].extend(range(first,len(scene.items)))
            metadata["tick_indices"].extend(i for i in range(first,len(scene.items)) if scene.items[i].clip is None)
        elif layer.kind=='mesh':
            if layer._array is None:continue
            lon,lat,rows=layer.data
            for j,row in enumerate(rows):
                for i,_ in enumerate(row):
                    value=layer._array[j*len(row)+i]
                    if value is None or not math.isfinite(value):continue
                    style=dict(layer.style,facecolor=layer.to_color(value))
                    ring=[(lon[i],lat[j]),(lon[i+1],lat[j]),(lon[i+1],lat[j+1]),(lon[i],lat[j+1]),(lon[i],lat[j])]
                    _polygon([ring],style,vp,scene)
        elif layer.kind=='vectors':
            _vectors(layer,vp,scene)
        elif layer.kind == "text":
            lon,lat,text = layer.data
            p = _axes_xy(lon,lat,mapbox) if layer.options["transform"] == "axes" else vp.project(lon,lat)
            if p:
                first = len(scene.items)
                _text(scene,*p, text, text_style(layer.style), mapbox)
                if layer.options["transform"] == "axes":
                    metadata["static_indices"].extend(range(first,len(scene.items)))
        elif layer.kind == "annotation":
            _annotation(layer, vp, scene)
        elif layer.kind == "labels":
            _labels(layer, vp, scene, planned)
    metadata["end"] = len(scene.items)
    tick_start=len(scene.items)
    if ax._frame and not inset:
        first=len(scene.items)
        _axis_ticks(vp,scene,ax)
        metadata["tick_indices"].extend(range(first,len(scene.items)))
    tick_end=len(scene.items)
    if ax._frame:
        edges=dict(left=[(x,y),(x,y+h)],right=[(x+w,y),(x+w,y+h)],
                   top=[(x,y),(x+w,y)],bottom=[(x,y+h),(x+w,y+h)])
        for side,spine in ax.spines.items():
            if spine.visible:scene.add(Path([edges[side]],False,dict(stroke=spine.color,stroke_width=spine.linewidth*POINT,linecap='square')))
    metadata["decoration_start"] = len(scene.items)
    if ax._scale_bar:
        with scene.layout_artist(ax._scale_bar):_scale(ax._scale_bar, vp, scene)
    if ax._north:
        with scene.layout_artist(ax._north):_north(ax._north, vp, scene)
    if ax._compass:
        with scene.layout_artist(ax._compass):_north(ax._compass, vp, scene)
    metadata["decoration_end"] = len(scene.items)
    if ax._legend:
        with scene.layout_artist(ax._legend):_legend(ax, vp, scene)
    if ax._colorbar:
        with scene.layout_artist(ax._colorbar):render_colorbar(ax._colorbar,barbox,scene)
    from .layout_engine import primitive_bounds
    tickboxes=[primitive_bounds(p) for p in scene.items[tick_start:tick_end] if isinstance(p,Text)]
    tick_bottom=max([y+h]+[b[1]+b[3] for b in tickboxes if b is not None and b[1]>=y+h])
    tick_left=min([x]+[b[0] for b in tickboxes if b is not None and b[0]+b[2]<=x])
    if getattr(ax,"_xlabel",None):
        label,style=ax._xlabel
        with scene.layout_artist(ax._xlabel):
            _text(scene,x+w/2,tick_bottom+ax._labelpad['x']*POINT,label,text_style(dict(style,ha="center",va="top")))
    if getattr(ax,"_ylabel",None):
        label,style=ax._ylabel
        with scene.layout_artist(ax._ylabel):
            _text(scene,tick_left-ax._labelpad['y']*POINT,mapbox[1]+mapbox[3]/2,label,text_style({'ha':"center",'va':"bottom",'rotation':90,**style}))
    if ax._title:
        title,style = ax._title
        align=style.get("ha","center")
        with scene.layout_artist(ax._title):
            _text(scene,x+{"left":0,"center":w/2,"right":w}[align],y-8-subtitle_height,title,text_style(dict(style,ha=align,va="bottom")))
    if ax._subtitle:
        title,style = ax._subtitle
        align=style.get("ha","center")
        with scene.layout_artist(ax._subtitle):
            _text(scene,x+{"left":0,"center":w/2,"right":w}[align],y-6,title,text_style(dict(style,ha=align,va="bottom")))
    if ax._overview:
        from .overview import render_overview
        with scene.layout_artist(ax._overview):render_overview(ax,vp,scene,metadata,cull=cull)
    for child in ax.insets:
        if not child.get_visible():continue
        ix,iy,iw,ih = child.position
        cx,cy,cw,ch = mapbox
        childbox = cx+ix*cw, cy+(1-iy-ih)*ch, iw*cw, ih*ch
        with scene.layout_artist(child):
            scene.add(Rect(childbox[0]-4,childbox[1]-4,childbox[2]+8,childbox[3]+8,dict(fill="white",stroke="#90a5ac",stroke_width=1)))
            render_axes(child,scene,childbox,inset=True,measure_layout=measure_layout,cull=cull)
    if not inset:
        fw,fh=scene.width,scene.height;px,py,pw,ph=ax.position
        scene._layout_groups.append(((ax,),layout_start,len(scene.items),(px*fw,(1-py-ph)*fh,pw*fw,ph*fh)))


def _axes_xy(x,y,box):
    bx,by,bw,bh = box
    return bx+x*bw, by+(1-y)*bh


def _text(scene,x,y,value,style,clip=None):
    """Lay out a multiline block using portable, single-line scene primitives.

    Backgrounds, collision boxes and line positions share font metrics and one
    rotation origin. Backends perform glyph rasterization without relayout.
    """
    lines = str(value).replace("\r\n","\n").replace("\r","\n").split("\n")
    style = dict(style)
    fs = style.get("font_size",12)
    advance = fs*1.2
    baseline = style.get("baseline","alphabetic")
    offset = {"top":0,"middle":-(len(lines)-1)*advance/2,
              "bottom":-(len(lines)-1)*advance,"alphabetic":0}[baseline]
    angle = math.radians(style.get("rotation",0))
    def point(dx,dy):
        return x+dx*math.cos(angle)-dy*math.sin(angle),y+dx*math.sin(angle)+dy*math.cos(angle)
    background = style.pop("background",None)
    if background:
        from .typography import text_bounds
        left,top,width,height=text_bounds(value,style)
        corners=[point(left-3,top-3),point(left+width+3,top-3),
                 point(left+width+3,top+height+3),point(left-3,top+height+3)]
        scene.add(Path([corners],True,dict(fill=background,opacity=style.get("opacity",1)),clip))
    for i,line in enumerate(lines):
        if line:
            scene.add(Text(*point(0,offset+i*advance),line,style,clip))


_add_text = _text


def _geometry_padding(style,pixel_padding):
    width=style.get('linewidth',.8)
    if style.get('hatch'):width=max(width,style.get('hatch_linewidth',1))
    return 4*width*POINT+pixel_padding


def _geometry_candidates(layer,vp,pixel_padding):
    """Index only immutable cylindrical data; preserve callback evaluation."""
    from .geometry import FeatureCollection
    from .projections import Equirectangular,Mercator
    if (type(layer.data) is not FeatureCollection or len(layer.data)<64 or
            type(vp.projection) not in (Equirectangular,Mercator) or
            layer.options.get('feature_style') is not None):return None
    unsafe=('curved','arrow','marker','symbol')
    if any(layer.style.get(key) for key in unsafe):return None
    width=layer.style.get('linewidth',.8)
    def valid_width(value):
        return isinstance(value,Real) and not isinstance(value,bool) and math.isfinite(value) and value>=0
    if not valid_width(width):return None
    if layer.style.get('hatch'):
        hatch_width=layer.style.get('hatch_linewidth',1)
        if not valid_width(hatch_width):return None
        width=max(width,hatch_width)
    extra=[];styles=layer.options.get('feature_styles')
    if styles is not None:
        if not isinstance(styles,(tuple,list)) or len(styles)!=len(layer.data):return None
        for i,style in enumerate(styles):
            if not isinstance(style,dict):return None
            candidate=style.get('linewidth',layer.style.get('linewidth',.8))
            if not valid_width(candidate):return None
            width=max(width,candidate)
            if style.get('hatch',layer.style.get('hatch')):
                hatch_width=style.get('hatch_linewidth',layer.style.get('hatch_linewidth',1))
                if not valid_width(hatch_width):return None
                width=max(width,hatch_width)
            if any(style.get(key) for key in unsafe):extra.append(i)
    padding=4*width*POINT+pixel_padding
    prepared=layer.data._viewport_indexes.get(layer.data,vp.projection)
    return prepared.query(vp._query_bounds(padding),extra)


def _geometry(geometry, style, vp, scene, *, cull=False,pixel_padding=2):
    kind,coords = geometry.type,geometry.coordinates
    # Keep callbacks, feature indices, decorations and display-sized symbols
    # unchanged. Curves/arrows/markers need their own conservative envelopes.
    if (cull and kind in ("LineString","MultiLineString","Polygon","MultiPolygon") and
            not any(style.get(key) for key in ("curved","arrow","marker","symbol"))):
        padding = _geometry_padding(style,pixel_padding)
        if not vp.may_intersect(geometry.bounds,padding):
            return
    if kind == "GeometryCollection":
        for child in geometry.geometries:
            _geometry(child,style,vp,scene,cull=cull,pixel_padding=pixel_padding)
    elif kind in ("Point", "MultiPoint"):
        for coordinate in (coords,) if kind == "Point" else coords:
            p = vp.project(*coordinate[:2])
            if p:
                _marker(p,style.get("markersize",7),style,scene,vp.box)
    elif kind in ("LineString", "MultiLineString"):
        for line in (coords,) if kind == "LineString" else coords:
            _line(line,style,vp,scene)
            if style.get("marker"):
                for coordinate in line:
                    p=vp.project(*coordinate[:2])
                    if p:
                        _marker(p,style.get("markersize",6),style,scene,vp.box)
    elif kind in ("Polygon", "MultiPolygon"):
        for polygon in (coords,) if kind == "Polygon" else coords:
            _polygon(polygon,style,vp,scene)


def _line(coordinates,style,vp,scene):
    parts = split_antimeridian(coordinates, vp.projection.central_longitude)
    rendered=[]
    for part in parts:
        groups, current = [], []
        for point in densify(part):
            p = vp.project(*point)
            if p is None:
                if len(current)>1:
                    groups.append(current)
                current=[]
            else:
                current.append(p)
        if len(current)>1:
            groups.append(current)
        for points in groups:
            if style.get("curved"):
                points = _curve(points, float(style["curved"]))
            scene.add(Path([points],False,path_style(style),vp.box))
            rendered.append(points)
    # Arrowheads belong to the actual route endpoints, never a clipping seam.
    arrow=style.get("arrow",False)
    if rendered and arrow:
        if arrow in (True,"end","both") and vp.project(*coordinates[-1][:2]) is not None:
            _arrowhead(rendered[-1][-2],rendered[-1][-1],style,scene,vp.box)
        if arrow in ("start","both") and vp.project(*coordinates[0][:2]) is not None:
            _arrowhead(rendered[0][1],rendered[0][0],style,scene,vp.box)


def _curve(points, amount):
    # Each segment is a quadratic Bezier. Densification before this stage can
    # be dense; using original path endpoints produces a deliberate diagram arc.
    a,b = points[0],points[-1]
    control = ((a[0]+b[0])/2-(b[1]-a[1])*amount,(a[1]+b[1])/2+(b[0]-a[0])*amount)
    return [((1-t)**2*a[0]+2*(1-t)*t*control[0]+t*t*b[0],
             (1-t)**2*a[1]+2*(1-t)*t*control[1]+t*t*b[1]) for t in (i/48 for i in range(49))]

def _vectors(layer,vp,scene):
    from .geometry import destination
    magnitudes=[math.hypot(u,v) for lon,lat,u,v in layer.data]
    scale=layer.options['scale'] or (sum(magnitudes)/max(1,len(magnitudes))*max(10,math.sqrt(len(magnitudes)))) or 1
    for i,((lon,lat,u,v),magnitude) in enumerate(zip(layer.data,magnitudes)):
        if magnitude==0:continue
        p=vp.project(lon,lat)
        if not vp.inside(p):continue
        q=vp.project(*destination(lon,lat,math.degrees(math.atan2(u,v)),1000))
        if q is None:continue
        dx,dy=q[0]-p[0],q[1]-p[1];length=math.hypot(dx,dy)
        if length<1e-10:continue
        size=magnitude/scale*vp.box[2];end=(p[0]+dx/length*size,p[1]+dy/length*size)
        if vp.projection.name=='orthographic':
            cx,cy=vp.xy(0,0);radius=vp.projection.radius*vp.scale
            ex,ey=end[0]-p[0],end[1]-p[1];px,py=p[0]-cx,p[1]-cy
            if (end[0]-cx)**2+(end[1]-cy)**2>radius*radius:
                a=ex*ex+ey*ey;b=2*(px*ex+py*ey);c=px*px+py*py-radius*radius
                t=max(0,min(1,(-b+math.sqrt(max(0,b*b-4*a*c)))/(2*a)))
                end=p[0]+ex*t,p[1]+ey*t;size*=t
                if size<2:continue
        style=dict(layer.style)
        if layer._array is not None:style['color']=layer.to_color(layer._array[i])
        style.setdefault('arrowsize',min(size*.4,6*POINT))
        scene.add(Path([[p,end]],False,path_style(style),vp.box));_arrowhead(p,end,style,scene,vp.box)


def _clip_latitude(ring, low, high):
    points=list(ring[:-1] if ring and ring[0]==ring[-1] else ring)
    for boundary,above in ((low,True),(high,False)):
        result=[]
        if not points:
            break
        a=points[-1]
        ain=a[1]>=boundary if above else a[1]<=boundary
        for b in points:
            bin_=b[1]>=boundary if above else b[1]<=boundary
            if ain != bin_:
                t=(boundary-a[1])/(b[1]-a[1])
                result.append((a[0]+t*(b[0]-a[0]),boundary))
            if bin_:
                result.append(b[:2])
            a,ain=b,bin_
        points=result
    return points+[points[0]] if len(points)>=3 else []


def _polygon(rings,style,vp,scene):
    if not rings:
        return
    if vp.projection.name == "orthographic":
        from .geometry import clip_orthographic_polygon
        projected = clip_orthographic_polygon(rings, vp.projection)
        for polygon in projected:
            paths=[[vp.xy(*p) for p in ring] for ring in polygon]
            if paths:
                scene.add(Path(paths,True,path_style(style,True),vp.box))
                add_hatches(scene,paths,style,vp.box)
        return
    for polygon in clip_polygon_antimeridian(rings,vp.projection.central_longitude):
        paths=[]
        for index,ring in enumerate(polygon):
            if vp.projection.name == "mercator":
                ring = _clip_latitude(ring,-vp.projection.max_latitude,vp.projection.max_latitude)
            if not ring:
                if index==0:
                    break
                continue
            points=[vp.project(*p) for p in densify(ring)]
            if any(p is None for p in points):
                raise ValueError("Polygon crosses an unsupported projection singularity; use a regional extent/data subset")
            if len(points)>2:
                paths.append(points)
        else:
            if paths:
                scene.add(Path(paths,True,path_style(style,True),vp.box))
                add_hatches(scene,paths,style,vp.box)


def _marker(point,size,style,scene,clip):
    x,y=point
    marker=style.get("marker","o")
    radius=size*POINT/2
    drawstyle=path_style(dict(facecolor=style.get("color","#157e92"),edgecolor="white",linewidth=.9,**{k:v for k,v in style.items() if k not in ("facecolor","edgecolor","linewidth")}),True)
    drawstyle.update(fill=style.get("markerfacecolor",style.get("facecolor",style.get("color","#1f77b4"))),
        stroke=style.get("markeredgecolor",style.get("edgecolor",style.get("color","#1f77b4"))),
        stroke_width=style.get("markeredgewidth",1)*POINT,dash=())
    if style.get("symbol") is not None:
        _text(scene,x,y,str(style["symbol"]),text_style(dict(style,fontsize=size,ha="center",va="center")),clip)
        return
    if marker in ("o","circle"):
        scene.add(Circle(x,y,radius,drawstyle,clip))
        return
    shapes={"s":[(-1,-1),(1,-1),(1,1),(-1,1)],"square":[(-1,-1),(1,-1),(1,1),(-1,1)],
            "^": [(0,-1),(1,1),(-1,1)],"v":[(0,1),(1,-1),(-1,-1)],
            "D":[(0,-1.4),(1,0),(0,1.4),(-1,0)],"diamond":[(0,-1.4),(1,0),(0,1.4),(-1,0)]}
    if marker=="*":
        shape=[(math.sin(i*math.pi/5)*(1.3 if i%2==0 else .55),-math.cos(i*math.pi/5)*(1.3 if i%2==0 else .55)) for i in range(10)]
    elif marker in ("p","h"):
        count=5 if marker=="p" else 6
        shape=[(math.sin(i*2*math.pi/count),-math.cos(i*2*math.pi/count)) for i in range(count)]
    elif marker in ("+","x"):
        shape=None
    else:
        if marker not in shapes:
            raise ValueError(f"Unsupported marker {marker!r}; use o,s,^,v,D,*,p,h,+,x or symbol='text'")
        shape=shapes[marker]
    angle=math.radians(-style.get("rotation",0))
    def transform(p):
        return x+radius*(p[0]*math.cos(angle)-p[1]*math.sin(angle)),y+radius*(p[0]*math.sin(angle)+p[1]*math.cos(angle))
    if shape:
        scene.add(Path([[transform(p) for p in shape]],True,drawstyle,clip))
    else:
        segments=[[(-1,0),(1,0)],[(0,-1),(0,1)]] if marker=="+" else [[(-1,-1),(1,1)],[(-1,1),(1,-1)]]
        drawstyle.update(fill="none",stroke=style.get("color","#157e92"),stroke_width=max(1.3,drawstyle["stroke_width"]))
        scene.add(Path([[transform(p) for p in line] for line in segments],False,drawstyle,clip))


def _arrows(points,style,scene,clip):
    arrow=style.get("arrow",False)
    if not arrow or len(points)<2:
        return
    if arrow in (True,"end","both"):
        _arrowhead(points[-2],points[-1],style,scene,clip)
    if arrow in ("start","both"):
        _arrowhead(points[1],points[0],style,scene,clip)


def _arrowhead(a,b,style,scene,clip):
    dx,dy=b[0]-a[0],b[1]-a[1]
    norm=math.hypot(dx,dy)
    if norm<1e-9:
        return
    dx,dy=dx/norm,dy/norm
    size=style.get("arrowsize",max(8,style.get("linewidth",1)*4))
    left=(b[0]-dx*size-dy*size*.42,b[1]-dy*size+dx*size*.42)
    right=(b[0]-dx*size+dy*size*.42,b[1]-dy*size-dx*size*.42)
    points=[left,b,right]
    arrowstyle=style.get("arrowstyle","triangle")
    if arrowstyle=="stealth":
        points.append((b[0]-dx*size*.62,b[1]-dy*size*.62))
    drawstyle=path_style(style)
    drawstyle.update(fill=drawstyle["stroke"] if arrowstyle!="open" else "none",dash=())
    scene.add(Path([points],arrowstyle!="open",drawstyle,clip))


def axis_tick_values(ax,axis,pixels,*,minor=False):
    controller=getattr(ax,axis+'axis');controller._pixels=pixels
    if minor:return controller.get_minorticklocs()
    if controller.locator_explicit:return controller.get_major_locator()()
    if ax._ticks[axis] is not None:return ax._ticks[axis]
    low,high=ax.get_xlim() if axis=='x' else ax.get_ylim()
    grid=ax._grid_format if ax._grid_format and ax._grid_format['labels'] else None
    if grid:
        step=grid['step']
        if step is None:
            w,e,s,n=ax.get_extent()
            step=next((v for v in (1,2,5,10,15,20,30,45,60,90) if v>=max(e-w,n-s)/6),90)
    else:
        target=(high-low)/max(2,min(9,pixels/(65 if axis=='x' else 42)))
        power=10**math.floor(math.log10(target))
        step=next(v*power for v in (1,2,2.5,5,10) if v*power>=target)
    if (high-low)/step>1500:raise ValueError('Too many ticks')
    return _ticks(low,high,step)


def _axis_ticks(vp,scene,ax):
    for minor in (False,True):_axis_tick_group(vp,scene,ax,minor=minor)

def _axis_tick_group(vp,scene,ax,*,minor):
    west,south,east,north=vp.extent
    x,y,w,h=vp.box
    degrees=bool(ax._grid_format and ax._grid_format['labels'])
    for axis in ('x','y'):
        settings=(ax._minor_tick_params if minor else ax._tick_params)[axis]
        values=axis_tick_values(ax,axis,w if axis=='x' else h,minor=minor)
        labels=(ax._minor_tick_labels if minor else ax._tick_labels)[axis]
        controller=getattr(ax,axis+'axis');formatter=controller.get_minor_formatter() if minor else controller.get_major_formatter()
        if degrees and not minor and not controller.formatter_explicit:
            from .ticker import LongitudeFormatter,LatitudeFormatter
            formatter=LongitudeFormatter(dateline_direction_label=True) if axis=='x' else LatitudeFormatter()
        formatter.set_locs(values)
        length=settings['length']*POINT
        inward=length if settings['direction']=='in' else length/2 if settings['direction']=='inout' else 0
        outward=length-inward
        for index,value in enumerate(values):
            low,high=(west,east) if axis=='x' else (south,north)
            if not low<=value<=high:continue
            # Minor locations may have been filtered against major ticks.
            source_index=(ax._minor_ticks[axis].index(value) if minor and labels is not None else index)
            label_visible=labels is None or labels[source_index].visible
            if labels is not None:label,custom=labels[source_index]
            else:
                custom={}
                label=str(formatter(value,index))
            for side in ('bottom','top') if axis=='x' else ('left','right'):
                if axis=='x':
                    p=vp.project(value,south if side=='bottom' else north)
                    if p is None or not x-1e-6<=p[0]<=x+w+1e-6:continue
                    base=y+h if side=='bottom' else y;sign=1 if side=='bottom' else -1
                    segment=[(p[0],base-sign*inward),(p[0],base+sign*outward)]
                    tx,ty=p[0],base+sign*(outward+settings['pad']*POINT)
                    alignment=dict(ha='center',va='top' if sign==1 else 'bottom')
                else:
                    p=vp.project(west if side=='left' else east,value)
                    if p is None or not y-1e-6<=p[1]<=y+h+1e-6:continue
                    base=x if side=='left' else x+w;sign=-1 if side=='left' else 1
                    segment=[(base-sign*inward,p[1]),(base+sign*outward,p[1])]
                    tx,ty=base+sign*(outward+settings['pad']*POINT),p[1]
                    alignment=dict(ha='right' if sign==-1 else 'left',va='center')
                if settings[side]:scene.add(Path([segment],False,dict(stroke=settings['color'],stroke_width=settings['width']*POINT)))
                if settings['label'+side] and label_visible and label:
                    style=dict(fontsize=settings['labelsize'],color=settings['labelcolor'],rotation=settings['rotation'],**alignment)
                    style.update(custom)
                    with scene.layout_artist(labels[source_index] if labels is not None else None):
                        _text(scene,tx,ty,label,text_style(style))


def _grid(layer,vp,scene):
    w,s,e,n=vp.extent
    x,y,bw,bh=vp.box
    ax=layer._axes
    minor=layer.options.get('which','major')=='minor'
    specs=[]
    for axis,config in layer.options['axes_config'].items():
        step=config['step'];controller=getattr(ax,axis+'axis')
        if step is None:
            values=axis_tick_values(ax,axis,bw if axis=='x' else bh,minor=minor)
        else:
            step=step or next((v for v in (1,2,5,10,15,20,30,45,60,90) if v>=max(e-w,n-s)/6),90)
            low,high=(w,e) if axis=='x' else (s,n)
            if (high-low)/step>1500:raise ValueError('Grid step creates too many lines for the current extent')
            values=_ticks(low,high,step)
            if minor:
                major=axis_tick_values(ax,axis,bw if axis=='x' else bh)
                values=[v for v in values if not any(abs(v-m)<1e-8 for m in major)]
        first=len(scene.items)
        for value in values:
            if axis=='x':
                if w<=value<=e:_line([(value,s),(value,n)],config['style'],vp,scene)
            elif s<=value<=n:
                _line([(w+(e-w)*i/90,value) for i in range(91)],config['style'],vp,scene)
        specs.append(dict(axis=axis,which='minor' if minor else 'major',step=config['step'],style=path_style(config['style']),indices=list(range(first,len(scene.items)))))
    return specs


def _ticks(low,high,step):
    start=math.ceil(low/step)
    return [i*step for i in range(start,math.floor(high/step)+1)]


def _annotation(layer,vp,scene):
    xy,xytext,text=layer.data
    target=vp.project(*xy)
    if target is None:
        return
    coords=layer.options["textcoords"]
    p=(target[0]+xytext[0],target[1]+xytext[1]) if coords=="offset pixels" else (_axes_xy(*xytext,vp.box) if coords=="axes" else vp.project(*xytext))
    if p is None:
        return
    if layer.style.get("arrow"):
        style=dict(layer.style)
        line=[p,target]
        scene.add(Path([line],False,path_style(style),vp.box))
        _arrowhead(p,target,style,scene,vp.box)
    _text(scene,*p,text,text_style(layer.style),vp.box)


def _labels(layer,vp,scene,planned):
    for i,feature in enumerate(layer.data):
        item=planned.get((id(layer),i))
        if item is None:continue
        p,text,anchor=item.position,item.text,item.anchor
        if layer.options.get('leader') and p!=anchor:
            scene.add(Path([[anchor,p]],False,dict(stroke=layer.style.get('color','black'),stroke_width=.5*POINT),vp.box))
        _text(scene,*p,text,item.style,vp.box)


@lru_cache(maxsize=4096)
def _label_position(geometry):
    if geometry.type=="Point":
        return geometry.coordinates[:2]
    if geometry.type in ("Polygon","MultiPolygon"):
        polygons=[geometry.coordinates] if geometry.type=="Polygon" else geometry.coordinates
        def area(r):
            return abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(r,r[1:])))
        rings=max(polygons,key=lambda p:area(p[0]))
        ring=rings[0]
        w,s,e,n=min(p[0] for p in ring),min(p[1] for p in ring),max(p[0] for p in ring),max(p[1] for p in ring)
        candidates=[((w+e)/2,(s+n)/2)]+[(w+(e-w)*(i+.5)/11,s+(n-s)*(j+.5)/11) for i in range(11) for j in range(11)]
        inside=[p for p in candidates if _inside_ring(p,ring) and not any(_inside_ring(p,r) for r in rings[1:])]
        if inside:
            # Prefer positions well inside the feature; labels do not fall in holes.
            edges=[(a,b) for r in rings for a,b in zip(r,r[1:])]
            return max(inside,key=lambda p:min(_segment_distance(p,a,b) for a,b in edges))
        return ring[0][:2]
    bounds=geometry.bounds
    if geometry.type in ('LineString','MultiLineString'):
        line=geometry.coordinates if geometry.type=='LineString' else max(geometry.coordinates,key=len,default=())
        if line:
            lengths=[math.hypot(b[0]-a[0],b[1]-a[1]) for a,b in zip(line,line[1:])];target=sum(lengths)/2
            for a,b,length in zip(line,line[1:],lengths):
                if length and target<=length:return (a[0]+(b[0]-a[0])*target/length,a[1]+(b[1]-a[1])*target/length)
                target-=length
            return line[0][:2]
    return ((bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2) if bounds else None


def _inside_ring(p,ring):
    x,y=p
    inside=False
    for a,b in zip(ring,ring[1:]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            inside=not inside
    return inside


def _segment_distance(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy))) if dx or dy else 0
    return (p[0]-a[0]-t*dx)**2+(p[1]-a[1]-t*dy)**2


def _overlap(a,b):
    return a[0]<b[0]+b[2] and a[0]+a[2]>b[0] and a[1]<b[1]+b[3] and a[1]+a[3]>b[1]


def _anchor(box,loc,width,height,pad=18):
    x,y,w,h=box
    return x+pad if "left" in loc else x+w-width-pad, y+pad if "upper" in loc else y+h-height-pad


def _component_frame(scene,x,y,width,height,options):
    """Shared legend/scale frame in physical point units."""
    if not options.get('frameon',True):return
    radius=2*POINT
    corners=[]
    for cx,cy,start in ((x+width-radius,y+radius,-90),(x+width-radius,y+height-radius,0),
                       (x+radius,y+height-radius,90),(x+radius,y+radius,180)):
        corners.extend((cx+radius*math.cos(math.radians(start+i*90/6)),cy+radius*math.sin(math.radians(start+i*90/6))) for i in range(7))
    scene.add(Path([corners],True,dict(fill=options.get('facecolor','white'),stroke=options.get('edgecolor','#cccccc'),stroke_width=options.get('linewidth',.8)*POINT,opacity=options.get('framealpha',.8))))


def _legend(ax,vp,scene):
    from .legend_layout import render_legend
    render_legend(ax._legend,vp,scene)


def _scale_labels(length,width,units,style):
    """Keep readable labels without stretching the measured distance.

    Use three graduations when they fit, then just the endpoints, then one
    combined total/unit caption. All candidates use the user's font size.
    """
    full=((0.,'0'),(.5,f'{length/2:g}'),(1.,f'{length:g}'))
    gap=max(2*POINT,style['font_size']*.3)
    for labels in (full,(full[0],full[-1])):
        edges=[(fraction*width-text_width(value,style)/2,
                fraction*width+text_width(value,style)/2) for fraction,value in labels]
        if all(a[1]+gap<=b[0] for a,b in zip(edges,edges[1:])):return labels,False
    return ((.5,f'{length:g} {units}'),),True


def _scale(options,vp,scene):
    fs=options['fontsize']*POINT
    maxwidth=min(vp.box[2]*.25,180)
    boxheight=fs*3.4
    factor={"m":1,"km":1000,"mi":1609.344}[options["units"]]
    labelstyle=text_style(dict(fontsize=options['fontsize'],ha='center',va='bottom',color=options['color']))
    unitstyle=text_style(dict(fontsize=options['fontsize'],ha='center',va='top',color=options['color']))
    # Center the measured bar inside a symmetric content envelope. Keep just
    # half a font size of breathing room beyond the widest label on either end.
    labels=();compact=False;metrics=()
    def placement(width):
        left,right=-.3*POINT,width+.3*POINT  # Bar stroke extends past its ends.
        for fraction,text_width_ in metrics:
            left=min(left,fraction*width-text_width_/2)
            right=max(right,fraction*width+text_width_/2)
        if not compact:
            unitwidth=text_width(options['units'],unitstyle)
            left=min(left,(width-unitwidth)/2);right=max(right,(width+unitwidth)/2)
        sidepad=fs*.5+max(-left,right-width)
        framewidth=width+2*sidepad
        bx,by=_anchor(vp.box,options['loc'],framewidth,boxheight,pad=fs*.5)
        return bx,by,bx+sidepad,by+fs*1.45,framewidth
    def measure(width):
        _,_,x,y,_=placement(width)
        reference,endpoint=vp.inverse(x,y),vp.inverse(x+width,y)
        if reference is None or endpoint is None:
            raise ValueError("Scale bar anchor lies outside the projection; choose a regional extent or another location")
        return haversine(reference,endpoint)/factor
    available=measure(maxwidth)
    if available <= 0:
        raise ValueError("Scale bar has no measurable geographic span at this location")
    def nice_length(available):
        power=10**math.floor(math.log10(available))
        return max(v for v in (power*.1,power*.2,power*.5,power,power*2,power*5) if v<=available)
    length=options["length"]
    if length is None:
        length=nice_length(available)
    # Test each label density at its final anchored size. This avoids a layout
    # oscillation at thresholds and recalculates distance after any frame shift.
    for count in (3,2,1):
        compact=count==1
        boxheight=fs*(1.45+.48+.5) if compact else fs*3.4
        while True:
            full=((0.,'0'),(.5,f'{length/2:g}'),(1.,f'{length:g}'))
            labels=full if count==3 else (full[0],full[-1]) if count==2 else ((.5,f'{length:g} {options["units"]}'),)
            metrics=tuple((fraction,text_width(value,labelstyle)) for fraction,value in labels)
            available=measure(maxwidth)
            if available<=0:raise ValueError('Scale bar has no measurable geographic span at this location')
            if options['length'] is None and length>available:
                length=nice_length(available);continue
            break
        if length>available:continue
        lo,hi=0.,maxwidth
        for _ in range(36):
            middle=(lo+hi)/2
            if measure(middle)>length:hi=middle
            else:lo=middle
        width=(lo+hi)/2
        gap=max(2*POINT,fs*.3)
        if all(a*width+aw/2+gap<=b*width-bw/2 for (a,aw),(b,bw) in zip(metrics,metrics[1:])):break
    else:
        raise ValueError("Requested scale bar is wider than its allotted space; use a shorter length")
    bx,by,x,y,framewidth=placement(width)
    _component_frame(scene,bx,by,framewidth,boxheight,options)
    for i in range(2):
        scene.add(Rect(x+i*width/2,y,width/2,fs*.48,dict(fill=options['color'] if i==0 else 'white',stroke=options['color'],stroke_width=.6*POINT)))
    for fraction,value in labels:_text(scene,x+fraction*width,y-fs*.3,value,labelstyle)
    if not compact:_text(scene,x+width/2,y+fs*.85,options['units'],unitstyle)


def _north(options,vp,scene):
    size=options['size']*POINT
    labelpad=13*POINT
    x,y=_anchor(vp.box,options['loc'],size+2*labelpad,size+2*labelpad,pad=10)
    cx,cy=x+size/2+labelpad,y+size/2+labelpad
    geo=vp.inverse(cx,cy)
    angle=0.
    if geo and abs(geo[1])<89.9:
        north=vp.project(geo[0],min(89.99,geo[1]+.1))
        if north:
            angle=math.atan2(north[0]-cx,-(north[1]-cy))
    def point(dx,dy):
        return cx+dx*math.cos(angle)-dy*math.sin(angle),cy+dx*math.sin(angle)+dy*math.cos(angle)
    if options["compass"]:
        # Eight symmetric points; each arm has contrasting halves. Draw
        # intercardinal arms first so cardinal arms remain visually dominant.
        for arm in (1,3,5,7,0,2,4,6):
            theta=arm*math.pi/4
            radius=size/2*(1 if arm%2==0 else .63)
            tip=(radius*math.sin(theta),-radius*math.cos(theta))
            side=(size*.105*math.cos(theta),size*.105*math.sin(theta))
            for sign,fill in ((1,options['color']),(-1,'white')):
                vertices=[point(0,0),point(*tip),point(side[0]*sign,side[1]*sign)]
                scene.add(Path([vertices],True,dict(fill=fill,stroke=options['color'],stroke_width=.55*POINT)))
        for text,dx,dy in (('N',0,-size/2-labelpad*.65),('S',0,size/2+labelpad*.65),
                           ('E',size/2+labelpad*.65,0),('W',-size/2-labelpad*.65,0)):
            _text(scene,*point(dx,dy),text,text_style(dict(fontsize=10,fontweight='bold' if text=='N' else 'normal',ha='center',va='center',color=options['color'],halo='white',halo_width=1)))
    else:
        for sign,fill in ((-1,options['color']),(1,'white')):
            vertices=[point(0,-size/2),point(sign*size*.4,size*.45),point(0,size*.18)]
            scene.add(Path([vertices],True,dict(fill=fill,stroke=options['color'],stroke_width=.65*POINT)))
        _text(scene,*point(0,-size/2-labelpad*.65),'N',text_style(dict(fontsize=11,fontweight='bold',ha='center',va='center',color=options['color'])))


