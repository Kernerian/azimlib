# 0.4 foundation: units, frames, time and rendering contracts

This guide describes the **local development foundation for 0.4**, not features
in the published 0.3.0 wheel. Runtime metadata stays 0.3.0 until version preparation;
no new package, tag or release is implied. [Progress](release-progress-0.4.md).
Names in `_frames`, `_timescales` and `_contracts` are internal and may evolve.
The inventory below records the initial foundation baseline. Later source
stages add [GPU rendering](gpu-0.4.md) and [regular volumes](volumes-0.4.md).
There is no public planetary `Body` API or ephemeris in this baseline.

## Existing API inventory and regression matrix

| Domain | Existing entry points | Coverage retained | Limits remain explicit |
| --- | --- | --- | --- |
| Plotting state | `import azimlib as azl`, `import azimlib.pyplot as plt`, `subplots`, `savefig`, `show` | `test_api`, `test_figure_state`, `test_foundation_040` | Familiar supported subset, no blanket compatibility |
| Map core | Geometry, CRS/Transformer, Geodesic, projections, extent/bearing | `test_core`, `test_geodesy`, `test_orientation` | WGS84 geographic/Web Mercator/UTM; no datum grids |
| Urban/data | GeoJSON/Shapefile/KML/OSM XML, GeoRaster, catalog, urban layers | `test_formats`, `test_urban`, `test_raster_bands` | Selected variants; no PBF/geocoder/route graph |
| Typography | Text/Annotation, symbols, expressions, collision priorities | `test_finishing`, `test_text_rotation`, `test_label_placement` | Internal limited expressions, not TeX or complex shaping |
| Terrain | TerrainAxes, Mesh, Camera, LocalFrame | `test_terrain3d`, `test_foundation_040` | Opaque regional CPU triangles, no volumes |
| Time/atlas | TemporalSeries, ScalarBinding, FuncAnimation, Atlas/PdfPages | `test_temporal`, `audit_atlas_pdf.py` | Bounded playback, no implicit astronomy |
| Output/interaction | PNG/SVG/PDF, Tk/Qt/browser, Artist lifecycle | `test_renderers`, `test_component_lifecycle`, `test_navigation` | Optional dependencies and owner-thread rules |

The full existing test suite remains a regression gate. New foundation tests
exercise the same root/pyplot plotting state, editable/removable Artists and
static exports. Components remain opt-in. `show()` does not change `savefig()`
into an export of toolbar or UI. Existing naive-date handling in TemporalSeries
(assume UTC) is preserved; the new astronomical Instant intentionally requires
timezone-aware input. A temporal `Frame` payload is not a spatial reference frame.

## Units, axes, precision and errors

`Unit` reuses the existing length/angle model and adds the `time` dimension.
`SECOND` and `DAY` are available at the root; one DAY is **86400 SI seconds**, not
a guarantee that every UTC calendar day has that many elapsed seconds.
Cross-dimension conversion raises ValueError. Inputs require finite real numbers
and reject booleans. No degrees/metres/pixels or milliseconds/seconds coercion
is inferred from coordinate magnitude.

| Space | Units and axes |
| --- | --- |
| Geographic | Longitude then geodetic latitude, degrees; ellipsoidal height, metres |
| Body fixed | Right-handed XYZ metres; X at Greenwich/equator, Y at 90E, Z north |
| Observer | Right-handed east/north/up metres; azimuth clockwise from north, elevation above tangent plane |
| Projected CRS | Existing explicit easting/northing and CRS units |
| Scene | Pixels, Y down, clockwise primitive rotation; physical styles converted once at DPI boundary |
| Camera | Existing homogeneous clip coordinates; display exaggeration is not physical height |

Geodetic conversion supports the existing oblate Ellipsoid model, canonical
lon/lat and heights >= -10000 m. The inverse rejects deep-interior coordinates
and fails explicitly on nonconvergence. Pole longitude is undefined physically;
roundtrip comparisons exclude longitude at the exact pole. Tested range extends
to 35786000 m height, with <=1e-10 degree and <=1e-7 m roundtrip errors. These are
tested numerical tolerances, not observational geodetic accuracy or a promise
for arbitrary floating-point magnitude/model. The fixed frame is an ideal static
reference ellipsoid, not an ITRF realization with tectonic motion or polar motion.

`linear_error_bound(J, bounds)` computes a conservative first-order local bound
using absolute coefficients, with explicit units inherited from the Jacobian.
It does not infer covariance, atmospheric error or a global nonlinear bound.
Invalid inputs/domain raise ValueError/TypeError; exhausted numeric convergence
raises ArithmeticError; unsupported renderer features raise NotImplementedError.
Failures propagate, rather than silently clamping, changing datum or substituting
another time scale. Callers must supply source/measurement uncertainties.

## Shared body, frame and observer implementation

Internal immutable Body reuses Ellipsoid; EARTH reuses the existing WGS84 object.
Coordinates carry their frame. RigidTransform validates a proper orthonormal
rotation, metre translation, body identity and exact intermediate-frame matching.
Positions translate; directions do not. Inverse/composition preserve frame tags.
Reflections, scales and cross-body/datum transformations are rejected. Inertial
frames/Earth rotation require later validated models; an arbitrary rotation is
not labelled an IERS celestial transformation.

Observer stores lon/lat, ellipsoidal height and an explicit angular horizon.
Its ENU transform gives geometric topocentric directions from body-fixed points;
direction mode handles a supplied far-field vector. `local_direction()` supports
manual azimuth/elevation; `above_horizon()` compares geometric elevation to the
stored horizon. Zenith/nadir azimuth returns None; coincident targets fail.
Geocentric and topocentric positions differ by the observer translation.
Apparent coordinates require refraction/aberration/light-time and are **not**
computed here. No geoid height is guessed from an unspecified building elevation.

Existing LocalFrame now uses this shared conversion/ENU transform, retaining
its zero-height horizontal rule, independent supplied elevation and 250 km limit.
The immutable origin transform is cached per LocalFrame, rather than rebuilt
for every vertex. This integrates the foundation into actual terrain rendering.

## Calendar and time corrections

Instant accepts aware datetime, normalizes to UTC and supports years 1972..9999
with the proleptic Gregorian calendar. Python datetime cannot represent `:60`;
leap-second labels and pre-1972 UTC drift are explicitly outside this contract.
There is no bundled leap/EOP table or automatic network access.

TimeOffsets carries source/version, UTC start/end, TAI-UTC integer seconds,
optional UT1-UTC seconds and caller-declared uncertainty. The validity interval
is **[start,end)** with constant offsets; callers must split it at a leap or any
correction change. A stale interval, absent correction or unknown scale fails.
No current or historical offset is guessed. UT1-UTC is constrained to [-1,1] s
for this post-1972 contract; it is not computed from longitude or local clock.

Conversions implement TAI = UTC + supplied TAI-UTC, TT(TAI) = TAI + 32.184 s,
and UT1 = UTC + supplied UT1-UTC. JulianCoordinate stores integer day plus
seconds from noon and an explicit scale, avoiding a single large Julian-date
float. The UTC calendar anchor at 2000-01-01 12:00 is day 2451545, seconds 0;
it is not J2000 TT at that same UTC instant. TT/TAI same-scale differences give
elapsed SI seconds when the supplied corrections are correct. UTC/UT1 differences
are rejected as atomic durations; cross-scale subtraction is rejected.
Reverse conversions, TDB/TCB/TCG and offset interpolation are future work.
Sub-microsecond arithmetic is tested, without claiming better source accuracy.

## Renderer capability and lifecycle contract

```python
from azimlib.renderers import get_capabilities

caps = get_capabilities('svg')
caps.require('vector_output')
assert not caps.gpu and not caps.volumes
```

Queries return immutable capabilities for exactly png/svg/pdf. PNG availability
depends on Pillow; SVG/PDF core exports do not. Terrain depth is CPU raster,
embedded into SVG/PDF where needed; it is not vector 3D. Current limited mathtext
is distinct from full TeX and complex shaping. Unsupported/unknown requests fail.

Future backends must consume the same scene/Artists and advertise capabilities
before allocation. Device/context/resources belong to the creating viewer thread;
creation, prepare/upload, draw/readback, cancellation, invalidation, context loss
and idempotent disposal must be explicit. No graphics context is created at import.
Workers may prepare immutable CPU data; stale generations cannot repaint a newer
scene. Recoverable GPU failure must use an explicit supported CPU path or raise,
without altering data/geometry. Static export remains independent of UI state.
Font shaping/metrics are composed once before backend-specific painting. Volume
and light primitives must carry frames, physical units, bounds and versioned
resource identity. These are extension requirements, **not implemented GPU APIs**.

That inventory describes the initial foundation snapshot. The later
[stage 9 GPU implementation](gpu-0.4.md) now supplies explicit contexts,
original shaders, shared scenes and bounded resources; its outstanding
performance/CI gate is recorded separately.

## Budgets and measurement policy

| Workload/resource | Initial budget/target | Enforcement/status |
| --- | --- | --- |
| Existing mesh | 50000 vertices, 20000 triangles | Same runtime allocation/scene checks as 0.3, shared constants |
| Existing depth raster | 8M pixels, 64M projected pixel tests | Same runtime guards; CPU stays available |
| Future streamed block | 32 MiB, 1M decoded items | ResourceBudget provided; reader integration belongs to step 2 |
| Future stream working set | 256 MiB, 2M in-memory indexed items | Initial per-operation budget; disk spill required, not planet RAM |
| 1000 geodetic roundtrips | p95 <=250 ms, 7 repeats | Local synthetic target, not universal CI timing threshold |
| Hold 1000 fixed coordinates | <=4 MiB traced Python allocations | Separate allocation measurement, not total process RSS |
| Navigation target | p95 <=33 ms frame work, <=100 ms initial response | Future GPU/viewer target on identified hardware, not achieved claim |

`ResourceBudget.check()` validates usage before allocation, preserving integer
counts and raising at overflow. Future steps must add raster/volume/grid-specific
allocation estimates and real-data benchmarks before advertising scale. Latency
targets require hardware, OS/Python, samples and cold/warm distinction; data size,
peak memory and numerical errors must accompany throughput. Synthetic loops cannot
prove planet-scale ingestion or real viewer input latency.

Run `python -I tools/benchmark_foundation.py --output foundation.json` for the
deterministic synthetic workload, numeric errors, local-frame timings and source
hashes. Timing targets are reported; numerical tolerance failure stops the tool.
All later lots must retain declared limits or document a measured revision.

## Fixtures, provenance and gates

The implementation and fixtures are original Azimlib code under BSD 3-Clause.
No external implementation, table, font, binary or dataset was added. Analytic
cardinal cases and a 60-digit Decimal derivation at 45 degrees use mathematical
identities; [fixture metadata](../tests/fixtures/foundation-040.json) records origin.
Synthetic time offsets deliberately do not impersonate an IERS bulletin.
Published definitions used for validation, without copying source implementations:

- [NGA WGS84 defining constants](https://earth-info.nga.mil/index.php?action=wgs84&dir=wgs84).
- [IERS TT(TAI) relation](https://www.iers.org/iers/en/service/faqs/time/howisttcomputedfromtai-163).
- [IERS time scales and correction sources](https://www.iers.org/iers/en/service/faqs/time/time).
- [IERS Conventions chapter 5](https://iers-conventions.obspm.fr/content/chapter5/icc5.pdf)
  defines the full terrestrial/celestial transformation; that model is not yet implemented.

Later grids/ephemerides/shaders/fonts require source, license, redistribution terms,
validity, hashes and independent accuracy fixtures before inclusion. Existing
third-party notices remain unchanged. Validation includes analytic expected values,
global roundtrips, singular/domain failures, ENU/parallax, synthetic leap boundaries,
timezone/precision, resource ceilings, renderer capabilities and facade/export
regressions. New Artists must retain atomic edits, visibility, removal/ownership,
optional placement, picking and deterministic static export; new models must fail
on unavailable transforms/corrections rather than silently approximating them.

Local [validation evidence](foundation-validation-0.4.json) and commands are recorded
in the [batch checklist](release-progress-0.4.md).
It does not constitute hosted CI or native human approval on other platforms.
