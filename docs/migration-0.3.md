# Moving to Azimlib 0.3

This guide describes **Azimlib 0.3.0**. To install the release when available on
[PyPI](https://pypi.org/project/azimlib/), use `pip install "azimlib==0.3.0"`.
See [API stability](api-stability.md) and [precise compatibility](compatibility.md).

## Familiar figure and Artist workflow

```python
import azimlib.pyplot as plt
# Equivalent figure workflow: import azimlib as azl
fig, ax = plt.subplots(figsize=(5, 4), projection="mercator")
ax.map("brazil", facecolor="#f3f5f6", linewidth=0.6)
route, = ax.plot([-50, -47, -43], [-25, -22, -20], "r--o", label="Synthetic route")
ax.set_xlabel("Longitude", labelpad=4)
ax.set_ylabel("Latitude", labelpad=4)
ax.set_title("Independent geographic plot")
ax.legend()
route.set_linewidth(1.2)
fig.savefig("migration-map.svg")
plt.close(fig)
```

`plot` receives longitude/latitude, not arbitrary categorical X/Y. Geographic
`set_extent` uses west/east/south/north in degrees with an explicit projection.
`scatter(s=...)` sizes are points squared; line widths/text sizes are points,
converted by DPI. A 2D orthographic globe is distinct from a 3D terrain scene.

## Static output and optional viewers

`fig.savefig(...)` produces static SVG/PNG/PDF; controls are not exported.
PNG requires Pillow. PDF uses our own vector writer (3D is explicitly embedded
raster); outlined text is not searchable text. `plt.show()` opens Tk, with
explicit Qt/live/notebook alternatives. `draw_idle` belongs to the GUI owner
thread. Offline HTML is a scene snapshot, not a general live Python callback.
See [viewer contracts](interaction.md) and [export limits](finishing.md).

## Opt-in components and units

Grid, legend, colorbar, scale bar, compass, north arrow and overview are optional.
Use returned Artists for editing, visibility/removal; compass and north arrow
are separate components. A legend title only exists if passed explicitly.

```python
import azimlib as azl
fig, ax = azl.subplots(figsize=(4, 3))
ax.set_extent((-55, -40, -30, -15))
image = ax.imshow([[1, 2], [3, 4]], extent=(-55, -40, -30, -15), origin="lower")
bar = fig.colorbar(image, ax=ax, orientation="horizontal", label="Synthetic value")
image.set_clim(0, 5)
bar.set_label("Updated value")
scale = ax.scale_bar()
scale.set_visible(False)
fig.savefig("migration-colors.svg")
azl.close(fig)
```

Replacing a norm resets automatic colorbar ticks; editing the same norm/clim
retains applicable custom settings. Missing data and masks are explicit.
`geojson` is not a GeoPandas object; readers return Azimlib-owned geometry/raster
models. [Format limits](formats.md), [CRS](geodesy.md) and [urban](urban.md) describe
supported variants and coordinate conventions. There are no implicit downloads.

## Animation and atlas

```python
import azimlib as azl
from azimlib.animation import FuncAnimation
from azimlib.backends.backend_pdf import PdfPages
fig, ax = azl.subplots(figsize=(4, 3))
ax.set_extent((-55, -40, -30, -15))
points = ax.scatter([-50, -45], [-25, -20], c=[1, 2])
series = azl.TemporalSeries([2000, 2010], [[1, 2], [3, 4]], unit="year")
binding = series.bind(points, scale="global")
movie = FuncAnimation(fig, lambda i: binding.apply(i), 2, autoplay=False)
movie.seek(1, draw=False)
with PdfPages("migration-atlas.pdf") as pages:
    pages.savefig(fig)
    movie.seek(0, draw=False)
    pages.savefig(fig)
movie.close()
azl.close(fig)
```

The finite animation interface does not implement infinite frame generators,
all Matplotlib writers or blitting. Native timers run on Tk/Qt's owner thread;
manual/headless exports remain independent. GIF requires Pillow; FFmpeg is an
explicit separate executable, not bundled software. [Temporal guide](temporal.md).

3D APIs are experimental. Coordinates, height/base and vertical exaggeration
have explicit metric units; no global datum transform, GPU, transparent surface
sorting or volumetric renderer is promised. [3D guide](terrain3d.md).
