# Terrestrial Sun — 0.4 development

This is an original, bounded low-precision solar implementation, not a general
ephemeris or a navigation/surveying service. Stable PyPI metadata remains 0.3.0;
these APIs describe the local development tree.

## Model, provenance and limits

`azim-usno-approx-v1` independently evaluates the published
[USNO approximate solar equations](https://aa.usno.navy.mil/faq/sun_approx): mean
anomaly/longitude, two periodic longitude terms, changing obliquity and orbital
distance. No USNO/JPL/NOAA implementation, ephemeris library, kernel, leap table
or EOP file is embedded. The equations are mathematical model definitions;
source code was independently written. USNO identifies its public information
as reusable subject to stated exceptions and requests credit in its
[notice](https://aa.usno.navy.mil/about/PrivacyNotice).

Supported UTC years are **1972–2100**, inclusive, at terrestrial WGS84 observers
with heights from −10,000 to 100,000 metres. The API rejects naive datetimes,
pre-1972 UTC, leap-second labels and extrapolation past the supported years.
The published model is approximately one arcminute over a wider interval;
Azimlib adopts a conservative **0.05° model allowance**, plus Earth-rotation
uncertainty `360.98564736629 / 86400 × offset_uncertainty_seconds`.
This is a declared engineering budget, not a statistical confidence interval
or a proof for every instant. It excludes weather, terrain horizons, clock
errors exceeding supplied bounds and arbitrary observer-position errors.
Distance validation uses a relative tolerance of **0.0003**.

The solar longitude includes the approximate aberration in the published
model. `aberration=False` removes its leading 20.49 arcsecond/distance term.
There is no full nutation/precession/relativity or light-time iteration.
RA/declination use the approximate date equator; Earth-fixed direction uses
mean sidereal rotation on UT1. Calling it apparent does not promise an exact
IAU/GCRS/CIRS apparent frame. `parallax=True` translates the finite geocentric
position by the observer's WGS84 ECEF position before computing ENU angles;
`False` uses the parallel geocentric direction.

## Explicit clocks and angles

The default `SolarModel()` is strict: supply `SolarTimeOffsets` for **both**
TAI−UTC (TT = TAI + 32.184 s) and UT1−UTC over an explicit validity interval.
An offsets callable may select intervals, including leap boundaries. TT drives
the orbital terms and UT1 the sidereal rotation. Provenance and an uncertainty
bound are required by the existing [time contract](foundation-0.4.md).
No time corrections are downloaded or inferred.

For illustrations, `SolarModel(time_policy="utc-approx")` explicitly uses
UTC as TT and UT1, with a one-second rotation allowance. Supplying offsets to
this policy fails rather than ignoring them. This approximation remains part
of the returned state and is unsuitable for precision timing.

```python
from datetime import datetime, timezone
import azimlib as azl                    # azimlib.pyplot also works

model = azl.SolarModel(time_policy="utc-approx")
observer = azl.SolarObserver(-46.63, -23.55, height=0)
sun = model.position(datetime(2025, 6, 21, 12, tzinfo=timezone.utc), observer)
print(sun.azimuth, sun.elevation, sun.subsolar)
manual = azl.SunDirection(azimuth=90, elevation=30, observer=observer)
```

Angles are degrees; longitude is east-positive, latitude north-positive.
Azimuth increases clockwise from north; elevation is above the local tangent
plane. ENU unit vectors mean east/north/up. Distances and observer height are
metres. `SunDirection` is manual: no date, distance, terminator or physical
solar ephemeris is invented. A manual geographic point requires an observer.

`SunPosition.fixed` is a frame-tagged Earth-fixed metre vector.
`lighting_direction` is a normalized observer-to-Sun ENU vector before optical
refraction, using the selected parallax/aberration model. This provides the
shared geometry for stage 13; it does not itself implement terrain shadows or
eclipses. `fixed_direction` is the geocentric unit vector.

## Optical refraction and events

Refraction is disabled by default. `SolarRefraction(pressure_hpa=1010,
temperature_c=10)` independently evaluates the piecewise angular approximation
described by [NOAA](https://gml.noaa.gov/grad/solcalc/calcdetails.html).
It is an average optical estimate, not observed atmosphere or ray tracing.
It is zero below −1° and above 85°; the low-altitude cutoff is explicit and
not a continuous atmospheric extrapolation. Zero pressure disables it.
`geometric_elevation` and `refraction_degrees` remain separately inspectable;
the lighting vector is never bent by refraction.

`model.events(date, observer, zone=timezone.utc)` returns all rises, sets and
upper meridian transits within the civil day, plus first-event convenience
properties. Timezones are explicit; DST days use their actual UTC duration.
The default geometric center threshold is −5/6° plus `observer.horizon`, an
average upper-limb/refraction convention consistent with
[event definitions](https://aa.usno.navy.mil/faq/RST_defs).
No second refraction correction is applied. Height-dependent horizon dip,
weather and variable obstacles are **not inferred**; supply the desired center
threshold/horizon explicitly. A positive horizon delays rise and advances set.

Roots use bounded ten-minute bracketing and ≤0.25-second numeric refinement;
numeric convergence is not physical accuracy. The independent normal-latitude
event validation tolerance is 120 seconds. Near tangency, timing uncertainty
grows as angular budget / elevation rate; no universal polar timing accuracy
is asserted. Status is `crossings`, `always_above`, `always_below` or
`grazing_or_uncertain`. The latter is not silently converted to a fabricated
sunrise. Very short events within an unsampled ten-minute extremum can remain
unresolved; this is not an exhaustive grazing-event solver. At exact poles,
the meridian is undefined, so transits are absent. Their azimuth remains the
explicit observer-frame convention, not a unique physical north direction.
An event interval must lie wholly within model/time-correction validity.

`model.seasons(year)` solves solar ecliptic longitude 0°, 90°, 180°, 270°.
These approximate instants are not high-precision almanac entries: the angular
budget corresponds to roughly two hours of seasonal timing, not subsecond
physical precision despite numeric root refinement.

## Optional Artists, projections and time

```python
fig, ax = azl.subplots(figsize=(8, 4))
ax.map("world", facecolor="#e6ebee", linewidth=0.3)
night = ax.nightshade(sun, model=model, step=3, alpha=0.25)
boundary = ax.solar_terminator(sun, model=model)
marker = ax.sun(sun, model=model, annotation="Subsolar point")
marker.set_picker(4)
marker.set_time(datetime(2025, 6, 21, 15, tzinfo=timezone.utc))
marker.set_visible(False)
fig.savefig("solar.svg")
```

No solar component is inserted by default. Handles support visibility, removal
and the existing style/picking contracts. Marker labels use a white outline,
not a compulsory background box. `set_position` prevalidates observer identity
before changing geometry; `set_time` uses the explicitly stored model/offsets.
Attaching a precomputed state alone does not silently opt into approximate UTC
for future edits. `set_manual` exists on the geographic marker.

The subsolar point is geocentric on the model sphere, not a claim about an
ellipsoidal terrain zenith. The terminator is the perpendicular great circle
for parallel solar rays, using the own projection and antimeridian pipeline.
`night_region()` returns an analytic spherical hemisphere. `nightshade` is a
cell-center approximation at explicit 1–30° geographic resolution: its boundary
can differ from the continuous terminator by about one cell diagonal. Cells
without visible orthographic area are excluded analytically. This does not
close the separate general topology/visual acceptance gate in 14.05.

For apparent daily/seasonal trajectories, `model.path(instants, observer)`
requires 2–4096 strictly increasing instants. `ax.sun_path(path)` on 3D axes
draws an ENU ribbon; `ax.sun(state)` draws a round planar sky marker. Both use
the existing 3D camera/depth/export system and the observer's `LocalFrame`
(its origin latitude must be within ±89°). **visual_radius** and marker/ribbon
sizes are explicit illustrative metre coordinates centered on the diagram's
local origin, not the real Sun distance, diameter or observer-height geometry.
They must not be reused as physical occluders for eclipse calculations.

`TemporalSeries(times, states).bind(marker)` works for markers, nightshade and
3D sky markers, retaining the Artist and camera. Every frame is validated for
observer identity; dated frames must match their calculated instants. These
are direction bindings, so scalar normalization policies are rejected.
`FuncAnimation` supplies existing playback and PNG/GIF exports; map SVG/PDF
remain vector, while 3D SVG/PDF use their established raster-layer policy.
`show()` remains separate and uses existing optional native backends.

## Reproducible validation and reference boundaries

- `examples/solar_maps.py`: world/globe and seasonal sky; no external ephemeris.
- `tests/test_solar_040.py`: time contracts, manual frames, parallax/refraction,
  root residuals, polar/grazing status, projection/limb, editing, picking and time.
- `tools/validate_solar.py --references EXTERNAL_DIRECTORY --fetch --report REPORT.json`
  makes 13 bounded sequential public Horizons requests. Raw responses stay
  outside the repository; omit `--fetch` to repeat from identical inputs.
  Reports record exact queries, signature, SHA-256 and original error statistics.
  The predetermined limits are 0.06° angular, 0.0003 relative range and 120 s
  for the tested event crossings/transits. Inputs cover 1972–2100, four seasons,
  six observer sites, 2,500 m height, the dateline and both exact poles.
- [Local validation report](solar-validation-0.4.json).

[JPL Horizons](https://ssd.jpl.nasa.gov/horizons/manual.html) supplies independent
reference calculations only. Its [terms](https://ssd.jpl.nasa.gov/faq.html)
are separate from Azimlib's BSD license: **no raw Horizons responses, reference
numerical tables, kernels or JPL code are distributed**. Validation uses an
approximate date frame versus Horizons' fuller apparent frame; polar azimuth
and meridian are excluded because their conventions are not equivalent, while
polar RA/declination, elevation and no-rise/no-set status are checked. Published
reports contain Azimlib's own analysis and source hashes/queries, not a copied
ephemeris. General font/dataset/export notices remain applicable.
