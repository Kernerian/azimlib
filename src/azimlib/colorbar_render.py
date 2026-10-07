"""Backend-neutral colorbar layout, gradient, ticks and extensions."""
from .scene import Rect,Path
from .styles import text_style
from .typography import POINT
from .colors import BoundaryNorm,LogNorm


def contour_position(bar,value):
    """Own interpolation along unfilled contour colorbars (geographic levels)."""
    import math
    levels=bar.mappable.levels
    if not math.isfinite(value):return None
    if len(levels)==1:return value-levels[0]+.5
    if isinstance(bar.norm,LogNorm):
        if value<=0 or levels[0]<=0:return None
        return math.log(value/levels[0])/math.log(levels[-1]/levels[0])
    if bar['spacing']=='proportional':return (value-levels[0])/(levels[-1]-levels[0])
    if value<levels[0]:return -1.
    if value>levels[-1]:return 2.
    return next((i+(value-a)/(b-a) for i,(a,b) in enumerate(zip(levels,levels[1:])) if a<=value<=b),0)/(len(levels)-1)

def colorbar_layout(bar,box):
    x,y,w,h=box;fraction,pad=bar['fraction'],bar['pad'];shrink=bar['shrink']
    location=bar['location']
    if bar.orientation=='vertical':
        length=h*shrink;thickness=min(w*fraction,length/bar['aspect'])
        bx=x+w*fraction-thickness if location=='left' else x+w-w*fraction
        barbox=(bx,y+(h-length)/2,thickness,length)
        reserve=w*(fraction+pad)+getattr(bar,'_layout_clearance',0)
        available=(x+reserve if location=='left' else x,y,w-reserve,h)
    else:
        length=w*shrink;thickness=min(h*fraction,length/bar['aspect'])
        by=y+h*fraction-thickness if location=='top' else y+h-h*fraction
        barbox=(x+(w-length)/2,by,length,thickness)
        reserve=h*(fraction+pad)+getattr(bar,'_layout_clearance',0)
        available=(x,y+reserve if location=='top' else y,w,h-reserve)
    return available,barbox

def render_colorbar(bar,box,scene):
    from .render_map import _text
    x,y,w,h=box;vertical=bar.orientation=='vertical';location=bar['location']
    mapped=bar.mappable;norm=mapped.norm
    contour=getattr(mapped,'options',{}).get('contour',False)
    if norm is not bar._norm:bar.update_normal(mapped)
    alpha=bar['alpha']
    count=256
    if contour and getattr(mapped,'filled',False):
        levels=mapped.levels
        stops=[i/(len(levels)-1) for i in range(len(levels))] if bar['spacing']=='uniform' else [(v-levels[0])/(levels[-1]-levels[0]) for v in levels]
        colors=[mapped._mapped_color(i) for i in range(len(levels)-1)]
    elif contour:
        # Unfilled ContourSet uses colored solid lines, not a gradient image.
        stops=[];colors=[]
        from .config import rcParams
        scene.add(Rect(x,y,w,h,dict(fill=bar.cax.facecolor if bar.cax is not None else rcParams['axes.facecolor'])))
        for index,level in enumerate(mapped.levels):
            t=contour_position(bar,level)
            if t is None:continue
            points=[(x,y+(1-t)*h),(x+w,y+(1-t)*h)] if vertical else [(x+t*w,y),(x+t*w,y+h)]
            scene.add(Path([points],False,dict(stroke=mapped._mapped_color(index),
                stroke_width=mapped.get_linewidths()[index]*POINT,
                opacity=alpha*(mapped.get_alpha() if mapped.get_alpha() is not None else 1),linecap='butt')))
    elif isinstance(norm,BoundaryNorm):
        boundaries=norm.boundaries
        stops=[i/(len(boundaries)-1) for i in range(len(boundaries))] if bar['spacing']=='uniform' else [(v-boundaries[0])/(boundaries[-1]-boundaries[0]) for v in boundaries]
        colors=[mapped.to_color((a+b)/2) for a,b in zip(boundaries,boundaries[1:])]
    elif getattr(mapped,'options',{}).get('mapped') and not mapped.options.get('continuous'):
        count=mapped.options['bins'];stops=[i/count for i in range(count+1)]
        colors=[mapped.cmap((i+.5)/count) for i in range(count)]
        if mapped.options.get('scheme')=='quantile' and bar['spacing']=='proportional':
            scale=mapped.options['color_scale'];span=scale['vmax']-scale['vmin']
            if span:stops=[(v-scale['vmin'])/span for v in scale['edges']]
    else:
        stops=[i/count for i in range(count+1)]
        colors=[mapped.to_color(norm.inverse((i+.5)/count)) for i in range(count)]
    for a,b,color in zip(stops,stops[1:],colors):
        cell=(x,y+(1-b)*h,w,(b-a)*h) if vertical else (x+a*w,y,(b-a)*w,h)
        # Adjacent cells must share device-pixel edges in SVG: independent
        # edge antialiasing otherwise reveals the page through tiny seams.
        scene.add(Rect(*cell,dict(fill=color,opacity=alpha,shape_rendering='crispEdges')))
    if bar['drawedges']:
        for t in stops[1:-1]:
            points=[(x,y+(1-t)*h),(x+w,y+(1-t)*h)] if vertical else [(x+t*w,y),(x+t*w,y+h)]
            scene.add(Path([points],False,dict(stroke=bar.outline.color,stroke_width=.4*POINT)))
    if bar.outline.visible:
        scene.add(Rect(x,y,w,h,dict(fill='none',stroke=bar.outline.color,stroke_width=bar.outline.linewidth*POINT)))
    for end in ('min','max'):
        if bar['extend'] not in (end,'both'):continue
        t=0 if end=='min' else 1
        length=(h if vertical else w)*bar['extendfrac']
        if vertical:
            by=y+(1-t)*h;tip=by+length if t==0 else by-length
            points=[(x,by),(x+w,by),(x+w/2,tip)]
        else:
            bx=x+t*w;tip=bx-length if t==0 else bx+length
            points=[(bx,y),(bx,y+h),(tip,y+h/2)]
        scene.add(Path([points],True,dict(fill=bar.cmap.under if t==0 else bar.cmap.over,stroke=bar.outline.color,stroke_width=bar.outline.linewidth*POINT,opacity=alpha)))
    tick_start=len(scene.items)
    bar._long_axis._pixels=h if vertical else w
    entries=[]
    for minor in (False,True):
        settings=bar._tickaxis.minor_settings if minor else bar._tickaxis.settings
        ticks=bar.get_ticks(minor=minor)
        formatter=bar.minorformatter if minor else bar.formatter;formatter.set_locs(ticks)
        artists=bar._minor_ticklabels if minor else bar._ticklabels
        for i,value in enumerate(ticks):
            source_index=bar._minor_ticks.index(value) if minor and artists is not None else i
            entries.append((value,settings,artists[source_index] if artists is not None else None,formatter,i))
    for value,settings,artist,fmt,i in entries:
        if contour:t=contour_position(bar,value)
        elif isinstance(norm,BoundaryNorm) and bar['spacing']=='uniform':
            edges=norm.boundaries
            t=next((j+(value-a)/(b-a) for j,(a,b) in enumerate(zip(edges,edges[1:])) if a<=value<=b),-1)/(len(edges)-1)
        else:t=norm(value)
        if getattr(mapped,'options',{}).get('scheme')=='quantile' and bar['spacing']=='uniform' and t is not None:
            scale=mapped.options['color_scale'];span=scale['vmax']-scale['vmin']
            if span:
                edges=[(v-scale['vmin'])/span for v in scale['edges']]
                t=next(((j+(t-a)/(b-a))/(len(edges)-1) for j,(a,b) in enumerate(zip(edges,edges[1:])) if a<=t<=b and a!=b),-1)
        if t is None or not 0<=t<=1:continue
        sign=-1 if location in ('left','top') else 1
        tick=settings['length']*POINT;gap=settings['pad']*POINT
        inward=tick if settings['direction']=='in' else tick/2 if settings['direction']=='inout' else 0
        outward=tick-inward
        if vertical:
            bx=x if sign<0 else x+w;by=y+(1-t)*h
            points=[(bx-sign*inward,by),(bx+sign*outward,by)]
            tx,ty=bx+sign*(outward+gap),by
            align=dict(ha='right' if sign<0 else 'left',va='center')
        else:
            bx=x+t*w;by=y if sign<0 else y+h
            points=[(bx,by-sign*inward),(bx,by+sign*outward)]
            tx,ty=bx,by+sign*(outward+gap)
            align=dict(ha='center',va='bottom' if sign<0 else 'top')
        scene.add(Path([points],False,dict(stroke=settings['color'],stroke_width=settings['width']*POINT)))
        if artist is not None and not artist.visible:continue
        label=artist.text if artist is not None else str(fmt(value,i))
        if not label:continue
        style=dict(fontsize=settings['labelsize'],color=settings['labelcolor'],rotation=settings['rotation'],
                   rotation_mode=settings['rotation_mode'],**align)
        if artist:style.update(artist.style)
        style=text_style(style);_text(scene,tx,ty,label,style)
    offset=bar._long_axis.get_offset_text();offset.text=bar.formatter.get_offset()
    if offset.visible and offset.text:
        from .layout_engine import primitive_bounds
        from .scene import Text
        boxes=[primitive_bounds(p) for p in scene.items[tick_start:] if isinstance(p,Text)]
        if vertical:
            tx,ty=x+w,y-3*POINT;align=dict(ha='right',va='bottom')
        else:
            top=location=='top';edge=min([y]+[b[1] for b in boxes if b]) if top else max([y+h]+[b[1]+b[3] for b in boxes if b])
            tx,ty=x+w,edge+(-1 if top else 1)*3*POINT;align=dict(ha='right',va='bottom' if top else 'top')
        with scene.layout_artist(offset):_text(scene,tx,ty,offset.text,text_style(dict(align,**offset.style)))
    if bar.label_artist:
        settings=bar._tickaxis.settings
        style=dict(bar.label_artist.style)
        from .layout_engine import primitive_bounds
        from .label_layout import text_box
        from .scene import Text
        # Measure rendered major/minor labels and the offset. Font size/width
        # estimates miss rotated or multiline ticks and can overlap the label.
        boxes=[primitive_bounds(p) for p in scene.items[tick_start:] if isinstance(p,Text)]
        boxes=[b for b in boxes if b is not None]
        sign=-1 if location in ('left','top') else 1
        inward=settings['length']*POINT if settings['direction']=='in' else settings['length']*POINT/2 if settings['direction']=='inout' else 0
        outward=settings['length']*POINT-inward
        if vertical:
            edge=min([x-outward]+[b[0] for b in boxes]) if sign<0 else max([x+w+outward]+[b[0]+b[2] for b in boxes])
            loc=bar.label_loc if bar.label_loc in ('bottom','center','top') else 'center'
            ty=y+{'bottom':1,'center':.5,'top':0}[loc]*h;style.setdefault('rotation',90);style.update(ha= {'bottom':'left','center':'center','top':'right'}[loc],va='center')
            labelstyle=text_style(style);bx,by,bw,bh=text_box(0,0,bar.label_artist.text,labelstyle,padding=0)
            tx=edge+sign*bar.labelpad*POINT-(bx+bw if sign<0 else bx)
        else:
            edge=min([y-outward]+[b[1] for b in boxes]) if sign<0 else max([y+h+outward]+[b[1]+b[3] for b in boxes])
            loc=bar.label_loc if bar.label_loc in ('left','center','right') else 'center'
            tx=x+{'left':0,'center':.5,'right':1}[loc]*w
            style.update(ha=loc,va='center')
            labelstyle=text_style(style);bx,by,bw,bh=text_box(0,0,bar.label_artist.text,labelstyle,padding=0)
            ty=edge+sign*bar.labelpad*POINT-(by+bh if sign<0 else by)
        _text(scene,tx,ty,bar.label_artist.text,labelstyle)
