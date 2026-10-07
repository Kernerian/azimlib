"""Legend layout and data-aware placement, independent of rendering backends."""
import math
from .typography import POINT,text_width,text_bounds
from .styles import text_style,path_style
from .scene import Scene,Path,Rect,Circle,Text
from .hatches import add_hatches

LOCATIONS={0:'best',1:'upper right',2:'upper left',3:'lower left',4:'lower right',
           5:'right',6:'center left',7:'center right',8:'lower center',9:'upper center',10:'center'}
ANCHORS={'upper right':(1,1),'upper left':(0,1),'lower left':(0,0),'lower right':(1,0),
         'center left':(0,.5),'center right':(1,.5),'right':(1,.5),
         'upper center':(.5,1),'lower center':(.5,0),'center':(.5,.5)}

def canonical_loc(value):
    if isinstance(value,int) and value in LOCATIONS:return LOCATIONS[value]
    if isinstance(value,str) and value in (*ANCHORS,'best'):return value
    if isinstance(value,(tuple,list)) and len(value)==2 and all(math.isfinite(float(v)) for v in value):return tuple(map(float,value))
    raise ValueError('Invalid legend location')

def validate_options(options):
    from .layers import Layer
    from .legend_handler import get_handler
    handlers=options.get('handler_map',{})
    if any(not callable(getattr(h,'legend_artist',None)) for h in handlers.values()):raise TypeError('Invalid legend handler')
    handles=options['handles'];labels=options['labels']
    if labels is not None and handles is None:raise ValueError('labels requires handles')
    if handles is not None:
        handles=list(handles)
        if any(not isinstance(h,Layer) and not (isinstance(h,tuple) and h and all(isinstance(v,Layer) for v in h)) and get_handler(handlers,h) is None for h in handles):raise TypeError('Legend handles must be layers or nonempty tuples of layers')
        options['handles']=handles
    if labels is not None:
        labels=list(labels)
        if len(labels)!=len(handles):raise ValueError('handles and labels must match')
        options['labels']=labels
    options['loc']=canonical_loc(options['loc'])
    for key in ('fontsize','title_fontsize','borderpad','labelspacing','handlelength','handletextpad','borderaxespad','columnspacing','linewidth'):
        if not math.isfinite(float(options[key])) or options[key]<0:raise ValueError(f'Invalid legend {key}')
    if options['fontsize']<=0 or options['title_fontsize']<=0:raise ValueError('Legend font size must be positive')
    if not math.isfinite(options['framealpha']) or not 0<=options['framealpha']<=1:raise ValueError('Invalid framealpha')
    if not isinstance(options['ncols'],int) or isinstance(options['ncols'],bool) or options['ncols']<1:raise ValueError('ncols must be a positive integer')
    if options['mode'] not in (None,'expand'):raise ValueError('mode must be None or expand')
    if options['bbox_transform'] not in ('axes','figure'):raise ValueError('bbox_transform must be axes or figure')
    bbox=options['bbox_to_anchor']
    if bbox is not None:
        bbox=tuple(float(v) for v in bbox)
        if len(bbox) not in (2,4) or any(not math.isfinite(v) for v in bbox) or len(bbox)==4 and min(bbox[2:])<0:raise ValueError('bbox_to_anchor needs 2 or 4 finite values; sizes nonnegative')
        options['bbox_to_anchor']=bbox
    return options

def symbol(layer,legend=None):
    from .legend_handler import get_handler
    handler=get_handler(legend.get('handler_map',{}),layer) if legend is not None else None
    if handler is not None:return {'_handler':handler,'_handle':layer},'custom'
    kind='scatter' if layer.kind=='scatter' else 'line'
    if layer.kind=='geometry' and any(f.geometry and f.geometry.type in ('Polygon','MultiPolygon') for f in layer.data):kind='polygon'
    style=layer._scatter_style(0) if kind=='scatter' and layer.data else dict(layer.style)
    if layer.options.get('contour'):
        if layer.data:style=layer._feature_style(0,layer.data[0])
        else:style.update(color=layer.get_color()[0],linewidth=layer.get_linewidth()[0],linestyle=layer.get_linestyle()[0])
    if kind=='scatter':
        sizes=layer.options['sizes']
        style['markersize']=math.sqrt((min(sizes)+max(sizes))/2) if sizes else 0.
        if layer._array:style['color']=layer.to_color(layer._array[0])
        elif layer.options['colors']:style['color']=layer.options['colors'][0]
    if legend is not None:style['_legend_visible']=legend._symbol_visibility.get(id(layer),layer.get_visible())
    return style,kind

def entries(legend):
    items=[];options=legend
    layers=options['handles'] if options['handles'] is not None else legend.axes.layers
    for i,layer in enumerate(layers):
        explicit=options['labels'][i] if options['labels'] is not None else None
        if isinstance(layer,tuple):
            if explicit is not None:items.append((str(explicit),[symbol(h,legend) for h in layer]))
        elif getattr(layer,'legend_entries',None) and explicit is None:
            items.extend((str(label),[(style,kind)]) for label,style,kind in layer.legend_entries)
        elif explicit is not None or getattr(layer,'style',{}).get('label'):
            label=str(explicit if explicit is not None else layer.style['label'])
            if explicit is None and label.startswith('_'):continue
            items.append((label,[symbol(layer,legend)]))
    return items

def anchor_box(legend,vp):
    box=vp.box
    if legend['bbox_transform']=='figure':box=(0,0,legend.axes.figure.figsize[0]*100,legend.axes.figure.figsize[1]*100)
    bbox=legend['bbox_to_anchor']
    if bbox is None:return box
    if len(bbox)==2:bbox=(*bbox,0,0)
    x,y,w,h=box;bx,by,bw,bh=bbox
    return x+bx*w,y+(1-by-bh)*h,bw*w,bh*h

def place(box,loc,width,height,pad):
    x,y,w,h=box
    if isinstance(loc,tuple):return x+loc[0]*w,y+(1-loc[1])*h-height
    hx,hy=ANCHORS[loc]
    return (x+hx*w-hx*width+(pad if hx==0 else -pad if hx==1 else 0),
            y+(1-hy)*h-(1-hy)*height+(pad if hy==1 else -pad if hy==0 else 0))

def obstacles(ax,vp):
    """Projected data geometry and explicit decorations for best placement."""
    from .render_map import _geometry,_marker,_annotation,_text,_axes_xy,_north,_scale
    scene=Scene(1,1)
    for layer in ax.layers:
        if not layer.visible:continue
        if layer.kind=='geometry':
            style=dict(layer.style);style.pop('hatch',None)
            for feature in layer.data:
                if feature.geometry:_geometry(feature.geometry,style,vp,scene)
        elif layer.kind=='scatter':
            for i,p in enumerate(layer.data):
                size=layer._scatter_size(i)
                if size==0:continue
                q=vp.project(*p)
                if q:_marker(q,math.sqrt(size),layer._scatter_style(i),scene,None)
        elif layer.kind=='text':
            x,y,text=layer.data;p=_axes_xy(x,y,vp.box) if layer.options['transform']=='axes' else vp.project(x,y)
            if p:_text(scene,*p,text,text_style(layer.style))
        elif layer.kind=='annotation':_annotation(layer,vp,scene)
    for make,options in ((_north,ax._north),(_north,ax._compass),(_scale,ax._scale_bar)):
        if options:make(options,vp,scene)
    return scene.items

def score(box,items):
    from .render_map import _overlap
    from .label_layout import text_box
    x,y,w,h=box;result=0
    def inside(p):return x<=p[0]<=x+w and y<=p[1]<=y+h
    for item in items:
        if isinstance(item,Path):
            for part in item.paths:
                result+=sum(inside(p) for p in part)
                for a,b in zip(part,part[1:]):
                    # Segment/rectangle intersection using a parametric clip.
                    t0,t1=0.,1.;dx,dy=b[0]-a[0],b[1]-a[1]
                    for p,q in ((-dx,a[0]-x),(dx,x+w-a[0]),(-dy,a[1]-y),(dy,y+h-a[1])):
                        if p==0:
                            if q<0:t0,t1=1,0;break
                        elif p<0:t0=max(t0,q/p)
                        else:t1=min(t1,q/p)
                    if t0<=t1:result+=1
        else:
            b=(item.x-item.r,item.y-item.r,2*item.r,2*item.r) if isinstance(item,Circle) else (item.x,item.y,item.width,item.height) if isinstance(item,Rect) else text_box(item.x,item.y,item.text,item.style)
            if _overlap(box,b):result+=10
    return result

def layout(legend,vp):
    data=entries(legend);texts=legend._sync_texts([label for label,_ in data])
    fs=legend['fontsize']*POINT;pad=legend['borderpad']*fs;gap=legend['labelspacing']*fs
    handle=legend['handlelength']*fs;textgap=legend['handletextpad']*fs
    ncols=min(legend['ncols'],len(data)) or 1;columns=[];cursor=0
    for col in range(ncols):
        count=len(data)//ncols+(col<len(data)%ncols)
        column=[]
        for i in range(cursor,cursor+count):
            artist=texts[i];style=text_style(dict(artist.style,va='center'))
            height=text_bounds(artist.text,style)[3]
            column.append((data[i][1],artist.text,style,height,artist.visible))
        cursor+=count
        width=max((handle+textgap+text_width(text,style) for _,text,style,_,_ in column),default=0)
        height=sum(row[3] for row in column)+max(0,len(column)-1)*gap
        columns.append((column,width,height))
    title=legend.title_artist
    titlestyle=text_style(dict(title.style,va='top',ha='center'))
    titleheight=text_bounds(title.text,titlestyle)[3]+gap if title.visible and title.text else 0
    colgap=legend['columnspacing']*fs
    content=sum(c[1] for c in columns)+(ncols-1)*colgap
    width=2*pad+max(content,text_width(title.text,titlestyle) if titleheight else 0)
    height=2*pad+max(c[2] for c in columns)+titleheight
    reference=anchor_box(legend,vp);border=legend['borderaxespad']*fs
    if legend['mode']=='expand' and ncols>1:
        width=max(width,reference[2]-2*border)
        colgap=(width-2*pad-sum(c[1] for c in columns))/(ncols-1);content=width-2*pad
    loc=legend['loc']
    if loc=='best':
        dataitems=obstacles(legend.axes,vp)
        loc=min((LOCATIONS[i] for i in range(1,11)),key=lambda l:score((*place(reference,l,width,height,border),width,height),dataitems))
    x,y=place(reference,loc,width,height,border)
    return dict(box=(x,y,width,height),columns=columns,pad=pad,gap=gap,colgap=colgap,handle=handle,textgap=textgap,
                titleheight=titleheight,title=title.text,titlestyle=titlestyle,content=content,loc=loc)

def render_legend(legend,vp,scene):
    from .render_map import _component_frame,_text,_marker
    if not legend.get_visible():return
    if not entries(legend) and not legend.title_artist.text:return
    plan=layout(legend,vp);x,y,width,height=plan['box'];legend._last_box=plan['box'];legend._last_loc=plan['loc']
    _component_frame(scene,x,y,width,height,legend)
    if plan['titleheight']:_text(scene,x+width/2,y+plan['pad'],plan['title'],plan['titlestyle'])
    cx=x+plan['pad']+(width-2*plan['pad']-plan['content'])/2
    for column,colwidth,_ in plan['columns']:
        cy=y+plan['pad']+plan['titleheight']
        for symbols,label,style,rowheight,visible in column:
            center=cy+rowheight/2
            for symbolstyle,kind in symbols:
                if not symbolstyle.get('_legend_visible',True):continue
                handle=plan['handle'];fs=legend['fontsize']*POINT
                if kind=='custom':
                    from .legend_handler import HandleBox
                    symbolstyle['_handler'].legend_artist(legend,symbolstyle['_handle'],fs,HandleBox(legend,scene,(cx,center-fs/2,handle,fs)))
                elif kind=='polygon':
                    scene.add(Rect(cx,center-fs*.35,handle,fs*.7,path_style(symbolstyle,True)))
                    add_hatches(scene,[[(cx,center-fs*.35),(cx+handle,center-fs*.35),(cx+handle,center+fs*.35),(cx,center+fs*.35)]],symbolstyle)
                elif kind=='scatter':_marker((cx+handle/2,center),symbolstyle.get('markersize',6),symbolstyle,scene,None)
                else:
                    scene.add(Path([[(cx,center),(cx+handle,center)]],False,path_style(symbolstyle)))
                    if symbolstyle.get('marker'):_marker((cx+handle/2,center),symbolstyle.get('markersize',6),symbolstyle,scene,None)
            if visible:_text(scene,cx+plan['handle']+plan['textgap'],center,label,style)
            cy+=rowheight+plan['gap']
        cx+=colwidth+plan['colgap']
