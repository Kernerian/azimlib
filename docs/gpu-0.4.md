# Optional GPU rendering — 0.4 source development

This implementation is in the development source tree, **not the published
0.3.0 package**. CPU rendering remains the default. Geographic geometry,
projections, labels, layout, picking, camera and shaders are Azimlib's own.
ModernGL and glcontext provide generic OpenGL bindings and context creation.
No Matplotlib, GIS renderer, game engine or external tessellator is used.
Stage 10 extends this renderer with [regular volumes, absorption, slices and
isosurfaces](volumes-0.4.md); the stage 9 measurements below remain historical
evidence for their exact source snapshot.

## Explicit selection

Install the development source with `python -m pip install '.[gpu]'`.
OpenGL 3.3 and a working driver/context are required. Installation alone does
not prove device availability; `get_capabilities('gpu')` checks installed
bindings without initializing a context.

```python
import azimlib as azl
# import azimlib.pyplot as plt also uses the same figure state.

fig, ax = azl.subplots(figsize=(7, 5))
ax.map('brazil')
ax.set_title('Brazil')

fig.savefig('map.png', renderer='gpu')  # static PNG, no viewer
fig.savefig('map.svg')                 # original CPU vector export
fig.show(backend='tk', renderer='gpu')  # native interactive viewer
```

Tk and Qt support explicit GPU rendering, retaining their existing toolbar,
navigation, coordinate display and optional components. Qt still requires the
separate `qt` extra. Browser/notebook GPU selection and GPU SVG/PDF requests
are rejected explicitly; their existing CPU paths remain available. Changing
the selected renderer while its viewer is open requires closing that viewer.

The default failure policy is `gpu_fallback='raise'`. To authorize CPU fallback
with a warning, pass `gpu_fallback='cpu'` to `show()` or `savefig()`. Cancellation
never triggers fallback. GPU budgets apply to GPU resources; an explicitly
requested CPU fallback uses the CPU renderer's own resource policy.

## Context ownership and resources

```python
from azimlib.renderers.gpu import GpuConfig, GpuRenderer

config = GpuConfig(max_surface_bytes=128 * 1024**2,
                   max_cache_bytes=16 * 1024**2)
with GpuRenderer(config) as renderer:
    image = renderer.render(fig.to_scene())
    try:
        image.save('readback.png')
    finally:
        image.close()
```

The context belongs to its creating thread and must be closed there. Native
viewers own a persistent renderer in their navigation subprocess, serialize
pipe requests and retain the original scene/picking records in the parent.
Worker snapshots exclude private Artist/layout state. A lost context is marked
unusable and requires explicit recreation or the requested CPU fallback.

`GpuConfig.context_backend` accepts the platform default (`None`) or explicitly
`'egl'` for an environment providing EGL. No silent backend search is performed.
Context creation validates OpenGL 3.3; driver failures raise a diagnostic error.
An import, capability query or ordinary CPU figure never creates a GPU context.

Default bounds are 256 MiB for framebuffer payload, 32 MiB each for retained
GPU buffers, prepared CPU mesh payload and textures, 2 million generated 2D
vertices per frame, 50,000 scene primitives and 20,000 terrain triangles.
These are separate payload budgets, **not a total process RSS/VRAM quota**.
Prepared-cache keys include an estimated overhead; Python objects and driver
allocations add memory. Surfaces are checked before allocation against the
configured budget and driver texture dimensions. Caches evict by bounded LRU.

## Shared geometry, styles and text

- Geographic transforms and seam handling finish before rendering. GPU inputs
  are screen primitives or homogeneous camera triangles. Buffer coordinates
  use local float32 offsets with translation uniforms; source data stay intact.
- Closed polygons use even-odd triangle coverage, including holes and concave
  rings. Text uses signed nonzero winding. Original CPU dash subdivision and
  stroke geometry supply physical widths, caps, joins and miter limits.
- Fill, edge, opacity, clipping and scene paint order share the CPU scene.
  Geographic rasters and hatches already composed into scene primitives use
  the same painting path. They are not a separate GPU spatial resampling engine.
- Basic text, optional HarfBuzz shaping and real TeX use prepared shared glyph
  contours. Text halos precede ink; optional backgrounds and rotation remain
  editable. Font/material notices remain in static GPU PNG metadata.
- A threefold supersampled premultiplied RGBA16F framebuffer resolves to an
  ordinary RGBA PNG/Pillow readback. Gamma, font hinting, coverage and depth
  quantization can differ from CPU output; byte-identical parity is not promised.

Translated meshes and uploaded buffers are reused. Zoom and geometry/style
edits invalidate affected preparation keys. Generation numbers reject stale
frames; cancellation is checked between primitives and before presentation.
A running driver draw cannot be preempted by that check. Picking uses the
unchanged CPU geographic/Artist records, not a separate approximate GPU model.

## Terrain, extrusions and textures

The same camera, mesh, lighting and `SurfaceArtist` supply CPU and GPU output.
OpenGL clips homogeneous triangles and depth-tests opaque/masked faces. Shared
axes combine textured and untextured materials into one depth scene.

```python
fig = azl.figure()
ax = fig.add_subplot(111, projection='3d')
texture = (2, 2, bytes([220, 180, 90, 255,
                       40, 140, 100, 255] * 2))
surface = ax.plot_surface([0, 1], [0, 1], [[0, 1], [1, 2]],
                          color='white', texture=texture, shade=True)
surface.set_texture(texture, uv=((0, 1), (1, 1), (0, 0), (1, 0)))
surface.set_visible(False)
surface.set_visible(True)
fig.savefig('terrain.png', renderer='gpu')
```

Textures are `(width, height, immutable_RGBA_bytes)`, top row first, at most
8 million pixels; alpha must be 0 or 255. Sampling is nearest-neighbor with
normalized, top-left UV pairs, perspective-correct interpolation and edge
clamping. Default UV maps local X/Y across the surface, with north at the top;
degenerate planar mapping requires explicit UV. `set_texture()` validates
atomically, `get_texture()`/`get_texture_uv()` inspect it, and
`set_texture(None)` removes it. No image is downloaded implicitly.

CPU PNG and embedded terrain in SVG/PDF use an original bounded perspective
texture reference (at most 64 million candidate pixel evaluations and 8 million
output pixels). GPU depth precision and CPU epsilon/tie rules can differ at
coplanar faces. Transparent 3D sorting, mipmaps, bilinear textures and volume
rendering are not provided by this stage; volumes belong to stage 10. Texture
copyright/provenance supplied by applications remains their responsibility.

## Validation, performance and outstanding gate

Run `python -m unittest discover -s tests -p test_gpu_040.py -v` without a
graphics device for contracts. Set `AZIMLIB_GPU_TEST=1` to require the actual
device tests; an opted-in unavailable device fails instead of silently skipping.
For EGL also set `AZIMLIB_GPU_CONTEXT=egl`.

`python -I tools/validate_gpu.py --output NEW_DIRECTORY --native` generates
CPU/GPU PNG pairs, differences, vector references, source/file hashes, device
identity, cold/warm/pan/resume/zoom/edit timings and verified Tk/Qt captures.
With `--measure-memory` and psutil already installed, it samples process plus
worker RSS every 10 ms. Run this separately from timing-only measurements:
profiling overhead can materially change timings. Shared pages can be counted
twice and a short peak can be missed; this is separate from GPU payload
accounting and does not measure driver VRAM.
Without `--native` it does not open a viewer. On a developer Windows desktop,
Tk capture uses the verified application HWND, not an arbitrary desktop crop.
Captures prove rendering, not human acceptance or physical input latency.

The final timing-only Windows NVIDIA RTX 2060 trial found warm/pan median
drawing around 25–27 ms, but scene composition p95 around 146–180 ms and
changed-zoom median drawing/preparation around 756 ms. Sequential composition
plus draw measured roughly 6 FPS for pan and 1.2 FPS for zoom in that scene.
An earlier local pass was faster; neither result is a universal guarantee.
Renderer-only time is not viewer FPS.
The 33 ms/100 ms interaction goals are **not established** by these results.
The CPU/GPU image mean channel error was about 1.2/255 for the map and 1/255
for terrain; individual edge pixels differ substantially.

[Local evidence snapshot](gpu-validation-0.4.json) distinguishes source-tree
tests, native captures, optional typography, packaging and memory measurements.
The manual `gpu-review-0.4.yml` workflow prepares no-GPU contracts on three
systems and a clearly identified **software Mesa** EGL reference, not hardware
acceleration. It has not been run remotely for this stage.

**9.01–9.07 are validated locally; 9.08 remains pending** for CI without a GPU
and the complete performance/portability gate. Reduce scene composition and
changed-zoom preparation before claiming fluent GPU interaction; revisit this
gate before final release. No release/tag/upload is produced by these tools.

## Follow-up profiling of gate 9.08

[Detailed measurements](gpu-profile-0.4.json) retain the original 33 ms frame
and 100 ms interaction targets. The fixed map workload uses 24 frames per
warm/pan/resume/zoom phase, with an independent cold frame. On the identified
RTX 2060 / NVIDIA 617.42, baseline median pan/zoom were 197/761 ms; the final
timing-only run measured 69/160 ms. These are sequential scene-to-image
measurements, not a claim about display FPS.

Profiling identified repeated best-legend collision tests and scalar stroke
mesh construction. Candidate indexing/bulk collision arithmetic retain exact
inclusive tests and original tie ordering. Optional NumPy bulk stroke
arithmetic emits the same quads/circle fans; NumPy absence retains the scalar
path. Widths, joins, caps, dash rules, supersampling and resource budgets were
not reduced. CPU/GPU mean channel error remains approximately 1.2/255; this
does not imply pixel-identical edges.

`python -I tools/profile_gpu_pipeline.py --output NEW_DIRECTORY` reproduces
the fixed workload. A separate `--diagnostic` run records CPU composition,
mesh/key preparation and packing, driver buffer submission, GPU draw-command
timer sums, completion wait/readback and sampled RSS. Synchronous GPU query
retrieval changes scheduling; its timings must not be used as normal frame
performance. Draw queries exclude uploads/clears, and buffer submission time
does not isolate PCIe transfer bandwidth.

Tk/Qt synthetic native event-to-toolkit-paint measurements, first show,
initial pan, resume, zoom and RSS are recorded separately. Neither toolkit
consistently met 100 ms; the 33 ms frame goal also remains unmet. Physical
input-to-photon latency, compositor scanout and driver VRAM are unmeasured.
**9.08 remains pending.** Performance gains do not waive the gate.

## Dependency notices

[Dependency inventory](gpu-dependencies-0.4.json),
[third-party notices](../THIRD_PARTY_LICENSES.md),
[ModernGL MIT](../licenses/ModernGL.txt) and
[glcontext MIT](../licenses/Glcontext.txt) preserve their separate copyrights.
Only license texts are distributed here, not the dependencies' implementations.
GPU bindings do not become Azimlib-owned code. Original geometry, GLSL shaders,
renderer and integration remain under Azimlib's BSD-3-Clause terms.
