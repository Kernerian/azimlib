# Optional, local and versioned datasets

The development `DatasetCatalog` reads a local schema-1 JSON manifest. It does
not download, register data globally, or guess a version when multiple versions
exist. Dataset ID/version, format, CRS, source, copyright, attribution and license
are mandatory. `files` maps relative POSIX paths to SHA256, including the data,
license text and every referenced sidecar. Loading verifies the exact bytes
that the reader consumes. Symlinks resolving outside the catalog are rejected.
Hashes establish integrity relative to the manifest, not source authenticity.
Trust and preserve the manifest/provenance as well as its payloads.

```python
import azimlib as azl

catalog = azl.DatasetCatalog("optional-data/urban-sao-paulo-1.0/catalog.json")
catalog.verify()
features = catalog.load("urban-sao-paulo", version="1.0")
fig, ax = azl.subplots()
ax.geojson(features)
```

Supported dispatch formats are geojson, csv, shapefile, kml, osm, raster and
geotiff. Reader options are allowlisted; CSV converters cannot execute from JSON.
Vector KML/OSM/CSV/GeoJSON declare EPSG:4326. SHP/raster CRS follows the supported
reader contract. DBF/SHX/world_file sidecars must be explicitly declared and hashed.
`available()` returns detached metadata; editing it cannot alter loading behavior.

## São Paulo sample 1.0

The optional source directory `optional-data/urban-sao-paulo-1.0` contains a real
OpenStreetMap extraction around Praça Ramos de Azevedo, retrieved 2026-10-06:
3,876 referenced nodes, 464 complete ways (332 polygons and 132 lines), approximately
430 KiB. Selection rules, original response hash and retained tag allowlist are
recorded in provenance.json. No editor identities, timestamps, contacts or addresses
are distributed. No geometry or administrative boundary was invented. A complete
selected way may extend outside the display bbox; relations are not bundled.

The derivative database is **ODbL-1.0, © OpenStreetMap contributors**. Its README,
LICENSE.txt, provenance.json and catalog must stay with it. Original implementation
code remains BSD-3-Clause. The full license copy comes from the SPDX license-list
repository, with the official Open Data Commons license URL recorded. Database
redistribution/modification and produced maps must respect the ODbL obligations;
see [OSM copyright](https://www.openstreetmap.org/copyright/en) and
[the official ODbL](https://opendatacommons.org/licenses/odbl/1-0/).

This optional database is **excluded from wheel and sdist**, not a runtime asset.
Get the full optional directory from a source checkout and pass its catalog path
explicitly. The [real example](../examples/urban_real.py) exports PNG/SVG with
visible OpenStreetMap/ODbL attribution. `tools/audit_optional_data.py` verifies
file hashes, allowed metadata, license and reference completeness offline.
No downloading, publishing or dataset installation occurs as an import side effect.

```bash
python examples/urban_real.py --catalog optional-data/urban-sao-paulo-1.0/catalog.json --output gallery/urban-real
python tools/audit_optional_data.py
```

The sample is frozen and incomplete for navigation; it is a reproducible example,
not an up-to-date urban service. User-provided OSM tags need their own privacy
review. See [reader contracts](formats.md) and [third-party notices](../THIRD_PARTY_LICENSES.md).
