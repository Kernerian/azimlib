# 0.4 development integration and delivery gates

This is an **unreleased source-tree preview**, not an installed PyPI 0.4 release.
Candidate metadata is 0.4.0; published stable files remain 0.3.0. The authoritative
[112-item checklist](release-progress-0.4.md) records completed work and pending
evidence; successful local examples do not approve a release.

## Reproduce the cumulative gallery

From a reviewed source checkout, install only the required extras explicitly:

```sh
python -m pip install '.[gui,qt,gpu,dev]'
python -I tools/validate_integration_040.py --gpu --native --output integration-review
python -I tools/check_release_progress_040.py
```

Use a new output directory for every run. The validator checks the source import,
shared `azimlib`/`azimlib.pyplot` state, original geocoding-to-route scene, topology
clipping, geocentric roundtrip, urban shadows, Earth–Moon composition, solar globe
and lit volume. It exports PNG/SVG/PDF according to capabilities, records source,
example and export SHA-256s, and writes an HTML comparison index. GPU is explicit:
an unavailable context fails rather than silently falling back. Native review
captures only the application's verified windows. They do not grant human approval.

For an isolated wheel installation, pass `--installed`. For the dependency-free
core, use `--installed --core` without GPU/native flags. Core produces vector
SVG/PDF where supported and PDF volumes; raster export requires a provider.
Small core images test packaging and capabilities, not typography at display size.

| Scene | Inspect |
| --- | --- |
| City | Labels and physical symbols, legend, scale, route, geocentric conversion |
| Urban light | Building/terrain occlusion, shadow bounds, original synthetic input |
| Earth–Moon | Depth, spherical bodies, explicit visual distance/radius scaling |
| Solar globe | Orthographic boundary, night/terminator, labels and seams |
| Volume light | Transparent volume, local physical frame, CPU/GPU raster exports |
| Tk/Qt captures | Toolbar, margins, resize, text; manually exercise pan/zoom/history |

CPU/GPU antialiasing and edge pixels may differ. Compare legibility, dimensions,
holes, alpha, depth and relative placement, not only exact pixel equality. Follow
the separate [text review](text-review-0.4.md), [TeX](tex-0.4.md) and
[GPU](gpu-0.4.md) procedures for their complete platform gates.

## Coverage and explicit boundaries

| Subsystem | Development contract | Guide |
| --- | --- | --- |
| Geographic formats | Existing GeoJSON/CSV/SHP/DBF/KML/OSM XML/raster; own bounded PBF stream/index | [Formats](formats.md), [PBF](osm-pbf.md) |
| CRS | Catalog, axis/unit rules, geographic/projected/geocentric transforms, explicit datum/height grids | [CRS](crs-0.4.md), [grids](datum-grids.md) |
| Topology | Own planar overlay and spherical regions, declared precision/domain and resource errors | [Topology](topology-0.4.md) |
| Urban operations | Local provenance-bearing geocoder and own road graph; no implicit online address service | [Geocoding](geocoding-0.4.md), [routing](routing-0.4.md) |
| Text | Optional shaping/fonts and explicit TeX toolchain; no bundled engine binaries | [International text](international-text-0.4.md), [TeX](tex-0.4.md) |
| Rendering | Own CPU/GPU scene renderers; explicit optional context and failure/fallback rules | [GPU](gpu-0.4.md) |
| Volumes | Bounded field/brick storage, ray integration, slices/isosurfaces; SVG volume embedding needs Pillow | [Volumes](volumes-0.4.md) |
| Sun/Moon | Bounded terrestrial models, explicit units/frames/time policies and accuracy | [Sun](solar-0.4.md), [Moon](lunar-0.4.md) |
| Lighting | Physical local shadows, finite source geometry; precise real eclipses remain blocked | [Lighting](lighting-0.4.md) |

No universal CRS, arbitrary TeX, planetary throughput, precise eclipse prediction
or universal real-time performance is claimed. Query renderer capabilities before
requesting an optional output. Map components remain opt-in and editable Artists.

## CI and release separation

The existing 28-job CI contract is preserved. The manual
`integration-0.4.yml` workflow prepares **22 additional jobs**: 15 core OS/Python
combinations, three native capture jobs, three optional-provider absence jobs and
one explicitly software Mesa GPU job. Software Mesa is not hardware-GPU evidence.
This workflow has read-only repository permissions and no publication steps.
Its configuration/tests do not constitute a successful hosted execution.

Before release, run complete exact-candidate CI, the applicable native review,
final 14.01/14.06 revalidation and same-commit distribution audits. Four original
IDs are explicitly deferred, not passed: [rescope](deferred-gates-0.4.md).
[Current stage-14 preparation](stage14-0.4.md) distinguishes local evidence from
exact hosted CI, human review and final distributions. The scoped publication
checker rejects every unchecked active ID; four named deferments are preserved.
Unknown series, arbitrary unchecked-ID bypasses and failed functional checks
remain rejected.

See [migration](migration-0.4.md), [draft release notes](release-notes-0.4.0.md),
[the static original gallery](gallery-0.4.md),
[benchmark methodology](integration-benchmarks-0.4.md) and
[third-party boundaries](../THIRD_PARTY_LICENSES.md). Raw external references,
private paths, logs and local development environments are excluded from packages.

## Unpublished preparation and publication gate

Stage-14 tooling distinguishes `--purpose prepare` from the default publication
gate. Preparation permits only 14.04/14.05/14.07/14.08 to remain open; it is not
publication approval. Publication requires all 108 active IDs complete, exactly
the four named deferments still unchecked, and no other unchecked ID. Human
14.05 and explicit final 14.08 acceptance cannot be inferred from CI.

For explicitly headless Linux Mesa validation, select `--gpu --gpu-context egl`
(and an installed EGL driver). Desktop default context selection is unchanged;
the validator does not silently consume a GPU-context environment variable.
