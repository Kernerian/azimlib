"""Independent finite spherical emitter/occluder geometry, not event prediction.

Boundaries use exact angular radii; partial area uses tangent angular disks
limited to <=2 degree radii. Approximate lunar states require explicit opt-in.
"""
from dataclasses import dataclass
import math
from ._frames import Coordinates,EARTH_FIXED,Observer
from .lunar import MoonPosition,MOON_RADIUS_M
from .solar import _unit,_cross
from .geometry import _number
from ._timescales import Instant

SUN_RADIUS_M=695700000.  # IAU 2015 B3 nominal conversion constant.
EARTH_SHADOW_RADIUS_M=6378137. # Equatorial enclosing sphere, not an ellipsoid.
def _sub(a,b):return tuple(x-y for x,y in zip(a,b))
def _dot(a,b):return sum(x*y for x,y in zip(a,b))
def _norm(v):return math.sqrt(_dot(v,v))

@dataclass(frozen=True)
class ShadowSphere:
    center:Coordinates
    radius_m:float
    def __post_init__(self):
        if not isinstance(self.center,Coordinates) or self.center.frame!=EARTH_FIXED:raise ValueError('Shadow spheres require Earth-fixed metre coordinates')
        object.__setattr__(self,'radius_m',_number(self.radius_m))
        if self.radius_m<=0:raise ValueError('Sphere radius must be positive metres')
    @classmethod
    def from_xyz(cls,xyz,*,radius_m):return cls(Coordinates(tuple(xyz),EARTH_FIXED),radius_m)

def disk_overlap(a,b,d):
    """Area of two planar disks, independent analytic circle intersection."""
    a,b,d=map(_number,(a,b,d))
    if min(a,b)<=0 or d<0:raise ValueError('Disk radii positive; separation nonnegative')
    if d>=a+b:return 0.
    if d<=abs(a-b):return math.pi*min(a,b)**2
    x=max(-1,min(1,(d*d+a*a-b*b)/(2*d*a)));y=max(-1,min(1,(d*d+b*b-a*a)/(2*d*b)))
    product=max(0,(-d+a+b)*(d+a-b)*(d-a+b)*(d+a+b))
    return a*a*math.acos(x)+b*b*math.acos(y)-.5*math.sqrt(product)

@dataclass(frozen=True)
class Occultation:
    visible_fraction:float
    classification:str
    separation_degrees:float
    source_radius_degrees:float
    occulter_radius_degrees:float
    fraction_bounds:tuple
    uncertainty_degrees:float
    @property
    def uncertain(self):return self.fraction_bounds[1]-self.fraction_bounds[0]>1e-12

def occultation(point,source,occulter,*,uncertainty_degrees=0.):
    if not isinstance(point,Coordinates) or point.frame!=EARTH_FIXED:raise ValueError('Evaluation point requires Earth-fixed metres')
    if not isinstance(source,ShadowSphere) or not isinstance(occulter,ShadowSphere):raise TypeError('Require typed source and occulter spheres')
    uncertainty=_number(uncertainty_degrees)
    if not 0<=uncertainty<=10:raise ValueError('Angular uncertainty must lie in 0..10 degrees')
    a,b=_sub(source.center.xyz,point.xyz),_sub(occulter.center.xyz,point.xyz);da,db=_norm(a),_norm(b)
    if da<=source.radius_m or db<=occulter.radius_m:raise ValueError('Evaluation point must lie outside source and occulter spheres')
    ra,rb=math.asin(source.radius_m/da),math.asin(occulter.radius_m/db)
    if max(ra,rb)>math.radians(2):raise ValueError('Tangent-disk area approximation requires angular radii <=2 degrees')
    delta=math.atan2(_norm(_cross(a,b)),_dot(a,b))
    def visible(d):return max(0,min(1,1-disk_overlap(ra,rb,d)/(math.pi*ra*ra)))
    if db>=da:
        fraction=1.;kind='clear';bounds=(1.,1.)
    else:
        fraction=visible(delta)
        kind='clear' if delta>=ra+rb else 'umbra' if rb>=ra+delta else 'antumbra' if ra>=rb+delta else 'penumbra'
        error=math.radians(uncertainty);bounds=(visible(max(0,delta-error)),visible(delta+error))
    return Occultation(fraction,kind,math.degrees(delta),math.degrees(ra),math.degrees(rb),bounds,uncertainty)

@dataclass(frozen=True)
class ShadowCone:
    source:ShadowSphere
    occulter:ShadowSphere
    def __post_init__(self):
        if _norm(_sub(self.source.center.xyz,self.occulter.center.xyz))<=self.source.radius_m+self.occulter.radius_m:raise ValueError('Source and occulter spheres intersect')
        if self.source.radius_m<=self.occulter.radius_m:raise ValueError('Cone requires a larger finite emitting sphere')
    @property
    def axis(self):return _unit(_sub(self.occulter.center.xyz,self.source.center.xyz))
    @property
    def angles(self):
        d=_norm(_sub(self.source.center.xyz,self.occulter.center.xyz));s,o=self.source.radius_m,self.occulter.radius_m
        return math.asin((s-o)/d),math.asin((s+o)/d)
    @property
    def apex_distance_m(self):return self.occulter.radius_m/math.sin(self.angles[0])
    def radii(self,distance_m):
        q=_number(distance_m)
        if q<0:raise ValueError('Cone axial distance must be nonnegative')
        a,b=self.angles;r=self.occulter.radius_m
        # Negative umbra radius means the antumbra beyond the apex.
        return r/math.cos(a)-q*math.tan(a),r/math.cos(b)+q*math.tan(b)

@dataclass(frozen=True)
class EclipseGeometry:
    sun:ShadowSphere
    moon:ShadowSphere
    source:str
    instant:object=None
    angular_uncertainty_degrees:float=0.
    earth_radius_m:float=EARTH_SHADOW_RADIUS_M
    def __post_init__(self):
        if not isinstance(self.sun,ShadowSphere) or not isinstance(self.moon,ShadowSphere):raise TypeError('Require typed Sun and Moon spheres')
        if self.instant is not None and not isinstance(self.instant,Instant):raise TypeError('Geometry instant must be a typed Instant or None')
        if not isinstance(self.source,str) or not self.source.strip():raise ValueError('Geometry provenance is required, including synthetic input')
        for k in ('angular_uncertainty_degrees','earth_radius_m'):object.__setattr__(self,k,_number(getattr(self,k)))
        if not 0<=self.angular_uncertainty_degrees<=10 or self.earth_radius_m<=0:raise ValueError('Invalid eclipse geometry uncertainty/radius')
        if _norm(self.moon.center.xyz)<=self.earth_radius_m+self.moon.radius_m:raise ValueError('Earth and Moon spheres intersect')
        ShadowCone(self.sun,self.moon);ShadowCone(self.sun,self.earth)
    @classmethod
    def from_moon(cls,moon):
        if not isinstance(moon,MoonPosition):raise TypeError('Calculated eclipse geometry requires MoonPosition')
        # Range uncertainty also changes apparent disk sizes, conservatively.
        angular=moon.angular_budget_degrees+moon.sun.angular_budget_degrees+math.degrees(math.asin(MOON_RADIUS_M/moon.distance_m))*moon.distance_budget_m/(moon.distance_m-moon.distance_budget_m)
        return cls(ShadowSphere(moon.sun.fixed,SUN_RADIUS_M),ShadowSphere(moon.fixed,MOON_RADIUS_M),'Azimlib bounded solar/lunar models; illustrative only',moon.instant,angular)
    @property
    def earth(self):return ShadowSphere(Coordinates((0,0,0),EARTH_FIXED),self.earth_radius_m)
    @property
    def solar_cone(self):return ShadowCone(self.sun,self.moon)
    @property
    def lunar_cone(self):return ShadowCone(self.sun,self.earth)
    def require_visual_permission(self,allow_approximate):
        if self.angular_uncertainty_degrees and not allow_approximate:raise ValueError('Uncertain ephemeris: explicitly allow_approximate=True for illustration, not event prediction')
    def at(self,point,*,occulter='moon'):
        if occulter not in ('earth','moon'):raise ValueError('Occulter must be earth or moon')
        return occultation(point,self.sun,self.earth if occulter=='earth' else self.moon,uncertainty_degrees=self.angular_uncertainty_degrees)
    def solar(self,observer,*,solar_disk=None):
        if not isinstance(observer,Observer) or observer.geodetic.fixed!=EARTH_FIXED:raise ValueError('Solar occultation requires a terrestrial observer')
        if solar_disk is not None:
            from .solar_disk import SolarDiskConvention
            if not isinstance(solar_disk,SolarDiskConvention):raise TypeError('Require an explicit SolarDiskConvention')
            return occultation(observer.fixed_position,ShadowSphere(self.sun.center,solar_disk.radius_m),self.moon,uncertainty_degrees=self.angular_uncertainty_degrees)
        return self.at(observer.fixed_position)
    def compare_solar_disks(self,observer,conventions):
        from .solar_disk import compare_disks
        return compare_disks(lambda model:self.solar(observer,solar_disk=model),conventions)
    def lunar(self):return self.at(self.moon.center,occulter='earth')
    def events(self,*args,**kwargs):raise NotImplementedError('Contact/event prediction is not validated by this bounded ephemeris; stage 13.07 remains pending')
