"""GeoJSON interchange without any geospatial dependency."""
from __future__ import annotations

import json
from collections.abc import Mapping
from os import PathLike
from pathlib import Path

from .geometry import Feature, FeatureCollection, Geometry
from .tabular import read_csv
from .shapefile import read_shapefile, read_dbf, DBFRecord
from .xmlio import read_kml, read_osm
from .raster import GeoRaster, read_raster, read_geotiff, read_world_file
from .catalog import DatasetCatalog



def _object(value, context):
    if not isinstance(value, Mapping):
        raise ValueError(f"{context} must be a JSON object")
    if value.get("crs") is not None:
        raise ValueError("legacy GeoJSON CRS members are unsupported; transform to longitude/latitude first")
    return value


def _geometry(data):
    _object(data, "geometry")
    kind = data.get("type")
    if kind == "GeometryCollection":
        values = data.get("geometries")
        if not isinstance(values, (list, tuple)):
            raise ValueError("GeometryCollection requires a geometries array")
        return Geometry(kind, geometries=tuple(_geometry(g) for g in values))
    if "coordinates" not in data:
        raise ValueError("geometry requires coordinates")
    return Geometry(kind, data["coordinates"])


def _feature(data):
    _object(data, "feature")
    if data.get("type") != "Feature" or "geometry" not in data or "properties" not in data:
        raise ValueError("Feature requires type, geometry and properties members")
    geometry = _geometry(data["geometry"]) if data["geometry"] is not None else None
    return Feature(geometry, data["properties"], data.get("id"))


def read_geojson(source, *, crs=None):
    """Read a path, JSON string, mapping, text stream or __geo_interface__.

    Return FeatureCollection uniformly, wrapping standalone geometries and
    features. Validate before rendering. RFC 7946 longitude/latitude axis order
    is always used; legacy CRS declarations must be transformed explicitly.
    No network requests are made and foreign members are not retained.
    """
    if crs is not None:
        from .crs import transform_geojson
        source=transform_geojson(source,crs,"EPSG:4326")
    if isinstance(source, FeatureCollection):
        return source
    if isinstance(source, Feature):
        return FeatureCollection((source,))
    if isinstance(source, Geometry):
        return FeatureCollection((Feature(source),))
    if hasattr(source, "__geo_interface__"):
        source = source.__geo_interface__
    if isinstance(source, PathLike):
        source = json.loads(Path(source).read_text(encoding="utf-8-sig"))
    elif isinstance(source, str):
        if source.lstrip("\ufeff \t\r\n").startswith(("{", "[")):
            source = json.loads(source.lstrip("\ufeff"))
        else:
            source = json.loads(Path(source).read_text(encoding="utf-8-sig"))
    elif isinstance(source, bytes):
        source = json.loads(source.decode("utf-8-sig"))
    elif hasattr(source, "read"):
        source = json.load(source)
    _object(source, "GeoJSON")
    kind = source.get("type")
    if kind == "FeatureCollection":
        features = source.get("features")
        if not isinstance(features, (list, tuple)):
            raise ValueError("FeatureCollection requires a features array")
        return FeatureCollection(tuple(_feature(f) for f in features))
    if kind == "Feature":
        return FeatureCollection((_feature(source),))
    return FeatureCollection((Feature(_geometry(source)),))


def write_geojson(data, destination=None, *, indent=2):
    """Serialize native objects or validated input; optionally write a path/stream.

    The returned text is always available, whether or not a destination is set.
    """
    if isinstance(data, (Geometry, Feature, FeatureCollection)):
        payload = data.to_geojson()
    else:
        payload = read_geojson(data).to_geojson()
    text = json.dumps(payload, ensure_ascii=False, allow_nan=False, indent=indent)
    if destination is not None:
        if hasattr(destination, "write"):
            destination.write(text)
        else:
            Path(destination).write_text(text, encoding="utf-8")
    return text
