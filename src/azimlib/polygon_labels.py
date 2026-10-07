"""Independent bounded interior-anchor search in projected screen coordinates."""
import heapq
import math
from .viewport import densify

def interior_anchors(geometry,vp,*,tolerance=.75,max_cells=1024):
    """Largest-clearance anchors per visible polygon, including its holes.

    A best-first subdivision uses the distance function's Lipschitz bound;
    max_cells bounds work. Coordinates and source topology remain immutable.
    """
    from .render_map import _inside_ring,_segment_distance
    polygons=[geometry.coordinates] if geometry.type=='Polygon' else geometry.coordinates
    answers=[]
    for polygon in polygons:
        rings=[]
        for ring in polygon:
            points=[vp.project(*p) for p in densify(ring)]
            if any(p is None for p in points):rings=[];break
            rings.append(points)
        if not rings:continue  # Horizon cuts retain the existing geographic fallback.
        edges=[(a,b) for ring in rings for a,b in zip(ring,ring[1:])]
        x,y,w,h=vp.box
        left=max(x,min(p[0] for p in rings[0]));right=min(x+w,max(p[0] for p in rings[0]))
        top=max(y,min(p[1] for p in rings[0]));bottom=min(y+h,max(p[1] for p in rings[0]))
        if left>=right or top>=bottom:continue
        def distance(px,py):
            point=(px,py);d=math.sqrt(min(_segment_distance(point,a,b) for a,b in edges))
            inside=_inside_ring(point,rings[0]) and not any(_inside_ring(point,r) for r in rings[1:])
            return min(d,px-x,x+w-px,py-y,y+h-py) if inside else -d
        queue=[];serial=0;best=(-math.inf,None)
        def add(cx,cy,hx,hy):
            nonlocal serial,best
            d=distance(cx,cy)
            if d>best[0]:best=d,(cx,cy)
            heapq.heappush(queue,(-(d+math.hypot(hx,hy)),serial,cx,cy,hx,hy));serial+=1
        add((left+right)/2,(top+bottom)/2,(right-left)/2,(bottom-top)/2)
        for _ in range(max_cells):
            if not queue:break
            upper,_,cx,cy,hx,hy=heapq.heappop(queue)
            if -upper-best[0]<=tolerance:continue
            for sx,sy in ((-1,-1),(-1,1),(1,-1),(1,1)):add(cx+sx*hx/2,cy+sy*hy/2,hx/2,hy/2)
        if best[0]>0:answers.append(best)
    return [p for d,p in sorted(answers,key=lambda v:-v[0])]

def leader_endpoint(anchor,box):
    """Terminate an outside leader on the label footprint, not under its text."""
    x,y,w,h=box;cx,cy=x+w/2,y+h/2
    dx,dy=anchor[0]-cx,anchor[1]-cy
    if abs(dx)<=w/2 and abs(dy)<=h/2:return anchor
    t=min(w/(2*abs(dx)) if dx else math.inf,h/(2*abs(dy)) if dy else math.inf)
    return cx+dx*t,cy+dy*t
