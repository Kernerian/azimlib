# Datum grids — 0.4 development

This guide covers **3.05–3.08**, complementing the [CRS and Helmert contracts](crs-0.4.md).
The published stable version remains 0.3.0. Readers, interpolation and operations
are independently implemented in Python; no GIS engine or third-party solver is
used. Data and code have separate licenses. No model downloads on import/transform.

## Selected format coverage

| Format | Supported | Explicit limits |
| --- | --- | --- |
| NTv2 GSB | Either endian; 11 overview and 11 subgrid records; SECONDS; float32 shifts/accuracy; nested subgrids | No NTv1, arbitrary header extensions, ASCII GSA, alternate numeric layouts or overlapping sibling interiors |
| NOAA GTX | Big-endian four float64 coordinates/increments, two int32 dimensions, float32 node offsets | Binary 2009+ layout; positive increments; at least two nodes per axis; no old float64-node/ASCII variant |

`read_ntv2(path_or_bytes)` / `read_gtx(path_or_bytes)` return immutable `ShiftGrid`.
Defaults: **128 MiB input, 16 million nodes, 4096 NTv2 subgrids**. Path reads are
chunked; values remain packed bytes, rather than millions of Python objects.
`tiles`, `metadata`, `sha256` and `units` are inspectable. Metadata includes the
NTv2 abbreviated endpoints and ellipsoid axes. It does not identify an EPSG
operation automatically. Unsupported/corrupt layouts and resource violations fail.

Public input is canonical **longitude/latitude**, degrees east/north. Equivalent
longitudes are resolved only inside the actual tile, including a dateline tile.
NTv2 file longitude and shift signs are west-positive; `sample(lon,lat)` returns
**(east shift, north shift), arcseconds**. GTX returns **(offset,), metres** in the
selected vertical model; GTX files with millimetres/arcseconds are not vertical
metre models and must not be registered as such.

Interpolation is **bilinear**, with float64 arithmetic over unchanged float32
nodes. Exact nodes and all four outer edges work. Only positive-weight missing
nodes invalidate a sample. NaN/infinity are missing; GTX's default sentinel is
the float32 representation of `-88.8888`. Explicit `nodata=` replaces the sentinel
list, including `()` for no numeric sentinel. The LINZ preset additionally declares
`-9999`. Missing values raise `GridNoDataError`, outside coverage raises
`GridCoverageError`; there is no extrapolation, nearest-node fill or silent
renormalization. GTX storage does not imply the NOAA service's biquadratic models.

The deepest supported NTv2 subgrid wins. A missing fine-grid value **does not**
fall back to its parent. Shared sibling edges use lexical tile-name order,
independent of file order; different values may produce a genuine discontinuity.
Siblings with overlapping interiors, missing/cyclic parents or children outside
their parent fail. `accuracy(lon,lat)` preserves/interpolates NTv2 longitude and
latitude accuracy fields in arcseconds, separately from shifts. Unknown accuracy
raises; these fields are not a new guarantee of survey accuracy.

## Explicit operations, heights and epochs

```python
import azimlib as azl

catalog = azl.DatasetCatalog("local-horizontal/catalog.json")
horizontal = catalog.grid_operation(
    "linz-nzgd1949-nzgd2000", version="20200110"
)
point = horizontal.transform(173.0, -41.0, 100.0)
restored = horizontal.inverse().transform(*point)

vertical = azl.DatasetCatalog("local-vertical/catalog.json").grid_operation(
    "linz-nzgeoid2016", version="20200110"
)
gravity_height = vertical.transform(*point)
pipeline = azl.CoordinatePipeline((horizontal, vertical))
assert pipeline.source == horizontal.source
```

`GridOperation(source,target,grid,kind,factor=1,valid_epochs=None)` requires exact
geographic `CoordinateFrame` endpoints. NTv2 horizontal operations preserve the
height component; they are **not a 3D datum-height transformation**. Ellipsoid axes
must match the file within its published millimetre rounding and prime meridians
must be Greenwich. Full realization names are supplied explicitly by the caller
or reviewed catalog, never inferred solely from abbreviated NTv2 labels.

Vertical GTX operations require the same horizontal frame/datum and different
`height_reference` identities. `target_h = source_h + factor*offset`, factor ±1.
For geoid separation N, **H = h − N**. NZVD2016 is normal-orthometric, not an
ellipsoidal height. A gravity-related frame cannot be converted straight to XYZ:
an explicit vertical operation must first recover ellipsoidal height.

The horizontal inverse iterates the **actual forward interpolant**, including
shifted boundary coordinates, and checks the forward residual. It rejects
non-convergence or multiple solutions, rather than returning a negated shift or
last iterate. The vertical inverse uses the same horizontal location and opposite
offset sign. `CoordinatePipeline.inverse()` reverses steps and their inverses.

`valid_epochs` requires an explicit in-range `epoch=` in both directions. Static
grid files contain no velocity and do not acquire one from a date. Reviewed dynamic
Helmert steps can be composed with static horizontal/vertical grids, using the
same explicit epoch throughout, with exact intermediate frame identities. No
earthquake patches, plate model, date propagation, full NZGD2000 semi-dynamic
correction or present-day realization is inferred by these static presets.

`OperationSet({name: operation_or_pipeline})` selects exact endpoints at the
supplied coordinate/epoch. Outside-coverage grids can be excluded; NoData, epoch
or model errors are not treated as a reason to substitute another model. Several
applicable choices require explicit `name=`. There is no implicit approximate
fallback, accuracy ranking, network search or undeclared datum bridge.

## Official optional models and provenance

The [pinned model manifest](grid-models-0.4.json) describes two LINZ models from
`proj-datumgrid-nz` **20200110**, commit
`62ff69da8713f0167d319d0263f1657ac380f273`. This is the publisher's data repository,
not incorporation of PROJ code. The publisher documents the 20200110 update as a
numerical-resolution correction to its GTX distribution.

| Model | Payload | Direction | License |
| --- | --- | --- | --- |
| NZGD1949 → NZGD2000 | `nzgd2kgrid0005.gsb`, 318464 bytes | Horizontal east/north shifts; International 1924 → GRS80 | CC BY 4.0, LINZ |
| NZGeoid2016 | `nzgeoid2016.gtx`, 10093244 bytes | NZGD2000 ellipsoidal → NZVD2016 normal-orthometric, subtract N | CC BY 4.0, LINZ |

These payloads are **not bundled** in wheel/sdist. Metadata, the original source
URLs/versions/hashes, a complete license copy and attribution instructions are
bundled. Downloaded data retain LINZ attribution, original publisher notice and
CC BY 4.0. Redistribution must retain attribution/license links and disclose
modifications; no endorsement is implied. Azimlib's BSD license covers its code,
not exclusive ownership of LINZ data. [Third-party boundaries](../THIRD_PARTY_LICENSES.md).

Acquisition is a separate explicit source-checkout tool:

```sh
python tools/acquire_datum_grid.py --model linz-nzgd1949-nzgd2000 --output local-horizontal
python tools/acquire_datum_grid.py --model linz-nzgeoid2016 --output local-vertical
```

Only new destinations are accepted. HTTPS source URLs are pinned to the reviewed
upstream commit. Payload size, all SHA-256 hashes, original notice and complete
license are checked before an atomic catalog delivery. Default download ceiling
is 128 MiB, total generated storage ceiling **20 GB**, free-space reserve **15 GB**;
budgets can be made smaller. On failure temporary data are removed; an incomplete
catalog is never delivered. Runtime `DatasetCatalog` performs no acquisition.
It hashes the exact consumed data and notices before decoding or creating an
operation, checks source registration/units/interpolation/frame profiles, and
fails on a missing model or grid. A third-party catalog still needs external
provenance review; self-declared hashes alone do not certify an authority.

## Raster, viewport and exports

`GeoRaster(...,height_frame=source_frame)` can explicitly identify scalar height
values. `vertical.transform_raster(raster,epoch=...)` corrects heights at pixel
centres, preserves existing missing pixels, affine and horizontal CRS, and returns
the target height reference. Missing grid corrections abort; old heights are never
silently mixed with corrected heights. The horizontal frame must agree with the
raster's supported CRS; unsupported datum/CRS pairs require a separately verified
registration/warp and fail. `resample()` preserves the height frame; changing
horizontal CRS without an explicit frame operation is rejected.

This is **vertical scalar-raster integration**, not automatic horizontal grid
warping, curvilinear raster support or writing vertical CRS GeoTIFF keys. The own
mesh Artist, viewport, colorbar, PNG and SVG operate normally on corrected data.
Optional components remain optional; `savefig()` contains no viewer UI.

## Independent validation and reproduction

`tests/test_datum_grids.py` covers analytic bilinear surfaces, primary NOAA header/
sentinel numeric facts, both NTv2 endians, sign/order/accuracy, fine-grid NoData,
hierarchy and boundary discontinuities, resource limits, converged/ambiguous/
non-convergent inverses, epochs, explicit selection, catalog integrity/license
failures, acquisition cleanup, raster metadata and PNG/SVG integration.

For real data, expected numbers come from **separate primary published formats**:
LINZ's original NTv2 ASCII grid and the authoritative NZGeoid2016 Sideris grid.
`tools/validate_datum_grids.py` pins their SHA-256, consumes/hashes the complete
reference files with bounded memory, compares all 19881 horizontal nodes and 100
off-node cells, and samples 651 vertical nodes and 100 off-node cells. Expected
off-node values use Decimal arithmetic on the published decimal numbers, not the
Azimlib decoder. Tolerances are **1e-6 arcsec** horizontal and **0.00011 m** vertical
(source rounding plus binary quantization), separate from physical model accuracy.
The test also verifies 100 real-grid roundtrips in both directions.

```sh
python tools/validate_datum_grids.py --horizontal-catalog local-horizontal/catalog.json --vertical-catalog local-vertical/catalog.json --ntv2-ascii references/nzgd2kgrid9911.asc --geoid-sideris references/New_Zealand_Quasigeoid_2016.sid --output validation.json
```

References are extracted explicitly from the publisher ZIPs listed in the tool;
no external code is downloaded or used. Data remain optional/outside archives.
The online converter was inaccessible in the validation environment (HTTP 403);
no live converter comparison is claimed. Numerical cross-format agreement proves
reader/interpolation correctness at the checked values, **not field accuracy**.
See [recorded local validation](grid-validation-0.4.json).

Primary references:

- [LINZ grid data, license and version](https://github.com/linz/proj-datumgrid-nz/tree/62ff69da8713f0167d319d0263f1657ac380f273).
- [LINZ original horizontal distortion grid](https://www.linz.govt.nz/products-services/geodetic/geodetic-software-and-downloads/horizontal-distortion-grids).
- [LINZ authoritative NZGeoid2016](https://www.linz.govt.nz/guidance/geodetic-system/coordinate-systems-used-new-zealand/vertical-datums/gravity-and-geoid/new-zealand-quasigeoid-2016-nzgeoid2016).
- [NOAA GTX layout and null values](https://www.vdatum.noaa.gov/docs/gtx_info.html).
- [NTv2 format description and original Canadian specification link](https://github.com/Esri/ntv2-file-routines#ntv2-file-formats) (format documentation only; no implementation copied).

No standard document, source implementation or binary data file is vendored in
the library. This selected coverage does not claim arbitrary CRS/grids, complete
EPSG database coverage, WKT/PROJJSON parsing, all geoid interpolation models or
automatic deformation-model selection.
