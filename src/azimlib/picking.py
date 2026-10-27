"""Feature hit tests on final physical scene geometry; no spatial dependency."""
import math
from types import SimpleNamespace
from .scene import Path,Circle,Rect,RasterIcon
from .colors import to_rgba

def segment_distance(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den)) if den else 0
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)

def inside(p,rings):
    result=False;x,y=p
    for ring in rings:
        for a,b in zip(ring,ring[1:]+ring[:1]):
            if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:result=not result
    return result

def _painted(style,key):
    color=style.get(key,'none')
    return color is not None and color!='none' and to_rgba(color)[3]*style.get('opacity',1)>0

def primitive_hit(item,p,tolerance):
    if item.style.get('_icon_effect'):return False
    x,y=p
    if item.clip:
        a,b,w,h=item.clip
        if not (a<=x<=a+w and b<=y<=b+h):return False
    if isinstance(item,RasterIcon):
        if item.width<=0 or item.height<=0 or not (item.x<=x<item.x+item.width and item.y<=y<item.y+item.height):return False
        col=min(item.pixel_width-1,int((x-item.x)/item.width*item.pixel_width));row=min(item.pixel_height-1,int((y-item.y)/item.height*item.pixel_height))
        return item.rgba[(row*item.pixel_width+col)*4+3]*item.style.get('opacity',1)>0
    fill,stroke=_painted(item.style,'fill'),_painted(item.style,'stroke')
    radius=tolerance+item.style.get('stroke_width',1)/2
    if isinstance(item,Circle):
        d=math.hypot(x-item.x,y-item.y)
        return fill and d<=item.r+tolerance or stroke and abs(d-item.r)<=radius
    if isinstance(item,Rect):
        ring=[(item.x,item.y),(item.x+item.width,item.y),(item.x+item.width,item.y+item.height),(item.x,item.y+item.height)]
        rings=[ring];closed=True
    elif isinstance(item,Path):rings=[list(r) for r in item.paths];closed=item.closed
    else:return False
    if closed and fill and inside(p,rings):return True
    if not stroke:return False
    for ring in rings:
        pairs=zip(ring,ring[1:]+ring[:1]) if closed else zip(ring,ring[1:])
        if any(segment_distance(p,a,b)<=radius for a,b in pairs):return True
    return False

def scene_for(event):
    canvas=event.canvas
    scene=getattr(canvas,'scene',None) or getattr(canvas,'_pick_scene',None)
    if scene is None or canvas.figure.stale:
        scene=canvas.figure.to_scene(cull=True,interactive=True)
        canvas._pick_scene=scene
    return scene

def contains(artist,event,*,tolerance=None):
    if event.x is None or event.y is None:return False,{'ind':[],'features':[]}
    scene=scene_for(event);p=(event.x,scene.height-event.y)
    tolerance=artist.get_pickradius() if tolerance is None else tolerance
    indices=[]
    for owner,index,start,end in scene._pick_records:
        if owner is artist and getattr(artist,'kind',None)=='volume3d':
            from .volume_render import pick_volume
            for item in scene.items[start:end]:
                hit=pick_volume(item,*p)
                if hit is not None and hit['layer']==index:return True,dict(ind=[index],features=[],**hit)
            continue
        if owner is artist and index not in indices and any(primitive_hit(item,p,tolerance) for item in scene.items[start:end]):indices.append(index)
    features=[artist.data[i] for i in indices] if getattr(artist,'kind',None)=='geometry' else []
    return bool(indices),dict(ind=indices,features=features)

def pick(canvas,event,*,only=None):
    scene=scene_for(event);owners=[];seen=set()
    for owner,_,_,_ in scene._pick_records:
        if (only is None or owner is only) and id(owner) not in seen:owners.append(owner);seen.add(id(owner))
    for artist in sorted(owners,key=lambda a:a.zorder,reverse=True):
        picker=artist.get_picker()
        if picker is None or picker is False or not artist.get_visible():continue
        hit,props=picker(artist,event) if callable(picker) else contains(artist,event,tolerance=artist.get_pickradius() if isinstance(picker,bool) else picker)
        if hit:canvas._dispatch('pick_event',SimpleNamespace(name='pick_event',canvas=canvas,mouseevent=event,artist=artist,**props))
