"""Static coordinate conversions and immutable data context, no network access."""
from dataclasses import dataclass
import math
from .bodies import Body,EARTH,LongitudeConvention,UnsupportedBodyOperation
from .geodesy import Unit,METRE,DEGREE
from .geometry import _number,FeatureCollection


@dataclass(frozen=True)
class PlanetaryContext:
    body: Body = EARTH
    latitude_type: str = 'planetocentric'
    longitude: LongitudeConvention = LongitudeConvention()
    prime_meridian: float = 0
    vertical: str = 'radial'
    datum: str | None = None
    frame: str | None = None
    epoch: str | None = None
    angle_unit: Unit = DEGREE
    height_unit: Unit = METRE

    def __post_init__(self):
        if not isinstance(self.body,Body):raise TypeError('Require Body')
        if not isinstance(self.longitude,LongitudeConvention):raise TypeError('Require LongitudeConvention')
        if self.latitude_type not in ('planetocentric','planetographic'):raise ValueError('Unknown latitude convention')
        expected='radial' if self.latitude_type=='planetocentric' else 'normal'
        if self.vertical!=expected:raise ValueError('Vertical reference must be '+expected+'; no geoid/areoid correction is implied')
        for value,quantity in ((self.angle_unit,'angle'),(self.height_unit,'length')):
            if not isinstance(value,Unit) or value.quantity!=quantity:raise ValueError('Invalid coordinate units')
        offset=_number(self.prime_meridian)
        if not -180<=offset<=180:raise ValueError('Invalid prime meridian offset')
        object.__setattr__(self,'prime_meridian',offset)
        for key,default in (('datum',self.body.datum),('frame',self.body.frame),('epoch',self.body.epoch)):
            value=getattr(self,key)
            if value is None:object.__setattr__(self,key,default)
            elif not isinstance(value,str) or not value.strip():raise ValueError('Invalid '+key+' identifier')
        if self.datum!=self.body.datum or self.frame!=self.body.frame:
            raise UnsupportedBodyOperation('Datum/frame changes need an explicitly implemented transform; identifiers do not transform data')

    @classmethod
    def for_body(cls, body, *, latitude_type='planetocentric', **kwargs):
        return cls(body,latitude_type,longitude=body.longitude,prime_meridian=body.prime_meridian,
                   vertical='radial' if latitude_type=='planetocentric' else 'normal',**kwargs)

    def canonical(self, lon, lat):
        lon=self.angle_unit.convert(lon,DEGREE);lat=self.angle_unit.convert(lat,DEGREE)
        if not -90<=lat<=90:raise ValueError('Latitude outside [-90,90] degrees')
        return self.longitude.to_east(lon,self.prime_meridian),lat

    def to_fixed(self, lon, lat, height=0):
        from ._frames import Coordinates,ReferenceFrame,GeodeticFrame
        lon,lat=self.canonical(lon,lat);h=self.height_unit.convert(height,METRE)
        fixed=ReferenceFrame(self.frame,self.body,epoch=self.epoch)
        if self.body.shape=='irregular':raise UnsupportedBodyOperation('Irregular radial/normal intersection is not implemented')
        if self.latitude_type=='planetographic':
            if h < -min(10000,self.body.ellipsoid.semi_minor_axis*.01):raise ValueError('Normal-height conversion is limited to the shallow/exterior domain')
            return GeodeticFrame(fixed).to_fixed(lon,lat,h)
        l,p=math.radians(lon),math.radians(lat)
        direction=(math.cos(p)*math.cos(l),math.cos(p)*math.sin(l),math.sin(p))
        radius=1/math.hypot(*(v/a for v,a in zip(direction,self.body.axes)))
        if h<=-radius:raise ValueError('Radial coordinate must lie strictly beyond the body center')
        return Coordinates(tuple(v*(radius+h) for v in direction),fixed)

    def from_fixed(self, coordinates):
        from ._frames import Coordinates,ReferenceFrame,GeodeticFrame
        fixed=ReferenceFrame(self.frame,self.body,epoch=self.epoch)
        if not isinstance(coordinates,Coordinates) or coordinates.frame!=fixed:raise ValueError('Body/frame mismatch')
        if self.body.shape=='irregular':raise UnsupportedBodyOperation('Irregular surface coordinates not implemented')
        if self.latitude_type=='planetographic':
            lon,lat,h=GeodeticFrame(fixed).from_fixed(coordinates)
            if h < -min(10000,self.body.ellipsoid.semi_minor_axis*.01)-1e-7:raise ValueError('Normal height outside shallow/exterior domain')
        else:
            x,y,z=coordinates.xyz;r=math.hypot(x,y,z)
            if r==0:raise ValueError('Body center has no surface coordinate')
            lon=math.degrees(math.atan2(y,x));lat=math.degrees(math.atan2(z,math.hypot(x,y)))
            radius=1/math.hypot(*(v/r/a for v,a in zip((x,y,z),self.body.axes)));h=r-radius
        return (DEGREE.convert(self.longitude.from_east(lon,self.prime_meridian),self.angle_unit),
                DEGREE.convert(lat,self.angle_unit),METRE.convert(h,self.height_unit))

    def convert(self, lon, lat, height=0, *, target):
        if not isinstance(target,PlanetaryContext):raise TypeError('Require target PlanetaryContext')
        if self.body!=target.body or self.datum!=target.datum or self.frame!=target.frame or self.epoch!=target.epoch:
            raise UnsupportedBodyOperation('Body/datum/frame/epoch changes are not inferred')
        return target.from_fixed(self.to_fixed(lon,lat,height))


@dataclass(frozen=True)
class PlanetaryData:
    """Immutable geographic features with explicit static coordinate context.

    This wrapper is not RFC 7946 GeoJSON. Plain GeoJSON remains terrestrial;
    explicit wrapping is the caller's declaration about the source coordinates.
    """
    features: FeatureCollection
    context: PlanetaryContext

    def __post_init__(self):
        if not isinstance(self.features,FeatureCollection) or not isinstance(self.context,PlanetaryContext):
            raise TypeError('PlanetaryData requires FeatureCollection and PlanetaryContext')
        for feature in self.features:
            if feature.geometry:
                for point in feature.geometry.iter_positions():self.context.canonical(*point[:2])

    @property
    def body(self):return self.context.body

    def select(self,*args,**kwargs):return PlanetaryData(self.features.select(*args,**kwargs),self.context)


def axis_context(body):
    # Existing terrestrial numeric plotting remains WGS84 geodetic lon/lat.
    return PlanetaryContext.for_body(body,latitude_type='planetographic' if body==EARTH else 'planetocentric')


def resolve_context(body=None,context=None,*,default=None):
    if body is not None and context is not None:raise ValueError('Use body or context, not both')
    if context is not None:
        if not isinstance(context,PlanetaryContext):raise TypeError('Require PlanetaryContext')
        return context
    if body is not None:
        if not isinstance(body,Body):raise TypeError('Require Body')
        return axis_context(body)
    return default if default is not None else axis_context(EARTH)


def angular_projection(context, projection, parameters):
    from .projections import Equirectangular,get_projection
    if context.body==EARTH:
        if (context.latitude_type!='planetographic' or context.longitude!=LongitudeConvention() or
                context.angle_unit!=DEGREE or context.prime_meridian!=0):
            raise UnsupportedBodyOperation('Terrestrial Axes retain canonical geodetic east-positive signed degrees; convert data explicitly')
        return get_projection(projection,**(parameters or {}))
    if (context.latitude_type!='planetocentric' or context.longitude!=LongitudeConvention() or
            context.angle_unit!=DEGREE or context.prime_meridian!=0):
        raise UnsupportedBodyOperation('Phase A angular Axes require east-positive signed degrees, zero meridian offset and planetocentric latitude; convert data explicitly')
    context.body.capability('angular_map').require(experimental=True)
    if parameters and set(parameters)-{'central_longitude','central_latitude','standard_parallel'}:
        raise UnsupportedBodyOperation('Planetary metric projection parameters are not supported in Phase A')
    if isinstance(projection,str):
        if projection!='equirectangular':raise UnsupportedBodyOperation('Planetary surface projections await Phase B; use the nonmetric equirectangular angular chart')
        return Equirectangular(radius=1,**(parameters or {}))
    if type(projection) is not Equirectangular or projection.radius!=1:
        raise UnsupportedBodyOperation('Non-Earth Phase A uses an explicit radius=1 angular chart, not surface metres')
    return projection
