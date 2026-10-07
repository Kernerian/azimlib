"""Own arc-length glyph placement, with upright baselines and repeated names."""
import bisect
import math
from .typography import text_width,POINT
from .line_labels import visible_paths

def curve_candidates(geometry,vp,text,style,repeat=None):
    """Yield glyph poses; repeat is baseline center spacing in physical points."""
    from .mathtext import has_math
    if has_math(text) or '\n' in text:raise ValueError('Curved labels require single-line plain text')
    paths=visible_paths(geometry,vp);paths.sort(key=lambda p:-sum(math.dist(a,b) for a,b in zip(p,p[1:])))
    advances=[];previous=''
    for char in text:
        # Pair width accounts for bundled Latin kerning in the arc advance.
        char_width=text_width(char,style)
        kern=text_width(previous+char,style)-text_width(previous,style)-char_width
        advances.append((char_width,kern));previous=char
    width=sum(a+k for a,k in advances)
    for path in paths:
        def distances(path):
            ds=[0.]
            for a,b in zip(path,path[1:]):ds.append(ds[-1]+math.dist(a,b))
            return ds
        ds=distances(path);length=ds[-1]
        if length<width+4:continue
        def at(d):
            i=max(1,min(len(path)-1,bisect.bisect_left(ds,d)));a,b=path[i-1],path[i];span=ds[i]-ds[i-1]
            t=(d-ds[i-1])/span if span else 0
            return (a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])),math.degrees(math.atan2(b[1]-a[1],b[0]-a[0]))
        if abs(at(length/2)[1])>90:path=list(reversed(path));ds=distances(path)
        if repeat is None:centers=[length*f for f in (.5,.35,.65)]
        else:
            stride=max(width+8,repeat*POINT);n=max(1,int(length//stride));centers=[length/2+(k-(n-1)/2)*stride for k in range(n)]
        for center in centers:
            cursor=center-width/2;poses=[]
            if cursor<2 or center+width/2>length-2:continue
            for char,(advance,kern) in zip(text,advances):
                cursor+=kern;point,angle=at(cursor+advance/2);cursor+=advance
                if abs(angle)>85:poses=[];break
                if poses and abs(angle-poses[-1][2])>35:poses=[];break
                poses.append((char,point,angle))
            if poses:yield tuple(poses)
