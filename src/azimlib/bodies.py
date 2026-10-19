"""Static body surfaces and explicit capability contracts; no ephemeris engine."""
from dataclasses import dataclass, field
from enum import Enum
import math
import re
from .geometry import _number
from .geodesy import Ellipsoid, WGS84, METRE, Unit


class UnsupportedBodyOperation(NotImplementedError):
    """The declared surface/frame has no demonstrated implementation here."""


class CapabilityStatus(str, Enum):
    SUPPORTED = 'supported'
    EXPERIMENTAL = 'experimental'
    RESEARCH = 'research'
    NOT_IMPLEMENTED = 'not_implemented'


@dataclass(frozen=True)
class Capability:
    operation: str
    status: CapabilityStatus
    reason: str

    def require(self, *, experimental=False):
        if self.status is CapabilityStatus.SUPPORTED or experimental and self.status is CapabilityStatus.EXPERIMENTAL:
            return self
        raise UnsupportedBodyOperation(f'{self.operation}: {self.status.value}: {self.reason}')


@dataclass(frozen=True)
class BodySource:
    """Small source identity for factual model parameters, not bundled kernels."""
    origin: str
    version: str
    description: str
    sha256: str = ''

    def __post_init__(self):
        for name in ('origin', 'version', 'description'):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError('Source requires origin, version and description')
        if not isinstance(self.sha256, str) or self.sha256 and not re.fullmatch('[0-9a-f]{64}', self.sha256):
            raise ValueError('Source SHA-256 must be empty or 64 lowercase hex characters')


@dataclass(frozen=True)
class LongitudeConvention:
    direction: str = 'east'
    interval: str = 'signed'

    def __post_init__(self):
        if self.direction not in ('east', 'west') or self.interval not in ('signed', 'positive'):
            raise ValueError('Longitude requires east/west and signed/positive')

    def to_east(self, value, prime_meridian=0):
        value = _number(value, 'longitude')
        low, high = (-180, 180) if self.interval == 'signed' else (0, 360)
        if not low <= value <= high:
            raise ValueError('Longitude outside declared interval')
        return ((value if self.direction == 'east' else -value) + prime_meridian + 180) % 360 - 180

    def from_east(self, value, prime_meridian=0):
        value = (_number(value) - prime_meridian) * (1 if self.direction == 'east' else -1)
        return (value + 180) % 360 - 180 if self.interval == 'signed' else value % 360


@dataclass(frozen=True)
class SurfaceMesh:
    """Explicit bounded, immutable triangle data; not a geodesy certificate."""
    vertices: tuple
    faces: tuple
    source: BodySource

    def __post_init__(self):
        if not isinstance(self.source, BodySource):
            raise TypeError('Mesh requires explicit BodySource')
        if not 3 <= len(self.vertices) <= 100000 or not 1 <= len(self.faces) <= 200000:
            raise ValueError('Mesh size outside bounded representation')
        vertices = tuple(tuple(_number(v) for v in p) for p in self.vertices)
        faces = tuple(tuple(f) for f in self.faces)
        if any(len(p) != 3 for p in vertices):raise ValueError('Mesh vertices require XYZ metres')
        if any(abs(v)>1e12 for p in vertices for v in p):raise ValueError('Mesh vertex magnitude exceeds the supported 1e12 metre range')
        if any(len(f) != 3 or any(type(i) is not int or not 0 <= i < len(vertices) for i in f) or len(set(f)) != 3 for f in faces):
            raise ValueError('Mesh faces require three distinct valid indices')
        for f in faces:
            a,b,c=(vertices[i] for i in f)
            u,v=tuple(b[i]-a[i] for i in range(3)),tuple(c[i]-a[i] for i in range(3))
            cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
            if math.hypot(*cross)==0:raise ValueError('Degenerate mesh triangle')
        object.__setattr__(self, 'vertices', vertices);object.__setattr__(self, 'faces', faces)


@dataclass(frozen=True, init=False)
class Body:
    """Immutable static reference surface. Axes and mesh coordinates use metres.

    The legacy Body(name, Ellipsoid) constructor is retained. Orientation/frame
    are identifiers only: they never evaluate an inertial/time transformation.
    """
    name: str
    identifier: str
    shape: str
    axes: tuple
    mesh: SurfaceMesh | None
    prime_meridian: float
    longitude: LongitudeConvention
    frame: str
    datum: str
    epoch: str | None
    orientation: str
    provenance: tuple
    metadata: tuple
    unit: Unit
    _ellipsoid: Ellipsoid | None = field(repr=False)

    def __init__(self, name, ellipsoid=None, *, identifier=None, shape=None, axes=None,
                 mesh=None, prime_meridian=0, longitude=LongitudeConvention(), frame=None,
                 datum=None, epoch=None, orientation='body-fixed; inertial orientation not evaluated',
                 provenance=(), metadata=(), unit=METRE):
        if not isinstance(name,str) or not name.strip():raise ValueError('Body requires a name')
        identifier=name if identifier is None else identifier
        if not isinstance(identifier,str) or not identifier.strip():raise ValueError('Body requires an identifier')
        if ellipsoid is not None and not isinstance(ellipsoid,Ellipsoid):raise TypeError('Require an Ellipsoid')
        if not isinstance(unit,Unit) or unit != METRE:raise ValueError('Body dimensions are explicitly metres')
        if ellipsoid is not None:
            if axes is not None or mesh is not None:raise ValueError('Use ellipsoid or axes/mesh, not both')
            axes=(ellipsoid.semi_major_axis,ellipsoid.semi_major_axis,ellipsoid.semi_minor_axis)
        if mesh is not None:
            if not isinstance(mesh,SurfaceMesh) or axes is not None:raise ValueError('Irregular body requires only a SurfaceMesh')
            inferred='irregular';axes=()
        else:
            if axes is None:raise ValueError('Body requires axes, an ellipsoid or an explicit mesh')
            axes=tuple(_number(v,'semi-axis') for v in axes)
            if len(axes)!=3 or not 1e-3<=min(axes)<=max(axes)<=1e12 or not axes[0]>=axes[1]>=axes[2]:
                raise ValueError('Require ordered semi-axes a >= b >= c in the supported [1e-3,1e12] metre range')
            inferred='sphere' if axes[0]==axes[2] else 'ellipsoid' if axes[0]==axes[1] else 'triaxial'
        if shape is not None and shape != inferred:raise ValueError('Declared shape disagrees with axes/mesh')
        if not isinstance(longitude,LongitudeConvention):raise TypeError('Require LongitudeConvention')
        meridian=_number(prime_meridian,'prime meridian')
        if not -180<=meridian<=180:raise ValueError('Prime meridian offset must be signed degrees')
        frame=name+' fixed' if frame is None else frame;datum=name+' reference surface' if datum is None else datum
        for value in (frame,datum,orientation):
            if not isinstance(value,str) or not value.strip():raise ValueError('Frame, datum and orientation must be declared identifiers')
        if epoch is not None and (not isinstance(epoch,str) or not epoch.strip()):raise ValueError('Epoch must be a nonempty declared identifier')
        provenance=tuple(provenance)
        if any(not isinstance(s,BodySource) for s in provenance):raise TypeError('Require BodySource provenance entries')
        metadata=tuple(tuple(pair) for pair in metadata)
        if any(len(p)!=2 or any(not isinstance(v,str) for v in p) for p in metadata) or len({p[0] for p in metadata})!=len(metadata):
            raise ValueError('Metadata requires unique string key/value pairs')
        for key,value in dict(name=name,identifier=identifier,shape=inferred,axes=axes,mesh=mesh,
            prime_meridian=meridian,longitude=longitude,frame=frame,datum=datum,epoch=epoch,
            orientation=orientation,provenance=provenance,metadata=metadata,unit=METRE,_ellipsoid=ellipsoid).items():
            object.__setattr__(self,key,value)

    @property
    def ellipsoid(self):
        if self._ellipsoid is not None:return self._ellipsoid
        if self.shape not in ('sphere','ellipsoid'):raise UnsupportedBodyOperation('No oblate ellipsoid for '+self.shape)
        a,_,c=self.axes;rf=0 if a==c else a/(a-c)
        if rf and rf<150:raise UnsupportedBodyOperation('Existing geodetic solver requires inverse flattening >= 150')
        return Ellipsoid(a,rf,self.name+' static surface')

    def capability(self, operation, *, backend='cpu'):
        known=('static_coordinates','planetocentric','planetographic','angular_map','planetary_projection','surface_geodesy',
               'temporal_orientation','irregular_geodesy','groups')
        if operation not in known:raise ValueError('Unknown capability: '+str(operation))
        if backend not in ('cpu','svg','png','pdf','gpu'):raise ValueError('Unknown backend')
        status=CapabilityStatus.NOT_IMPLEMENTED;reason='Not implemented in Phase A'
        if operation in ('static_coordinates','planetocentric') and self.shape!='irregular':
            status=CapabilityStatus.SUPPORTED;reason='Static radial coordinates; oblate normal coordinates within declared domain'
        elif operation=='planetographic':
            try:self.ellipsoid
            except UnsupportedBodyOperation:reason='Normal coordinates for this shape/flattening are not implemented'
            else:status=CapabilityStatus.SUPPORTED;reason='Static oblate normal-height conversion, height >= -10 km'
        elif operation=='angular_map' and self.shape!='irregular':
            status=CapabilityStatus.EXPERIMENTAL;reason='Nonmetric longitude/latitude chart; not a validated planetary surface projection'
        elif operation=='groups':status=CapabilityStatus.SUPPORTED;reason='Owned 2D Layer groups; physical clip paths remain unsupported'
        elif operation=='irregular_geodesy':status=CapabilityStatus.RESEARCH;reason='No demonstrated irregular-surface solver'
        if backend=='gpu' and operation in ('angular_map','groups'):
            status=CapabilityStatus.NOT_IMPLEMENTED;reason='Planetary/group GPU coverage not validated in Phase A'
        return Capability(operation,status,reason)


_PCK=BodySource('https://naif.jpl.nasa.gov/pub/naif/generic_kernels/pck/pck00011.tpc',
    '2022-12-27 / pck00011','BODY199/299/301/499_RADII, km converted to metres; facts only, no kernel/code bundled',
    '3dff7b1dbeceaa01f25467767d3fa25816051c85d162d1edf04acb310ee28bb1')
EARTH=Body('Earth',WGS84,identifier='earth',frame='Earth fixed',datum='WGS84',provenance=(
    BodySource('https://earth-info.nga.mil/index.php?dir=wgs84&action=wgs84','WGS84',
               'Existing Azimlib WGS84: a=6378137 m, inverse flattening=298.257223563; no realization/epoch shift implied'),))
MOON=Body('Moon',identifier='moon',axes=(1737400,)*3,frame='IAU_MOON',provenance=(_PCK,))
MARS=Body('Mars',identifier='mars',axes=(3396190,3396190,3376200),frame='IAU_MARS',provenance=(_PCK,))
VENUS=Body('Venus',identifier='venus',axes=(6051800,)*3,frame='IAU_VENUS',provenance=(_PCK,))
MERCURY=Body('Mercury',identifier='mercury',axes=(2440530,2440530,2438260),frame='IAU_MERCURY',provenance=(_PCK,))


@dataclass(frozen=True)
class BodyRegistry:
    bodies: tuple = (EARTH,MOON,MARS,VENUS,MERCURY)

    def __post_init__(self):
        values=tuple(self.bodies)
        if any(not isinstance(b,Body) for b in values):raise TypeError('Registry requires Bodies')
        if len({b.identifier for b in values})!=len(values):raise ValueError('Duplicate Body identifier')
        object.__setattr__(self,'bodies',values)

    def get(self, identifier):
        if not isinstance(identifier,str):raise TypeError('Body identifier must be a string')
        for body in self.bodies:
            if body.identifier==identifier:return body
        raise KeyError(identifier)

    def with_body(self, body):return BodyRegistry((*self.bodies,body))


BODIES=BodyRegistry()
