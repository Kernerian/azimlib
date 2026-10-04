"""Shared locator composition for static exports, desktop and browser."""
from .viewport import Viewport
from .scene import Path,Rect

def overview_box(options,viewport):
    """Shared visible component bounds, used by drawing and label placement."""
    from .render_map import _anchor
    context=options.context_axes
    probe=Viewport(context.projection,context._get_extent(),(0,0,100,100))
    west,south,east,north=probe.projected_bounds
    width=min(options['width'],viewport.box[2]*.45)
    height=width*(north-south)/(east-west)
    if height>viewport.box[3]*.45:
        width*=viewport.box[3]*.45/height;height=viewport.box[3]*.45
    x,y=_anchor(viewport.box,options['loc'],width,height,pad=10)
    return x,y,width,height


def render_overview(ax,viewport,scene,metadata,*,measure_layout=False,cull=False):
    from .render_map import render_axes,_component_frame
    options=ax._overview;context=options.context_axes
    x,y,width,height=overview_box(options,viewport)
    _component_frame(scene,x-4,y-4,width+8,height+8,{'framealpha':1})
    first=len(scene.items)
    render_axes(context,scene,(x,y,width,height),inset=True,measure_layout=measure_layout,cull=cull)
    mini=scene.maps.pop()
    mini['content_start']=first;mini['content_end']=len(scene.items)
    metadata['overview_map']=mini
    vp=Viewport(context.projection,context._get_extent(),mini['box'])
    left,bottom,right,top=viewport.projected_bounds
    a,b=vp.xy(left,top),vp.xy(right,bottom)
    x,y,width,height=mini['box']
    x0=max(x,min(x+width,min(a[0],b[0])));x1=max(x,min(x+width,max(a[0],b[0])))
    y0=max(y,min(y+height,min(a[1],b[1])));y1=max(y,min(y+height,max(a[1],b[1])))
    shade={'fill':'black','opacity':options['shade_alpha']}
    mini['shade_indices']=list(range(len(scene.items),len(scene.items)+4))
    scene.add(Rect(x,y,width,y0-y,shade))
    scene.add(Rect(x,y1,width,y+height-y1,shade))
    scene.add(Rect(x,y0,x0-x,y1-y0,shade))
    scene.add(Rect(x1,y0,x+width-x1,y1-y0,shade))
    mini['focus_index']=len(scene.items)
    mini['focus_box']=(x0,y0,x1-x0,y1-y0)
    scene.add(Rect(x0,y0,x1-x0,y1-y0,{'fill':'none','stroke':'black','stroke_width':1.0}))
