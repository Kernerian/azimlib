[![Tests](https://github.com/Kernerian/azimlib/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/Kernerian/azimlib/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://github.com/Kernerian/azimlib/blob/main/pyproject.toml)
[![Original code license](https://img.shields.io/badge/original_code-BSD--3--Clause-green)](https://github.com/Kernerian/azimlib/blob/main/LICENSE)
[![Contributions](https://img.shields.io/badge/contributions-welcome-238b98)](https://github.com/Kernerian/azimlib/blob/main/CONTRIBUTING.md)

![Azimlib](https://raw.githubusercontent.com/Kernerian/azimlib/main/docs/_static/branding/azimlib-wordmark.png)

**Independent cartography in Python, with a familiar plotting API.**

Build maps from geographic data, compose scientific figures, and explore them
in an interactive viewer. Azimlib owns its geometry, projections, coordinate
transformations, map layers, layout and rendering. Matplotlib and other GIS
engines are not runtime dependencies.

[Getting started](https://github.com/Kernerian/azimlib/blob/main/docs/getting-started.md) ·
[API reference](https://github.com/Kernerian/azimlib/blob/main/docs/api.md) ·
[Examples](https://github.com/Kernerian/azimlib/tree/main/examples) ·
[Compatibility](https://github.com/Kernerian/azimlib/blob/main/docs/compatibility.md)

![Maps rendered by Azimlib: Brazil, a thematic map, an orthographic globe and synthetic terrain](https://raw.githubusercontent.com/Kernerian/azimlib/main/docs/_static/showcase/overview.png)

The examples above use Azimlib's own renderer. Boundaries and rivers are from
Natural Earth; thematic values, terrain and vectors are synthetic. See the
[reproducible showcase](https://github.com/Kernerian/azimlib/blob/main/docs/showcase.md).

## Install

Requires **Python 3.10 or newer**. Version 0.2.0 is being prepared for its first
PyPI publication. Once available, choose the output you need:

```bash
python -m pip install azimlib           # SVG and portable HTML; no dependencies
python -m pip install "azimlib[png]"    # PNG export
python -m pip install "azimlib[gui]"    # Interactive desktop viewer + PNG
```

Until the PyPI release is available, install directly from the source:

```bash
git clone https://github.com/Kernerian/azimlib.git
cd azimlib
python -m pip install ".[gui]"
```

The desktop viewer requires Tk, normally included with official Windows and
macOS Python installations; on Linux it may need an operating-system package.
Pillow, aggdraw and NumPy provide low-level raster support. Optional
`azimlib[accelerate]` uses NumPy/Numba to compile Azimlib's own coverage kernel.
No external cartography library is required for any of these installations.

## Your first map

Both import styles expose the familiar figure/axes workflow:

```python
import azimlib as azl
# Or: import azimlib.pyplot as plt

fig, ax = azl.subplots(figsize=(8, 9), projection="mercator")
ax.map("brazil", facecolor="white", edgecolor="black", linewidth=0.8)
ax.states(edgecolor="#777777", linewidth=0.4)
ax.rivers(color="#237f96", linewidth=0.8, label="Rivers")
ax.scatter(
    lon=[-46.63, -43.17], lat=[-23.55, -22.90],
    s=[40, 60], c="#c34968", label="Cities",
)
ax.set_title("Brazil")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.legend()
ax.scale_bar()
ax.north_arrow()

fig.savefig("brazil.svg")        # Static export; no viewer controls
fig.savefig("brazil.png", dpi=200)
azl.show()                       # Interactive desktop viewer
```

Longitude and latitude are geographic coordinates. Use
`subplot_kw={"projection": "mercator"}` if you prefer the Matplotlib-style
subplot configuration. A GeoJSON path, dictionary or feature collection can be
added with `ax.geojson(data)`.

`savefig()` writes a static PNG or SVG. `show()` opens the independent desktop
canvas with **Home, Back, Forward, Pan, Zoom, Subplots, Save** and cursor
coordinates. A separate portable HTML viewer is available with
`fig.show(backend="browser", path="map.html")`; it navigates an exported scene,
without a live Python connection.

## Add only the components you need

Grid, legend, colorbar, scale bar, north arrow, compass and overview map are
**optional**. There is no default minimap or grid. North arrow and compass are
separate components, and a legend has a title only when you provide one.

```python
ax.grid(linestyle="--", linewidth=0.5)
scale = ax.scale_bar()
scale.set_visible(False)
scale.set_visible(True)
ax.compass()
ax.overview(context="brazil")
fig.canvas.draw_idle()
```

Artists expose editing, visibility and removal controls. You can set limits,
change styles, edit labels and update scalar data while retaining the same
figure. See [components](https://github.com/Kernerian/azimlib/blob/main/docs/components.md)
and [Artist editing](https://github.com/Kernerian/azimlib/blob/main/docs/artist-scope-0.2.md).

## Thematic and scientific maps

```python
import azimlib.pyplot as plt
from azimlib import datasets

data = datasets.load("states", country="brazil")
values = list(range(len(data["features"])))  # Synthetic example values

fig, ax = plt.subplots(projection="mercator")
layer = ax.choropleth(data, values, cmap="viridis", bins=None)
bar = fig.colorbar(layer, ax=ax, orientation="horizontal", label="Example value")
ax.set_title("Values by state")
layer.set_clim(0, 30)
bar.set_label("Updated example value")
fig.savefig("thematic.svg")
```

| Build | With |
| --- | --- |
| Political and regional maps | Countries, states, boundaries, `ax.state("SP")` |
| Physical and hydrographic maps | Coastlines, rivers, lakes, geographic labels |
| Choropleths and categories | Feature styles, colormaps, norms, editable colorbars |
| Points and proportional bubbles | Scatter, markers, symbols, values mapped to size/color |
| Routes and vector fields | Styled lines, arrows, spherical routes, quiver |
| Density and scalar fields | Heatmaps, raster fields, isolines, hillshade |
| Atlases and regional focus | Subplots, GridSpec, mosaics, shared axes, insets/overviews |

Lines support widths, opacity, dashes, caps, joins and arrows; polygons support
per-feature styling and hatches. Text offers alignment, rotation, backgrounds
and halos. Layout includes tight/constrained modes, physical sizing and editable
ticks. Colorbars support horizontal/vertical placement, ticks, labels and norms.

The spherical projection implementations include equirectangular, Mercator,
orthographic, Lambert conformal conic, Albers equal area and Equal Earth.
An orthographic globe is a 2D projection, not a 3D terrain engine.

## Learn more

- [Tutorial and Matplotlib → Azimlib guide](https://github.com/Kernerian/azimlib/blob/main/docs/getting-started.md)
- [API reference](https://github.com/Kernerian/azimlib/blob/main/docs/api.md)
- [Maps and components gallery](https://github.com/Kernerian/azimlib/blob/main/docs/showcase.md)
- [Coordinate systems and datasets](https://github.com/Kernerian/azimlib/blob/main/docs/data.md)
- [Architecture](https://github.com/Kernerian/azimlib/blob/main/docs/architecture.md)
- [Roadmap](https://github.com/Kernerian/azimlib/blob/main/docs/roadmap.md) and [remaining work](https://github.com/Kernerian/azimlib/blob/main/docs/pending.md)
- [Changelog](https://github.com/Kernerian/azimlib/blob/main/CHANGELOG.md)

Azimlib 0.2.0 is an early independent cartography library, **not a complete
replacement for every Matplotlib API**. Read the
[compatibility boundaries](https://github.com/Kernerian/azimlib/blob/main/docs/compatibility.md)
before migrating. Detailed views can still require expensive rasterization.
Urban data workflows, more file formats, 3D and temporal visualization are
future work. Automated CI covers Windows, Linux and macOS; native human visual
acceptance currently covers Windows.

## Contribute and get help

Report bugs or ask questions through
[GitHub Issues](https://github.com/Kernerian/azimlib/issues). Include a minimal
example, Python/Azimlib versions and the relevant output format.
See the [contribution guide](https://github.com/Kernerian/azimlib/blob/main/CONTRIBUTING.md)
for local tests, data provenance and independent implementation requirements.
Please follow the [code of conduct](https://github.com/Kernerian/azimlib/blob/main/CODE_OF_CONDUCT.md).
Use the [security policy](https://github.com/Kernerian/azimlib/blob/main/SECURITY.md)
for sensitive vulnerability reports.

## License and provenance

Original code and visual compositions: **BSD 3-Clause**, copyright 2026
Kernerian. Bundled geographic data, fonts and palettes retain their own terms:
Natural Earth is public domain; DejaVu fonts retain their license; Viridis,
Plasma, Inferno and Magma tables are CC0; Blues retains ColorBrewer terms.
The default AZIM10 color sequence is independently selected.

This product includes color specifications and designs developed by Cynthia
Brewer (http://colorbrewer.org/).

See [LICENSE](https://github.com/Kernerian/azimlib/blob/main/LICENSE),
[third-party notices](https://github.com/Kernerian/azimlib/blob/main/THIRD_PARTY_LICENSES.md)
and [branding assets](https://github.com/Kernerian/azimlib/tree/main/docs/_static/branding).
The familiar API and navigation are implemented independently; Matplotlib
artwork and source code are not distributed as Azimlib's implementation.
