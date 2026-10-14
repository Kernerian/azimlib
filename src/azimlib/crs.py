"""Own explicit WGS84 conversions; finite catalog, always longitude first.

Geocentric XYZ and geographic 3D require explicit height. No global datum
database, realization alignment or implicit epoch/grid operation is implied.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
import json
from os import PathLike
from pathlib import Path
from math import atan, degrees, exp, log, pi, radians, tan

from .geometry import _number, position
from .geodesy import WGS84_DATUM
from .transverse import tm_forward, tm_inverse, utm_zone, utm_crs
from ._crs_catalog import CRSCatalog, CRSDefinition, crs_catalog
from ._frames import GEODETIC, Coordinates

WEB_MERCATOR_RADIUS = 6_378_137.0
WEB_MERCATOR_MAX_LATITUDE = 85.0511287798066


@dataclass(frozen=True)
class CRS:
    """A supported CRS; all geographic coordinates explicitly use x=lon,y=lat."""
    code: str = "EPSG:4326"

    def __post_init__(self):
        object.__setattr__(self, "code", crs_catalog.get(self.code).code)

    @classmethod
    def from_user_input(cls, value):
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            return cls.from_dict(value)
        return cls(value)

    @property
    def definition(self): return crs_catalog.get(self.code)
    @property
    def dimensions(self): return self.definition.dimensions
    @property
    def is_geocentric(self): return self.definition.kind == 'geocentric'
    @property
    def authority_axis_order(self): return self.definition.authority_axes
    @property
    def axis_units(self): return self.definition.axis_units
    @property
    def area_of_use(self): return self.definition.area_of_use

    def to_string(self): return self.code
    def to_dict(self): return self.definition.to_dict()

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, Mapping) or 'code' not in value:
            raise ValueError('Require the complete azimlib-crs profile')
        result = cls(value['code'])
        if dict(value) != result.to_dict():
            raise ValueError('CRS profile differs from this catalog; do not infer from an embedded identifier')
        return result

    @property
    def is_geographic(self):
        return self.definition.kind == 'geographic'

    @property
    def units(self):
        return "degrees" if self.is_geographic else "metres"

    @property
    def datum(self): return WGS84_DATUM
    @property
    def ellipsoid(self): return self.datum.ellipsoid
    @property
    def axis_order(self): return self.definition.axes
    @property
    def zone(self):
        return int(self.code[5:])%100 if self.code.startswith(('EPSG:326','EPSG:327')) else None
    @property
    def hemisphere(self): return ('north' if self.code.startswith('EPSG:326') else 'south') if self.zone else None
    def _utm_parameters(self):
        return dict(central_longitude=self.zone*6-183,scale_factor=.9996,false_easting=500000,false_northing=0 if self.hemisphere=='north' else 10000000)
    def _check_utm_latitude(self,lat):
        if not -80<=lat<=84 or (lat<0 and self.hemisphere=='north') or (lat>0 and self.hemisphere=='south'):
            raise ValueError('Latitude outside UTM hemisphere/domain')

    def transform_to(self, target, x, y, z=None):
        return Transformer(self, target).transform(x, y, z)


def transform(x, y, source="EPSG:4326", target="EPSG:3857"):
    """Transform one coordinate pair, always using longitude before latitude.

    Raises ValueError outside the conventional square Web Mercator domain,
    instead of clamping coordinates or silently accepting another datum.
    """
    source, target = CRS.from_user_input(source), CRS.from_user_input(target)
    if source.dimensions == 3 or target.dimensions == 3:
        raise ValueError('3D CRS requires explicit z via Transformer.transform(x,y,z)')
    x, y = _number(x, "x"), _number(y, "y")
    if source.is_geographic:
        lon, lat = position((x, y))
        if not -180 <= lon <= 180:
            raise ValueError("CRS longitude must lie between -180 and 180")
    elif source.zone:
        if not 0<=x<=1000000 or not 0<=y<=10000000: raise ValueError("Coordinate outside UTM domain")
        lon,lat=tm_inverse(x,y,**source._utm_parameters())
        source._check_utm_latitude(lat)
    else:
        maximum = pi*WEB_MERCATOR_RADIUS
        if abs(x) > maximum+1e-6 or abs(y) > maximum+1e-6:
            raise ValueError("coordinate lies outside the conventional EPSG:3857 domain")
        lon = degrees(x/WEB_MERCATOR_RADIUS)
        lat = degrees(2*atan(exp(y/WEB_MERCATOR_RADIUS))-pi/2)
    if source == target:
        return x, y
    if target.is_geographic:
        return lon, lat
    if target.zone:
        target._check_utm_latitude(lat)
        result=tm_forward(lon,lat,**target._utm_parameters())
        if not 0<=result[0]<=1000000 or not 0<=result[1]<=10000000: raise ValueError("Coordinate outside UTM domain")
        return result
    if abs(lat) > WEB_MERCATOR_MAX_LATITUDE+1e-12:
        raise ValueError("latitude lies outside the conventional EPSG:3857 domain")
    return WEB_MERCATOR_RADIUS*radians(lon), WEB_MERCATOR_RADIUS*log(tan(pi/4+radians(lat)/2))


def transform_coordinates(coordinates, source="EPSG:4326", target="EPSG:3857"):
    """Transform positions; actual XYZ conversion for explicit 3D CRS.

    The legacy 2D-to-2D path preserves optional elevation without datum shifts.
    Explicit 3D CRSs require three input/output values; no zero height inferred.
    """
    result = []
    transformer = Transformer(source, target)
    for point in coordinates:
        values = tuple(point)
        if len(values) not in (2, 3):
            raise ValueError("coordinates require two or three numbers")
        result.append(transformer.transform(*values))
    return tuple(result)


def transform_geojson(data, source="EPSG:4326", target="EPSG:3857"):
    """Transform raw GeoJSON coordinates before geographic geometry validation.

    Accept a mapping, path, JSON string, file or __geo_interface__. Return a
    new mapping with transformed coordinates. Bounding boxes and legacy CRS
    members are omitted because their coordinate values would become stale.
    The caller supplies the source CRS explicitly, including for legacy data.
    """
    source, target = CRS.from_user_input(source), CRS.from_user_input(target)
    if hasattr(data, "__geo_interface__"):
        data = data.__geo_interface__
    if isinstance(data, PathLike):
        data = json.loads(Path(data).read_text(encoding="utf-8-sig"))
    elif isinstance(data, str):
        if data.lstrip("\ufeff \t\r\n").startswith(("{", "[")):
            data = json.loads(data.lstrip("\ufeff"))
        else:
            data = json.loads(Path(data).read_text(encoding="utf-8-sig"))
    elif isinstance(data, bytes):
        data = json.loads(data.decode("utf-8-sig"))
    elif hasattr(data, "read"):
        data = json.load(data)
    depths = {"Point": 0, "MultiPoint": 1, "LineString": 1,
              "MultiLineString": 2, "Polygon": 2, "MultiPolygon": 3}
    def coordinates(value, depth):
        if not isinstance(value, (list, tuple)):
            raise ValueError("GeoJSON coordinates must be arrays")
        if not value:
            return []
        if depth == 0:
            return list(transform_coordinates((value,), source, target)[0])
        return [coordinates(child, depth-1) for child in value]
    def convert(obj):
        if not isinstance(obj, Mapping):
            raise ValueError("GeoJSON must contain objects")
        result = {k: v for k, v in obj.items() if k not in ("crs", "bbox")}
        kind = obj.get("type")
        if kind in depths:
            if "coordinates" not in obj:
                raise ValueError("geometry requires coordinates")
            result["coordinates"] = coordinates(obj["coordinates"], depths[kind])
        elif kind == "GeometryCollection":
            values = obj.get("geometries")
            if not isinstance(values, (list, tuple)):
                raise ValueError("GeometryCollection requires a geometries array")
            result["geometries"] = [convert(g) for g in values]
        elif kind == "Feature":
            if "geometry" not in obj:
                raise ValueError("Feature requires a geometry member")
            result["geometry"] = convert(obj["geometry"]) if obj["geometry"] is not None else None
        elif kind == "FeatureCollection":
            values = obj.get("features")
            if not isinstance(values, (list, tuple)):
                raise ValueError("FeatureCollection requires a features array")
            result["features"] = [convert(f) for f in values]
        else:
            raise ValueError(f"unknown GeoJSON type {kind!r}")
        return result
    return convert(data)


@dataclass(frozen=True)
class Transformer:
    source: CRS
    target: CRS

    def __post_init__(self):
        object.__setattr__(self, "source", CRS.from_user_input(self.source))
        object.__setattr__(self, "target", CRS.from_user_input(self.target))

    @classmethod
    def from_crs(cls, source, target):
        return cls(source, target)

    def transform(self, x, y, z=None):
        source, target = self.source, self.target
        if source.dimensions != 3 and target.dimensions != 3:
            extra = () if z is None else (_number(z, 'elevation'),)
            return transform(x, y, source, target) + extra
        if z is None:
            raise ValueError('3D CRS conversion requires explicit z/ellipsoidal height')
        x, y, z = _number(x, 'x'), _number(y, 'y'), _number(z, 'z')
        if source.is_geocentric:
            lon, lat, height = GEODETIC.from_fixed(Coordinates((x, y, z)))
        else:
            if source.is_geographic:
                lon, lat = position((x, y))
            else:
                lon, lat = transform(x, y, source, 4326)
            height = z
            GEODETIC.to_fixed(lon, lat, height)  # Validate the full 3D domain.
        if source == target:
            return x, y, z
        if target.is_geocentric:
            return GEODETIC.to_fixed(lon, lat, height).xyz
        if target.is_geographic:
            return lon, lat, height
        return transform(lon, lat, 4326, target) + (height,)

    def inverse(self):
        return Transformer(self.target, self.source)
