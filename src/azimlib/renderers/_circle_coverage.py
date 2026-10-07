"""Original analytic disk/unit-square area integration, avoiding polygonized strokes."""
import math

def disk_area(x0,y0,x1,y1,r):
    if r<=0 or x0>=x1 or y0>=y1:return 0.
    r2=r*r
    nearx=max(x0,min(x1,0));neary=max(y0,min(y1,0))
    if nearx*nearx+neary*neary>=r2:return 0.
    if max(x0*x0,x1*x1)+max(y0*y0,y1*y1)<=r2:return (x1-x0)*(y1-y0)
    lo,hi=max(-r,x0),min(r,x1)
    if lo>=hi:return 0.
    cuts=[lo,hi]
    for y in (y0,y1):
        if abs(y)<r:
            x=math.sqrt(max(0,r2-y*y))
            for value in (-x,x):
                if lo<value<hi:cuts.append(value)
    cuts=sorted(set(cuts));area=0.
    def integral(x):return .5*(x*math.sqrt(max(0,r2-x*x))+r2*math.asin(max(-1,min(1,x/r))))
    for a,b in zip(cuts,cuts[1:]):
        root=math.sqrt(max(0,r2-((a+b)/2)**2));upper=min(y1,root);lower=max(y0,-root)
        if upper<=lower:continue
        k=(1 if y1>=root else 0)+(1 if y0<=-root else 0)
        constant=(y1 if y1<root else 0)-(y0 if y0>-root else 0)
        area+=constant*(b-a)+k*(integral(b)-integral(a))
    return max(0,min((x1-x0)*(y1-y0),area))

def disk_mask(Image,size,cx,cy,r,*,inner=0,check=None):
    width,height=size;data=bytearray(width*height)
    for y in range(height):
        if check is not None and y%32==0:check()
        for x in range(width):
            area=disk_area(x-cx,y-cy,x+1-cx,y+1-cy,r)
            if inner:area-=disk_area(x-cx,y-cy,x+1-cx,y+1-cy,inner)
            data[y*width+x]=round(max(0,min(1,area))*255)
    return Image.frombytes('L',size,bytes(data))
