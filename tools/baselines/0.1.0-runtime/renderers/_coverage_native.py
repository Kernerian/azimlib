"""Optional compilation of Azimlib's own scalar stroke coverage algorithm.

Numba compiles only these numerical loops. Dash/segment/disk construction still
uses the normal Python implementation. Same clipping/intersection/term order;
no fastmath, geometry reduction, alternate rasterizer or disk approximation.
No persistent JIT cache: read-only installations work; cold compile is measured.
"""
import math
import sys
import numpy as np
from numba import njit

_COMPENSATED=sys.version_info>=(3,12)


@njit(fastmath=False)
def _clip(points,count,axis,bound,greater,out):
    if count==0:return 0
    ax,ay=points[count-1,0],points[count-1,1]
    av=ax if axis==0 else ay
    inside_a=av>=bound if greater else av<=bound
    size=0
    for i in range(count):
        bx,by=points[i,0],points[i,1];bv=bx if axis==0 else by
        inside_b=bv>=bound if greater else bv<=bound
        if inside_a!=inside_b:
            t=(bound-av)/(bv-av)
            out[size,0]=ax+t*(bx-ax);out[size,1]=ay+t*(by-ay);size+=1
        if inside_b:
            out[size,0]=bx;out[size,1]=by;size+=1
        ax,ay,av,inside_a=bx,by,bv,inside_b
    return size


@njit(fastmath=False)
def _area(points,count):
    if count<3:return 0.
    x0,y0=points[0,0],points[0,1];hi=0.;lo=0.
    for i in range(count):
        j=i+1 if i+1<count else 0
        ax,ay=points[i,0]-x0,points[i,1]-y0
        bx,by=points[j,0]-x0,points[j,1]-y0
        term=ax*by-bx*ay;t=hi+term
        if _COMPENSATED:
            lo+=(hi-t)+term if abs(hi)>=abs(term) else (term-t)+hi
        hi=t
    if _COMPENSATED and lo!=0. and math.isfinite(lo):hi+=lo
    return abs(hi)/2


@njit(fastmath=False,nogil=True)
def _paint(pixels,vertices,offsets,fills):
    height,width=pixels.shape
    # Only convex stroke quads/disks/joins enter this adapter. Each half-plane
    # adds at most one vertex. Four buffers are reused for every unit square.
    row_lower=np.empty((264,2));row_upper=np.empty((264,2))
    square_lower=np.empty((264,2));square_upper=np.empty((264,2))
    for item in range(len(fills)):
        points=vertices[offsets[item]:offsets[item+1]];count=len(points)
        if count<3:continue
        ymin=points[0,1];ymax=ymin
        for i in range(1,count):ymin=min(ymin,points[i,1]);ymax=max(ymax,points[i,1])
        start=max(0,math.floor(ymin));end=min(height,math.ceil(ymax))
        for y in range(start,end):
            row=points;row_count=count
            if ymin<y:
                row_count=_clip(row,row_count,1,y,True,row_lower);row=row_lower
            if ymax>y+1:
                row_count=_clip(row,row_count,1,y+1,False,row_upper);row=row_upper
            if row_count<3:continue
            xmin=row[0,0];xmax=xmin
            for i in range(1,row_count):xmin=min(xmin,row[i,0]);xmax=max(xmax,row[i,0])
            left=max(0,math.floor(xmin));right=min(width,math.ceil(xmax))
            if right-left==1 and xmin>=left and xmax<=right:
                if pixels[y,left]!=255:
                    value=min(255,round(_area(row,row_count)*fills[item]))
                    if value>pixels[y,left]:pixels[y,left]=value
                continue
            for x in range(left,right):
                if pixels[y,x]==255:continue
                square=row;square_count=row_count
                if xmin<x:
                    square_count=_clip(square,square_count,0,x,True,square_lower);square=square_lower
                if xmax>x+1:
                    square_count=_clip(square,square_count,0,x+1,False,square_upper);square=square_upper
                value=min(255,round(_area(square,square_count)*fills[item]))
                if value>pixels[y,x]:pixels[y,x]=value


class NativeCoverage:
    """One mask shadow and <=128 polygon commands; no global scene/tile cache."""
    def __init__(self,mask,check=None):
        self.mask=mask;self.pixels=np.array(mask,dtype=np.uint8,copy=True)
        self.commands=[];self.check=check

    def polygon(self,points,fill):
        # Arbitrary/self-intersecting polygons can grow much more than +4 at
        # clipping. Only callers explicitly selecting stroke convexity enqueue.
        if len(points)>256 or any(abs(v)>2**30 or not math.isfinite(v) for p in points for v in p):return False
        self.commands.append((points,fill))
        if len(self.commands)>=128:self._execute()
        return True

    def _execute(self):
        if not self.commands:return
        if self.check:self.check()
        vertices=[];offsets=[0];fills=[]
        for points,fill in self.commands:
            vertices.extend(points);offsets.append(len(vertices));fills.append(fill)
        _paint(self.pixels,np.asarray(vertices,dtype=np.float64),np.asarray(offsets,dtype=np.int64),np.asarray(fills,dtype=np.float64))
        self.commands.clear()
        if self.check:self.check()

    def flush(self):
        self._execute();self.mask.frombytes(self.pixels.tobytes())

    def reload(self):self.pixels[:]=np.asarray(self.mask)
