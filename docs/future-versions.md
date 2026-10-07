# Future proposals: terrestrial sky, planetary maps and orbits

These are **proposals for 0.4–0.6**, not implemented features, release dates or
frozen public API names. They extend the [existing roadmap](roadmap.md); GPU,
volumes, large OSM PBF, universal grid-based CRS, global overlay/topology,
geocoding/routing and TeX/complex shaping remain planned and are not displaced.
Scope must be revisited after 0.3 release evidence and maintenance feedback.

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
positions, shadows or reliable eclipse timing. No model/dataset is selected yet.

## 0.5 proposal — Beyond Earth cartography

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
