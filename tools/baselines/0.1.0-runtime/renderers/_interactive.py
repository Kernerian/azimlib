"""Fast supersampled stroke masks for transient desktop navigation frames.

Stroke polygons, dashes, caps and joins still come from our normal renderer.
Pillow fills those masks at 3x resolution instead of our exact pixel-area
integrator. Exports and settled frames always use the exact integrator.
"""
from collections import OrderedDict


def simplify_path(points,tolerance=.15):
    """Display-space Douglas–Peucker; endpoints and ring closure are retained.

    Only temporary long render paths are simplified. Source geometries, Scene
    coordinates, markers and exported paths are never changed.
    """
    if len(points)<=32:return points
    keep={0,len(points)-1};pending=[(0,len(points)-1)];limit=tolerance*tolerance
    while pending:
        first,last=pending.pop();ax,ay=points[first];bx,by=points[last]
        dx,dy=bx-ax,by-ay;length=dx*dx+dy*dy;largest=limit*(length or 1);index=None
        for i in range(first+1,last):
            x,y=points[i];px,py=x-ax,y-ay
            dot=px*dx+py*dy
            if not length:distance=px*px+py*py
            elif dot<=0:distance=(px*px+py*py)*length
            elif dot>=length:
                qx,qy=x-bx,y-by;distance=(qx*qx+qy*qy)*length
            else:
                cross=px*dy-py*dx;distance=cross*cross
            if distance>largest:largest=distance;index=i
        if index is not None:
            keep.add(index);pending.extend(((first,index),(index,last)))
    result=[points[i] for i in sorted(keep)]
    if points[0]==points[-1] and len(result)<4:return points
    return result


class InteractivePathCache:
    """Bounded reuse of simplification indices for translated render paths.

    Every input vertex is checked before a hit; a changed/zoomed path is
    simplified again. Returned coordinates always come from the current Scene.
    Only the raster worker owns this cache (64 entries, 50,000 retained points).
    """
    def __init__(self):self.entries=OrderedDict();self.points=0;self.hits=0;self.misses=0

    def simplify(self,points):
        if len(points)<=32:return points
        x0,y0=points[0]
        signature=(len(points),*(round(v,6) for i in (len(points)//3,2*len(points)//3,-1)
                                for v in (points[i][0]-x0,points[i][1]-y0)))
        cached=self.entries.get(signature)
        if cached is not None:
            original,indices=cached;dx,dy=x0-original[0][0],y0-original[0][1]
            if all(abs(x-ox-dx)<1e-8 and abs(y-oy-dy)<1e-8 for (x,y),(ox,oy) in zip(points,original)):
                self.hits+=1;self.entries.move_to_end(signature)
                return [points[i] for i in indices]
        self.misses+=1;result=simplify_path(points)
        # DP retains a subsequence, including duplicate/closed endpoints.
        indices=[];next_index=0
        for point in result:
            while points[next_index]!=point:next_index+=1
            indices.append(next_index);next_index+=1
        if len(points)>50000:return result
        old=self.entries.pop(signature,None)
        if old is not None:self.points-=len(old[0])
        while self.entries and (len(self.entries)>=64 or self.points+len(points)>50000):
            _,old=self.entries.popitem(last=False);self.points-=len(old[0])
        self.entries[signature]=(tuple(tuple(p) for p in points),tuple(indices));self.points+=len(points)
        return result


