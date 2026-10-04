"""Own visible-line clipping and readable tangent label candidates.

One text block follows a locally straight section. This is deliberately not
glyph-by-glyph curved text, and does not modify source geographic geometry.
"""
import bisect
import math
from .geometry import split_antimeridian
from .viewport import densify


def clip_segment(a,b,box):
    """Liang-Barsky clipping in screen pixels; None means wholly outside."""
    x,y,w,h=box;dx=b[0]-a[0];dy=b[1]-a[1];lo,hi=0.0,1.0
    for p,q in ((-dx,a[0]-x),(dx,x+w-a[0]),(-dy,a[1]-y),(dy,y+h-a[1])):
        if abs(p)<1e-15:
            if q<0:return None
        elif p<0:lo=max(lo,q/p)
        else:hi=min(hi,q/p)
        if lo>hi:return None
    return ((a[0]+lo*dx,a[1]+lo*dy),(a[0]+hi*dx,a[1]+hi*dy))


def visible_paths(geometry,vp):
    lines=[geometry.coordinates] if geometry.type=='LineString' else geometry.coordinates
    result=[]
    for line in lines:
        for part in split_antimeridian(line,vp.projection.central_longitude):
            previous=None;current=[]
            for coordinate in densify(part):
                point=vp.project(*coordinate)
                if point is not None and previous is not None:
                    segment=clip_segment(previous,point,vp.box)
                    if segment is not None:
                        a,b=segment
                        if current and math.dist(current[-1],a)>1e-6:
                            if len(current)>1:result.append(current)
                            current=[]
                        if not current:current.append(a)
                        if math.dist(current[-1],b)>1e-8:current.append(b)
                    elif current:
                        if len(current)>1:result.append(current)
                        current=[]
                elif current:
                    if len(current)>1:result.append(current)
                    current=[]
                previous=point
            if len(current)>1:result.append(current)
    return result


def line_candidates(geometry,vp,width,height,padding=2):
    """Yield (screen anchor, clockwise scene angle), longest visible part first."""
    paths=[]
    for path in visible_paths(geometry,vp):
        distances=[0.0]
        for a,b in zip(path,path[1:]):distances.append(distances[-1]+math.dist(a,b))
        paths.append((distances[-1],path,distances))
    for length,path,distances in sorted(paths,key=lambda p:-p[0]):
        span=width+2*padding
        if length<span or span<=0:continue
        def at(distance):
            i=max(1,min(len(path)-1,bisect.bisect_left(distances,distance)))
            a,b=path[i-1],path[i];d=distances[i]-distances[i-1]
            t=(distance-distances[i-1])/d if d else 0
            return a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])
        centers=[length*f for f in (.5,.35,.65,.2,.8)]
        stride=max(span/2,length/64)
        distance=span/2
        while distance<=length-span/2:
            if all(abs(distance-c)>span*.1 for c in centers):centers.append(distance)
            distance+=stride
        for center in centers:
            if center<span/2 or center+span/2>length:continue
            a,b=at(center-span/2),at(center+span/2)
            dx,dy=b[0]-a[0],b[1]-a[1];chord=math.hypot(dx,dy)
            if chord<span*.85:continue
            # Avoid corners: sampled baseline deviation must fit the text height.
            samples=[at(center-span/2+span*i/8) for i in range(9)]
            start=bisect.bisect_left(distances,center-span/2)
            end=bisect.bisect_right(distances,center+span/2)
            samples.extend(path[start:end])
            if max(abs(dx*(p[1]-a[1])-dy*(p[0]-a[0]))/chord for p in samples)>height*.5:continue
            angle=math.degrees(math.atan2(dy,dx))
            if angle>=90:angle-=180
            elif angle<-90:angle+=180
            yield at(center),angle
