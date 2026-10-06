"""Strict, dependency-free tabular point interchange in longitude/latitude."""
from __future__ import annotations

import csv
import io
from collections.abc import Mapping
from os import PathLike
from pathlib import Path

from .geometry import Feature, FeatureCollection, Geometry


def read_csv(source, *, longitude="lon", latitude="lat", id_column=None,
             converters=None, delimiter=",", encoding="utf-8-sig"):
    """Read a local CSV into immutable Point features, without guessing a CRS.

    Accept a path, multiline CSV string, bytes or readable stream. Caller
    streams remain open. Coordinates must be finite degrees in lon/lat
    order; latitude must be in [-90, 90]. Longitude may be unwrapped.
    Coordinate properties become floats; other columns remain strings
    unless an explicit converter is provided. Converter results must be
    valid JSON properties. Optional IDs come from a named column.
    Invalid rows raise with a physical line number; no rows are silently
    dropped or returned as a partial collection. No network access occurs.
    """
    for name, value in (("longitude", longitude), ("latitude", latitude)):
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name} must be a nonempty column name")
    if longitude == latitude:
        raise ValueError("longitude and latitude require distinct columns")
    if id_column is not None and (not isinstance(id_column, str) or not id_column):
        raise ValueError("id_column must be a nonempty column name or None")
    if not isinstance(delimiter, str) or len(delimiter) != 1 or delimiter in '\r\n':
        raise ValueError("delimiter must be one character other than a newline")
    if converters is None:
        converters = {}
    if not isinstance(converters, Mapping) or any(not isinstance(k, str) or not callable(v)
                                                for k, v in converters.items()):
        raise TypeError("converters must map column names to callables")
    converters = dict(converters)
    if {longitude, latitude} & converters.keys():
        raise ValueError("coordinate columns already have numeric conversion")
    if isinstance(source, PathLike):
        text = Path(source).read_text(encoding=encoding)
    elif isinstance(source, str):
        text = source if '\n' in source or '\r' in source else Path(source).read_text(encoding=encoding)
    elif isinstance(source, bytes):
        text = source.decode(encoding)
    elif hasattr(source, 'read'):
        text = source.read()
        if isinstance(text, bytes):
            text = text.decode(encoding)
    else:
        raise TypeError("source must be a CSV path, text, bytes or readable stream")
    if not isinstance(text, str):
        raise TypeError("CSV streams must yield text or bytes")
    reader = csv.reader(io.StringIO(text.lstrip('\ufeff'), newline=''), delimiter=delimiter, strict=True)
    try:
        headers = next(reader, None)
        if not headers or any(not name for name in headers) or len(set(headers)) != len(headers):
            raise ValueError("CSV requires nonempty, unique column names")
        required = {longitude, latitude, *converters}
        if id_column is not None:
            required.add(id_column)
        if not required <= set(headers):
            raise ValueError("CSV is missing required columns: " + ', '.join(sorted(required - set(headers))))
        features = []
        for row in reader:
            if not row:  # An empty physical line is not a record.
                continue
            line = reader.line_num
            if len(row) != len(headers):
                raise ValueError(f"CSV line {line}: field count differs from header")
            properties = dict(zip(headers, row))
            try:
                lon, lat = float(properties[longitude]), float(properties[latitude])
                geometry = Geometry("Point", (lon, lat))
                properties[longitude], properties[latitude] = lon, lat
                for name, converter in converters.items():
                    properties[name] = converter(properties[name])
                feature = Feature(geometry, properties,
                                  None if id_column is None else properties[id_column])
            except (ValueError, TypeError, OverflowError) as exc:
                raise ValueError(f"CSV line {line}: invalid coordinates, properties or ID") from exc
            features.append(feature)
    except csv.Error as exc:
        raise ValueError(f"CSV line {reader.line_num}: malformed record") from exc
    return FeatureCollection(tuple(features))
