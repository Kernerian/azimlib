"""Independent bounded lunar geometry; published model, no ephemeris backend.

Short mean-of-date series: NASA GSFC Simpson (1999), equations 1--4.
Angles are degrees, ranges metres. Not an eclipse prediction ephemeris.
"""
from dataclasses import dataclass
import math
from .solar import SolarModel,SolarRefraction,SunPosition,_unit,_cross,_observer
from .geometry import _number,wrap_longitude,Geometry
from ._frames import Coordinates,EARTH_FIXED,Observer
from ._timescales import Instant

LUNAR_MODEL='azim-almanac-short-v1'
MOON_RADIUS_M=1737400.
# Numerical model definitions from the public-use NASA paper, not source code.
LONGITUDE_TERMS=((6.29,134.9,477198.85),(-1.27,259.2,-413335.38),(.66,235.7,890534.23),(.21,269.9,954397.70),(-.19,357.5,35999.05),(-.11,186.6,966404.05))
LATITUDE_TERMS=((5.13,93.3,483202.03),(.28,228.2,960400.87),(-.28,318.3,6003.18),(-.17,217.6,-407332.20))
PARALLAX_TERMS=((.0518,134.9,477198.85),(.0095,259.2,-413335.38),(.0078,235.7,890534.23),(.0028,269.9,954397.70))

def _series(terms,t,function):return sum(a*function(math.radians((b+c*t)%360)) for a,b,c in terms)
def _length(v):return math.sqrt(sum(x*x for x in v))
def _dot(a,b):return sum(x*y for x,y in zip(a,b))
def _angles(v):return math.degrees(math.atan2(v[1],v[0]))%360,math.degrees(math.atan2(v[2],math.hypot(v[0],v[1])))
def _rotate(v,angle):
    c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle))
    return (c*v[0]-s*v[1],s*v[0]+c*v[1],v[2])

@dataclass(frozen=True)
class MoonDirection:
    """Manual finite target: ENU angles, slant range and terrestrial observer."""
    azimuth:float
    elevation:float
    distance_m:float
    observer:Observer
    def __post_init__(self):
        for name in ('azimuth','elevation','distance_m'):object.__setattr__(self,name,_number(getattr(self,name)))
        _observer(self.observer)
        if self.observer is None or not -90<=self.elevation<=90 or self.distance_m<=0:raise ValueError('Manual Moon requires observer, elevation -90..90 and positive metre range')
        object.__setattr__(self,'azimuth',self.azimuth%360)
    @property
    def fixed(self):
        a,e=math.radians(self.azimuth),math.radians(self.elevation)
        v=(math.cos(e)*math.sin(a),math.cos(e)*math.cos(a),math.sin(e));r=self.observer.to_local.rotation
        origin=self.observer.fixed_position.xyz
        return Coordinates(tuple(origin[i]+self.distance_m*sum(r[j*3+i]*v[j] for j in range(3)) for i in range(3)),EARTH_FIXED)
    @property
    def sublunar(self):
        lon,lat=_angles(self.fixed.xyz);return wrap_longitude(lon),lat

@dataclass(frozen=True)
class MoonPosition:
    instant:Instant
    right_ascension:float
    declination:float
    distance_m:float
    ecliptic_longitude:float
    ecliptic_latitude:float
    sidereal_angle:float
    fixed:Coordinates
    sun:SunPosition
    observer:Observer|None
    topocentric_right_ascension:float|None
    topocentric_declination:float|None
    topocentric_distance_m:float|None
    azimuth:float|None
    geometric_elevation:float|None
    elevation:float|None
    refraction_degrees:float
    parallax:bool
    time_policy:str
    angular_budget_degrees:float
    distance_budget_m:float=5000000.
    model:str=LUNAR_MODEL
    @property
    def sublunar(self):return wrap_longitude(self.right_ascension-self.sidereal_angle),self.declination
    @property
    def observer_origin(self):return self.observer.fixed_position.xyz if self.observer is not None and self.parallax else (0.,0.,0.)
    @property
    def phase_angle(self):
        to_sun=_unit(tuple(s-m for s,m in zip(self.sun.fixed.xyz,self.fixed.xyz)))
        to_eye=_unit(tuple(o-m for o,m in zip(self.observer_origin,self.fixed.xyz)))
        return math.degrees(math.acos(max(-1,min(1,_dot(to_sun,to_eye)))))
    @property
    def illuminated_fraction(self):return (1+math.cos(math.radians(self.phase_angle)))/2
    @property
    def elongation(self):
        o=self.observer_origin
        a=_unit(tuple(m-v for m,v in zip(self.fixed.xyz,o)));b=_unit(tuple(s-v for s,v in zip(self.sun.fixed.xyz,o)))
        return math.degrees(math.acos(max(-1,min(1,_dot(a,b)))))
    @property
    def bright_limb_position_angle(self):
        """Degrees east of celestial north; None at the singular conjunctions."""
        look=_unit(tuple(m-o for m,o in zip(self.fixed.xyz,self.observer_origin)))
        east=_cross((0,0,1),look)
        if _length(east)<1e-10:return None
        east=_unit(east);north=_cross(look,east)
        sunlight=_unit(tuple(s-m for s,m in zip(self.sun.fixed.xyz,self.fixed.xyz)))
        x,y=_dot(sunlight,east),_dot(sunlight,north)
        if math.hypot(x,y)<1e-10:return None
        return math.degrees(math.atan2(x,y))%360
    @property
    def phase_name(self):
        names=('new','waxing-crescent','first-quarter','waxing-gibbous','full','waning-gibbous','last-quarter','waning-crescent')
        return names[int(((self.ecliptic_longitude-self.sun.ecliptic_longitude)%360+22.5)//45)%8]

@dataclass(frozen=True)
class LunarModel:
    time_policy:str='strict'
    parallax:bool=True
    refraction:SolarRefraction|None=None
    def __post_init__(self):SolarModel(self.time_policy,parallax=self.parallax,refraction=self.refraction)
    def position(self,instant,observer=None,*,offsets=None):
        instant=instant if isinstance(instant,Instant) else Instant(instant)
        # One clock correction evaluation, shared with the solar geometry.
        correction=offsets(instant) if callable(offsets) else offsets
        sun=SolarModel(self.time_policy,aberration=False,parallax=self.parallax).position(instant,observer,offsets=correction)
        tt=instant.coordinate('TT',offsets=correction) if self.time_policy=='strict' else instant.coordinate('UTC')
        t=((tt.day-2451545)+tt.seconds/86400)/36525
        longitude=(218.32+481267.883*t+_series(LONGITUDE_TERMS,t,math.sin))%360
        latitude=_series(LATITUDE_TERMS,t,math.sin)
        parallax=.9508+_series(PARALLAX_TERMS,t,math.cos)
        distance=6378140./math.sin(math.radians(parallax))
        l,b,e=map(math.radians,(longitude,latitude,23.439291111-.0130042*t))
        v=(distance*math.cos(b)*math.cos(l),distance*(math.cos(b)*math.sin(l)*math.cos(e)-math.sin(b)*math.sin(e)),distance*(math.cos(b)*math.sin(l)*math.sin(e)+math.sin(b)*math.cos(e)))
        ra,dec=_angles(v);fixed=Coordinates(_rotate(v,-sun.sidereal_angle),EARTH_FIXED)
        az=height=tra=tdec=trange=None;refr=0.
        if observer is not None:
            origin=observer.fixed_position.xyz if self.parallax else (0,0,0)
            relative=tuple(m-o for m,o in zip(fixed.xyz,origin));trange=_length(relative)
            tra,tdec=_angles(_rotate(relative,sun.sidereal_angle))
            az,height=observer.azimuth_elevation(fixed,direction=not self.parallax)
            if self.refraction is not None:refr=self.refraction.correction(height)
        uncertainty=correction.uncertainty_seconds if self.time_policy=='strict' else 1.
        return MoonPosition(instant,ra,dec,distance,longitude,latitude,sun.sidereal_angle,fixed,sun,observer,tra,tdec,trange,az,height,None if height is None else min(90,height+refr),refr,self.parallax,self.time_policy,.5+uncertainty*.0043)
    def path(self,instants,observer=None,*,offsets=None):
        if not hasattr(instants,'__len__') or not 2<=len(instants)<=4096:raise ValueError('Lunar path requires 2..4096 instants')
        return LunarPath(tuple(self.position(t,observer,offsets=offsets) for t in instants))

@dataclass(frozen=True)
class LunarPath:
    """Calculated Earth-fixed trajectory; not a Keplerian/inertial orbit."""
    positions:tuple
    def __post_init__(self):
        p=tuple(self.positions)
        if not 2<=len(p)<=4096 or any(not isinstance(v,MoonPosition) for v in p):raise ValueError('Require 2..4096 calculated lunar positions')
        if any(a.instant.utc>=b.instant.utc or a.observer!=b.observer for a,b in zip(p,p[1:])):raise ValueError('Lunar path requires increasing instants and one observer')
        object.__setattr__(self,'positions',p)
    @property
    def groundtrack(self):return Geometry('LineString',tuple(p.sublunar for p in self.positions))
    def mesh(self,*,distance_scale=1.,width=500000.):
        from .terrain3d import Mesh
        scale,width=_number(distance_scale),_number(width)
        if scale<=0 or width<=0:raise ValueError('Trajectory visual scale and ribbon width must be positive')
        vertices=[];faces=[]
        centers=[tuple(v*scale for v in p.fixed.xyz) for p in self.positions]
        for i,c in enumerate(centers):
            tangent=tuple(b-a for a,b in zip(centers[max(0,i-1)],centers[min(len(centers)-1,i+1)]))
            side=_cross(tangent,_unit(c))
            if _length(side)<1e-12:raise ValueError('Trajectory ribbon is degenerate; choose different sampling')
            side=_unit(side);vertices.extend(tuple(c[k]+sign*width*.5*side[k] for k in range(3)) for sign in (-1,1))
        for i in range(len(centers)-1):
            j=2*i;faces.extend(((j,j+1,j+3),(j,j+3,j+2)))
        return Mesh(tuple(vertices),tuple(faces))
