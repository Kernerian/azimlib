# Own topology and overlay — 0.4 development

This guide describes the source checkout, **not the published 0.3.0 package**.
The implementation uses Azimlib's own noding, predicates, shared-edge graph,
classifiers and Boolean boundary assembly. No Shapely/GEOS, S2, pyproj or other
geospatial implementation is imported or vendored. The existing regional
`validate_geometry()` API retains its earlier contract; new operations use
`validate_topology()` and do not silently change old checks.

## Two explicit geometric domains

| Contract | Planar | Spherical |
| --- | --- | --- |
| Input | Immutable `Geometry`, including mixed collections with valid nonoverlapping polygon interiors | Explicit `SphericalRegion` |
| Edges | Straight segments in the supplied coordinate plane | Minor great-circle arcs on a unit sphere |
| Longitude | Used literally; no seam unwrap or guessed CRS | Periodic; no map projection or seam cut used for topology |
| Interiors | Shell minus holes, multipart union; winding normalized in output | Filled side left of oriented boundaries, plus explicit reference point/membership |
| Precision | Exact rational predicates and intersection constructions for binary-float inputs | Float64 spherical construction with explicit angular tolerance and fail-closed ambiguity checks |
| Output | Polygon/line/point or mixed GeometryCollection, plus shared graph | Regularized region, possibly disconnected, larger than a hemisphere, empty or full |
| Area | Squared coordinate units | Steradians times chosen spherical radius squared; not ellipsoidal area |

Geometry positions retain the library's longitude/latitude primitive constraints
(finite 2D coordinates, latitude within ±90°). These operations are not an
arbitrary projected-coordinate container or an implicit CRS transformation.
No height is invented or interpolated. Three-dimensional input is rejected.

GeoJSON's coordinate-space segment semantics are distinct from the explicit
great-circle interpretation above. `SphericalRegion.from_geometry()` is an
intentional reinterpretation; reading a GeoJSON file does not do this implicitly.

## Planar set operations

```python
import azimlib as azl

a = azl.Geometry("Polygon", [[(0, 0), (3, 0), (3, 3), (0, 3), (0, 0)]])
b = azl.Geometry("Polygon", [[(1, 1), (4, 1), (4, 4), (1, 4), (1, 1)]])

result = azl.intersection(a, b)  # also union, difference, symmetric_difference
assert result.area() == 4
fig, ax = azl.subplots()
ax.geojson(result.geometry, facecolor="#77a9bb", edgecolor="black")
fig.savefig("intersection.svg")
```

`overlay(a, b, operation=..., domain="planar")` returns `OverlayResult`:

- `geometry`, `is_empty`, `area()`;
- immutable `topology.nodes`, `topology.edges`, `topology.shared_edges`;
- `shared_boundaries()` for edges coincident in both operands;
- `operation` and `domain`.

Each graph edge carries all source tuples
`(operand, kind, part, ring, segment, direction)`. Operand 0 is left, 1 is right;
direction records orientation relative to the shared edge. Crossings, endpoints,
partial overlaps and point inputs split the same graph. Planar graph nodes retain
`Fraction` values; spherical nodes are 3D unit vectors. A graph is not GeoJSON.

Coincident polygon edges dissolve as appropriate. Intersection of touching areas
can return a line or point, not a fabricated area. Polygon difference and XOR use
closed regularized area semantics: subtracting a line does not cut a zero-width
slit. Line/area clipping and line/line operations retain surviving atomic segments;
these need not be merged into one maximal LineString. Null features are skipped
by spatial selection/clip, without changing the original collection.

Inputs must have valid topology. Self crossings, repeated consecutive vertices,
overlapping multipart polygon interiors, nested/outside holes and touching hole
boundaries are diagnosed. Ambiguous or invalid output topology raises an error
rather than silently exporting a guessed polygon. Distinct exact nodes that would
collapse in float64 GeoJSON conversion are rejected. Exact rational construction
does not imply unlimited precision in the final float64 exchange format.

## Global regions, complements, poles and antimeridian

```python
north = azl.SphericalRegion.hemisphere(0, 90)
east = azl.SphericalRegion.hemisphere(0, 0)
quarter = azl.intersection(north, east, domain="spherical")
assert abs(quarter.area(radius=1) - 3.141592653589793) < 1e-10

outside_quarter = quarter.geometry.complement()
full = azl.union(quarter.geometry, outside_quarter, domain="spherical")
assert full.geometry.is_full

fig, ax = azl.subplots(projection="orthographic")
fill, boundary = ax.region(outside_quarter, fill_step=3, boundary_step=1)
boundary.set_visible(False)
fig.savefig("global.svg")
```

`SphericalRegion.from_geometry(polygon, interior="small")` explicitly chooses
each shell's smaller spherical interior and smaller excluded holes. With
`interior="left"`, shell orientation chooses its left interior, including areas
larger than a hemisphere. Holes remain smaller excluded regions. Crossings,
overlapping multipart interiors and invalid holes are rejected; reversing a
shell is not treated as a cosmetic change under the left-interior contract.

Alternatively construct `SphericalRegion(rings, reference=(lon, lat),
reference_inside=True/False)`. Boundaries must have filled side left and agree
with that reference. Empty boundaries plus a true membership represent the full
sphere. Classification follows crossing parity from the stored reference,
retrying deterministic intermediate rays when a direct ray meets a vertex,
coincident arc or antipodal direction. No unwrapping into a regional plane is used.

`location(lon, lat)` returns `inside`, `boundary` or `outside`; `covers()` includes
the boundary. `complement()`, `is_empty`, `is_full`, `area(radius=...)` and
`boundary(step=...)` are available. Default area radius is Azimlib's mean Earth
spherical radius; it is not an ellipsoidal/geodesic datum computation.

The default angular tolerance is `1e-10` radians, configurable from `1e-13` to
`1e-6`. This is a numerical topology tolerance, not a survey accuracy statement.
Arcs shorter than 32 tolerances, near-antipodal endpoints, unresolved nearly
coincident great-circle planes, unsafe side probes and ambiguous boundary
assembly raise `TopologyPrecisionError`/`TopologyError`. Inputs are not silently
snapped to a coarse longitude grid. Nearby constructed intersections may share a
node within the stated angular tolerance; too-short resulting edges fail.

Spherical area Boolean output is regularized: zero-area line/point contacts are
not represented as filled regions. The shared input graph retains their edges
and source lineage. General spherical line/point set algebra and ellipsoidal
overlay are **not** claimed by this contract.

## Rendering and serialization are explicit

`ax.region()` adds two ordinary, editable Artists only when called. Filled area
is sampled at geographic pixel centres using `fill_step` degrees; it is an
explicit display approximation, not a claim of exact vector tessellation. The
boundary follows great-circle interpolation with `boundary_step` degrees.
Changing display resolution does not change the spherical Boolean result.
`max_cells=100000` bounds fill size; excessive requests fail before adding layers.
PNG and SVG use the existing independent renderers. No minimap/grid/legend is
added by the topology API.

`region.to_dict()` / `SphericalRegion.from_dict()` preserve rings, minor-arc
semantics, reference membership and tolerance in a versioned Azimlib format.
There is deliberately no implicit GeoJSON polygon conversion: GeoJSON cannot
carry this full-sphere/reference-interior contract. `boundary()` can be exported
as a GeoJSON MultiLineString with the requested interpolation step. Planar
results use ordinary `read_geojson()` / `write_geojson()` interchange.

## Features, urban layers and raster masks

```python
features = azl.read_geojson("blocks-and-streets.geojson")
selected = features.spatial_select(a)  # original Feature objects and order
clipped = features.clip(a)            # new geometry, same IDs and properties
ax.geojson(clipped)

paired = azl.overlay_features(features[0], features[1], "intersection")
# paired.properties['left'] / ['right'] contain the original IDs/properties.
# No same-named property is silently overwritten.

masked = raster.mask_region(a)
global_mask = raster.mask_region(north, domain="spherical")
```

Raster masks transform each pixel centre from its explicit supported CRS to
geographic lon/lat, then classify against the declared region. Existing NoData,
alpha, affine, CRS and height reference are preserved. `invert=True` keeps the
opposite side. This is centre sampling, not area-weighted coverage, resampling
or a warp. Readers' outputs, urban features and clipped geometries feed the same
existing layers/renderers; inputs remain immutable.

## Validation and opt-in repair

`validate_topology()` returns a `TopologyReport`; construction/overlay never
repairs inputs implicitly. `repair_geometry(method="normalize")` deduplicates
consecutive positions and normalizes shell/hole winding, then requires valid
planar output. It does not guess a fix for crossings or outside holes.

`method="even_odd"` explicitly rebuilds shell even-odd fill minus holes through
the noded arrangement. A bow-tie can become separate polygon parts; portions of
holes outside a shell contribute nothing under that chosen rule. `RepairResult`
contains the new geometry, `before`/`after` reports and every applied change or
semantic policy. This opt-in operation can change partitioning; preserve the
original geometry when that matters. No spherical or elevation repair is inferred.

## Resource limits and evidence

Overlay defaults are 20,000 input segments, 2,000,000 candidate pairs and 100,000
noded edges, configurable explicitly. A budget failure produces no partial
result. An immutable STR hierarchy conservatively prunes planar and spherical
arc envelopes before exact/local intersection tests. Side isolation and some
validation/classification work remain quadratic; this is **not** a claim of
planetary throughput. Caller-supplied limits do not make arbitrary degeneracies
or unlimited input sizes supported.

[Tests](../tests/test_overlay_040.py) use independently calculated rectangle
areas, exact rational crossing coordinates, regular-polygon area, hemisphere
lunes, a spherical octant and Boolean area/De Morgan identities. They cover
coincidence, holes, multipart regions, contacts, near-parallel planar lines,
large coordinate translations, invalid input, precision/resource failures,
polar caps, antimeridian regions, large complements/full sphere, serialization,
urban attributes, raster masks and editable PNG/SVG Artists. These are analytic
synthetic fixtures, not field measurements or a third-party GIS engine oracle.

Reproduce `tools/benchmark_topology.py --output topology-benchmark.json` and
`examples/topology_overlay.py --output topology-output` from the source checkout.
The benchmark records timing and traced Python peak allocations (excluding
interpreter/import/native RSS), platform, input size, candidate-pair counts and
runtime hashes. [Local validation snapshot](topology-validation-0.4.json).

Conceptual/format references, without incorporated implementations or text:

- [RFC 7946](https://www.rfc-editor.org/rfc/rfc7946), coordinate-space geometry,
  ring orientation and antimeridian exchange semantics.
- [Robust-predicate research](https://www.cs.cmu.edu/~quake/robust.html), numerical
  robustness problem. Azimlib's planar implementation uses Python `Fraction`,
  not copied/adapted expansion arithmetic or predicates.c.
- [Spherical geometry overview](https://s2geometry.io/about/overview.html),
  great-circle/left-interior concepts. No S2 source, bindings, fixtures or
  database are used. Reference parity, noding and Boolean assembly here are own.

No new third-party code/data is distributed for this subsystem. The gallery's
optional country background remains the existing attributed Natural Earth data.
The global example deliberately uses unlabeled graticules: the existing renderer
can place equivalent longitude labels together at an orthographic seam/pole.
That label-placement issue remains tracked for the final visual integration gate;
it is not evidence of a spherical topology error or fixed by this subsystem.
Planet-trial item **2.08 remains pending exclusively for the full real dump**;
these synthetic topology results do not satisfy that gate.
