# Local 0.4 development scope notice

The published version remains 0.3.0. [0.4 rescope](deferred-gates-0.4.md):
107 completed, four deferred, one pending item (14.08: final acceptance and publication).
GPU and scientific eclipses are experimental; PBF validation is regional.
[Observed results](observed-validation-0.4.md), [current checklist](release-progress-0.4.md).
This candidate documentation has not been deployed to a public site.

# Azimlib documentation

**Independent cartography in Python.** This is the **unpublished 0.4.0 candidate documentation**.
Published files and availability are listed on [PyPI](https://pypi.org/project/azimlib/).
Each development guide states its scope. [Version policy](api-stability.md).

![Azimlib wordmark](_static/branding/azimlib-wordmark.png)

## Start here

- [First maps, installs and units](getting-started.md)
- [Migration from 0.3 to 0.4](migration-0.4.md)
- [Matplotlib-style API compatibility and differences](compatibility.md)
- [Public signatures](api.md)
- [Integrated 0.4 gallery](gallery-0.4.md)

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
- [Verified 0.3.0 publication and hashes](release-publication-0.3.0.md)
- [Release gates and evidence](release-progress-0.3.md)
- [Combined 0.4.0 implementation checklist](release-progress-0.4.md)
- [0.4 development foundation: units, frames and time](foundation-0.4.md)
- [0.4 development OSM PBF: streaming, extraction and budgets](osm-pbf.md)
- [Full-planet acceptance procedure — 2.08 pending](planet-trial.md)
- [0.4 development CRS catalog, XYZ and datum pipelines](crs-0.4.md)
- [0.4 development datum grids, optional official models and validation](datum-grids.md)
- [0.4 development own planar/spherical topology and global overlay](topology-0.4.md)
- [0.4 development local geocoding, addresses and reverse search](geocoding-0.4.md)
- [0.4 development own road graphs, routing and playback](routing-0.4.md)
- [0.4 development international text, fonts and shared shaping](international-text-0.4.md)
- [0.4 complex text: human visual review 7.08](text-review-0.4.md)
- [0.4 real TeX: explicit engines, metrics and exports](tex-0.4.md)
- [0.4 optional GPU: contexts, shared styles, textures and performance](gpu-0.4.md)
- [0.4 volumes: streaming fields, cloud absorption, slices and isosurfaces](volumes-0.4.md)
- [0.4 terrestrial Sun: explicit clocks, positions, events and sky paths](solar-0.4.md)
- [0.4 terrestrial Moon: positions, phases, trajectories and Earth–Moon 3D](lunar-0.4.md)
- [0.4 physical shadows and finite-source geometry; precise eclipses pending](lighting-0.4.md)
- [0.4 cumulative integration, coverage and delivery gates](integration-0.4.md)
- [0.4 original integration gallery — unreleased](gallery-0.4.md)
- [0.4 migration from the stable API](migration-0.4.md)
- [0.4 benchmark consolidation and limits](integration-benchmarks-0.4.md)
- [0.4 draft release notes — unreleased](release-notes-0.4.0.md)
- [Roadmap](roadmap.md) and [future proposals](future-versions.md)
- [Building/versioning the documentation](documentation-site.md)

The cartographic core and renderers are Azimlib's own implementations. API
familiarity does not mean importing Matplotlib or delegating geographic work.
