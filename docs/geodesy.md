# Geographic core — 0.3.0 development

These APIs belong to `dev/0.3.0`; they are not in the published 0.2.0 package.
The implementation is Azimlib's own Python code. No PROJ, GeographicLib,
Matplotlib or other GIS engine is a runtime dependency or backend.

## Models, units and geodesics

```python
import azimlib as azl

solver = azl.Geodesic(azl.WGS84)
route = solver.inverse(-46.63, -23.55, -43.17, -22.90)
endpoint = solver.direct(-46.63, -23.55, route.azimuth1, route.distance)
print(route.distance, route.azimuth1, route.method)
```

`Ellipsoid(a, inverse_flattening, name)` is immutable; distances and axes are
metres. WGS84 and GRS80 constants are provided. `inverse_flattening=0` defines
a sphere; other supported models are oblate with inverse flattening >=150.
`Datum(name, ellipsoid, prime_meridian)` records static model metadata; it does
**not** perform epoch, prime-meridian, vertical datum, geoid or datum shifts.
CRS operations implement WGS84/Greenwich only. Custom Datum objects are not
registered as CRS automatically. `Unit.convert` requires matching length/angle
quantities; METRE, KILOMETRE, DEGREE and RADIAN are available.

Geodesic inputs use canonical longitude [-180,180], latitude [-90,90], azimuth
in degrees and nonnegative distance in metres. `azimuth2` is the **forward
continuation** at the destination, not a reverse bearing. `GeodesicResult`
includes distance, endpoint, azimuths, iterations and method. Zero-length and
coincident-pole cases are explicit; azimuth is nonunique at coincident/exact
antipodal endpoints. `.line(start,end,steps=...)` returns both original endpoints.

Direct and ordinary inverse equations follow Vincenty. Failed fixed-point
inverses use an independent multistart damped Newton shooting solve of the
direct equations, with 3D endpoint errors and shortest converged candidate
selection. There is **no spherical distance fallback**. Exhausted convergence
raises ArithmeticError; this bounded solver is not a proof of correctness for
every possible ellipsoid/input. `iterations` describes the selected solution,
not cumulative attempts. Near-antipodal azimuths are ill-conditioned.

`haversine`, `destination` and `great_circle` retain their existing spherical
contracts. `ax.route(points, ellipsoid=azl.WGS84)` explicitly selects ellipsoidal
sampling; omitting ellipsoid preserves spherical route behavior. All routes
remain 2D; no altitude/geoid interpolation or urban routing is implied.

## Explicit CRS and regional Transverse Mercator

```python
crs = azl.utm_crs(-46.63, -23.55)  # EPSG:32723, WGS84 zone 23 south
x, y = azl.transform(-46.63, -23.55, "EPSG:4326", crs)
lon, lat = azl.transform(x, y, crs, "EPSG:4326")
points = azl.read_geojson({"type": "Point", "coordinates": [x, y]}, crs=crs)
```

| CRS | Domain / order |
| --- | --- |
| EPSG:4326 | Longitude, latitude in degrees, WGS84/Greenwich |
| EPSG:3857 | Existing conventional square Web Mercator, spherical radius 6378137 m |
| EPSG:32601–32660 | WGS84 UTM north, easting/northing metres, latitude 0..84° |
| EPSG:32701–32760 | WGS84 UTM south, easting/northing metres, latitude -80..0° |

UTM uses k0=.9996, central meridian `zone*6-183`, false easting 500000 m and
false northing 10000000 m in the south. Zone selection includes Norway/Svalbard
exceptions; +180 selects zone60 and -180 zone1. Hemisphere mismatch, unsupported
codes and positions outside the bounded projection domain fail explicitly.
Accepted projected coordinates also require easting 0..1000000 and northing
0..10000000. Zone CRS selection is explicit: there is no autozone per vertex.
`CRS.datum`, `.ellipsoid`, `.zone`, `.hemisphere`, `.units`, `.axis_order` expose
the contract; EPSG:4326 always uses longitude first in this library.

`TransverseMercator` uses its ellipsoid (the inherited spherical `radius`
parameter is not used), origin, scale and false offsets. Our Snyder series is
**regional**, latitude [-80,84], longitude within ±6° of the central meridian.
The inverse is refined against the same forward series. It is not exact/global
TM, a universal CRS database or survey-certified datum transformation.

GeoJSON/CSV accept `crs=` explicitly; CSV numeric source properties retain x/y
values while output geometry becomes WGS84. Default readers retain their old
geographic/unwrapped behavior. Shapefile/GeoTIFF also recognize these CRS codes.
`transform_coordinates` preserves optional third-coordinate values without
transforming vertical datum. UTM GeoRaster metadata is representable, but
plotting requires a curvilinear mesh and **raises** before adding an Artist;
only axis-aligned 4326/3857 rasters are currently drawn. No false separable UTM
raster transformation is performed.

## New spherical azimuthal projections

`projection="stereographic"` is conformal on the sphere; the antipode is
singular. `projection="azimuthal_equidistant"` preserves spherical distances
from its centre; the exact antipode has no unique projected direction and
returns None. Both have inverses, configurable centres/radius, pole-centred
views and registered short aliases `stereo`/`aeqd`. They do not silently claim
ellipsoidal accuracy. Use regional data/limits excluding their singularity;
polygon rendering raises when crossing unsupported singularities.

## Antimeridian limits and navigation

```python
fig, ax = azl.subplots()
ax.set_extent((170, -170, -15, 15))
ax.route([(175, 0), (-175, 5)], ellipsoid=azl.WGS84)
ax.pan(2, 0)
ax.zoom(2, center=(-175, 2))
fig.savefig("pacific.svg")
```

On equirectangular/Mercator axes, an explicit west>east canonical extent opts
into a continuous 360° longitude branch, recentering an immutable projection
copy at the first view midpoint. `get_extent()` returns increasing unwrapped
limits, e.g. `(170,190,-15,15)`. Pan, zoom, cursor inversion, shared x axes,
history/Home and SVG/PNG/HTML export use that branch. Navigation remains bounded
by the branch edges, not an endless world wrap. Ordinary extents retain their
old semantics. Shared crossing x axes must be cylindrical and use the same
branch. Other projections reject this crossing-extent shorthand.

`ax.fit_extent(data=None, margin=.05)` explicitly fits the smallest circular
longitude interval of point samples; omitted data uses geometry layers.
`longitude_bounds` is the reusable numeric helper. These point-sample fits do
not infer interiors of polygons covering most of Earth. Ordinary automatic
fitting still uses Cartesian geometry bounds and can be wide for seam data;
use explicit fit_extent for a local crossing map. `ax.zoom(center=...)` centres
the new window; viewer wheel zoom anchors the cursor, preserving existing rules.

Tk uses the Python projections/navigation. Portable HTML has real geographic
recomposition for cylindrical maps, including this branch; its other
projections still use the existing affine viewer and projected coordinate
fallback for TM. A live portable reprojection bridge is reserved to step 7.
Map legends, grids, scales, orientation and overview remain optional.

## Clipping and opt-in topology

Orthographic line clipping samples GeoJSON lon/lat edges (shorter longitude
branch, at most 2° by default), bisects horizon crossings and returns projected
metre paths. Polygons retain the existing spherical winding/limb stitching and
holes in an even-odd compound path. Each ring represents its smaller interior,
less than a hemisphere. Both algorithms are bounded rendering approximations;
they are not spherical overlay. Self-intersecting polygons, uncut polar rings,
antipodal polygon segments and interiors covering most of Earth remain outside
the documented cut. Zero-length lines/zero-area rings produce no paths.

`orientation` uses a float filter with exact rational determinant fallback.
`segment_intersection` distinguishes none/point/overlap, including endpoints
and zero-length edges. `ring_orientation`, `validate_ring` and
`validate_geometry` report closure, degeneracy, self-intersection, optional
winding, outside/touching holes, nested holes and multipolygon overlaps.
Reports are immutable; `.valid` and `.raise_if_invalid()` support validation.
This is opt-in regional **planar lon/lat topology** (seams are unwrapped), O(n²),
not global great-circle boundary validation or repair. Existing Geometry
construction remains permissive so legacy geographic datasets are preserved.

## Numeric evidence, provenance and reproduction

The [reference matrix](geodesy-reference-0.3.json) contains **579 calculated
cases**: 287 inverse, 100 direct, 40 TM, 120 UTM (all 60 zones/two hemispheres), 32
forward/inverse projection comparisons. Seed 3003 and oracle versions are recorded:
pyproj 3.8.0 and GeographicLib 2.1 were used only through black-box calls in an
isolated development environment. No oracle implementation or published test
dataset was read, copied or vendored; records are factual computed numbers.
Tests consume JSON and the own core, not those packages. Existing analytic,
clipping, differential-property, cache, reader and viewer tests also remain.

| Comparison | Tested tolerance |
| --- | --- |
| WGS84 inverse distance / endpoint closure | 1 mm |
| Direct lon/lat/azimuth | 2e-8° |
| Inverse azimuth, excluding nonunique poles/antipodes/coincidence | 1e-7° |
| UTM versus numeric oracle | 2 mm |
| Regional TM to ±6° | 2 cm |
| Regional TM/UTM inverse roundtrip | 1e-8° |
| Spherical projection forward | 1e-5 m |

These are observed test-domain gates, not universal error guarantees. Run
`python -m unittest discover -s tests -p test_geodesy.py` from a source checkout
with Azimlib installed. [Atlas](../examples/geodesy_atlas.py) and
[Pacific](../examples/pacific.py) produce PNG/SVG/HTML with our renderer,
synthetic routes and credited Natural Earth data. See the [batch record](release-progress-0.3.md)
for installed-suite and distribution evidence.

Implementation references (formulas/models, not external source-code ports):

- [Vincenty 1975, Survey Review — direct/inverse nested equations, NOAA copy](https://www.ngs.noaa.gov/PUBS_LIB/inverse.pdf).
- [Snyder 1987, USGS Professional Paper 1395 — TM, stereographic and azimuthal equidistant](https://pubs.usgs.gov/publication/pp1395).
- [NGA WGS84 defining parameters](https://earth-info.nga.mil/?action=wgs84&dir=wgs84).

The numerical references add no runtime dependency or vendored license payload.
Original implementation remains BSD 3-Clause; existing Natural Earth, DejaVu,
ColorBrewer and CC0 notices stay separate and unchanged.
