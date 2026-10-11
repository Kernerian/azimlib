"""Owned emission/absorption reference in physical distance; no cloud simulator."""
from dataclasses import dataclass,replace
from array import array
import math
import struct
from .terrain3d import finite,normalized,transform_point,dot,RasterResult
from .volume import VolumeField,VolumeBudget


@dataclass(frozen=True)
class OpacityTransfer:
    knots:tuple=((0.,0.),(1.,.2))
    def __post_init__(self):
        points=tuple(tuple(finite(v) for v in p) for p in self.knots)
        if not 2<=len(points)<=256 or any(len(p)!=2 or not 0<=p[0]<=1 or not 0<=p[1]<=1 for p in points) or points[0][0]!=0 or points[-1][0]!=1 or any(a[0]>=b[0] for a,b in zip(points,points[1:])):raise ValueError('Opacity knots require increasing normalized 0..1 endpoints and alpha in 0..1')
        object.__setattr__(self,'knots',points)
    @classmethod
    def constant(cls,alpha):return cls(((0,alpha),(1,alpha)))
    def __call__(self,t):
        t=max(0,min(1,float(t)))
        for a,b in zip(self.knots,self.knots[1:]):
            if t<=b[0]:return a[1]+(b[1]-a[1])*(t-a[0])/(b[0]-a[0])
        return self.knots[-1][1]


@dataclass(frozen=True)
class VolumeLight:
    direction:tuple=(1.,-1.,2.)
    ambient:float=.35
    diffuse:float=.65
    shadow_steps:int=0
    def __post_init__(self):
        direction=tuple(finite(v) for v in self.direction)
        if len(direction)!=3:raise ValueError('Volume light requires a world XYZ direction toward the light')
        object.__setattr__(self,'direction',normalized(direction))
        if not all(math.isfinite(v) and 0<=v<=1 for v in (self.ambient,self.diffuse)) or self.ambient+self.diffuse>1:raise ValueError('Volume ambient/diffuse require nonnegative total <=1')
        if isinstance(self.shadow_steps,bool) or not isinstance(self.shadow_steps,int) or not 0<=self.shadow_steps<=32:raise ValueError('Volume self-shadow steps must be 0..32')


@dataclass(frozen=True)
class VolumeLayer:
    field:VolumeField
    inverse:tuple
    table:bytes
    limits:tuple
    logarithmic:bool
    step:float
    reference_length:float
    density:float=1.
    light:VolumeLight|None=None
    def __post_init__(self):
        if not isinstance(self.field,VolumeField) or self.field.components!=1:raise ValueError('Rendering requires a scalar volume; select an explicit vector component or nodal magnitude')
        if self.field.values is None:raise ValueError('Prepare a bounded dense region before volume rendering')
        if len(self.inverse)!=16 or not all(math.isfinite(v) for v in self.inverse):raise ValueError('Require a finite inverse camera matrix')
        if not isinstance(self.table,bytes) or len(self.table)!=256*4*4 or any(not math.isfinite(v[0]) or not 0<=v[0]<=1 for v in struct.iter_unpack('<f',self.table)):raise ValueError('Volume transfer table must contain 256 float32 RGBA entries in 0..1')
        if len(self.limits)!=2 or not all(math.isfinite(v) for v in self.limits) or self.limits[0]>self.limits[1] or self.logarithmic and self.limits[0]<=0:raise ValueError('Invalid volume transfer limits')
        if not all(math.isfinite(v) and v>0 for v in (self.step,self.reference_length)) or not math.isfinite(self.density) or not 0<=self.density<=1e6:raise ValueError('Volume step/reference length require positive metres and density in 0..1e6')
        if self.light is not None and not isinstance(self.light,VolumeLight):raise TypeError('Require VolumeLight or None')
    def rgba(self,value):
        if value is None or self.logarithmic and value<=0:return (0.,)*4
        lo,hi=self.limits
        v=math.log(value) if self.logarithmic else value
        if self.logarithmic:lo,hi=math.log(lo),math.log(hi)
        t=0. if hi==lo else max(0.,min(1.,(v-lo)/(hi-lo)))*255
        a=min(254,int(t));u=t-a
        x=struct.unpack_from('<4f',self.table,a*16);y=struct.unpack_from('<4f',self.table,(a+1)*16)
        return tuple(p+(q-p)*u for p,q in zip(x,y))


def inverse_matrix(matrix):
    """Own bounded Gauss-Jordan inversion, row major."""
    if len(matrix)!=16:raise ValueError('Require a 4x4 matrix')
    rows=[[finite(matrix[r*4+c]) for c in range(4)]+[float(r==c) for c in range(4)] for r in range(4)]
    for k in range(4):
        pivot=max(range(k,4),key=lambda r:abs(rows[r][k]))
        if abs(rows[pivot][k])<1e-15:raise ValueError('Singular volume camera')
        rows[k],rows[pivot]=rows[pivot],rows[k];scale=rows[k][k];rows[k]=[v/scale for v in rows[k]]
        for r in range(4):
            if r!=k:
                s=rows[r][k];rows[r]=[a-s*b for a,b in zip(rows[r],rows[k])]
    return tuple(v for row in rows for v in row[4:])


def unproject(inverse,x,y,z):
    q=transform_point(inverse,(x,y,z,1.))
    if abs(q[3])<1e-15:raise ValueError('Volume unprojection at infinity')
    return tuple(v/q[3] for v in q[:3])


def ray(inverse,x,y):
    a=unproject(inverse,x,y,-1);b=unproject(inverse,x,y,1);v=tuple(y-x for x,y in zip(a,b));length=math.sqrt(dot(v,v))
    return a,tuple(x/length for x in v),length


def interval(bounds,origin,direction,maximum=math.inf):
    lo,hi=0.,maximum
    for k in range(3):
        if abs(direction[k])<1e-15:
            if not bounds[2*k]<=origin[k]<=bounds[2*k+1]:return None
        else:
            a=(bounds[2*k]-origin[k])/direction[k];b=(bounds[2*k+1]-origin[k])/direction[k]
            lo=max(lo,min(a,b));hi=min(hi,max(a,b))
    return (lo,hi) if hi>lo else None


def extinction(alpha):return -math.log(max(1e-12,1-alpha))


def _shade(layer,sampler,p):
    light=layer.light
    if light is None:return 1.
    g=[]
    for k,s in enumerate(layer.field.spacing):
        a=list(p);b=list(p);a[k]-=s*.5;b[k]+=s*.5;va=sampler.sample(a);vb=sampler.sample(b)
        g.append(0. if va is None or vb is None else -(vb-va)/s)
    norm=math.sqrt(dot(g,g));diff=max(0.,dot(tuple(v/norm for v in g),light.direction)) if norm>1e-12 else 0.
    shade=light.ambient+light.diffuse*diff
    if light.shadow_steps:
        hit=interval(layer.field.bounds,p,light.direction)
        if hit:
            ds=hit[1]/light.shadow_steps;tau=0.
            for i in range(light.shadow_steps):
                point=tuple(a+(i+.5)*ds*d for a,d in zip(p,light.direction));alpha=layer.rgba(sampler.sample(point))[3]
                tau+=extinction(alpha)*ds/layer.reference_length*layer.density
            shade=light.ambient+(shade-light.ambient)*math.exp(-tau)
    return shade


def trace_ray(layers,origin,direction,maximum=math.inf,*,samplers=None,pick=False):
    """Reference midpoint integration; overlapping fields mix optical depth."""
    layers=tuple(layers)
    if not layers:return ((0.,0.,0.,0.),None)
    hits=[interval(v.field.bounds,origin,direction,maximum) for v in layers];active=[h for h in hits if h]
    if not active:return ((0.,0.,0.,0.),None)
    start=min(h[0] for h in active);end=max(h[1] for h in active);step=min(v.step for v in layers);steps=math.ceil((end-start)/step)
    if steps>min(v.field.budget.max_steps for v in layers):raise ValueError('Volume ray exceeds step budget; increase physical step explicitly')
    samplers=samplers or [v.field.sampler() for v in layers];rgb=[0.,0.,0.];alpha=0.;first=None
    for i in range(steps):
        ds=min(step,end-start-i*step);t=start+i*step+ds/2;p=tuple(a+t*d for a,d in zip(origin,direction));tau=0.;color=[0.,0.,0.]
        for layer,sampler,hit in zip(layers,samplers,hits):
            if hit is None or not hit[0]<=t<=hit[1]:continue
            value=sampler.sample(p);rgba=layer.rgba(value);amount=extinction(rgba[3])*ds/layer.reference_length*layer.density
            if not amount:continue
            shade=_shade(layer,sampler,p);tau+=amount
            for k in range(3):color[k]+=amount*rgba[k]*shade
            if pick and first is None:first=dict(position=p,value=value,distance=t,layer=layers.index(layer))
        if tau:
            a=1-math.exp(-tau)
            for k in range(3):rgb[k]+=(1-alpha)*a*color[k]/tau
            alpha+=(1-alpha)*a
        if alpha>=.999999:break
    return ((*rgb,alpha),first)


def rasterize_volume(item,width,height,*,check=None,accelerate=True):
    """Opaque geometry plus front-to-back volumes, at final pixel resolution."""
    from .terrain3d import rasterize
    from ._texture3d import rasterize_textured
    layers=item.volumes
    if not 1<=len(layers)<=4:raise ValueError('One scene supports 1..4 overlapping volume fields')
    budget=VolumeBudget(max_samples=min(v.field.budget.max_samples for v in layers),max_steps=min(v.field.budget.max_steps for v in layers),max_pixels=min(v.field.budget.max_pixels for v in layers))
    if width*height>budget.max_pixels:raise ValueError('Volume output pixel budget exceeded')
    diagonal=math.sqrt(sum((max(v.field.bounds[2*k+1] for v in layers)-min(v.field.bounds[2*k] for v in layers))**2 for k in range(3)))
    steps=math.ceil(diagonal/min(v.step for v in layers));cost=sum(1+(6+v.light.shadow_steps if v.light is not None else 0) for v in layers)
    if steps>budget.max_steps or width*height*steps*cost>budget.max_samples:raise ValueError('Volume ray/sample budget exceeded before rasterization; reduce resolution, select ROI or increase step')
    geometry=rasterize_textured(item,width,height,check=check) if item.texture is not None else rasterize(item.triangles,width,height,check=check)
    if accelerate:
        try:
            from ._volume_numpy import compose
            return compose(item,geometry,width,height,steps,check)
        except ImportError:pass
    inverse=layers[0].inverse;samplers=[v.field.sampler() for v in layers];rgba=bytearray(geometry.rgba)
    for y in range(height):
        if check:check()
        for x in range(width):
            nx,ny=2*(x+.5)/width-1,1-2*(y+.5)/height;o,d,far=ray(inverse,nx,ny)
            index=y*width+x;z=geometry.depth[y,x] if getattr(geometry.depth,'ndim',None)==2 else geometry.depth[index]
            if math.isfinite(z):far=min(far,dot(tuple(b-a for a,b in zip(o,unproject(inverse,nx,ny,z))),d))
            (r,g,b,a),_=trace_ray(layers,o,d,far,samplers=samplers);base=rgba[index*4:index*4+4];ba=base[3]/255;outa=a+(1-a)*ba
            rgb=[r,g,b]
            rgba[index*4:index*4+4]=bytes([round(255*(rgb[k]+(1-a)*ba*base[k]/255)/outa) if outa else 0 for k in range(3)]+[round(outa*255)])
    return RasterResult(width,height,bytes(rgba),geometry.depth)


def pick_volume(item,x,y):
    if not item.volumes or not item.x<=x<=item.x+item.width or not item.y<=y<=item.y+item.height:return None
    nx,ny=2*(x-item.x)/item.width-1,1-2*(y-item.y)/item.height;o,d,far=ray(item.volumes[0].inverse,nx,ny)
    if item.triangles:
        from .terrain3d import rasterize
        from ._texture3d import rasterize_textured
        triangles=tuple((tuple((item.width*(q[0]-nx*q[3]),item.height*(q[1]-ny*q[3]),q[2],q[3]) for q in face),color) for face,color in item.triangles)
        tiny=replace(item,x=0,y=0,width=1,height=1,triangles=triangles,volumes=())
        g=rasterize_textured(tiny,1,1) if item.texture is not None else rasterize(triangles,1,1,accelerate=False)
        z=g.depth[0,0] if getattr(g.depth,'ndim',None)==2 else g.depth[0]
        if math.isfinite(z):far=min(far,dot(tuple(b-a for a,b in zip(o,unproject(item.volumes[0].inverse,nx,ny,z))),d))
    _,hit=trace_ray(item.volumes,o,d,far,pick=True)
    return hit
