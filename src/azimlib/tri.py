"""Own deterministic regional planar Delaunay triangulation and interpolation.

Not a spherical/constrained mesh. Coordinates are geographic degrees; hulls
must not cross the date line. Predicates operate in normalized coordinates.
"""
import math
from numbers import Integral
from .scientific import scalar


def _orient(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def _incircle(a,b,c,p):
    x,y=a[0]-p[0],a[1]-p[1];u,v=b[0]-p[0],b[1]-p[1];s,t=c[0]-p[0],c[1]-p[1]
    return (x*x+y*y)*(u*t-v*s)-(u*u+v*v)*(x*t-y*s)+(s*s+t*t)*(x*v-y*u)


class Triangulation:
    """Immutable nodes/connectivity with editable per-triangle mask.

    Duplicate, nonfinite, collinear or numerically unresolved points are
    rejected. Automatic triangulation is limited to 5000 nodes (quadratic
    reference kernel). Cocircular ties resolve deterministically by input order.
    """
    def __init__(self,x,y,triangles=None,mask=None):
        x,y=tuple(float(v) for v in x),tuple(float(v) for v in y)
        if len(x)!=len(y) or len(x)<3: raise ValueError('Require at least three equal-length nodes')
        if any(not math.isfinite(v) for v in x+y) or any(not -180<=v<=180 for v in x) or any(not -90<=v<=90 for v in y):
            raise ValueError('Nodes must be finite geographic coordinates')
        if max(x)-min(x)>180: raise ValueError('Regional triangulation must not cross the date line')
        points=tuple(zip(x,y))
        if len(set(points))!=len(points): raise ValueError('Duplicate triangulation nodes')
        span=max(max(x)-min(x),max(y)-min(y))
        if span==0: raise ValueError('Collinear nodes')
        norm=[((a-min(x))/span,(b-min(y))/span) for a,b in points]
        if triangles is None:
            if len(x)>5000: raise ValueError('Automatic triangulation is limited to 5000 nodes')
            norm.extend(((-32.,-16.),(32.,-16.),(0.,32.)))
            count=len(x);mesh=[(count,count+1,count+2)]
            for index in sorted(range(count),key=lambda i:(x[i],y[i],i)):
                bad=[t for t in mesh if _incircle(*(norm[i] for i in t),norm[index])>1e-14]
                boundary=set()
                for t in bad:
                    for a,b in zip(t,t[1:]+t[:1]):
                        if (b,a) in boundary: boundary.remove((b,a))
                        else: boundary.add((a,b))
                mesh=[t for t in mesh if t not in bad]
                mesh.extend((a,b,index) for a,b in sorted(boundary) if _orient(norm[a],norm[b],norm[index])>1e-14)
            triangles=[t for t in mesh if max(t)<count]
            if not triangles or set(i for t in triangles for i in t)!=set(range(count)):
                raise ValueError('Collinear or numerically unresolved triangulation nodes')
        prepared=[]
        for t in triangles:
            t=tuple(t)
            if len(t)!=3 or any(isinstance(i,bool) or not isinstance(i,Integral) or not 0<=i<len(x) for i in t) or len(set(t))!=3:
                raise ValueError('Triangles require three distinct valid node indices')
            orientation=_orient(*(norm[i] for i in t))
            if abs(orientation)<=1e-14: raise ValueError('Degenerate triangle')
            prepared.append(t if orientation>0 else (t[0],t[2],t[1]))
        if not prepared or len({tuple(sorted(t)) for t in prepared})!=len(prepared): raise ValueError('Empty or duplicate triangles')
        self._x,self._y,self._triangles=x,y,tuple(prepared)
        self.set_mask(mask)

    x=property(lambda self:self._x)
    y=property(lambda self:self._y)
    triangles=property(lambda self:self._triangles)
    mask=property(lambda self:self._mask)
    def set_mask(self,mask):
        mask=(False,)*len(self.triangles) if mask is None else tuple(bool(v) for v in mask)
        if len(mask)!=len(self.triangles): raise ValueError('Mask must match triangle count')
        self._mask=mask

    def field(self,values):
        values=tuple(scalar(v) for v in values)
        if len(values)!=len(self.x): raise ValueError('Field must match nodes')
        return [tuple((self.x[i],self.y[i],values[i]) for i in triangle)
                for triangle,masked in zip(self.triangles,self.mask) if not masked and all(values[i] is not None for i in triangle)]


class LinearTriInterpolator:
    """Barycentric scalar interpolation; None outside hull/masked triangles.

    Uses the current triangulation mask at each call, not an obsolete snapshot.
    Explicit connectivity is caller supplied and must be a nonoverlapping mesh.
    """
    def __init__(self,triangulation,z):
        if not isinstance(triangulation,Triangulation): raise TypeError('Require an Azimlib Triangulation')
        self.triangulation=triangulation;self.z=tuple(scalar(v) for v in z)
        if len(self.z)!=len(triangulation.x): raise ValueError('Field must match nodes')
    def __call__(self,x,y):
        if isinstance(x,(int,float)) and isinstance(y,(int,float)): return self._point(float(x),float(y))
        x,y=tuple(x),tuple(y)
        if len(x)!=len(y): raise ValueError('Interpolation coordinates must match')
        return [self._point(float(a),float(b)) for a,b in zip(x,y)]
    def _point(self,x,y):
        if not math.isfinite(x+y): return None
        for a,b,c in self.triangulation.field(self.z):
            det=_orient(a,b,c)
            u=_orient((x,y),b,c)/det;v=_orient(a,(x,y),c)/det;w=1-u-v
            if min(u,v,w)>=-1e-12: return u*a[2]+v*b[2]+w*c[2]
        return None
