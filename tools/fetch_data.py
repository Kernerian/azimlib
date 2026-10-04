"""Rebuild the offline Natural Earth bundle with Python's standard library.

Run explicitly as a maintainer: python tools/fetch_data.py --cache ../../work/natural-earth
The installed library never calls this script or makes network requests.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import urllib.request


COMMIT = "ca96624a56bd078437bca8184e78163e5039ad19"
BASE = f"https://raw.githubusercontent.com/nvkelso/natural-earth-vector/{COMMIT}/geojson"
LAYERS = {
    "countries": "ne_110m_admin_0_countries.geojson",
    "brazil": "ne_10m_admin_0_countries.geojson",
    "states": "ne_10m_admin_1_states_provinces.geojson",
    "rivers": "ne_50m_rivers_lake_centerlines.geojson",
    "lakes": "ne_50m_lakes.geojson",
    "coastlines": "ne_50m_coastline.geojson",
}
KEEP = {
    "name", "name_en", "name_pt", "name_long", "admin", "sovereignt",
    "iso_a2", "iso_a2_eh", "iso_a3", "iso_a3_eh", "adm0_a3",
    "iso_3166_2", "postal", "continent", "region_un", "subregion",
    "pop_est", "pop_year", "gdp_md", "gdp_year", "scalerank", "featurecla",
    "type", "type_en", "region", "ne_id", "rank",
}


def rounded(value):
    """Retain all vertices and ring closure; round angular precision to 1e-5°."""
    if isinstance(value, list):
        return [rounded(item) for item in value]
    if isinstance(value, float):
        return round(value, 5)
    return value


def normalize(feature):
    properties = {key.lower(): value for key, value in feature["properties"].items()}
    properties = {key: value for key, value in properties.items() if key in KEEP and value is not None}
    geometry = feature["geometry"]
    result = {
        "type": "Feature",
        "properties": properties,
        "geometry": {"type": geometry["type"], "coordinates": rounded(geometry["coordinates"])},
    }
    identifier = properties.get("iso_3166_2") or properties.get("adm0_a3") or properties.get("ne_id")
    if identifier is not None:
        result["id"] = identifier
    return result


def build(output: Path, cache: Path):
    output.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": "Natural Earth",
        "source_repository": "https://github.com/nvkelso/natural-earth-vector",
        "source_commit": COMMIT,
        "license": "Public domain",
        "license_url": "https://www.naturalearthdata.com/about/terms-of-use/",
        "attribution": "Made with Natural Earth.",
        "coordinate_system": "WGS 84 longitude, latitude (degrees)",
        "processing": "Properties normalized to lower case and selected; all vertices retained, coordinates rounded to 5 decimal places; empty geometries omitted; Brazil-only filters for states and detailed national boundary. Deterministic gzip (mtime=0).",
        "layers": {},
    }
    for name, filename in LAYERS.items():
        url = f"{BASE}/{filename}"
        cached = cache / f"{COMMIT}-{filename}"
        if not cached.exists():
            print(f"Downloading {filename}", flush=True)
            request = urllib.request.Request(url, headers={"User-Agent": "azimlib-data-builder/0.1"})
            with urllib.request.urlopen(request, timeout=180) as response:
                cached.write_bytes(response.read())
        raw = cached.read_bytes()
        original = json.loads(raw)
        features = original["features"]
        if name in ("brazil", "states"):
            features = [feature for feature in features if (feature["properties"].get("ADM0_A3") or feature["properties"].get("adm0_a3")) == "BRA"]
        empty_count = sum(not feature.get("geometry") or not feature["geometry"].get("coordinates") for feature in features)
        features = [feature for feature in features if feature.get("geometry") and feature["geometry"].get("coordinates")]
        payload = {
            "type": "FeatureCollection",
            "name": name,
            "features": [normalize(feature) for feature in features],
        }
        packed = gzip.compress(json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"), mtime=0)
        destination = output / f"{name}.geojson.gz"
        destination.write_bytes(packed)
        manifest["layers"][name] = {
            "filename": destination.name,
            "source_url": url,
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "sha256": hashlib.sha256(packed).hexdigest(),
            "features": len(features),
            "empty_geometries_omitted": empty_count,
            "scale": "1:" + ("110,000,000" if name == "countries" else "10,000,000" if name in ("states", "brazil") else "50,000,000"),
            "coverage": "Brazil" if name in ("brazil", "states") else "World",
        }
        print(f"{name}: {len(features)} features, {len(packed):,} compressed bytes", flush=True)
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "src" / "azimlib" / "data")
    parser.add_argument("--cache", type=Path, required=True, help="Intermediate upstream download directory")
    arguments = parser.parse_args()
    build(arguments.output, arguments.cache)
