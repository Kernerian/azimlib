"""Explicit fixed-frame geometry light, independent of clocks and ephemerides."""
from dataclasses import dataclass
import math
from .planetary import PlanetaryContext
from .bodies import UnsupportedBodyOperation
from .surfaces import BodySurface,_unit
from .geometry import _number
from ._frames import Coordinates,ReferenceFrame
from .lighting import SolarLighting


@dataclass(frozen=True)
class GeometricLight:
    context:PlanetaryContext
    direction:tuple | None=None
    position:tuple | None=None
    def __post_init__(self):
        if not isinstance(self.context,PlanetaryContext):raise TypeError('GeometricLight requires an explicit PlanetaryContext')
        BodySurface(self.context)
        if (self.direction is None)==(self.position is None):raise ValueError('Provide fixed-frame direction OR position, not both')
        if self.direction is not None:object.__setattr__(self,'direction',_unit(self.direction))
        else:
            q=tuple(_number(v) for v in self.position)
            if len(q)!=3 or not all(math.isfinite(v) for v in q):raise ValueError('Position must be finite XYZ metres')
            if math.hypot(*(v/a for v,a in zip(q,self.context.body.axes)))<=1:raise ValueError('Light position must lie outside reference surface')
            object.__setattr__(self,'position',q)
    def vector_at(self,xyz):return self.direction if self.direction is not None else _unit(tuple(l-p for l,p in zip(self.position,xyz)))
    def normal(self,lon,lat):
        p=self.context.to_fixed(lon,lat).xyz
        return _unit(tuple(x/(a*a) for x,a in zip(p,self.context.body.axes)))
    def incidence(self,lon,lat):
        p=self.context.to_fixed(lon,lat).xyz
        return sum(n*l for n,l in zip(self.normal(lon,lat),self.vector_at(p)))
    def terminator(self,*,samples=361):
        if type(samples) is not int or not 17<=samples<=4097:raise ValueError('Terminator samples require 17..4097')
        axes=self.context.body.axes
        w=tuple(v/a for v,a in zip(self.direction or self.position,axes))
        length=math.hypot(*w);n=_unit(w)
        center=(0.,0.,0.) if self.direction is not None else tuple(v/length for v in n)
        radius=1. if self.direction is not None else math.sqrt(1-1/(length*length))
        a=_unit((n[1],-n[0],0) if abs(n[2])<.9 else (0,n[2],-n[1]))
        b=(n[1]*a[2]-n[2]*a[1],n[2]*a[0]-n[0]*a[2],n[0]*a[1]-n[1]*a[0])
        frame=ReferenceFrame(self.context.frame,self.context.body,epoch=self.context.epoch);points=[]
        for i in range(samples):
            t=2*math.pi*i/(samples-1);p=tuple(axis*(c+radius*(u*math.cos(t)+v*math.sin(t))) for axis,c,u,v in zip(axes,center,a,b))
            points.append(self.context.from_fixed(Coordinates(p,frame))[:2])
        return tuple(points)


class GeometricTerrainLight(SolarLighting):
    """Reuse own shadow BVH and physical face painter with an explicit direction.

    No solar model is constructed. Finite positions are supported by 2D surface
    incidence/terminator, but not approximated as parallel rays for 3D terrain.
    """
    def _default_model(self):return None
    def _validate_frame(self,frame):
        from .planetary_raster import SurfaceFrame
        if frame is not None and (not isinstance(frame,SurfaceFrame) or frame.context!=self.axes.get_context()):raise ValueError('Geometric terrain light requires matching SurfaceFrame or body-fixed terrain')
    def _prepare_lighting(self,value):
        if not isinstance(value,GeometricLight) or value.context!=self.axes.get_context():raise ValueError('Geometric light Body/context mismatch')
        if value.direction is None:raise UnsupportedBodyOperation('Finite-position 3D shadow rays are not implemented; no distant-source approximation')
        return value
    @property
    def direction(self):return self.state.direction if self.frame is None else self.frame.vector(self.state.direction)
    @property
    def semidiameter(self):return 0.
    def set_time(self,*args,**kwargs):raise UnsupportedBodyOperation('GeometricLight has no clock or astronomical ephemeris')


def attach_geometric_light(axes,value,**options):
    if not getattr(axes,'_terrain3d',False):raise ValueError('Terrain geometric_light requires 3D Axes; use GeometricLight.incidence for maps')
    if not axes.layers:raise ValueError('Add terrain before binding its light frame')
    if getattr(axes,'_solar_lighting',None) is not None:raise ValueError('Remove existing light before rebinding')
    if any(k in options for k in ('model','offsets','angular_radius','samples','frame')):raise ValueError('Geometric lighting is a declared single direction with hard shadows')
    light=GeometricTerrainLight(axes,value,frame=axes.local_frame,angular_radius=0,samples=1,**options)
    axes._solar_lighting=light;axes._changed();return light


def planetary_terrain(axes,raster,*,origin=None,**style):
    """Existing SurfaceArtist/Mesh renderer; fixed XYZ or exact regional ENU."""
    from .planetary_raster import PlanetaryRaster,SurfaceFrame
    from .terrain_axes import SurfaceArtist
    from .terrain3d import Mesh,dot,cross
    from ._contracts import TERRAIN_MAX_VERTICES,TERRAIN_MAX_TRIANGLES
    if not isinstance(raster,PlanetaryRaster) or raster.context!=axes.get_context():raise ValueError('Terrain raster Body/context mismatch')
    ny,nx=raster.shape
    if min(ny,nx)<2 or ny*nx>TERRAIN_MAX_VERTICES or 2*(ny-1)*(nx-1)>TERRAIN_MAX_TRIANGLES:raise ValueError('Terrain mesh budget exceeded; resample explicitly')
    frame=None if origin is None else SurfaceFrame(raster.context,*origin)
    if frame is None and axes.vertical_exaggeration!=1:raise UnsupportedBodyOperation('Body-fixed XYZ has no global vertical axis; use an ENU terrain origin for visual vertical exaggeration')
    if axes.layers and axes.local_frame!=frame:raise ValueError('Cannot mix body-fixed and local terrain frames')
    vertices=[];heights=[];valid=[]
    from .geodesy import METRE
    for j in range(ny):
        for i in range(nx):
            geo=raster.geographic(i,j,center=True);h=raster._height(raster.values[j][i]);okay=geo is not None and h is not None
            valid.append(okay);heights.append(h if okay else None)
            vertices.append((0.,0.,0.) if not okay else frame.position(*geo,h) if frame is not None else raster.context.to_fixed(*geo,METRE.convert(h,raster.context.height_unit)).xyz)
    faces=[]
    for j in range(ny-1):
        for i in range(nx-1):
            a=j*nx+i;b=a+1;c=a+nx;d=c+1
            if not all(valid[k] for k in (a,b,c,d)):continue
            for t in ((a,b,d),(a,d,c)):
                p,q,r=(vertices[k] for k in t);normal=cross(tuple(y-x for x,y in zip(p,q)),tuple(y-x for x,y in zip(p,r)))
                if not math.hypot(*normal):continue
                orientation=normal[2] if frame is not None else dot(normal,p)
                faces.append(t if orientation>0 else tuple(reversed(t)))
    if not faces:raise ValueError('No terrain faces remain after NoData/domain masking')
    artist=SurfaceArtist(Mesh(tuple(vertices),tuple(faces)),elevation_reference=raster.context.vertical+'; '+raster.context.datum,**style)
    artist._body_context=raster.context;artist.set_array(heights);artist._planetary_raster=raster
    result=axes._attach(artist);axes.local_frame=frame;return result
