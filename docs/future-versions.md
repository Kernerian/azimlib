# Future proposals: terrestrial sky, planetary maps and orbits

Planning update (2026-10-18): the cumulative **0.5.0 proposal now has 19 fronts**:
the ten planetary foundations are retained in full and nine thematic/editorial
fronts use the same Body-aware Artists. Read the
[consolidated proposal](proposal-0.5.md) and
[development checklist](release-plan-0.5.md). Phase A now has a limited
[implemented foundation](foundation-0.5.md), followed by the bounded
[Phase B surfaces](surfaces-0.5.md); the remaining proposal is future work.
Earlier release documents and the v0.4.0
tag/distributions remain immutable. Below, earlier development descriptions are
historical context, not current publication status. 0.4.0 is now published;
its separate operational receipt records 108 active completed and four deferred.

Except for the documented Phase A/B subsets, these are future requirements, not
implemented features, release dates or frozen public API names. The terrestrial Sun/Moon requirements below are now included in
the [combined 0.4.0 implementation checklist](release-progress-0.4.md), alongside
GPU/volumes, large OSM PBF, CRS/grids, global topology, geocoding/routing and
TeX/complex shaping reserved by 0.3.0. That checklist is the single source of
0.4 inventory counts, explicit deferments and delivery/revalidation dependencies. Beyond Earth (0.5) and Orbits (0.6)
retain their sequence in the [roadmap](roadmap.md); the 0.5 foundation does not
claim the complete planetary/editorial scope.

## 0.4 proposal — terrestrial Sun and Moon

- Own scene objects for Sun/Moon; manual solar azimuth/elevation and positions
  computed from explicit UTC instant, observer longitude/latitude/elevation.
- Solar lighting of 3D terrain/buildings, incidence, physically defined shadows
  and temporal shadow animation. Apparent daily/seasonal paths, sunrise/sunset,
  subsolar point, day/night terminator, solstices/equinoxes.
- Moon position, Earth-relative orbit, temporal playback and 3D Earth–Moon view;
  sublunar point and phases from Sun–Earth–Moon illumination geometry.
- Eclipses only where spatial/temporal precision and extended-source/occluder
  geometry justify them; a decorative overlap must not be advertised as prediction.
- Initial scope remains terrestrial geography, not generic solar-system simulation.

Acceptance requires declared ephemeris/model accuracy, validity dates, UTC/time
scale conversion, reference frame, coordinate units and observer/refraction
assumptions. Validate against independent authoritative fixtures whose source and
license are recorded. Renderer light vectors alone do not establish solar/lunar
positions, shadows or reliable eclipse timing. The independently implemented
[solar](solar-0.4.md) and [lunar](lunar-0.4.md) bounded models now exist, together
with [local physical shadows and synthetic finite-source geometry](lighting-0.4.md).
Real eclipse certification remains deferred under 13.06–13.07. Centers pass
the later frozen corpus; boundaries and reference/precision obligations remain
unresolved. [Observed evidence](observed-validation-0.4.md), [rescope](deferred-gates-0.4.md).

## 0.5 proposal — Beyond Earth cartography

The original planetary requirements below remain intact. The consolidated
proposal numbers them as fronts 1–10; fronts 11–19 extend the same cartographic
language for atlas, historical, economic, geological, educational, scientific
and exploratory maps on Earth and other bodies. There is no parallel historical
plotting API or desktop GIS/editor scope.

- Public body model: name/identity, size/shape, sphere/ellipsoid/triaxial model,
  prime meridian, axes/orientation and coordinate conventions. Earth becomes a
  preset; initial candidates Moon, Mars, Venus and Mercury. Extensible to moons,
  dwarf planets/asteroids and explicitly supplied irregular meshes.
- Planetocentric versus planetographic coordinates, longitude conventions,
  body-specific global/polar projections, geodesy (distance, azimuth, routes,
  lengths, area), physical units and surface elevation profiles between points.
- Extraterrestrial DEMs, orbital georeferenced imagery/mosaics, terrain textures,
  2D/3D relief, hillshade, vertical exaggeration and geological legends/features:
  craters, volcanoes, mountains, canyons, maria, caps, faults and named regions.
- Extend illumination/terminators/incidence from 0.4; atmospheric models only with
  declared data/physics. Compare worlds in a Figure with explicit physical or
  normalized visual scales; whole body → region → feature → local terrain.
- Unwrapped global maps; irregular-mesh unwrap remains separate research work.
- Landing sites, rover tracks/waypoints/explored regions and temporal seasonal
  caps, dust storms and illumination when appropriate data are supplied.
- Existing scatter/line/raster/terrain/labels/scales/geojson operate on the active
  body; no second parallel plotting library. Earth defaults retain compatibility.

Acceptance requires authoritative body constants, datum/epoch/frame identifiers,
units and source licensing. Triaxial/irregular geodesics, projection inverses and
area require their own numerical limits; an Earth formula with a new radius is
not automatically a correct irregular-body implementation.

### Added thematic/editorial fronts 11–19

11. Georeferenced native/vector/custom SVG/PNG/user symbols, categories,
    visual/map units, anchoring, rotation, clipping, priorities, labels and legends.
12. Independent thematic Polygon/MultiPolygon regions, patterns/masks/overlap,
    antimeridian, and explicit binary/discrete/stepped/appropriate-gradient modes;
    no automatic historical heatmaps or inferred probability.
13. Editorial, geodesic and graph routes, waypoints, Bézier/splines/explicit paths,
    directional arrows, flow widths, repeated symbols and path labels; preserve
    scientific geometry and keep physical orbital trajectories in 0.6.0.
14. Multiple Axes-compatible insets/locators, independent bodies/projections/views,
    geographical footprints, focus masks, connectors and optional synchronization.
15. Full programmatic editorial composition: mixed sectional legends, titles,
    subtitles, notes/sources, orientation/scale, frames/neatlines and page layout.
16. Advanced point/area/line/curved labels, halos/outlines/backgrounds, callouts,
    leader lines, collisions/priorities/overrides, scale rules and international shaping.
17. Compatible Artist/Layer groups: visibility, zorder, clip/style/legend controls,
    safe reuse across layouts/insets and existing interactive lifecycle.
18. Optional extensible atlas/historical/political/physical/scientific/geological/
    planetary exploration themes, with granular API preserved and no embedded data.
19. PNG/SVG/PDF-as-supported editorial exports, vectors where possible, explicit
    font/outline/raster fallbacks, physical dimensions/DPI and three-OS validation.

Future acceptance includes a synthetic/licensed historical trade atlas page and
a Mars exploration page using the same primitives, plus lunar/venusian and
cross-world cases. The atlas case reproduces a cartographic structure, not
protected assets from a reference illustration. Full contracts, architecture
reuse, dependencies, research risks and implementation phases are in the
[consolidated proposal](proposal-0.5.md). Only the Phase A/B subsets linked above
is implemented; remaining capabilities are future work.

## 0.6 proposal — Orbits and spatial visualization

- Scientific 2D/3D solar-system scenes: Sun, planets, moons, dwarf planets,
  asteroids/comets; explicit hierarchical objects/referentials.
- Keplerian orbit elements: semimajor axis, eccentricity, inclination, ascending
  node, periapsis argument and anomaly/epoch; finite temporal updates/play/pause/
  slider/speed/steps/animation/export. Specify elliptical/hyperbolic/parabolic
  domains and precision rather than treating every conic as an ellipse.
- Heliocentric/barycentric/geocentric/body-centric reference frames; changing
  center must transform the whole scene consistently. Ecliptic/orbital planes,
  inclination, perihelion/aphelion/nodes and past/present/future tracks.
- Data-supplied spacecraft trajectories, flybys/encounters and comparisons;
  no implicit mission optimization or operational navigation.
- Explicit physical versus visual scales/exaggeration for both distance and size;
  asteroid/Kuiper belts and trans-Neptunian objects when licensed data permit.
- Geometric lighting, mutual shadows, alignments, eclipses/simple occultations
  with precision limitations; spatial camera orbit/pan/zoom/follow/focus/reset.
- Picking exposes name/position/distance/period/velocity/elements when valid.
  Possible high-level APIs include time, focus, orbits, bodies and trajectories;
  names such as `space3d`/`solar_system` are proposals, not reserved promises.
- No initial promise of high-accuracy N-body, professional full propagators,
  maneuver planning, transfer optimization or operational astrodynamics.

## Shared architecture and sequencing

The sequence is terrestrial sky → body-general cartography → orbit/reference
connections. Adopt compatible internal body/frame/unit/time abstractions before
0.4 creates Earth/Moon objects, then stabilize the public Body interface in 0.5.
0.6 must use the same bodies and scene/Artist/picking/temporal/export mechanisms,
not parallel representations of planets. Current 3D/temporal APIs remain bounded.
Celestial work complements urban/cartographic maintenance; it does not replace it.

## Approved development sequence after the 0.4 rescope

0.4.1 is reserved for compatible fixes/refinements and the full-planet trial
only if infrastructure permits it. No scientific-gate closure is promised.
0.5.0 remains Planetary Cartography / Beyond Earth as specified above; deep
renderer/science foundations may support it, but global eclipse certification
is not an automatic prerequisite. 0.6.0 remains Orbits. Experimental scientific
APIs are promoted only with adequate evidence, regardless of version number.
Original 2.08/9.08/13.06/13.07 IDs, criteria and failures remain traceable in
the [deferred register](deferred-gates-0.4.md); no item was erased or marked passed.
