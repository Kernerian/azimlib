"""Owned composable transforms. Public display coordinates are DPI pixels, y up."""
import math
from numbers import Real

def _pair(p):
    p=tuple(float(v) for v in p)
    if len(p)!=2 or not all(math.isfinite(v) for v in p):raise ValueError('Expected finite coordinate pair')
    return p

class Transform:
    input_dims=output_dims=2
    def transform_point(self,point):raise NotImplementedError
    def transform(self,values):
        values=list(values)
        if len(values)==2 and all(isinstance(v,Real) for v in values):return self.transform_point(values)
        return [self.transform_point(p) for p in values]
    def inverted(self):raise NotImplementedError
    def __add__(self,other):
        if not isinstance(other,Transform):return NotImplemented
        return CompositeTransform(self,other)
    def owners(self):return ()

class IdentityTransform(Transform):
    def transform_point(self,p):return _pair(p)
    def inverted(self):return self

class Affine2D(Transform):
    def __init__(self,matrix=None):
        self.clear()
        if matrix is not None:
            rows=[list(r) for r in matrix]
            if len(rows)!=3 or any(len(r)!=3 for r in rows) or rows[2]!=[0,0,1]:raise ValueError('Require affine 3x3 matrix')
            self._m=tuple(float(v) for row in rows[:2] for v in row)
            if not all(math.isfinite(v) for v in self._m):raise ValueError('Matrix must be finite')
    def clear(self):self._m=(1.,0.,0.,0.,1.,0.);return self
    def get_matrix(self):
        a,b,c,d,e,f=self._m;return ((a,b,c),(d,e,f),(0.,0.,1.))
    def transform_point(self,p):
        x,y=_pair(p);a,b,c,d,e,f=self._m;return a*x+b*y+c,d*x+e*y+f
    def _after(self,values):
        a,b,c,d,e,f=self._m;u,v,w,x,y,z=values
        self._m=(u*a+v*d,u*b+v*e,u*c+v*f+w,x*a+y*d,x*b+y*e,x*c+y*f+z);return self
    def translate(self,tx,ty):tx,ty=_pair((tx,ty));return self._after((1,0,tx,0,1,ty))
    def scale(self,sx,sy=None):sx,sy=_pair((sx,sx if sy is None else sy));return self._after((sx,0,0,0,sy,0))
    def rotate(self,theta):
        theta=float(theta)
        if not math.isfinite(theta):raise ValueError('Angle must be finite')
        c,s=math.cos(theta),math.sin(theta);return self._after((c,-s,0,s,c,0))
    def rotate_deg(self,degrees):return self.rotate(math.radians(float(degrees)))
    def rotate_deg_around(self,x,y,degrees):return self.translate(-x,-y).rotate_deg(degrees).translate(x,y)
    def inverted(self):
        a,b,c,d,e,f=self._m;det=a*e-b*d
        if not math.isfinite(det) or det==0:raise ValueError('Singular affine transform')
        return Affine2D(((e/det,-b/det,(b*f-e*c)/det),(-d/det,a/det,(d*c-a*f)/det),(0,0,1)))

class CompositeTransform(Transform):
    def __init__(self,first,second):self.first,self.second=first,second
    def transform_point(self,p):
        p=self.first.transform_point(p);return None if p is None else self.second.transform_point(p)
    def inverted(self):return self.second.inverted()+self.first.inverted()
    def owners(self):return self.first.owners()+self.second.owners()

class _Inverse(Transform):
    def __init__(self,source):self.source=source
    def transform_point(self,p):return self.source._inverse(_pair(p))
    def inverted(self):return self.source
    def owners(self):return self.source.owners()

class FigureTransform(Transform):
    def __init__(self,figure):self.figure=figure
    def owners(self):return (self.figure,)
    def transform_point(self,p):
        x,y=_pair(p);f=self.figure;return x*f.figsize[0]*f.dpi,y*f.figsize[1]*f.dpi
    def _inverse(self,p):
        f=self.figure;return p[0]/(f.figsize[0]*f.dpi),p[1]/(f.figsize[1]*f.dpi)
    def inverted(self):return _Inverse(self)

class PhysicalTransform(Transform):
    def __init__(self,figure,unit='inches'):
        if unit not in ('inches','points','mm'):raise ValueError('Physical unit must be inches, points or mm')
        self.figure,self.unit=figure,unit
    def owners(self):return (self.figure,)
    def _factor(self):return self.figure.dpi/{'inches':1,'points':72,'mm':25.4}[self.unit]
    def transform_point(self,p):return tuple(v*self._factor() for v in _pair(p))
    def _inverse(self,p):return tuple(v/self._factor() for v in p)
    def inverted(self):return _Inverse(self)

class AxesTransform(Transform):
    def __init__(self,axes,space='axes'):
        if space not in ('axes','geo','projected'):raise ValueError('Unknown axes coordinate space')
        self.axes,self.space=axes,space
    def owners(self):return (self.axes.figure,)
    def transform_point(self,p):
        p=_pair(p);v=self.axes._transform_viewport();x,y,w,h=v.box
        q=(x+p[0]*w,y+(1-p[1])*h) if self.space=='axes' else v.xy(*p) if self.space=='projected' else v.project(*p)
        f=self.axes.figure;return None if q is None else (q[0]*f.dpi/100,(f.figsize[1]*100-q[1])*f.dpi/100)
    def _inverse(self,p):
        f=self.axes.figure;px,py=p[0]*100/f.dpi,f.figsize[1]*100-p[1]*100/f.dpi
        v=self.axes._transform_viewport();x,y,w,h=v.box
        return ((px-x)/w,1-(py-y)/h) if self.space=='axes' else v.projected_inverse(px,py) if self.space=='projected' else v.inverse(px,py)
    def inverted(self):return _Inverse(self)

class BlendedTransform(Transform):
    def __init__(self,x_transform,y_transform):
        if not isinstance(x_transform,Transform) or not isinstance(y_transform,Transform):raise TypeError('Require two transforms')
        self.x,self.y=x_transform,y_transform
    def owners(self):return self.x.owners()+self.y.owners()
    def transform_point(self,p):
        a,b=self.x.transform_point(p),self.y.transform_point(p)
        return None if a is None or b is None else (a[0],b[1])
    def inverted(self):
        # Geographic coordinates are coupled on curved/rotated projections.
        # Do not pretend separately inverted coordinates invert a mixed map.
        if not _separable(self.x) or not _separable(self.y):
            raise NotImplementedError('Inverse of coupled mixed geographic transforms is not separable')
        return BlendedTransform(self.x.inverted(),self.y.inverted())

def _separable(transform):
    if isinstance(transform,(IdentityTransform,FigureTransform,PhysicalTransform)):return True
    if isinstance(transform,Affine2D):return transform._m[1]==transform._m[3]==0
    if isinstance(transform,AxesTransform):return transform.space=='axes' or transform.axes.projection.name in ('equirectangular','mercator') and transform.axes.get_bearing()==0
    if isinstance(transform,CompositeTransform):return _separable(transform.first) and _separable(transform.second)
    return False

def blended_transform_factory(x_transform,y_transform):return BlendedTransform(x_transform,y_transform)
class OffsetTransform(Transform):
    def __init__(self,source,figure,x,y,unit):
        self.source=source;self.physical=PhysicalTransform(figure,unit);self.offset=_pair((x,y))
    def owners(self):return self.source.owners()+self.physical.owners()
    def transform_point(self,p):
        q=self.source.transform_point(p);d=self.physical.transform_point(self.offset)
        return None if q is None else (q[0]+d[0],q[1]+d[1])
    def _inverse(self,p):
        d=self.physical.transform_point(self.offset)
        return self.source.inverted().transform_point((p[0]-d[0],p[1]-d[1]))
    def inverted(self):return _Inverse(self)

def offset_copy(transform,fig=None,x=0,y=0,units='inches'):
    if units=='dots':delta=_pair((x,y))
    else:
        if fig is None:raise ValueError('Physical offsets require fig')
        return OffsetTransform(transform,fig,x,y,units)
    return transform+Affine2D().translate(*delta)

def scene_point(transform,p,figure):
    q=transform.transform_point(p)
    return None if q is None else (q[0]*100/figure.dpi,figure.figsize[1]*100-q[1]*100/figure.dpi)
