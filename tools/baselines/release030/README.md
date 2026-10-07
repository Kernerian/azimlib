# Original 0.3 regression fixtures

Three deterministic synthetic 320×280 scenes: physical line/marker/ticks/grid/
legend/hatch, scalar/colorbar/NoData and metric 3D depth. Original composition
and script: BSD-3-Clause, copyright 2026 Kernerian. DejaVu glyphs retain their
[font terms](../../../src/azimlib/fonts/LICENSE_DEJAVU); Viridis table is CC0,
[third-party notices](../../../THIRD_PARTY_LICENSES.md). No font binary here.

The checked manifest records original PNGs and rounded primitive hashes, not
reference-library output. `check_release_baselines.py --output NEW_DIRECTORY`
checks dimensions, geometry/layout (5-decimal screen rounding), RMS <=3 and <=2.5%
of RGB channels changing by more than 24. Both pixel conditions must hold.
Text boxes alone allow a symmetric two-pixel nearest-neighbour comparison for
optional Pillow RAQM/FreeType rasterization differences. Raw RMS is retained.
Non-text regions remain strict. Exact scene hashes still include text, fonts,
positions, rotations and styles; missing text or changed colors must fail.
This tolerance was reviewed against real Linux output, not reference-library images.
Exact payload/resource hashes are checked independently by distribution audits.

It also checks a one-degree equatorial geodesic against aπ/180 within 10 micrometres,
and bounded scene work (<500 primitives) with a generous 30-second/frame ceiling.
Four raster samples are measured, first discarded. The ceiling catches pathological
cost, not minor regressions or a promise of interactive FPS. Timings are retained
for same-host comparison. No GPU, RSS, large-world or native input performance claim.

`--record` only creates absent baselines. Baseline replacement requires explicit
review; CI never regenerates expected images. Old release snapshots are preserved.
