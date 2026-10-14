# Volumes and synthetic clouds — 0.4 development

This is unreleased development functionality. The published version remains
0.3.0. Numerical fields, interpolation, optical composition, slices,
isosurfaces and GLSL are Azimlib implementations. NumPy optionally accelerates
the CPU equations; ModernGL/glcontext provide optional OpenGL bindings.
There is no Matplotlib, GIS or external volume renderer underneath this API.

## A scalar field on physical axes

```python
import azimlib as azl
from azimlib.colors import Normalize

# Arrays are [z][y][x]; samples are at nodes, with cells between adjacent nodes.
data = [[[x + y + z for x in range(8)] for y in range(8)] for z in range(8)]
field = azl.VolumeField.from_array(
    data, origin=(0, 0, 0), spacing=(100, 100, 100),
    unit="m", value_unit="synthetic units",
)
fig = azl.figure()
ax = fig.add_subplot(111, projection="3d")
volume = ax.plot_volume(
    field, norm=Normalize(0, 21), cmap="viridis",
    opacity=azl.OpacityTransfer(((0, 0), (1, .2))),
    step=75, reference_length=100,
)
fig.colorbar(volume, ax=ax, label="Synthetic units")
fig.savefig("volume.png")
# fig.show() or fig.show(renderer="gpu") explicitly opens an interactive viewer.
```

`import azimlib.pyplot as plt` shares the same figure state. No component is
added implicitly: colorbar, title, scale, legend and other decorations remain
optional. A volume is continuous trilinear interpolation of nodal samples,
not a point cloud or a collection of independently opaque voxel cubes.

`origin` and `spacing` are XYZ, while array shape is ZYX. `unit="m"`, `"km"`
or `"ft"` converts spatial input to canonical metres. Positive spacing and at
least two nodes along each axis are required. The current contract is a
regular Cartesian grid; unstructured grids, curvilinear voxels, NIfTI,
NetCDF and generic scientific file readers are not claimed.

`value_unit` records the scalar's unit; it does not convert values or impose
cloud physics. Nonfinite/masked array values and explicit `nodata` become NaN.
Packed inputs accept finite float32 or NaN and reject infinity. Linear samples
outside the field return `None`; missing nodes with positive interpolation
weight make the sample missing. A zero-weight missing corner does not erase
an exact valid node. `method="nearest"` uses nearest nodal values, rounding
half upward. `components=3` accepts ZYXC vector nodes. Render a specific
`field.component(0)` or `field.component("magnitude")` explicitly; the latter
interpolates **nodal magnitudes**, rather than taking the magnitude after
interpolating vectors. No vector advection or fluid simulation is implied.

Set `frame=azimlib.terrain3d.LocalFrame(lon, lat)` for a terrestrial local
tangent frame. Cartesian `frame=None` is distinct. The existing physical 3D
camera, terrain and extrusion scene is shared; inconsistent field frames are
rejected. Longitude/latitude and vertical datums are never inferred from XYZ
arrays. Geographic terrain must use the same explicit local frame.

## Streaming and the AZV1 format

`write_volume(path, field, brick_size=16)` writes Azimlib's own AZV1 format.
`read_volume(path, budget=..., sha256=...)` checks the entire file, every brick
checksum, sample validity, expected length and optional whole-file SHA-256.
The result stores a verified disk source and a bounded sampling cache, not a
dense copy. Changed or corrupt sources fail when accessed.

```python
budget = azl.VolumeBudget(max_dense_bytes=1024**2, max_cache_bytes=256*1024)
field = azl.read_volume("density.azv", budget=budget)
small = field.select((100, 500, 100, 500, 100, 500))  # XYZ endpoint pairs
volume = ax.plot_volume(small, norm=Normalize(0, 1))
```

Selection copies a bounded nodal ROI, including adjacent nodes needed for
interpolation at its boundaries. Rendering requires bounded dense scalar
data; an oversized disk field fails with a request to select a region.
`plot_volume(field, region=...)` performs that selection explicitly. This
provides out-of-core acquisition/selection, not an unbounded GPU residency
manager or automatic multiresolution renderer.

Streaming writers may supply `shape=(nz,ny,nx)` and a `bricks` iterator instead
of a dense field. It must yield `((bx,by,bz), bytes)` in Z/Y/X brick order.
Each brick has `brick_size**3 * components` little-endian float32 values;
incomplete edge bricks are padded with NaN. Missing, extra or reordered
bricks are errors. Destinations must be new; failed writes remove the own
temporary file.

The binary layout is `AZIMVOL1\n`, a little-endian uint32 JSON-header length,
the UTF-8 JSON header, then fixed records of 32-byte SHA-256 followed by brick
bytes. Header metadata declares shape, XYZ origin/spacing, components,
value_unit, optional local-frame lon/lat and brick size. Headers are at most
64 KiB. Checksums provide corruption detection, not signatures or authenticity.

Default budgets: 32 MiB dense sample payload, 16 MiB brick-cache payload,
20 GB file, 1 million output pixels, 512 ray steps and 64 million bounded
field evaluations. Budgets are checked before the corresponding allocation
or drawing. Their hard configurable maxima are 128 MiB per dense field/cache,
20 GB/file, 1 million pixels, 512 steps and 128 million evaluations.
Temporal bindings cap accumulated dense field payload at 128 MiB. These are
payload/work bounds, **not process RSS or driver VRAM quotas**. Shader code,
contexts, arrays, temporary copies and native allocations have additional
cost. The sample bound counts field evaluations, including gradient and
shadow evaluations, rather than individual nodal fetches. GPU's existing
texture-cache bound also applies to the combined fields and transfer tables.

The validation tool separately checks a 20 GB generated-storage ceiling and
15 GB free-space reserve. Per-file `VolumeBudget` does not enforce a global
filesystem quota. The reproducible test writes/verifies all 2,097,152 nodes
of a 128³ file, then renders/selects a small ROI with a 256 KiB dense budget.
This is a bounded streaming demonstration, not a planet-scale benchmark.

## Transfer functions and physical distance

The renderer maps values with exact `Normalize` or `LogNorm`, and samples a
shared 256-entry float32 RGBA transfer table. Other norm subclasses fail
explicitly. `OpacityTransfer` has 2–256 increasing knots covering normalized
0 to 1; opacity values are in 0 to 1. A float supplies constant opacity.
Colorbar describes scalar normalization and colormap, not optical thickness.

For reference opacity `a`, density multiplier `d`, reference length `L` and
ray segment `ds`, optical depth is
`tau = -log(max(1e-12, 1-a)) * ds/L * d`. Segment opacity is `1-exp(-tau)`.
The finite logarithm floor bounds the opacity-one case. Composition proceeds
front to back with premultiplied color. Homogeneous alpha therefore depends
on physical path length rather than step count. `step` and `reference_length`
are positive metres; default step is 0.75 times minimum nodal spacing and
default reference length is minimum spacing. Heterogeneous data use midpoint
quadrature, with finite-step approximation error. Up to four overlapping
volumes combine optical depths at shared sample positions, independently of
Artist insertion order. They are not separate painter-sorted transparent
surfaces. LogNorm treats nonpositive samples as transparent; NoData and zero
opacity contribute nothing.

An all-missing field needs explicit norm limits. Constant data auto-normalize
to zero, which may be transparent under the default opacity transfer; set
explicit limits or constant opacity when appropriate.

## Light, sections and isosurfaces

`VolumeLight(direction=(1,-1,2), ambient=.35, diffuse=.65, shadow_steps=4)`
specifies a world XYZ direction **toward** the light. A central finite
difference estimates the scalar gradient, producing illustrative diffuse
light. `shadow_steps=0` disables self-shadow; 1–32 midpoint steps integrate
absorption toward the light through that same field. The model does not
simulate multiple scattering, atmospheric weather, calibrated radiance,
terrain-cast volumetric shadows or coupling between separate volumes' lights.
Terrain still correctly occludes the camera ray. Scientific claims about
cloud physics require a separate physical model and validation.

`ax.volume_slice(field, axis="z", position=300)` builds an interpolated
scalar-colored plane; missing triangles are omitted. `ax.isosurface(field,
level=.3)` creates actual geometry with original marching tetrahedra and a
fixed shared cube diagonal. Cubes containing missing nodes are omitted.
Limits are 1 million inspected cells, 50,000 output vertices and 20,000
triangles. Oversized/empty results fail explicitly; select a smaller ROI.
These return the existing editable surface Artists with their normal depth,
color and shading contracts. Arbitrarily transparent surface sorting remains
outside the 3D surface contract.

## Editing, time, picking and export

`volume.set_data(field)` / `set_array(field)`, `get_data()` / `get_array()`,
`set_norm`, `set_cmap`, `set_clim`, `set_opacity`, `set_density`, `set_step`,
`set_reference_length`, `set_light`, `set_visible` and `remove` keep the same
Artist/camera and colorbar connection. `get_array()` returns the field;
normalization uses its finite component extrema internally. Invalid edits
fail before replacing data/parameters. Temporal bindings require identical
shape, origin, spacing, value unit and spatial frame. Existing
`TemporalSeries.bind(volume, scale="global")` or `scale="frame"` handles
clim updates; `FuncAnimation` can drive that binding and export raster frames.
Picking reports the first positive optical contribution, its XYZ position,
value and volume index, stopping at opaque terrain. It does not promise a
unique physical surface inside a transparent field.

CPU has a pure Python reference and optional owned NumPy acceleration. GPU
uses original GLSL 3.3 with manual trilinear interpolation and a shared
camera/depth buffer. GPU local recentering reduces float32 error at large
Cartesian origins; it is still finite-precision rendering. Both integrate
one volume ray per final pixel, independently of the 3× 2D supersampling.
Opaque geometry depth coverage at edges can differ between CPU and GPU;
pixel-perfect equality at mesh silhouettes is not guaranteed. Analytic
interior alpha/depth and shaded overlaps have numeric tolerance tests.

`savefig()` exports static PNG; SVG/PDF embed raster volume/terrain layers
and retain their other vector elements. SVG embedding needs Pillow; PDF
uses the own image writer. Increasing export DPI increases work and may
hit the declared budget. GPU export remains PNG; CPU SVG/PDF are explicit.
`show()` separately provides the existing Tk/Qt viewer and optional GPU
worker. No new native backend is silently selected. Animation uses the same
raster policy and existing bounded writers; no vector-volume export is claimed.

## Reproduction and evidence

- `examples/volume_cloud.py`: original synthetic Gaussian density, terrain,
  slices, isosurface and optional colorbar; no external dataset.
- `tests/test_volume_040.py`: analytic interpolation/alpha/depth, NoData,
  corrupt files, work bounds, editing/time/picking and opt-in actual GPU.
- `python tools/validate_volume.py --output NEW_DIRECTORY --gpu --native`:
  CPU/GPU images, SVG/PDF, two temporal frames, verified own-window Tk/Qt
  captures, streaming trial, hashes and HTML comparison index. Omit optional
  flags for CPU-only validation. Native capture is not human acceptance.
- [Local validation evidence](volume-validation-0.4.json).

All fields and example formulas in this stage are original synthetic material
under the project license. Existing ColorBrewer `blues` attribution, optional
GPU binding notices and font licenses remain in the third-party inventory;
the new module does not acquire or embed any external dataset. Local tests
do not close pending platform/human gates in 7.08, 8.08, 9.08 or 14.

## Backing-file lifetime

Keep AZV backing files immutable while an index/sampler is open. Initial opening
verifies payload hashes; sampled bricks verify their checksums, and size/mtime
changes reject the source. Metadata checks alone do not detect an adversarial
same-size write with restored or unchanged coarse timestamps in unrequested
bricks. Reopen and verify the expected full SHA-256 after replacing a source.
