"""Small, real geographic datasets bundled for completely offline maps.

All datasets are Natural Earth public-domain data in WGS 84 longitude/latitude.
The API returns independent GeoJSON dictionaries, so modifying a result cannot
alter a later load. No third-party geographic library or network is used.
"""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import gzip
from importlib.resources import files
import json
import unicodedata

__all__ = ["load", "country", "state", "catalog", "provenance"]

_LAYERS = frozenset({"countries", "states", "rivers", "lakes", "coastlines"})
_ALIASES = {"world": "countries", "land": "countries", "coastline": "coastlines", "coasts": "coastlines"}
_WORLD = frozenset({"world", "mundo", "global"})
_COUNTRY_FIELDS = ("name", "name_en", "name_pt", "name_long", "admin", "iso_a2", "iso_a2_eh", "iso_a3", "iso_a3_eh", "adm0_a3")


def _key(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Supply a nonempty dataset or country name.")
    return "".join(character for character in unicodedata.normalize("NFKD", value.casefold()) if character.isalnum())


@lru_cache(maxsize=6)
def _read(name: str) -> dict:
    resource = files("azimlib").joinpath("data", f"{name}.geojson.gz")
    return json.loads(gzip.decompress(resource.read_bytes()))


@lru_cache(maxsize=1)
def _country_index() -> dict:
    result = {}
    for feature in _read("countries")["features"]:
        properties = feature["properties"]
        for field in _COUNTRY_FIELDS:
            value = properties.get(field)
            if isinstance(value, str) and value and value != "-99":
                result[_key(value)] = feature
    for alias in ("united states", "us", "usa", "america"):
        result[_key(alias)] = result["usa"]
    for alias in ("uk", "great britain"):
        result[_key(alias)] = result["gbr"]
    return result


def _country_data(name: str) -> dict:
    key = _key(name)
    if key in _WORLD:
        return deepcopy(_read("countries"))
    try:
        feature = _country_index()[key]
    except KeyError:
        raise ValueError(
            f"Country {name!r} is not in the bundled Natural Earth 1:110m dataset. "
            "Use an English/Portuguese name or ISO code, or load your own GeoJSON."
        ) from None
    if feature["properties"].get("adm0_a3") == "BRA":
        return deepcopy(_read("brazil"))
    return {"type": "FeatureCollection", "name": feature["properties"]["name"], "features": [deepcopy(feature)]}


def country(name: str) -> dict:
    """Return a country FeatureCollection by English/Portuguese name or ISO code.

    ``country('world')`` returns all 177 bundled country features at 1:110m.
    Brazil uses a more detailed 1:10m boundary, matching the scale of the
    bundled states. Names follow Natural Earth; small territories absent from
    the 1:110m dataset are unavailable. Boundaries are general-purpose data,
    not an authoritative legal statement.
    """
    return _country_data(name)


def state(name: str) -> dict:
    """Return one bundled Brazilian state by name, postal code or ISO code."""
    key=_key(name)
    for feature in _read('states')['features']:
        props=feature['properties']
        aliases=[props.get(field,'') for field in ('name','name_en','name_pt','postal','iso_3166_2')]
        if key in {_key(value) for value in aliases if value}:
            return {'type':'FeatureCollection','name':props['name'],'features':[deepcopy(feature)]}
    raise ValueError(f'Unknown Brazilian state {name!r}; use e.g. SP, BR-SP or São Paulo')


def _positions(coordinates):
    if coordinates and isinstance(coordinates[0], (float, int)):
        yield coordinates
    else:
        for part in coordinates:
            yield from _positions(part)


def _bounds(feature: dict) -> tuple[float, float, float, float]:
    coordinates = list(_positions(feature["geometry"]["coordinates"]))
    return (
        min(point[0] for point in coordinates), min(point[1] for point in coordinates),
        max(point[0] for point in coordinates), max(point[1] for point in coordinates),
    )


def _intersects(first, second):
    return first[0] <= second[2] and first[2] >= second[0] and first[1] <= second[3] and first[3] >= second[1]


def load(name: str, country: str | None = None) -> dict:
    """Load ``countries``, ``states``, ``rivers``, ``lakes``, or ``coastlines``.

    ``states`` provides Brazil's 26 states and Federal District; other
    countries require caller-supplied data. For physical layers, ``country``
    selects features intersecting the country's rectangular geographic bounds;
    it does not clip rivers or coastlines to political borders. The map's
    viewport performs visual clipping. Data are generalized, not complete
    inventories of local features.
    """
    normalized = _key(name)
    normalized = _ALIASES.get(normalized, normalized)
    if normalized not in _LAYERS:
        raise ValueError(f"Dataset {name!r} is not bundled. Available: {', '.join(sorted(_LAYERS))}. Use your own GeoJSON for other layers.")
    if normalized == "states":
        if country is not None:
            selected = _country_data(country)
            if len(selected["features"]) != 1 or selected["features"][0]["properties"].get("adm0_a3") != "BRA":
                raise ValueError("Bundled states cover Brazil only (26 states and the Federal District). Load your own GeoJSON for other countries.")
        return deepcopy(_read("states"))
    if normalized == "countries" and country is not None:
        return _country_data(country)
    payload = _read(normalized)
    if country is None or _key(country) in _WORLD:
        return deepcopy(payload)
    selected = _country_data(country)
    extent = _bounds(selected["features"][0])
    filtered = [feature for feature in payload["features"] if _intersects(_bounds(feature), extent)]
    return {"type": "FeatureCollection", "name": payload["name"], "features": deepcopy(filtered)}


def provenance() -> dict:
    """Return source URLs, pinned commit, license, processing, and SHA-256 hashes."""
    return json.loads(files("azimlib").joinpath("data", "manifest.json").read_text(encoding="utf-8"))


def catalog() -> dict:
    """Return a new mapping of offline layer names to coverage and provenance."""
    result = provenance()["layers"]
    for layer in result.values():
        layer["available"] = True
        layer["offline"] = True
    return result
