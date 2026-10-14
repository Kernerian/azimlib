"""Own bounded terrestrial solar geometry from published USNO equations.

No ephemeris library, kernel, network, leap table or inferred precision.
Angles are degrees, Cartesian distances metres, instants timezone-aware.
See docs/solar-0.4.md for the model, frame approximations and error budget.
"""
from dataclasses import dataclass
from datetime import date,datetime,time,timedelta,timezone
import math
from .geometry import _number,Geometry,wrap_longitude
from ._frames import Observer,Coordinates,EARTH_FIXED,EARTH
from ._timescales import Instant,TimeOffsets

AU_METRES=149597870700.
SOLAR_MODEL='azim-usno-approx-v1'


def _unit(values):
    length=math.sqrt(sum(v*v for v in values))
    if length<1e-15:raise ValueError('Direction has zero length')
    return tuple(v/length for v in values)


def _cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])


def _observer(value):
    if value is not None and (not isinstance(value,Observer) or value.geodetic.fixed!=EARTH_FIXED):
        raise ValueError('Solar observer must use the terrestrial WGS84 fixed frame')
    if value is not None and not -10000<=value.height<=100000:
        raise ValueError('Solar terrestrial observer height must be -10000..100000 metres')
    return value


@dataclass(frozen=True)
class SolarRefraction:
    """Explicit standard optical approximation, not an atmospheric observation."""
    pressure_hpa:float=1010.
    temperature_c:float=10.
    def __post_init__(self):
        for key in ('pressure_hpa','temperature_c'):object.__setattr__(self,key,_number(getattr(self,key)))
        if not 0<=self.pressure_hpa<=1100 or not -80<=self.temperature_c<=60:raise ValueError('Refraction requires pressure 0..1100 hPa and temperature -80..60 C')
    def correction(self,elevation):
        h=_number(elevation)
        if not -90<=h<=90:raise ValueError('Elevation outside -90..90 degrees')
        # Published NOAA piecewise angular approximation, independently expressed.
        if h>85 or not self.pressure_hpa:return 0.
        tangent=math.tan(math.radians(h))
        if h>5:seconds=58.1/tangent-.07/tangent**3+.000086/tangent**5
        elif h>=-.575:seconds=1735+h*(-518.2+h*(103.4+h*(-12.79+h*.711)))
        else:
            # Below -1 degree no horizon extrapolation is asserted.
            if h<-1:return 0.
            seconds=-20.774/tangent
        return seconds/3600*self.pressure_hpa/1010*283/(273+self.temperature_c)


@dataclass(frozen=True)
class SunDirection:
    """Manual ENU direction at an explicit observer; no date/distance inferred."""
    azimuth:float
    elevation:float
    observer:Observer|None=None
    def __post_init__(self):
        object.__setattr__(self,'azimuth',_number(self.azimuth)%360)
        object.__setattr__(self,'elevation',_number(self.elevation));_observer(self.observer)
        if not -90<=self.elevation<=90:raise ValueError('Elevation must lie in -90..90 degrees')
    @property
    def lighting_direction(self):
        a,e=math.radians(self.azimuth),math.radians(self.elevation)
        return (math.cos(e)*math.sin(a),math.cos(e)*math.cos(a),math.sin(e))
    @property
    def fixed_direction(self):
        if self.observer is None:raise ValueError('Manual geographic placement requires an observer')
        r=self.observer.to_local.rotation;v=self.lighting_direction
        return tuple(sum(r[j*3+i]*v[j] for j in range(3)) for i in range(3))
    @property
    def subsolar(self):
        x,y,z=self.fixed_direction
        return wrap_longitude(math.degrees(math.atan2(y,x))),math.degrees(math.asin(max(-1,min(1,z))))


@dataclass(frozen=True)
class SunPosition:
    instant:Instant
    right_ascension:float
    declination:float
    distance_m:float
    ecliptic_longitude:float
    sidereal_angle:float
    equation_of_time_minutes:float
    fixed:Coordinates
    observer:Observer|None
    azimuth:float|None
    geometric_elevation:float|None
    elevation:float|None
    refraction_degrees:float
    parallax:bool
    aberration:bool
    time_policy:str
    angular_budget_degrees:float
    model:str=SOLAR_MODEL
    @property
    def subsolar(self):
        return wrap_longitude(self.right_ascension-self.sidereal_angle),self.declination
    @property
    def semidiameter_degrees(self):return .2666/(self.distance_m/AU_METRES)
    @property
    def fixed_direction(self):return _unit(self.fixed.xyz)
    @property
    def lighting_direction(self):
        if self.observer is None:raise ValueError('Local lighting requires an observer')
        local=self.observer.to_local.apply(self.fixed,direction=not self.parallax)
        return _unit(local.xyz)  # Refraction never bends the lighting vector.
    @property
    def hour_angle(self):
        if self.observer is None:raise ValueError('Hour angle requires an observer')
        return wrap_longitude(self.sidereal_angle+self.observer.longitude-self.right_ascension)
    def night_region(self):
        from .overlay import SphericalRegion
        lon,lat=self.subsolar
        return SphericalRegion.hemisphere(wrap_longitude(lon+180),-lat)
    def terminator(self,*,samples=361):
        if isinstance(samples,bool) or not isinstance(samples,int) or not 17<=samples<=4097:raise ValueError('Terminator needs 17..4097 samples')
        n=self.fixed_direction;axis=(0.,0.,1.) if abs(n[2])<.9 else (1.,0.,0.)
        a=_unit(_cross(n,axis));b=_cross(n,a);points=[]
        for i in range(samples-1):
            t=2*math.pi*i/(samples-1);x,y,z=(a[k]*math.cos(t)+b[k]*math.sin(t) for k in range(3))
            points.append((wrap_longitude(math.degrees(math.atan2(y,x))),math.degrees(math.asin(max(-1,min(1,z))))))
        return Geometry('LineString',(*points,points[0]))


@dataclass(frozen=True)
class SolarModel:
    """Low precision 1972..2100 model; UTC approximation must be explicit."""
    time_policy:str='strict'
    aberration:bool=True
    parallax:bool=True
    refraction:SolarRefraction|None=None
    def __post_init__(self):
        if self.time_policy not in ('strict','utc-approx'):raise ValueError('Solar time_policy is strict or explicit utc-approx')
        if not isinstance(self.aberration,bool) or not isinstance(self.parallax,bool):raise TypeError('Solar corrections require booleans')
        if self.refraction is not None and not isinstance(self.refraction,SolarRefraction):raise TypeError('Require SolarRefraction or None')
    def position(self,instant,observer=None,*,offsets=None):
        instant=instant if isinstance(instant,Instant) else Instant(instant);_observer(observer)
        if not 1972<=instant.utc.year<=2100:raise ValueError('Solar model validity is 1972..2100 UTC')
        if self.time_policy=='strict':
            correction=offsets(instant) if callable(offsets) else offsets
            tt=instant.coordinate('TT',offsets=correction);ut=instant.coordinate('UT1',offsets=correction)
            uncertainty=correction.uncertainty_seconds
        else:
            if offsets is not None:raise ValueError('utc-approx cannot silently ignore supplied offsets; choose strict')
            tt=ut=instant.coordinate('UTC');uncertainty=1.
        d=(tt.day-2451545)+tt.seconds/86400;du=(ut.day-2451545)+ut.seconds/86400
        g=math.radians((357.529+.98560028*d)%360);q=(280.459+.98564736*d)%360
        distance=1.00014-.01671*math.cos(g)-.00014*math.cos(2*g)
        longitude=(q+1.915*math.sin(g)+.020*math.sin(2*g)+(0 if self.aberration else 20.49/(3600*distance)))%360
        obliquity=math.radians(23.439-.00000036*d);l=math.radians(longitude)
        ra=math.degrees(math.atan2(math.cos(obliquity)*math.sin(l),math.cos(l)))%360
        dec=math.degrees(math.asin(math.sin(obliquity)*math.sin(l)))
        t=du/36525
        sidereal=(280.46061837+360.98564736629*du+.000387933*t*t-t*t*t/38710000)%360
        angle=math.radians(ra-sidereal);delta=math.radians(dec);r=distance*AU_METRES
        fixed=Coordinates((r*math.cos(delta)*math.cos(angle),r*math.cos(delta)*math.sin(angle),r*math.sin(delta)),EARTH_FIXED)
        az=height=None;refr=0.
        if observer is not None:
            az,height=observer.azimuth_elevation(fixed,direction=not self.parallax)
            if self.refraction is not None:refr=self.refraction.correction(height)
        return SunPosition(instant,ra,dec,r,longitude,sidereal,4*wrap_longitude(q-ra),fixed,observer,az,height,
            None if height is None else min(90,height+refr),refr,self.parallax,self.aberration,self.time_policy,.05+uncertainty*360.98564736629/86400)
    def path(self,instants,observer,*,offsets=None):
        _observer(observer)
        if observer is None:raise ValueError('An apparent sky path requires an observer')
        if not hasattr(instants,'__len__') or not 2<=len(instants)<=4096:raise ValueError('Solar path requires a bounded sequence of 2..4096 instants')
        positions=tuple(self.position(t,observer,offsets=offsets) for t in instants)
        if any(a.instant.utc>=b.instant.utc for a,b in zip(positions,positions[1:])):raise ValueError('Solar path instants must increase strictly')
        return SolarPath(positions,observer)
    def events(self,day,observer,*,offsets=None,zone=timezone.utc,center_altitude=-5/6):
        return solar_events(day,observer,model=self,offsets=offsets,zone=zone,center_altitude=center_altitude)
    def seasons(self,year,*,offsets=None):
        if isinstance(year,bool) or not isinstance(year,int) or not 1972<=year<=2100:raise ValueError('Seasons year outside 1972..2100')
        output={}
        for name,month,target in (('march_equinox',3,0),('june_solstice',6,90),('september_equinox',9,180),('december_solstice',12,270)):
            start=datetime(year,month,15,tzinfo=timezone.utc);end=start+timedelta(days=12)
            def value(t):return wrap_longitude(self.position(t,offsets=offsets).ecliptic_longitude-target)
            output[name]=_root(value,start,end)
        return output


@dataclass(frozen=True)
class SolarPath:
    positions:tuple
    observer:Observer
    def __post_init__(self):
        _observer(self.observer)
        if self.observer is None or not hasattr(self.positions,'__len__') or not 2<=len(self.positions)<=4096:
            raise ValueError('Solar path requires an observer and 2..4096 positions')
        positions=tuple(self.positions)
        if any(not isinstance(p,SunPosition) or p.observer!=self.observer for p in positions):
            raise ValueError('Solar path positions must preserve their observer')
        if any(a.instant.utc>=b.instant.utc for a,b in zip(positions,positions[1:])):raise ValueError('Solar path instants must increase strictly')
        object.__setattr__(self,'positions',positions)
    def mesh(self,*,visual_radius=1000.,width=8.):
        """ENU ribbon on a visual sky sphere, not physical Sun-distance geometry."""
        from .terrain3d import Mesh
        radius,width=_number(visual_radius),_number(width)
        if radius<=0 or not 0<width<radius:raise ValueError('Sky ribbon needs positive visual radius and smaller width')
        vertices=[];faces=[]
        for p in self.positions:
            # Apparent elevation may include explicit optical refraction.
            direction=SunDirection(p.azimuth or 0,p.elevation,self.observer).lighting_direction
            side=_unit(_cross(direction,(0,0,1) if abs(direction[2])<.9 else (1,0,0)))
            vertices.extend(tuple(radius*direction[k]+sign*width*.5*side[k] for k in range(3)) for sign in (-1,1))
        for i in range(len(self.positions)-1):
            j=i*2;faces.extend(((j,j+1,j+3),(j,j+3,j+2)))
        return Mesh(tuple(vertices),tuple(faces))


def _root(function,start,end,*,seconds=.25):
    a=function(start);b=function(end)
    if a==0:return start
    if b==0:return end
    if a*b>0:raise ValueError('Solar root is not bracketed')
    for _ in range(64):
        middle=start+(end-start)/2;c=function(middle)
        if (end-start).total_seconds()<=seconds or c==0:return middle
        if a*c<=0:end=middle
        else:start=middle;a=c
    raise ArithmeticError('Solar root failed to converge')


@dataclass(frozen=True)
class SolarEvents:
    start:datetime
    end:datetime
    rises:tuple
    sets:tuple
    transits:tuple
    status:str
    center_altitude:float
    estimated_model_timing_seconds:tuple
    @property
    def sunrise(self):return self.rises[0] if self.rises else None
    @property
    def sunset(self):return self.sets[0] if self.sets else None
    @property
    def transit(self):return self.transits[0] if self.transits else None


def solar_events(day,observer,*,model=None,offsets=None,zone=timezone.utc,center_altitude=-5/6):
    """Events in a civil day, fixed geometric center threshold plus local horizon.

    Default -5/6 degree represents average upper-limb/refraction convention.
    Optical correction is never applied again to the elevation being solved.
    Sampling is ten minutes; near tangent/uncertain polar cases stay explicit.
    """
    if type(day) is not date:raise TypeError('Solar events require a date and explicit timezone, not a datetime')
    if _observer(observer) is None:raise ValueError('Events require an observer')
    model=model or SolarModel();threshold=_number(center_altitude)+observer.horizon
    if not -90<threshold<90:raise ValueError('Event center altitude plus horizon must be strictly within -90..90')
    local_start=datetime.combine(day,time(),zone);local_end=datetime.combine(day+timedelta(days=1),time(),zone)
    if local_start.utcoffset() is None or local_end.utcoffset() is None:raise ValueError('Solar civil day requires an explicit timezone')
    start=local_start.astimezone(timezone.utc);end=local_end.astimezone(timezone.utc)
    if not 0<(end-start).total_seconds()<=27*3600:raise ValueError('Unsupported civil-day duration')
    count=math.ceil((end-start).total_seconds()/600);grid=[start+(end-start)*i/count for i in range(count+1)]
    samples=[model.position(t,observer,offsets=offsets) for t in grid]
    values=[p.geometric_elevation-threshold for p in samples];rises=[];sets=[];transits=[];uncertainties=[]
    def elevation(t):return model.position(t,observer,offsets=offsets).geometric_elevation-threshold
    def hour(t):return model.position(t,observer,offsets=offsets).hour_angle
    for i,(a,b) in enumerate(zip(values,values[1:])):
        if a==0 or a*b<0:
            event=grid[i] if a==0 else _root(elevation,grid[i],grid[i+1])
            events=rises if b>a else sets
            if not events or abs((event-events[-1]).total_seconds())>1:events.append(event)
            rate=abs(b-a)/(grid[i+1]-grid[i]).total_seconds()
            uncertainties.append(None if rate<1e-12 else samples[i].angular_budget_degrees/rate)
        if abs(observer.latitude)<90 and samples[i].hour_angle<=0<samples[i+1].hour_angle:
            event=_root(hour,grid[i],grid[i+1])
            if not transits or abs((event-transits[-1]).total_seconds())>1:transits.append(event)
    budget=max(p.angular_budget_degrees for p in samples)
    # Interpolation between ten-minute extrema is not a proof of grazing absence.
    if min(abs(min(values)),abs(max(values)))<=budget+.01:status='grazing_or_uncertain'
    elif rises or sets:status='crossings'
    else:status='always_above' if min(values)>0 else 'always_below'
    return SolarEvents(start,end,tuple(rises),tuple(sets),tuple(transits),status,threshold,tuple(uncertainties))


# Public solar aliases reuse the existing typed terrestrial/time contracts.
SolarObserver=Observer
SolarTimeOffsets=TimeOffsets
