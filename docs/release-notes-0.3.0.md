# Azimlib 0.3.0

Status: **published on 2026-10-08; 80/80 release gates complete**.
Publication results and distribution files are available through the
[GitHub Release](https://github.com/Kernerian/azimlib/releases/tag/v0.3.0) and
[PyPI](https://pypi.org/project/azimlib/0.3.0/).
[Post-publication verification and exact hashes](release-publication-0.3.0.md).

Azimlib 0.3.0 expands the independent cartographic engine into urban,
scientific, temporal and experimental terrain visualization. Neither the
runtime nor its renderers use Matplotlib, Cartopy, GeoPandas, Shapely or pyproj.

## Highlights

- Urban layers: cities/POIs, neighbourhoods, streets and building footprints,
  immutable feature selection and CSV points.
- Own SHP/SHX/DBF, KML, local OSM XML, world-file and initial GeoTIFF readers;
  versioned optional data with explicit origin, licenses and integrity checks.
- Ellipsoidal direct/inverse geodesy, regional transverse Mercator, WGS84 UTM,
  stereographic/azimuthal-equidistant projections, crossing viewports and horizon
  clipping within the documented precision and topology limits.
- Composable transforms, mixed-coordinate Artists, public Paths, editable
  collections, expanded layout/GridSpec/SubFigure composition and map bearing.
- Scalar/RGB/RGBA raster, NoData/bilinear policies, contour fills and labels,
  regional triangulation, heatmaps/density, flows, hillshade and scientific maps.
- Adaptive Bezier strokes, physical caps/joins, curved/priority labels,
  provenance-aware custom hatches/symbols, limited inline expressions and own
  PDF export with outlined DejaVu text and attached font terms.
- Optional picking, selectors, sliders/layer controls, local live viewer,
  notebook updates and independent native Qt canvas alongside Tk/browser views.
- Experimental metric terrain: perspective/orthographic camera, depth buffer,
  surfaces, explicit local frame and building extrusion.
- Experimental finite animation, scalar bindings/playback controls, PNG/GIF
  sequences, explicit external encoders and regional multipage atlas/PDF.
- Versioned documentation, migration guide, original galleries, API stability
  policy and numerical/visual/build/installed-package validation.

Both import styles remain supported:

```python
import azimlib as azl
import azimlib.pyplot as plt
```

Cartographic components remain optional. `savefig()` exports static figures;
`show()` selects an interactive backend. The core has no mandatory dependency;
PNG, GUI, Qt, notebook, accelerated rendering and documentation use separate
extras. Python 3.10–3.14 is the supported test matrix on Linux, Windows and macOS.

## Compatibility and limits

Read the [migration guide](migration-0.3.md), [API stability policy](api-stability.md)
and individual format/geodesy/scientific/terrain/temporal guides before upgrading.
3D, temporal, Qt/notebook/live surfaces retain their documented experimental
contracts. This release does not claim complete Matplotlib API/pixel compatibility,
arbitrary global datum transforms, general solid 3D/GPU rendering or every file
variant. Data is not downloaded implicitly; real OSM-derived optional databases
remain separately licensed and outside the Python distributions.

## Validation and licenses

[Human visual acceptance](visual-acceptance-0.3.json) covers Linux/macOS PNG/SVG
and native Tk/Qt captures at the recorded commit. Final candidate CI and artifact
hashes belong to the pre-publication review report, not to historical snapshots.
The [release checklist](release-progress-0.3.md) records all 80 items complete;
[final acceptance](release-acceptance-0.3.json) is recorded separately from the
publication results. A successful workflow never constitutes human approval.

Original code is BSD 3-Clause, copyright Kernerian. Natural Earth, DejaVu,
ColorBrewer Blues, CC0 colormaps and wordmark/font credits retain their own terms
in `LICENSE`, `THIRD_PARTY_LICENSES.md`, `NOTICE_COLORMAPS` and `licenses/`.

## Publication procedure (completed; retained for reproducibility)

After recording final authorization, rebuild/audit the final distributions and
record their hashes. Promote the validated branch by a
fast-forward of `main`, wait for its 28-job CI, create annotated tag `v0.3.0`,
prepare the GitHub Release with distribution hashes and these notes, and dispatch
the gated `publish.yml` workflow on `main` for PyPI Trusted Publishing.
The workflow rechecks current main, complete acceptance, exact artifact provenance,
expected hashes, licensing and packaging before uploading the same audited bytes.
Verify the published PyPI files against the uploaded bytes and install directly
from PyPI in a clean environment. Any failed gate stops the publication sequence.

The earlier candidate hashes identify the reviewed pre-approval snapshot.
Recording final acceptance changes source documentation and therefore requires
rebuilding/auditing the sdist and recording its final hash; a wheel is also
rebuilt and rechecked. Candidate hashes are not silently relabelled as hashes
of a different post-approval commit. GitHub Pages deployment is separate.
