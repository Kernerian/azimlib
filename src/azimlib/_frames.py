"""Internal metric frames; independent equations, not an inertial/EOP engine.

Geodetic coordinates are longitude/latitude degrees and ellipsoidal metres.
Fixed XYZ is right handed: X at Greenwich/equator, Y at 90E, Z at north.
See docs/foundation-0.4.md for sources, limits and precision contracts.
"""
from dataclasses import dataclass
from functools import cached_property
import math

from .geometry import _number
from .geodesy import Ellipsoid, WGS84


def vector3(value):
    result = tuple(_number(v) for v in value)
    if len(result) != 3:
        raise ValueError('Require exactly three finite coordinates')
    return result


def _geodetic_xyz(lon, lat, height, ellipsoid):
    """Shared equations after validation at the typed/terrain input boundary."""
    l, p = math.radians(lon), math.radians(lat)
    s, c = math.sin(p), math.cos(p)
    n = ellipsoid.semi_major_axis / math.sqrt(1-ellipsoid.eccentricity_squared*s*s)
    return ((n+height)*c*math.cos(l), (n+height)*c*math.sin(l),
            (n*(1-ellipsoid.eccentricity_squared)+height)*s)


@dataclass(frozen=True)
class Body:
    """Internal oblate reference surface; no ephemeris, mass or public registry."""
    name: str
    ellipsoid: Ellipsoid

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError('Body requires a nonempty name')
        if not isinstance(self.ellipsoid, Ellipsoid):
            raise TypeError('Body requires an Ellipsoid')


EARTH = Body('Earth', WGS84)


@dataclass(frozen=True)
class ReferenceFrame:
    """Identity of a metric Cartesian frame; equality includes its full body."""
    name: str
    body: Body = EARTH
    kind: str = 'fixed'

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError('Frame requires a nonempty name')
        if not isinstance(self.body, Body):
            raise TypeError('Frame requires a Body')
        if self.kind not in ('fixed', 'local'):
            raise ValueError('Supported frame kinds are fixed and local')


EARTH_FIXED = ReferenceFrame('Earth fixed')


@dataclass(frozen=True)
class Coordinates:
    xyz: tuple
    frame: ReferenceFrame = EARTH_FIXED

    def __post_init__(self):
        object.__setattr__(self, 'xyz', vector3(self.xyz))
        if not isinstance(self.frame, ReferenceFrame):
            raise TypeError('Coordinates require a ReferenceFrame')


@dataclass(frozen=True)
class RigidTransform:
    """Explicit source-to-target rotation/translation in metres, row-major.

Directions skip translation. No scale, reflection, datum shift or inferred
celestial rotation is accepted. Composition requires matching intermediate frames.
"""
    source: ReferenceFrame
    target: ReferenceFrame
    rotation: tuple = (1, 0, 0, 0, 1, 0, 0, 0, 1)
    translation: tuple = (0, 0, 0)

    def __post_init__(self):
        if not isinstance(self.source, ReferenceFrame) or not isinstance(self.target, ReferenceFrame):
            raise TypeError('Transform requires source and target frames')
        if self.source.body != self.target.body:
            raise ValueError('Rigid transforms do not change reference bodies')
        r = tuple(_number(v) for v in self.rotation)
        if len(r) != 9:
            raise ValueError('Rotation requires nine row-major components')
        for i in range(3):
            for j in range(3):
                if abs(sum(r[i*3+k]*r[j*3+k] for k in range(3)) - (i == j)) > 1e-12:
                    raise ValueError('Rotation must be orthonormal')
        det = r[0]*(r[4]*r[8]-r[5]*r[7])-r[1]*(r[3]*r[8]-r[5]*r[6])+r[2]*(r[3]*r[7]-r[4]*r[6])
        if abs(det-1) > 1e-12:
            raise ValueError('Rotation must preserve handedness')
        object.__setattr__(self, 'rotation', r)
        object.__setattr__(self, 'translation', vector3(self.translation))

    def apply(self, coordinates, *, direction=False):
        if not isinstance(coordinates, Coordinates) or coordinates.frame != self.source:
            raise ValueError('Coordinate frame does not match transform source')
        r, p = self.rotation, coordinates.xyz
        values = tuple(sum(r[i*3+k]*p[k] for k in range(3)) +
                       (0 if direction else self.translation[i]) for i in range(3))
        return Coordinates(values, self.target)

    def inverse(self):
        r = tuple(self.rotation[j*3+i] for i in range(3) for j in range(3))
        t = tuple(-sum(r[i*3+k]*self.translation[k] for k in range(3)) for i in range(3))
        return RigidTransform(self.target, self.source, r, t)

    def then(self, following):
        if not isinstance(following, RigidTransform) or self.target != following.source:
            raise ValueError('Intermediate frames must match exactly')
        a, b = self.rotation, following.rotation
        r = tuple(sum(b[i*3+k]*a[k*3+j] for k in range(3)) for i in range(3) for j in range(3))
        t = tuple(sum(b[i*3+k]*self.translation[k] for k in range(3)) +
                  following.translation[i] for i in range(3))
        return RigidTransform(self.source, following.target, r, t)


@dataclass(frozen=True)
class GeodeticFrame:
    """Oblate surface conversion, h >= -10 km; no geoid/datum or epoch shifts."""
    fixed: ReferenceFrame = EARTH_FIXED

    def __post_init__(self):
        if not isinstance(self.fixed, ReferenceFrame):
            raise TypeError('Require a fixed ReferenceFrame')
        if self.fixed.kind != 'fixed':
            raise ValueError('Geodetic conversion requires a body-fixed frame')

    def to_fixed(self, lon, lat, height=0):
        lon, lat, height = _number(lon), _number(lat), _number(height)
        if not -180 <= lon <= 180 or not -90 <= lat <= 90 or height < -10000:
            raise ValueError('Require canonical lon/lat and ellipsoidal height >= -10000 m')
        return Coordinates(_geodetic_xyz(lon, lat, height, self.fixed.body.ellipsoid), self.fixed)

    def from_fixed(self, coordinates):
        if not isinstance(coordinates, Coordinates) or coordinates.frame != self.fixed:
            raise ValueError('Coordinate frame does not match fixed frame')
        x, y, z = coordinates.xyz
        e = self.fixed.body.ellipsoid
        p = math.hypot(x, y)
        if math.hypot(p, z) < e.semi_minor_axis-10001:
            raise ValueError('Coordinates outside shallow/exterior geodetic domain')
        lon = math.degrees(math.atan2(y, x))
        if p < 1e-9:
            lat, h = math.copysign(90., z), abs(z)-e.semi_minor_axis
        else:
            phi = math.atan2(z, p*(1-e.eccentricity_squared))
            for _ in range(20):
                n = e.semi_major_axis/math.sqrt(1-e.eccentricity_squared*math.sin(phi)**2)
                next_phi = math.atan2(z+e.eccentricity_squared*n*math.sin(phi), p)
                if abs(next_phi-phi) <= 1e-15:
                    phi = next_phi
                    break
                phi = next_phi
            else:
                raise ArithmeticError('Geodetic inverse failed to converge')
            s, c = math.sin(phi), math.cos(phi)
            # Projection onto the normal avoids division by cos(phi) near poles.
            h = p*c+z*s-e.semi_major_axis*math.sqrt(1-e.eccentricity_squared*s*s)
            lat = math.degrees(phi)
        if h < -10000-1e-7:
            raise ValueError('Ellipsoidal height outside supported domain')
        return _number(lon), _number(lat), _number(h)


GEODETIC = GeodeticFrame()


@dataclass(frozen=True)
class Observer:
    """Ellipsoidal observer and geometric ENU horizon, without atmosphere.

Azimuth is clockwise from north; elevation is above the local tangent plane.
Geocentric positions must be translated before topocentric directions are used.
Apparent positions/refraction/light time are intentionally not inferred here.
"""
    longitude: float
    latitude: float
    height: float = 0
    horizon: float = 0
    geodetic: GeodeticFrame = GEODETIC

    def __post_init__(self):
        if not isinstance(self.geodetic, GeodeticFrame):
            raise TypeError('Observer requires a GeodeticFrame')
        for name in ('longitude', 'latitude', 'height', 'horizon'):
            object.__setattr__(self, name, _number(getattr(self, name)))
        self.geodetic.to_fixed(self.longitude, self.latitude, self.height)
        if not -90 <= self.horizon <= 90:
            raise ValueError('Horizon must be in [-90,90] degrees')

    @cached_property
    def fixed_position(self):
        return self.geodetic.to_fixed(self.longitude, self.latitude, self.height)

    @cached_property
    def to_local(self):
        l, p = math.radians(self.longitude), math.radians(self.latitude)
        sl, cl, sp, cp = math.sin(l), math.cos(l), math.sin(p), math.cos(p)
        r = (-sl, cl, 0, -sp*cl, -sp*sl, cp, cp*cl, cp*sl, sp)
        origin = self.fixed_position.xyz
        t = tuple(-sum(r[i*3+k]*origin[k] for k in range(3)) for i in range(3))
        frame = ReferenceFrame(f'ENU:{self.longitude!r},{self.latitude!r},{self.height!r}',
                               self.geodetic.fixed.body, 'local')
        return RigidTransform(self.geodetic.fixed, frame, r, t)

    def azimuth_elevation(self, target, *, direction=False):
        east, north, up = self.to_local.apply(target, direction=direction).xyz
        horizontal = math.hypot(east, north)
        if math.hypot(horizontal, up) < 1e-12:
            raise ValueError('Coincident observer/target has no direction')
        azimuth = None if horizontal < 1e-12 else math.degrees(math.atan2(east, north)) % 360
        return azimuth, math.degrees(math.atan2(up, horizontal))

    def local_direction(self, azimuth, elevation):
        azimuth, elevation = _number(azimuth), _number(elevation)
        if not -90 <= elevation <= 90:
            raise ValueError('Elevation must be in [-90,90] degrees')
        a, e = math.radians(azimuth % 360), math.radians(elevation)
        return Coordinates((math.cos(e)*math.sin(a), math.cos(e)*math.cos(a), math.sin(e)),
                           self.to_local.target)

    def above_horizon(self, target, *, direction=False):
        return self.azimuth_elevation(target, direction=direction)[1] >= self.horizon
