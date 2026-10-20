# API stability and version policy

This policy covers published **0.3.0** and the **unreleased, re-scoped 0.4 development API**. Published files are listed on
[PyPI](https://pypi.org/project/azimlib/). [Release gates](release-progress-0.3.md)
are tracked separately from implementation milestones and publication results.

Azimlib follows a documented pre-1.0 policy: patch releases preserve supported
public signatures/semantics except necessary security fixes; minor releases may
introduce breaking changes, documented with a migration path. A future 1.x
series will require major versions for incompatible supported public contracts.
No numerical/pixel identity across all platforms is promised.

| Surface | Status in 0.3 development | Contract |
| --- | --- | --- |
| Root/pyplot Figure, MapAxes and ordinary Artists | Supported subset | [Compatibility](compatibility.md), [migration](migration-0.3.md), [signature reference](api.md) |
| Explicit geodesy/readers and scientific 2D | Supported within documented limits | Units, CRS, masks/format variants and tolerances in their guides |
| TerrainAxes, Camera/Mesh/SurfaceArtist, LocalFrame | Experimental | Metric regional terrain, opaque faces, bounded CPU depth rendering; [limits](terrain3d.md) |
| TemporalSeries, ScalarBinding, FuncAnimation, writers, Atlas/PdfPages | Experimental | Finite sources, deterministic callbacks, export/encoder budgets; [contracts](temporal.md) |
| Qt, notebook and browser-live integrations | Experimental | Optional dependencies, owner-thread/lifecycle rules; [interaction](interaction.md) |
| Names beginning `_`, renderer internals, private caches | Internal | No API stability guarantee; examples should use public interfaces |

Experimental APIs can change at a minor version boundary; changes belong in
CHANGELOG and migration notes. Existing runtime snapshots are evidence of their
recorded code, not evidence that later code passed those tests. Current gates
compare runtime/artifact hashes. Never rewrite old measurements to look current.

`import azimlib as azl` and `import azimlib.pyplot as plt` remain supported.
No blanket compatibility with Matplotlib internals, renderers, plugins,
callbacks, every keyword or every toolkit is claimed. Unknown options fail
explicitly; physical points/DPI and geographical CRS must not be conflated.

Optional dependencies preserve their own licensing. A release does not grant
rights to arbitrary user-supplied data, fonts, symbols or external encoders.

## 0.4 development surfaces

| Surface | Status | Supported claim |
|---|---|---|
| CPU Figure/MapAxes/root/pyplot | Existing supported subset | Same signatures, units and explicit format/coverage rules |
| `renderer="gpu"`, `GpuRenderer`, `GpuConfig`, GPU export | Experimental optional GPU backend | Functional declared coverage; no universal 33 ms/100 ms guarantee |
| `EclipseGeometry`, `occultation`, `ShadowCone`, disk conventions, `eclipse_shadow` | Experimental for astronomical/scientific use | Declared finite-body geometry; observed corpus results, no complete physical envelope or certified forecasts |
| `_eclipse_ephemeris`, `_spk` and scientific audit internals | Internal/experimental | No promotion to supported public API through examples |
| PBF public reader/index APIs | Supported within declared format/resource coverage | Regional real validation; planet trial deferred |

Experimental scientific status describes evidence/accuracy limitations; it does
not erase existing geometric contracts or authorize arbitrary patch breakage.
0.4.1 preserves supported public signatures and semantics. Deep changes belong
to a documented minor-version migration. GPU/science experimentation does not
change CPU defaults, root/pyplot imports or explicit fallback/approximation rules.
[Measured evidence](observed-validation-0.4.md), [deferred criteria](deferred-gates-0.4.md).

## 0.5 development foundation/surfaces

Body/PlanetaryContext/PlanetaryData/ArtistGroup retain the documented Phase A
contracts. Phase B adds BodySurface, SurfaceProjection, PlanetaryRaster,
RasterBudget, ElevationProfile, SurfaceFrame, GeometricLight and
GeometricTerrainLight. Their supported static sphere/oblate domains and
explicit refusals are in the [surface guide](surfaces-0.5.md). No universal
geodesy, triaxial/irregular solver, temporal orientation or atmosphere claim.

Non-Earth Axes now default to metric EQC; callers preserving Phase A's visual
angular scale must request `projection='angular'`. Earth defaults are preserved.
3D remains experimental under the existing camera/mesh/texture contracts.
Planetary GPU and HTML/browser coverage are not silently promoted; unsupported
paths refuse. This development work does not change the 0.4.0 frozen release,
its four deferred gates or the separate Orbits 0.6.0 roadmap.
