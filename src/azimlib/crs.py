"""Explicit lon/lat and Web Mercator coordinate-reference transformations.

Only EPSG:4326 and EPSG:3857 are implemented. This module deliberately does not
pretend to provide a global datum database or ellipsoidal transformations.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
import json
from os import PathLike
from pathlib import Path
from math import atan, degrees, exp, log, pi, radians, tan

from .geometry import _number, position

WEB_MERCATOR_RADIUS = 6_378_137.0
WEB_MERCATOR_MAX_LATITUDE = 85.0511287798066


@dataclass(frozen=True)
class CRS:
    """A supported CRS; all geographic coordinates explicitly use x=lon,y=lat."""
    code: str = "EPSG:4326"

    def __post_init__(self):
        code = str(self.code).strip().upper()
        if code.isdigit():
            code = "EPSG:"+code
        if code in ("WGS84", "WGS 84", "CRS84", "OGC:CRS84"):
            code = "EPSG:4326"
        if code not in ("EPSG:4326", "EPSG:3857"):
            raise ValueError(f"unsupported CRS {self.code!r}; supported: EPSG:4326, EPSG:3857")
        object.__setattr__(self, "code", code)

    @classmethod
    def from_user_input(cls, value):
        return value if isinstance(value, cls) else cls(value)

    @property
    def is_geographic(self):
        return self.code == "EPSG:4326"

    @property
    def units(self):
        return "degrees" if self.is_geographic else "metres"

    def transform_to(self, target, x, y):
        return transform(x, y, self, target)


def transform(x, y, source="EPSG:4326", target="EPSG:3857"):
    """Transform one coordinate pair, always using longitude before latitude.

    Raises ValueError outside the conventional square Web Mercator domain,
    instead of clamping coordinates or silently accepting another datum.
    """
    source, target = CRS.from_user_input(source), CRS.from_user_input(target)
    x, y = _number(x, "x"), _number(y, "y")
    if source.is_geographic:
        lon, lat = position((x, y))
        if not -180 <= lon <= 180:
            raise ValueError("CRS longitude must lie between -180 and 180")
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
    if abs(lat) > WEB_MERCATOR_MAX_LATITUDE+1e-12:
        raise ValueError("latitude lies outside the conventional EPSG:3857 domain")
    return WEB_MERCATOR_RADIUS*radians(lon), WEB_MERCATOR_RADIUS*log(tan(pi/4+radians(lat)/2))


def transform_coordinates(coordinates, source="EPSG:4326", target="EPSG:3857"):
    """Transform a sequence of 2D/3D positions, preserving optional elevation."""
    result = []
    for point in coordinates:
        values = tuple(point)
        if len(values) not in (2, 3):
            raise ValueError("coordinates require two or three numbers")
        extra = (_number(values[2], "elevation"),) if len(values) == 3 else ()
        result.append(transform(values[0], values[1], source, target)+extra)
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

    def transform(self, x, y):
        return transform(x, y, self.source, self.target)
