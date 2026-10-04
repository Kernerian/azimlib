"""Area coverage for stroke polygons; avoids inclusive pixel-edge inflation.

Pillow's integer polygon fill includes both boundary pixels. On narrow strokes
that adds a sizeable, angle-dependent width. Here each boundary pixel receives
the actual area of the stroke polygon intersected with its unit square.
"""
import math
from functools import lru_cache
from operator import itemgetter

_x = itemgetter(0)
_y = itemgetter(1)


@lru_cache(maxsize=32)
def unit_circle(count):
    """Reuse identical angular samples; preserve floating-point expressions."""
    return tuple((math.cos(i*2*math.pi/count),math.sin(i*2*math.pi/count)) for i in range(count))

class FillCoverageDraw:
    """Even-odd scan conversion with fractional area and horizontal exactness.

    Active edges define disjoint interior intervals. Each supersampled row is
    integrated in eight vertical strata, split at vertices, with exact horizontal
    pixel intersections. Full spans are written in bulk; holes and intersecting
    rings use parity together, rather than XOR of already quantized masks.
    """
    def __init__(self,mask):self.mask=mask;self.width,self.height=mask.size

    def polygons(self,paths,antialiased=True):
        edges=[]
        for ring in paths:
            for a,b in zip(ring,ring[1:]+ring[:1]):
                if a[1]==b[1]:continue
                if a[1]>b[1]:a,b=b,a
                edges.append((a[1],b[1],a[0],(b[0]-a[0])/(b[1]-a[1])))
        if not edges:return
        edges.sort();active=[];next_edge=0
        data=bytearray(self.width*self.height)
        first=max(0,math.floor(edges[0][0]));last=min(self.height,math.ceil(max(e[1] for e in edges)))
        for y in range(first,last):
            active=[e for e in active if e[1]>y]
            while next_edge<len(edges) and edges[next_edge][0]<y+1:
                edge=edges[next_edge];next_edge+=1
                if edge[1]>y:active.append(edge)
            if not active:continue
            if not antialiased:
                sy=y+.5
                hits=sorted(e[2]+(sy-e[0])*e[3] for e in active if e[0]<=sy<e[1])
                for a,b in zip(hits[::2],hits[1::2]):
                    left=max(0,math.ceil(a-.5));right=min(self.width,math.ceil(b-.5))
                    if left<right:data[y*self.width+left:y*self.width+right]=b'\xff'*(right-left)
                continue
            cuts=sorted({y+i/8 for i in range(9)}|{v for e in active for v in e[:2] if y<v<y+1})
            changes={};boundary={}
            for lower,upper in zip(cuts,cuts[1:]):
                sy=(lower+upper)/2;weight=upper-lower
                hits=sorted(e[2]+(sy-e[0])*e[3] for e in active if e[0]<=sy<e[1])
                for a,b in zip(hits[::2],hits[1::2]):
                    a,b=max(0,a),min(self.width,b)
                    if a>=b:continue
                    left,right=math.floor(a),math.floor(b)
                    if left==right:
                        boundary[left]=boundary.get(left,0)+(b-a)*weight
                        continue
                    start,end=math.ceil(a),math.floor(b)
                    if start<end:
                        changes[start]=changes.get(start,0)+weight
                        changes[end]=changes.get(end,0)-weight
                    if start>a:boundary[left]=boundary.get(left,0)+(start-a)*weight
                    if b>end:boundary[right]=boundary.get(right,0)+(b-end)*weight
            value=0;previous=0;row=bytearray(self.width)
            for x,delta in sorted(changes.items()):
                if value>0:row[previous:x]=bytes([min(255,round(value*255))])*(x-previous)
                value+=delta;previous=x
            for x,amount in boundary.items():row[x]=min(255,row[x]+round(amount*255))
            data[y*self.width:(y+1)*self.width]=row
        self.mask.frombytes(bytes(data))

def _clip(points,axis,bound,greater):
    result=[]
    if not points:return result
    a=points[-1]
    # Select the half-plane once, rather than at every vertex. Expressions,
    # edge order and intersection coordinates remain identical.
    if greater:
        inside_a=a[axis]>=bound
        for b in points:
            inside_b=b[axis]>=bound
            if inside_a!=inside_b:
                t=(bound-a[axis])/(b[axis]-a[axis])
                result.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
            if inside_b:result.append(b)
            a,inside_a=b,inside_b
    else:
        inside_a=a[axis]<=bound
        for b in points:
            inside_b=b[axis]<=bound
            if inside_a!=inside_b:
                t=(bound-a[axis])/(b[axis]-a[axis])
                result.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
            if inside_b:result.append(b)
            a,inside_a=b,inside_b
    return result

def _area(points):
    if len(points)<3:return 0
    # Translate near zero to avoid cancellation for large canvas coordinates.
    x0,y0=points[0]
    if len(points)==3:
        x1,y1=points[1];x2,y2=points[2]
        a,b=x0-x0,y0-y0;c,d=x1-x0,y1-y0;e,f=x2-x0,y2-y0
        # Keep every term, including the closing/zero terms, in the original
        # sum order. Python's float sum can use compensated accumulation.
        return abs(sum((a*d-c*b,c*f-e*d,e*b-a*f)))/2
    if len(points)==4:
        x1,y1=points[1];x2,y2=points[2];x3,y3=points[3]
        a,b=x0-x0,y0-y0;c,d=x1-x0,y1-y0;e,f=x2-x0,y2-y0;g,h=x3-x0,y3-y0
        return abs(sum((a*d-c*b,c*f-e*d,e*h-g*f,g*b-a*h)))/2
    return abs(sum([(a[0]-x0)*(b[1]-y0)-(b[0]-x0)*(a[1]-y0)
                   for a,b in zip(points,points[1:]+points[:1])]))/2

class CoverageDraw:
    def __init__(self,mask):
        self.mask=mask;self.pixels=mask.load();self.width,self.height=mask.size

    def polygon(self,points,fill=255):
        points=list(points)
        if len(points)<3:return
        ymin=min(map(_y,points));ymax=max(map(_y,points))
        start=max(0,math.floor(ymin))
        end=min(self.height,math.ceil(ymax))
        for y in range(start,end):
            # A fully contained half-plane leaves the exact vertex sequence
            # unchanged. Avoid allocating/clipping it again; no quantization.
            row=points if ymin>=y else _clip(points,1,y,True)
            if ymax>y+1:row=_clip(row,1,y+1,False)
            if len(row)<3:continue
            xmin=min(map(_x,row));xmax=max(map(_x,row))
            left=max(0,math.floor(xmin));right=min(self.width,math.ceil(xmax))
            if right-left==1 and xmin>=left and xmax<=right:
                # The strip is already entirely in one pixel column. Clipping
                # it twice more would leave the same vertex sequence unchanged.
                if self.pixels[left,y]!=255:
                    value=min(255,round(_area(row)*fill))
                    if value>self.pixels[left,y]:self.pixels[left,y]=value
                continue
            for x in range(left,right):
                if self.pixels[x,y]==255:continue
                square=row if xmin>=x else _clip(row,0,x,True)
                if xmax>x+1:square=_clip(square,0,x+1,False)
                value=min(255,round(_area(square)*fill))
                if value>self.pixels[x,y]:self.pixels[x,y]=value

    def ellipse(self,bounds,fill=255):
        left,top,right,bottom=bounds
        rx,ry=(right-left)/2,(bottom-top)/2
        cx,cy=(left+right)/2,(top+bottom)/2
        # These extrema bound every sampled vertex, including reversed bounds.
        # Disks outside the mask contribute no coverage; skip their construction.
        if (cx+abs(rx)<=0 or cx-abs(rx)>=self.width or
                cy+abs(ry)<=0 or cy-abs(ry)>=self.height):return
        count=max(24,min(256,math.ceil(2*math.pi*max(rx,ry))))
        self.polygon([(cx+rx*c,cy+ry*s) for c,s in unit_circle(count)],fill)
