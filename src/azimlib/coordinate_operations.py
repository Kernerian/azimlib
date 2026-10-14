"""Independent explicit coordinate operations; no implicit datum selection.

Helmert uses the small-angle model, not a finite Euler rotation. Units are
metres, arcseconds and ppm; rates use those units per decimal Julian year.
Equations: IOGP GN7-2 (2019), sections 4.1.1, 4.2.3 and 4.2.5.
"""
from dataclasses import dataclass
import math

from .geometry import _number, wrap_longitude
from .geodesy import Datum, WGS84_DATUM
from ._frames import Body, ReferenceFrame, GeodeticFrame, Coordinates, vector3


def _label(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Require a nonempty frame name')
    return value


@dataclass(frozen=True)
class CoordinateFrame:
    """Explicit user-defined datum/realization identity, not an EPSG lookup.

    Geographic triples are lon/lat degrees and metres in height_reference
    (ellipsoidal by default); geocentric triples are metric XYZ. Gravity-related
    heights require an explicit vertical operation before geocentric conversion.
    Equal ellipsoids do not imply equal datums/frames.
    The name must identify the realization consistently for a given application.
    """
    name: str
    kind: str
    datum: Datum = WGS84_DATUM
    height_reference: str = 'ellipsoidal'

    def __post_init__(self):
        _label(self.name)
        if self.kind not in ('geographic', 'geocentric'):
            raise ValueError('Operation frames support geographic 3D or geocentric XYZ')
        if not isinstance(self.datum, Datum):
            raise TypeError('Coordinate frame requires a Datum')
        _label(self.height_reference)
        if self.kind == 'geocentric' and self.height_reference != 'ellipsoidal':
            raise ValueError('Geocentric coordinates require ellipsoidal height identity')

    @property
    def axis_units(self):
        return ('degrees', 'degrees', 'metres') if self.kind == 'geographic' else ('metres',)*3

    def _geodetic(self):
        return GeodeticFrame(ReferenceFrame(self.name, Body(self.datum.name, self.datum.ellipsoid)))


@dataclass(frozen=True)
class GeodeticConversion:
    """Convert representations of the SAME datum; never shift datum/epoch."""
    source: CoordinateFrame
    target: CoordinateFrame

    def __post_init__(self):
        if not isinstance(self.source, CoordinateFrame) or not isinstance(self.target, CoordinateFrame):
            raise TypeError('Require explicit CoordinateFrame endpoints')
        if (self.source.datum != self.target.datum or self.source.name != self.target.name or
                self.source.kind == self.target.kind or
                self.source.height_reference != 'ellipsoidal' or self.target.height_reference != 'ellipsoidal'):
            raise ValueError('Conversion requires the same datum/realization identity and opposite representations')

    def transform(self, x, y, z, *, epoch=None):
        if epoch is not None:
            _number(epoch, 'epoch')
        point = vector3((x, y, z))
        frame = self.source._geodetic()
        if self.source.kind == 'geographic':
            lon, lat, height = point
            if not -180 <= lon <= 180:
                raise ValueError('Longitude outside canonical domain')
            lon = wrap_longitude(lon + self.source.datum.prime_meridian)
            return frame.to_fixed(lon, lat, height).xyz
        lon, lat, height = frame.from_fixed(Coordinates(point, frame.fixed))
        return wrap_longitude(lon - self.source.datum.prime_meridian), lat, height

    def inverse(self):
        return GeodeticConversion(self.target, self.source)


def _parameters(value, size, name):
    result = tuple(_number(v, name) for v in value)
    if len(result) != size:
        raise ValueError(f'{name} requires exactly {size} finite values')
    return result


@dataclass(frozen=True)
class Helmert:
    """7/14 parameters, explicit direction/convention/epoch, exact model inverse.

    Parameters: tx,ty,tz (m), rx,ry,rz (arcsec), scale difference (ppm).
    Rates: same order/units per decimal Julian year. Dynamic operations require
    reference_epoch, valid_epochs and an explicit coordinate epoch on every call.
    No plate-motion model, coordinate propagation or WGS84 realization inferred.
    Optional area_of_use is lon/lat (W,S,E,N) in the SOURCE datum, dateline aware.
    """
    source: CoordinateFrame
    target: CoordinateFrame
    parameters: tuple
    convention: str
    rates: tuple = None
    reference_epoch: float = None
    valid_epochs: tuple = None
    area_of_use: tuple = None

    def __post_init__(self):
        for endpoint in (self.source, self.target):
            if not isinstance(endpoint, CoordinateFrame) or endpoint.kind != 'geocentric':
                raise ValueError('Helmert endpoints require explicit geocentric frames')
        if self.source == self.target:
            raise ValueError('Datum transformation requires distinct frame identities')
        if self.convention not in ('position_vector', 'coordinate_frame'):
            raise ValueError('Specify position_vector or coordinate_frame convention')
        object.__setattr__(self, 'parameters', _parameters(self.parameters, 7, 'parameters'))
        if self.rates is not None:
            object.__setattr__(self, 'rates', _parameters(self.rates, 7, 'rates'))
            if self.reference_epoch is None or self.valid_epochs is None:
                raise ValueError('Dynamic Helmert requires reference_epoch and valid_epochs')
        elif self.reference_epoch is not None:
            raise ValueError('reference_epoch requires explicit rates')
        if self.valid_epochs is not None:
            bounds = _parameters(self.valid_epochs, 2, 'valid_epochs')
            if bounds[0] > bounds[1]:
                raise ValueError('Epoch validity must be ordered')
            object.__setattr__(self, 'valid_epochs', bounds)
        if self.reference_epoch is not None:
            reference = _number(self.reference_epoch, 'reference_epoch')
            if not self.valid_epochs[0] <= reference <= self.valid_epochs[1]:
                raise ValueError('Reference epoch outside declared validity')
            object.__setattr__(self, 'reference_epoch', reference)
        if self.area_of_use is not None:
            w, s, e, n = _parameters(self.area_of_use, 4, 'area_of_use')
            if not (-180 <= w <= 180 and -180 <= e <= 180 and -90 <= s <= n <= 90):
                raise ValueError('Invalid geographic area of use')
            object.__setattr__(self, 'area_of_use', (w, s, e, n))
        self._matrix(self.reference_epoch if self.rates is not None else
                     (self.valid_epochs[0] if self.valid_epochs else None))

    def _matrix(self, epoch):
        if self.rates is not None or self.valid_epochs is not None:
            if epoch is None:
                raise ValueError('Coordinate epoch is required')
        if epoch is not None:
            epoch = _number(epoch, 'epoch')
            if self.valid_epochs and not self.valid_epochs[0] <= epoch <= self.valid_epochs[1]:
                raise ValueError('Coordinate epoch outside operation validity')
        values = self.parameters
        if self.rates is not None:
            values = tuple(p + r*(epoch-self.reference_epoch) for p, r in zip(values, self.rates))
        tx, ty, tz, rx, ry, rz, ppm = values
        if max(abs(rx), abs(ry), abs(rz)) > 3600 or abs(ppm) > 10000:
            raise ValueError('Parameters outside supported small-angle/scale model domain')
        sign = 1 if self.convention == 'position_vector' else -1
        rx, ry, rz = (sign*math.radians(v/3600) for v in (rx, ry, rz))
        m = 1 + ppm*1e-6
        return tuple(m*v for v in (1, -rz, ry, rz, 1, -rx, -ry, rx, 1)), (tx, ty, tz)

    def _area(self, point):
        if self.area_of_use is not None:
            frame = self.source._geodetic()
            lon, lat, _ = frame.from_fixed(Coordinates(point, frame.fixed))
            lon = wrap_longitude(lon-self.source.datum.prime_meridian)
            w, s, e, n = self.area_of_use
            inside = w <= lon <= e if w <= e else lon >= w or lon <= e
            if not inside or not s <= lat <= n:
                raise ValueError('Coordinate outside operation area of use')

    def transform(self, x, y, z, *, epoch=None):
        point = vector3((x, y, z)); matrix, translation = self._matrix(epoch)
        self._area(point)
        return vector3(tuple(sum(matrix[i*3+k]*point[k] for k in range(3)) + translation[i]
                             for i in range(3)))

    def inverse(self):
        return _InverseHelmert(self)


@dataclass(frozen=True)
class _InverseHelmert:
    operation: Helmert

    @property
    def source(self): return self.operation.target
    @property
    def target(self): return self.operation.source

    def transform(self, x, y, z, *, epoch=None):
        # Invert the actual evaluated matrix, not negated approximate parameters.
        a, t = self.operation._matrix(epoch)
        b = tuple(v-t[i] for i, v in enumerate(vector3((x, y, z))))
        cofactors = (a[4]*a[8]-a[5]*a[7], a[5]*a[6]-a[3]*a[8], a[3]*a[7]-a[4]*a[6],
                     a[2]*a[7]-a[1]*a[8], a[0]*a[8]-a[2]*a[6], a[1]*a[6]-a[0]*a[7],
                     a[1]*a[5]-a[2]*a[4], a[2]*a[3]-a[0]*a[5], a[0]*a[4]-a[1]*a[3])
        determinant = sum(a[i]*cofactors[i] for i in range(3))
        point = vector3(tuple(sum(cofactors[k*3+i]*b[k] for k in range(3))/determinant
                              for i in range(3)))
        self.operation._area(point)
        return point

    def inverse(self): return self.operation


@dataclass(frozen=True)
class CoordinatePipeline:
    """Explicit ordered operations with exactly matching intermediate identities.

    Supports Transformer conversions or CoordinateFrame operations. No implicit
    bridge between these types, fallback shifts, operation discovery or network.
    Every step receives the same explicit epoch; no temporal propagation inferred.
    """
    steps: tuple

    def __post_init__(self):
        steps = tuple(self.steps)
        if not steps:
            raise ValueError('Pipeline requires at least one operation')
        from .crs import Transformer
        from .grid_operations import GridOperation, InverseGridOperation
        allowed = (Transformer, GeodeticConversion, Helmert, _InverseHelmert,
                   GridOperation, InverseGridOperation)
        if any(not isinstance(step, allowed) for step in steps):
            raise TypeError('Unsupported coordinate operation')
        if any(a.target != b.source for a, b in zip(steps, steps[1:])):
            raise ValueError('Intermediate coordinate identities must match exactly')
        object.__setattr__(self, 'steps', steps)

    @property
    def source(self): return self.steps[0].source
    @property
    def target(self): return self.steps[-1].target

    def transform(self, x, y, z=None, *, epoch=None):
        from .crs import Transformer
        if epoch is not None:
            _number(epoch, 'epoch')
        point = (x, y) if z is None else (x, y, z)
        for step in self.steps:
            point = (step.transform(*point) if isinstance(step, Transformer) else
                     step.transform(*point, epoch=epoch))
        return point

    def inverse(self):
        return CoordinatePipeline(tuple(step.inverse() for step in reversed(self.steps)))

    def then(self, operation):
        following = operation.steps if isinstance(operation, CoordinatePipeline) else (operation,)
        return CoordinatePipeline(self.steps + following)
