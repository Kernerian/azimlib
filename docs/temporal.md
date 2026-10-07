# Temporal maps and regional atlas

Azimlib 0.3 development uses its own finite frame model, Artist updates, native
GUI scheduler and multi-page PDF writer. It does not import another animator,
GIS backend, PDF merger or Matplotlib implementation. The default figure remains
light and clean: no playback controls, grid, north, scale or legend are inserted
unless explicitly requested.

## Frames and instants

```python
import azimlib as azl
from azimlib.animation import FuncAnimation

series = azl.TemporalSeries(
    [2000, 2010, 2020],
    [[[1, 2], [3, 4]], [[4, 8], [12, 16]], [[9, 18], [27, 36]]],
    unit="year", name="Synthetic population index",
)
fig, ax = azl.subplots()
image = ax.imshow(series[0].data, extent=(-54, -42, -28, -16), origin="lower")
ax.set_extent((-54, -42, -28, -16))
fig.colorbar(image, ax=ax, label="Population index")
binding = series.bind(image, scale="global")
ani = FuncAnimation(fig, lambda i: binding.apply(i), len(series), interval=400)
# Keep ani alive; start the native event loop when desired:
# azl.show()
```

`import azimlib.pyplot as plt` provides the same plotting state. Import animation
from `azimlib.animation`, or use `azl.animation`. `frames` accepts a positive
count, bounded sequence/NumPy array or TemporalSeries. With TemporalSeries the
callback receives an immutable Frame with `time` and `data`; with a count it
receives indices. Generators and infinite sources are rejected, not silently
cached forever. Frame payloads contain immutable nested numeric/text/date/array
or string-keyed mapping values; no arbitrary mutable application objects.

Numeric times require an explicit nonempty unit. They are not implicitly converted
or assumed to be longitude; dates/datetimes normalize to UTC (naive dates assume
UTC). Times must be strictly increasing, unique and finite. `series.at(time,
method="exact"|"nearest"|"previous"|"next")` and `index_at` select a frame.
Nearest clamps outside the series and chooses the earlier frame on a tie;
previous/next raise outside their respective available bounds. No implicit time
interpolation is performed. Playback cadence is `interval` in milliseconds,
independent of gaps between source dates.

## Update existing Artists and color policies

`series.bind(artist, scale="global"|"frame", norm=None)` prepares **every** frame
before altering an Artist. Supported targets: scalar imshow with fixed shape,
pcolormesh, scatter colors with fixed point count, existing choropleth features,
and experimental SurfaceArtist scalar colors with fixed mesh topology. `apply(i)`
edits scalar values/norm; boundaries, IDs, point positions, camera, limits,
visibility and existing components remain owned by the same Artists. Moving
points, proportional sizes, text, routes or geometry can instead be edited in
a reproducible custom callback through their existing setters.

- Global: one norm across all frames; without an explicit norm, infer limits
  across all finite scalar values in the series. An explicit complete norm
  preserves its supplied limits/classes. Same values retain the same colors.
- Frame: infer a separate norm for each nonempty frame. Identical colors may
  represent different magnitudes across frames; make this clear in titles/labels.
- BoundaryNorm retains its explicit class boundaries for both policies. Linked
  colorbars and thematic legends follow existing ScalarMappable callbacks.
- Missing/nonfinite values use the current colormap's bad color. A wholly missing
  frame uses the global norm, not invented local limits. An entirely missing
  series cannot infer automatic limits and is rejected.
- Editing a bound scalar image's shape externally invalidates the binding.
  Removing the Artist prevents further updates. Limits in prepared norms are
  snapshots; change/create the binding when intentionally changing the policy.

General callback code can update arbitrary state and cannot be rolled back by
Azimlib. Use callbacks that reproduce any requested frame, without accumulating
new layers or irreversible external side effects. A failed callback pauses
playback; its partial application changes remain the callback's responsibility.

## Playback and optional controls

`ani.seek(index)`, `step()`, `pause()`, `resume()`, `set_interval(milliseconds)`
and `close()` are explicit. Home/Back/Forward continue to control the map/camera,
not the time index. Native Tk/Qt auto-play starts on the first native draw;
`autoplay=False` disables this. `repeat=False` stops after the last frame.

```python
slider_ax = fig.add_axes((0.2, 0.02, 0.5, 0.05))
play_ax = fig.add_axes((0.75, 0.02, 0.15, 0.05))
controls = ani.add_controls(slider_ax, play_ax, label="Frame")
```

Controls require distinct empty axes and are optional. Seeking with the slider
pauses playback. Keep room for map ticks/labels. Controls are independently
visible/editable through `controls.slider` and `controls.play`; disconnect with
`controls.close()`. An animation close disconnects its controls/subscriptions.
Figure close stops native timers and removes scheduled callbacks. An explicit
external event_source follows start/stop/add_callback/remove_callback/interval;
it is stopped/detached but not destroyed by animation close.

`fig.canvas.new_timer(interval=200)` returns an owned timer. Callbacks run on the
native GUI thread via Tk after or Qt QTimer; no worker thread changes Artists.
No hard real-time frame rate, blitting, GPU or dropped-frame catch-up is promised.
Slow drawing stretches playback. Notebook, static HTML and headless Figures
support manual seek/step/exports, not an implicit background event loop. Browser-
live remains useful for Python-side manual updates; automatic timers in this cut
require Tk or Qt. Linux/macOS native GUI validation remains checklist **7.08**.

## Frames, GIF and an explicit video encoder

```python
ani.save_frames("outputs/frames")        # new directory, frame-00000.png ...
ani.save("outputs/map.gif", fps=4)       # optional Pillow encoder
# Optional, separately installed encoder, never auto-downloaded:
# ani.save("outputs/map.mp4", writer=azl.animation.FFMpegWriter(), fps=4)
```

Exports use the full own scene, no toolbar or pan-preview simplification. Files
are atomically replaced only after successful encoding; directory exports require
a new target and commit the complete sequence. On success or failure the selected
frame is reapplied, and prior playback resumes if possible. Arbitrary callback
side effects outside the reproducible frame cannot be restored. Exceptions do
not overwrite existing final files; encoder.abort cleans up owned processes.

GIF is RGB/palette output; antialiasing/color quantization differ from PNG. Its
frame delays are multiples of 10 ms; identical consecutive images may coalesce
while preserving their total duration. The default GIF loops; GUI repeat and GIF
loop metadata are separate contracts in this initial writer. Budgets: 1..10000
playback frames; 2 million bound scalar values; 8 million output pixels per frame;
GIF at most 1000 frames/100 million total pixels. PNG core export requires Pillow.

A custom FrameWriter implements `setup(path, width, height, fps, count)`,
`write_frame(Pillow_image)`, `finish()`, `abort()`. It must consume/copy the image
synchronously; Azimlib closes it after each call. FFMpegWriter uses a fixed
argument list, raw RGBA stdin, no shell, libx264 MP4, even dimensions, and bounded
finish/cleanup waits. It checks executable availability; no actual installed
video codec/build is validated by this batch. Encoder/codecs keep their own
licenses and possible patent obligations; see [third-party notices](../THIRD_PARTY_LICENSES.md).

## Regional and multipage atlas

```python
regions = [
    azl.Region("Southeast", (-54, -40, -26, -14)),
    azl.Region("North", (-74, -45, -13, 6)),
]
def draw(ax, region):
    ax.map("brazil", facecolor="white", edgecolor="black", linewidth=0.5)
    ax.set_title(region.name)

atlas = azl.Atlas.from_regions(regions, draw, style="default")
atlas.savefig("outputs/atlas.pdf")
atlas.save_pages("outputs/atlas-svg", format="svg")
```

Region extent is west,east,south,north; cylindrical crossings are supported.
A common projection/style/size is used for all pages and the region limits are
reapplied after the draw callback. No implicit basemap, grid or decorations are
added. The Figures remain editable; `Atlas([fig1, fig2], labels=...)` also accepts
existing compositions, including multiple maps and mixed 2D/3D on each page.
PNG/SVG/PDF sequences and own multipage PDF are supported; no PDF merger is used.

```python
from azimlib.backends.backend_pdf import PdfPages
with PdfPages("outputs/pages.pdf") as pdf:
    pdf.savefig(fig)
    # Edit the figure and capture a second page:
    ani.seek(1)
    pdf.savefig(fig)
```

PdfPages captures each page's own PDF objects at savefig time, preserving image
streams/vector text outlines/physical page size/material and DejaVu notices.
The final writer rebases only its own object dictionaries; binary streams are
unchanged. It does not parse/import arbitrary third-party PDF files. Context
failure leaves a previous target unchanged. Empty PdfPages writes nothing.
Budgets: 256 pages and 64 MB of captured PDF objects. Font outlines are not
searchable text, as in the existing single-page writer.

[Reproducible climate/population/region example](../examples/temporal_atlas.py),
[gallery](_static/temporal/README.md) and [contracts](../tests/test_temporal.py).
Only synthetic temporal fields are bundled; optional geographic data/font terms
remain applicable. Historical stage proofs retain their original hashes; the
current installed runtime is checked by `audit_temporal.py`.
