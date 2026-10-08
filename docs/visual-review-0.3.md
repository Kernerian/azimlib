# Visual review for 0.3.0

Checklist item **7.08 remains pending human approval** on Linux and macOS.
The review workflow does not approve a release, change the stable version,
deploy documentation or upload a package.

## Review packets

The `visual-review-0.3` workflow runs on native Ubuntu and macOS runners using
Python 3.12 and the installed development package. It generates two artifacts:

- `azimlib-0.3.0-visual-review-linux`
- `azimlib-0.3.0-visual-review-macos`

Extract each ZIP and open `index.html` locally. Its full-size links show PNG
and SVG alongside the same Windows reference exported by Azimlib. Reference
images are comparison aids, not previously approved expected results. Hashes
identify the generator, examples, fonts, installed code and outputs. Python
source comparison normalizes only LF/CRLF; raw installed hashes are also kept.
Platform-specific font rasterization can differ slightly. Missing text,
clipping, distorted symbols, incorrect widths or overlapping components must
be investigated rather than accepted as a font-engine difference.

## Scope and checklist

- Text: accents, bold/italic, rotation, geographic labels, multiline titles,
  ticks, axis spacing, annotations and label collision priorities.
- Strokes: .4/.8/1.5/3-point widths, 100/200-dpi proportions, dashes,
  butt/round/projecting caps, miter/round/bevel joins and cubic curves.
- Symbols: circle, square, diamond and triangle proportions in maps/legends.
- Cartography: boundaries, rivers, lakes, synthetic streets/buildings,
  neighbourhoods, overview focus, spherical/ellipsoidal projections and horizons.
- Scientific views: raster, NoData, contour labels, triangulation, continuous
  colorbars and their labels/layout.
- 3D/temporal: perspective and orthographic terrain, extrusions, colors, depth,
  frame 2 and native playback controls.
- Tk and Qt: real mapped windows, toolbars, Subplots dialog, urban view,
  pan and Home restoration. Linux uses native X11 toolkits on Xvfb; macOS uses
  Aqua/Cocoa. Captures contain only the application rectangle. Native toolkit
  chrome need not look identical across operating systems.
- Browser: `urban-interactive.html` provides the portable offline viewer.
  Screenshots and a local browser do not prove physical mouse latency on a
  remote operating system or substitute for a hardware interaction test.

Fourteen scenes produce 17 PNG/SVG pairs (three scenes also at 200 dpi) and
twelve native window captures per OS. Source/runtime/reference mismatches,
privacy findings, occluded Tk canvases, native plugin substitution and failed pan/Home checks stop
the workflow. A passing job means packet generation passed; it does not mean
the human review passed. Licenses and third-party notices accompany the ZIP.

Approval must identify both operating systems and the reviewed workflow
commit/run. Only an explicit human acceptance can complete 7.08. The final
10.08 acceptance and publication preparation remain separate subsequent work.

## Reproduction

Use a fresh environment with Tk installed by the Python distribution:

```bash
python -m pip install '.[gui,qt,notebook]' 'Pillow>=12.3'
python -I tools/prepare_visual_review.py --native --output visual-review
```

On Linux run the last command inside `xvfb-run` with a 1920×1440 screen and the
Qt X11 shared libraries listed in `.github/workflows/visual-review.yml`.
Outputs must go into a new empty directory. References live under
`tools/baselines/visual-review030`; regenerate deliberately with
`--record-reference` when the rendered examples or core change, preserving the
baseline's exact generator and image hashes. A new baseline is not an approval.

Tk captures are checked against the rendered canvas before saving. Windows
uses an explicit native window handle, with no desktop-crop fallback. The
review tool requires Pillow 12.3 for the platform capture APIs; this does not
raise the core library's Pillow requirement.
