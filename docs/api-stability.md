# API stability and version policy

This policy covers **0.3.0**. Published files are listed on
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
