# CRS and explicit coordinate operations — 0.4 development

This guide describes the local 0.4 implementation, not the published 0.3 package.
The core is independently implemented with Python and published equations. No
Matplotlib, PROJ, pyproj, Cartopy or other GIS engine performs these operations.

## Coverage matrix and axis contract (3.01)

| Identity / representation | Coordinates accepted | Units | Domain and limits |
| --- | --- | --- | --- |
| `EPSG:4326`, numeric `4326`, existing WGS84/CRS84 aliases | longitude, latitude | degrees | Longitude [-180,180], latitude [-90,90]; WGS84 ensemble, no realization inferred |
| `EPSG:4979` | longitude, latitude, ellipsoidal height | degrees, degrees, metres | Explicit third value; height >= -10000 m |
| `EPSG:4978` | geocentric X,Y,Z | metres | Earth fixed, right handed; X Greenwich/equator, Y 90E, Z north; shallow/exterior geodetic domain |
| `EPSG:3857` | easting, northing | metres | Conventional Web Mercator square; latitude limit 85.0511287798066° |
| `EPSG:32601`–`32660`, `32701`–`32760` | easting, northing | metres | WGS84 UTM north/south; regional TM within 6° of meridian; hemisphere, lat [-80,84], E [0,1e6], N [0,1e7] |
| `CRS.to_dict()` / `CRS.from_dict()` | exact versioned `azimlib-crs` profile | per-axis metadata | Reject conflicting/partial/stale profile; an embedded identifier cannot override other fields |
| WKT, PROJ strings, PROJJSON, arbitrary authority definitions | **unsupported in this batch** | — | Reject explicitly; never extract an ID and ignore the definition |
| Other datums, realizations, vertical/geoid CRS, grids | explicit operations only where implemented | — | No automatic datum match, grid download or approximate fallback |

The **API remains longitude first**, including for 4326 and 4979. Inspect
`CRS.axis_order` for the actual API and `CRS.authority_axis_order` for authority
order (latitude first in those geographic definitions). `axis_units` describes
each axis; legacy `units` describes the horizontal axes. The old 2D-to-2D path
continues to pass through an optional elevation without shifting its datum.

`area_of_use` describes a nominal zone/geographic envelope; `definition.domain`
describes the implemented numerical domain, which can differ (UTM's solver allows
up to 6° from the meridian). Accuracy/epoch, area and dimensional requirements are
not silently inferred from a matching ellipsoid or a familiar EPSG identifier.
The geocentric origin/deep-interior coordinates have no supported geodetic inverse.
At the poles longitude is indeterminate; a roundtrip cannot prove its uniqueness.

## Versioned catalog and conversions (3.02–3.03)

`crs_catalog.version == 'azimlib-crs-1'` declares **124 implemented identities**:
4326, 4979, 4978, 3857 and 120 UTM zones. `codes(kind=...)`, `get(code)` and frozen
definitions expose axes, units, nominal area, numerical domain and primary sources.
This is Azimlib's own finite capability catalog, **not the EPSG Dataset**, an EPSG
database version or a claim to universal CRS coverage. Its original declaration
code/profile is BSD-3-Clause; identifier numbers are interoperability facts.
No authority database, registry prose, WKT records or GIS source code is vendored.

```python
import azimlib as azl

crs = azl.CRS(4979)
print(crs.axis_units, crs.authority_axis_order)
xyz = azl.Transformer.from_crs(4979, 4978)
point = xyz.transform(-46.63, -23.55, 760)  # explicit ellipsoidal height
lon, lat, height = xyz.inverse().transform(*point)

pipeline = azl.CoordinatePipeline((
    azl.Transformer(32723, 4978),
    azl.Transformer(4978, 4979),
))
```

`transform(x,y,source,target)` retains its 2D signature and rejects a 3D CRS.
Use `Transformer.transform(x,y,z)`, `CRS.transform_to(...,x,y,z)` or
`transform_coordinates` for actual 3D conversion. Never assume zero height.
GeoJSON with explicit `crs=4978` converts XYZ **before** geographic geometry
validation and preserves height; existing GeoJSON Artists then render it normally.
An affine raster only supplies two coordinates and rejects 3D CRS at construction;
2D raster reprojection/plotting contracts remain unchanged.

`LambertAzimuthalEqualArea` / `projection='laea'` adds spherical equal-area
azimuthal mapping and inverse, alongside the existing families. It reuses the
Projection/viewport/Artist/PNG/SVG interfaces and the portable cursor inverse.
Specify `central_longitude`, `central_latitude` and radius explicitly as needed.
The antipode is singular and excluded (inverse disk radius < 2R); no ellipsoidal
LAEA or EPSG:3035 is implied. Regional maps away from that singularity use the
existing clipping/path contract; this does not claim arbitrary global seam topology.

## Parametric datum operations and epochs (3.04)

Use `CoordinateFrame(name, kind, datum)` for an explicit realization identity,
with kind `geographic` (3D) or `geocentric`. `GeodeticConversion` requires the
**same name and Datum** on both representations. Different realizations cannot
be bridged just because their ellipsoids match. Datum prime meridians are degrees
east of Greenwich. Pipeline endpoints must match exactly, in the declared order.

`Helmert(source,target,parameters,convention,...)` supports the small-angle
7-parameter model, including a 3-translation operation by zeroing rotations and
scale. Parameter order is tx,ty,tz (metres), rx,ry,rz (arcseconds), scale difference
(ppm). Convention must be `position_vector` or `coordinate_frame`; the latter
reverses rotation signs. Rotation bounds are ±3600 arcsec, scale ±10000 ppm.
These are model input bounds, not an accuracy guarantee at the bounds.

With `rates` in the same units per year, `reference_epoch` and ordered
`valid_epochs` are mandatory. Supply `epoch=` on every call. Epoch numbers are
decimal Julian years with rates per 365.25-day year; this API does not convert UTC
dates, leap seconds or decimal calendar years. The same epoch reaches all pipeline
steps. Applying parameters at a date does **not** propagate a point between dates
or supply plate velocities, a deformation model or an official realization tie.

`valid_epochs` on a static operation also requires a valid `epoch=`. Optional
`area_of_use=(west,south,east,north)` is in source-datum geographic coordinates,
including west > east at the dateline. The inverse checks the recovered source
coordinate. No area means an unbounded Cartesian mathematical operation, not a
claim of worldwide geodetic accuracy. Parameters, datum identity and applicable
area/epoch/accuracy must come from a separately verified model.

```python
# Entirely synthetic parameters; this is not an official datum transformation.
source = azl.CoordinateFrame('synthetic source', 'geocentric')
target = azl.CoordinateFrame('synthetic target', 'geocentric')
operation = azl.Helmert(
    source, target, (1, 2, 3, 0, 0, 0, 0), 'position_vector',
    rates=(0.01, 0, 0, 0, 0, 0, 0),
    reference_epoch=2000.0, valid_epochs=(1990.0, 2030.0),
)
shifted = operation.transform(*point, epoch=2020.0)
restored = operation.inverse().transform(*shifted, epoch=2020.0)
```

The inverse solves the evaluated affine matrix exactly to floating-point precision;
it does not negate parameters and pretend that is the inverse. Input/derived
non-finite coordinates, unsupported conventions, mismatched frames, missing epochs
and out-of-validity coordinates fail. Operations can be explicitly composed with
`CoordinatePipeline`; there is no implicit bridge between a user frame and an
ensemble CRS in the finite catalog. Supply explicit, verified realization data.

## Validation, sources and remaining work

[Tests](../tests/test_crs_040.py) cover all catalog identities, profiles, analytic
XYZ axes, global 3D roundtrips including poles/shallow heights, legacy 2D/UTM,
readers and PNG/SVG, spherical LAEA cardinal values, inverse and equal-area
Jacobian, convention signs, dynamic rates, validity, dateline areas and matrix
inverses. The independent published Helmert numeric fixture uses the worked
WGS72→WGS84 example in **IOGP GN7-2, September 2019, printed p108**, tolerance
0.01 m matching the source's rounded values; it is not an official operation
installed in the catalog. Synthetic tests are explicitly labeled.

Primary equation/constant sources:

- [NGA WGS84 constants](https://earth-info.nga.mil/index.php?action=wgs84&dir=wgs84).
- [USGS Professional Paper 1395](https://pubs.usgs.gov/pp/1395/report.pdf) for existing regional TM/UTM and projection geometry.
- [IOGP GN7-2, September 2019](https://www.iogp.org/wp-content/uploads/2019/09/373-07-02.pdf), sections 3.3.2.1, 4.1.1, 4.2.3 and 4.2.5.

These are references for mathematical contracts and numeric facts; no external
implementation, text, PDF, database or generated binding was incorporated.
The 2019 edition is pinned for reproducibility, not represented as the latest.

**3.05–3.08** are implemented in the subsequent [datum-grid delivery](datum-grids.md):
selected own NTv2/GTX readers, strict interpolation/NoData, explicit horizontal and
vertical operations/inverses, optional audited LINZ models and independent primary
ASCII/Sideris validation. That guide states exact coverage and limits; this earlier
snapshot below remains evidence of 3.01–3.04 only, not the later runtime.

[Local numerical/test evidence and runtime hashes](crs-validation-0.4.json).
