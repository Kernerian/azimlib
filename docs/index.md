# Azimlib documentation

**Independent cartography in Python.** The stable published package is 0.2.0;
this documentation checkout includes the **0.3.0 release candidate**, which is not yet published.
Each development guide states its scope. [Version policy](api-stability.md).

![Azimlib wordmark](_static/branding/azimlib-wordmark.png)

## Start here

- [First maps, installs and units](getting-started.md)
- [Migration to the 0.3 development API](migration-0.3.md)
- [Matplotlib-style API compatibility and differences](compatibility.md)
- [Public signatures](api.md)
- [Integrated 0.3 gallery](gallery-0.3.md)

## Geographic and scientific workflows

| Goal | Guide |
| --- | --- |
| Cities, streets, neighborhoods, buildings | [Urban layers](urban.md) |
| GeoJSON, CSV, SHP/DBF, KML, OSM XML and raster | [Formats](formats.md), [optional data](optional-data.md) |
| Ellipsoids, UTM, projections and seams | [Geodesy](geodesy.md) |
| Figure/layout/Transforms/Artists | [Composition](transforms-composition.md), [editing](artists.md) |
| Labels, symbols, hatches and PDF | [Finishing](finishing.md) |
| Images, contours, density, flows and terrain | [Scientific 2D](scientific-2d.md) |
| Optional widgets, Tk/Qt/live/notebook | [Interaction](interaction.md) |
| Experimental 3D terrain and extrusions | [3D](terrain3d.md) |
| Temporal maps, animation and regional pages | [Time and atlas](temporal.md) |

## Distribution and provenance

- [Third-party material boundaries](../THIRD_PARTY_LICENSES.md)
- [Dependency licensing](dependencies.md)
- [Release gates and evidence](release-progress-0.3.md)
- [Roadmap](roadmap.md) and [future proposals](future-versions.md)
- [Building/versioning the documentation](documentation-site.md)

The cartographic core and renderers are Azimlib's own implementations. API
familiarity does not mean importing Matplotlib or delegating geographic work.
