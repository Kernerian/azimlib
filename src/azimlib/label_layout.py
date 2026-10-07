"""Font-aware label placement with global priorities and a spatial hash."""
import math
from dataclasses import dataclass
from .typography import text_width,text_bounds,text_rotation_offset
from .styles import text_style

def text_box(x,y,value,style,padding=2):
    dx,dy=text_rotation_offset(value,style);x+=dx;y+=dy
    bx,by,width,height=text_bounds(value,style)
    left,top=x+bx,y+by
    angle=math.radians(style.get('rotation',0))
    points=[(x+(a-x)*math.cos(angle)-(b-y)*math.sin(angle),y+(a-x)*math.sin(angle)+(b-y)*math.cos(angle)) for a,b in ((left,top),(left+width,top),(left+width,top+height),(left,top+height))]
    pad=padding+style.get('stroke_width',0)/2+(3 if style.get('background') else 0)
    return min(p[0] for p in points)-pad,min(p[1] for p in points)-pad,max(p[0] for p in points)-min(p[0] for p in points)+2*pad,max(p[1] for p in points)-min(p[1] for p in points)+2*pad

class BoxIndex:
    def __init__(self,cell=48):self.cell=cell;self.cells={}
    def keys(self,box):
        x,y,w,h=box
        return [(i,j) for i in range(math.floor(x/self.cell),math.floor((x+w)/self.cell)+1) for j in range(math.floor(y/self.cell),math.floor((y+h)/self.cell)+1)]
    def add(self,box):
        for key in self.keys(box):self.cells.setdefault(key,[]).append(box)
    def crosses(self,a,b,*,allow_origin=False):
        from .line_labels import clip_segment
        envelope=(min(a[0],b[0]),min(a[1],b[1]),abs(a[0]-b[0]),abs(a[1]-b[1]))
        for key in self.keys(envelope):
            for x,y,w,h in self.cells.get(key,()):
                if allow_origin and x<=a[0]<=x+w and y<=a[1]<=y+h:continue
                if clip_segment(a,b,(x,y,w,h)) is not None:return True
        return False
    def overlaps(self,box):
        from .render_map import _overlap
        return any(_overlap(box,other) for key in self.keys(box) for other in self.cells.get(key,()))

@dataclass(frozen=True)
class LabelPlacement:
    position: tuple
    text: str
    anchor: tuple
    style: dict
    box: tuple
    glyphs: tuple=()
    repetitions: tuple=()


def obstacle_boxes(ax,vp):
    """Visible explicit artists reserve space regardless of in_layout status."""
    from .render_map import _axes_xy,_legend,_scale,_north,_annotation,_text,_marker,render_axes
    from .scene import Scene,Rect
    from .layout_engine import primitive_bounds
    scene=Scene(1,1)
    for layer in ax.layers:
        if not layer.visible:continue
        if layer.kind=='scatter':
            for i,coordinate in enumerate(layer.data):
                size=layer._scatter_size(i)
                if size==0:continue
                p=vp.project(*coordinate)
                if p:
                    _marker(p,math.sqrt(size),layer._scatter_style(i),scene,vp.box)
        elif layer.kind=='text':
            x,y,text=layer.data;p=_axes_xy(x,y,vp.box) if layer.options['transform']=='axes' else vp.project(x,y)
            if p:_text(scene,*p,text,text_style(layer.style),vp.box)
        elif layer.kind=='annotation':_annotation(layer,vp,scene)
    for make,options in ((_legend,ax._legend),(_scale,ax._scale_bar),(_north,ax._north),(_north,ax._compass)):
        if not options:continue
        make(ax,vp,scene) if make is _legend else make(options,vp,scene)
    if ax._overview:
        from .overview import overview_box
        x,y,w,h=overview_box(ax._overview,vp)
        scene.add(Rect(x-4,y-4,w+8,h+8,{'fill':'white'}))
    for child in ax.insets:
        if not child.get_visible():continue
        x,y,w,h=vp.box;ix,iy,iw,ih=child.position
        box=(x+ix*w,y+(1-iy-ih)*h,iw*w,ih*h)
        scene.add(Rect(box[0]-4,box[1]-4,box[2]+8,box[3]+8,{'fill':'white'}))
        render_axes(child,scene,box,inset=True,measure_layout=True)
    boxes=[]
    for item in scene.items:
        if item.style.get('opacity',1)==0:continue
        box=primitive_bounds(item)
        if box is not None:boxes.append((box[0]-2,box[1]-2,box[2]+4,box[3]+4))
    return boxes


def _polygon_contains_box(geometry,box,vp):
    from .render_map import _inside_ring
    from .line_labels import clip_segment
    from .viewport import densify
    polygons=[geometry.coordinates] if geometry.type=='Polygon' else geometry.coordinates
    x,y,w,h=box
    # Conservative footprint check, including holes and the complete text box.
    for dx,dy in ((0,0),(.5,0),(1,0),(0,.5),(.5,.5),(1,.5),(0,1),(.5,1),(1,1)):
        geo=vp.inverse(x+dx*w,y+dy*h)
        if geo is None or not any(_inside_ring(geo,p[0]) and not any(_inside_ring(geo,r) for r in p[1:]) for p in polygons):return False
    # Detect narrow holes/concavities between samples, including boundaries
    # wholly enclosed by the text box. Use the same projection densification.
    for polygon in polygons:
        for ring in polygon:
            previous=None
            for coordinate in densify(ring):
                point=vp.project(*coordinate)
                if point is not None and previous is not None and clip_segment(previous,point,box) is not None:return False
                previous=point
    return True


def plan_labels(ax,vp):
    from .render_map import _label_position
    index=BoxIndex();leader_index=BoxIndex();candidates=[];plan={}
    for box in obstacle_boxes(ax,vp):index.add(box)
    span=max(vp.extent[2]-vp.extent[0],vp.extent[3]-vp.extent[1])
    for layer in ax.layers:
        if not layer.visible or layer.kind!='labels':continue
        if span<layer.options.get('min_span',0) or layer.options.get('max_span') is not None and span>layer.options['max_span']:continue
        for i,feature in enumerate(layer.data):
            value=feature.properties.get(layer.options['field'])
            if value is None or not str(value) or feature.geometry is None:continue
            field=layer.options.get('priority_field','priority')
            value_priority=feature.properties.get(field) if field is not None else None
            priority=float(layer.style.get('priority',0) if value_priority is None else value_priority)
            candidates.append((-priority,len(candidates),layer,i,feature,str(value)))
    for _,_,layer,i,feature,text in sorted(candidates):
        style=text_style(layer.style);fs=style['font_size']
        width=text_width(text,style);d=fs*.9
        default=((0,0),(width/2+d,0),(-width/2-d,0),(0,-fs*1.5),(0,fs*1.5),(width/2+d,-fs*1.5),(-width/2-d,-fs*1.5),(width/2+d,fs*1.5),(-width/2-d,fs*1.5))
        padding=layer.options.get('padding',2)
        if layer.options.get('placement')=='curve':
            from .curved_text import curve_candidates
            placements=[];repeat=layer.options.get('repeat')
            for poses in curve_candidates(feature.geometry,vp,text,style,repeat):
                boxes=[text_box(*p,char,dict(style,rotation=angle,rotation_mode='anchor'),padding) for char,p,angle in poses]
                x0=min(b[0] for b in boxes);y0=min(b[1] for b in boxes)
                box=(x0,y0,max(b[0]+b[2] for b in boxes)-x0,max(b[1]+b[3] for b in boxes)-y0)
                x,y,w,h=vp.box
                if x0<x or y0<y or x0+box[2]>x+w or y0+box[3]>y+h:continue
                if layer.options['avoid_overlap'] and index.overlaps(box):continue
                index.add(box);leader_index.add(box);p=poses[len(poses)//2][1]
                placements.append(LabelPlacement(p,text,p,style,box,poses))
                if repeat is None:break
            if placements:
                first=placements[0]
                plan[(id(layer),i)]=LabelPlacement(first.position,text,first.anchor,style,first.box,first.glyphs,tuple(placements[1:]))
            continue
        along=feature.geometry.type in ('LineString','MultiLineString') and layer.options.get('placement','auto')!='point'
        padding=layer.options.get('padding',2)
        if along:
            from .line_labels import line_candidates
            anchors=line_candidates(feature.geometry,vp,width,text_bounds(text,style)[3],padding)
        else:
            position=_label_position(feature.geometry);p=vp.project(*position) if position else None
            anchors=[(p,style.get('rotation',0))] if vp.inside(p) else []
            if feature.geometry.type in ('Polygon','MultiPolygon'):
                from .polygon_labels import interior_anchors
                anchors=[(q,style.get('rotation',0)) for q in interior_anchors(feature.geometry,vp)]+anchors
        placed=False
        for p,angle in anchors:
            candidate_style=dict(style)
            if along and 'rotation' not in layer.style:candidate_style['rotation']=angle
            if along:
                theta=math.radians(angle);normal=(-math.sin(theta)*fs,math.cos(theta)*fs)
                offsets=layer.options.get('offsets') or ((0,0),normal,(-normal[0],-normal[1]))
            else:offsets=layer.options.get('offsets') or default
            for dx,dy in offsets:
                q=(p[0]+dx,p[1]+dy);box=text_box(*q,text,candidate_style,padding)
                x,y,w,h=vp.box
                if box[0]<x or box[1]<y or box[0]+box[2]>x+w or box[1]+box[3]>y+h:continue
                if feature.geometry.type in ('Polygon','MultiPolygon') and not _polygon_contains_box(feature.geometry,box,vp):continue
                if layer.options['avoid_overlap'] and index.overlaps(box):continue
                if layer.options.get('leader') and q!=p:
                    from .polygon_labels import leader_endpoint
                    endpoint=leader_endpoint(p,box)
                    if leader_index.crosses(p,endpoint) or index.crosses(p,endpoint,allow_origin=True):continue
                index.add(box);leader_index.add(box);plan[(id(layer),i)]=LabelPlacement(q,text,p,candidate_style,box)
                placed=True;break
            if placed:break
    return plan
