# Terrestrial Moon and Earth–Moon scenes — 0.4 development

Independent standard-library numerics; no ephemeris engine, kernel, network or
downloaded table at runtime. These APIs describe development sources; stable
metadata stays 0.3.0.

## Model, provenance and precision

`azim-almanac-short-v1` evaluates the short Almanac lunar series reproduced in
equations **1–4**, pages 176–177 of David G. Simpson, *An Alternative Lunar
Ephemeris Model for On-Board Flight Software Use*, NASA GSFC, 1999 Flight
Mechanics Symposium. The [NTRS record](https://ntrs.nasa.gov/citations/19990040527)
identifies it as a US government work permitting public use. NTRS dates the
record 1998; the [paper](https://caps.gsfc.nasa.gov/simpson/pubs/slunar.pdf)
bears the 1999 symposium header. This uses the review's **mean-of-date** series,
not the paper's later direct J2000 alternative. See
[model provenance](lunar-model-0.4.json). No third-party code or paper text is
bundled. Model definitions are not claimed as exclusive Azimlib property.

Longitude has six periodic terms, latitude four, horizontal parallax four.
Distance uses the model's historical IAU-1976 radius **6,378,140 m**, distinct
from the WGS84 observer ellipsoid. Ecliptic-of-date coordinates rotate by date
obliquity `23.439291111 - 0.0130042 T` degrees and mean sidereal angle on UT1.
This approximate date equator is not exact GCRS/CIRS, J2000 or ITRF.

Validity: **1972–2100 UTC**, WGS84 observer heights −10,000…100,000 m.
Engineering allowances: **0.5°** plus `0.0043 × clock_uncertainty_seconds`, and
**5,000 km** in range. These conservative budgets are not confidence intervals
or proofs for every instant. There is no full lunar theory, light-time
iteration, stellar aberration, nutation, polar motion, lunar libration,
surface texture or perturbation integration. Eclipse contact/timing requires
a separately validated accuracy contract in stage 13.

## Position, clocks and corrections

```python
from datetime import datetime, timezone
import azimlib as azl

model = azl.LunarModel(time_policy="utc-approx")
observer = azl.SolarObserver(-46.63, -23.55, height=0)
moon = model.position(datetime(2025, 1, 7, 12, tzinfo=timezone.utc), observer)
print(moon.sublunar, moon.distance_m, moon.topocentric_distance_m)
print(moon.azimuth, moon.elevation, moon.illuminated_fraction)
```

Default `LunarModel()` requires explicit `SolarTimeOffsets` for TT and UT1,
with source, validity and uncertainty. TT drives orbital terms; UT1 drives
Earth rotation. An offsets callable is evaluated once per state and shared
with its solar state. No leap/EOP values are guessed/downloaded. Explicit
`utc-approx` uses UTC for both scales and rejects supplied corrections.
Naive dates, leap-second labels and extrapolation outside validity fail.

Angles are degrees; longitude east-positive, latitude north-positive, azimuth
clockwise from north, elevation above the tangent plane. Distances, heights
and tagged Earth-fixed XYZ are **metres**. Geocentric `right_ascension`,
`declination`, `distance_m` remain separate from `topocentric_*` values.
`parallax=True` subtracts WGS84 observer XYZ before angles and slant range;
`False` uses geocentric parallel directions and geocentric phase geometry.
Optional `SolarRefraction` affects reported optical elevation only, never
positions, phases or 3D light. Exact poles have conventional azimuths.

`sublunar` plots directional longitude `RA - GMST` and geocentric declination;
it is not an exact geodetic ellipsoid intersection or ellipsoidal zenith
footpoint. Manual input requires an observer and finite range:
`MoonDirection(90, 30, distance_m=384e6, observer=observer)`. ENU rotates and
translates to Earth-fixed XYZ; no date, phase or Sun is inferred for it.

## Optional Artists and playback

```python
fig, ax = azl.subplots()
ax.map("world")
handle = ax.moon(moon, model=model, annotation="Sublunar point")
handle.set_picker(4)
handle.set_visible(False)
handle.set_visible(True)
handle.set_annotation("Moon")
handle.set_time(datetime(2025, 1, 8, 12, tzinfo=timezone.utc))
fig.savefig("moon.svg")
```

Map picking retains feature identity, units, UTC, model, geocentric distance
and phase metadata. Labels use existing halo/text styles. Observer changes
fail atomically. Date setters require a configured clock/model; manual edits
preserve observer identity.

`model.path(instants, observer=None)` accepts 2…4096 strictly increasing dates.
`ax.moon_path(path)` draws a geographic groundtrack, or a metre-width 3D ribbon
through calculated **Earth-fixed** XYZ. This rotating-frame trajectory is not
a Keplerian/inertial orbit. Lines interpolate samples visually, without orbit
propagation. `TemporalSeries(times, positions).bind(handle)` prevalidates
dates and states, keeps the same Artist and preserves map extent/camera.
Scalar normalization options do not apply to lunar states.

## Earth–Moon 3D and illuminated orientation

```python
fig, ax = azl.subplots(subplot_kw={"projection": "3d"})
system = ax.earth_moon(moon)       # physical radii/distances by default
system.set_scales(distance_scale=0.1, moon_radius_scale=3)
ax.set_title("Distance ×0.1; Moon radius ×3")
ax.set_axis_off()
fig.savefig("earth-moon.png")
```

`ax.moon(moon)` in 3D draws only the Moon; `ax.earth_moon(moon)` composes both
bodies using the existing camera/depth painter, CPU/GPU and PNG/SVG/PDF paths.
Earth is an oblate WGS84 ellipsoid; Moon is a sphere of mean radius
**1,737,400 m** ([NASA factsheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html)).
Meshes are opaque and flat-shaded, with optional body colors, shading and
ambient fraction; no cast shadows/eclipses or geographic textures are implied.
Global bodies reject mixed local terrain frames and vertical exaggeration
other than one. Bounded visual scales reject intersecting body volumes.

`physical_centers` retains calculated metres; `display_centers` uses the
declared distance multiplier. Radius scaling changes only the drawn Moon.
Neither changes phases or lighting vectors. A free camera can show a different
illuminated fraction from the Earth observer: compare the numerical fraction
with a view from Earth, not an arbitrary viewpoint. Camera magnification is
not an angular-size measurement.

Phase angle uses **Moon→Sun** and **Moon→observer** vectors; illuminated
fraction is `(1 + cos(phase_angle))/2`. The existing solar model runs on the
same clock. `bright_limb_position_angle` is east of celestial north in the sky
plane; exact conjunction or undefined polar basis returns `None`. Near
conjunction it is ill-conditioned. The 2° validation budget applies only at
elongations **20°…160°**. `phase_name` is an eight-sector longitude
classification, not an event timestamp or inferred lunar age.

## Validation

[Evidence](lunar-validation-0.4.json) separates local regression, independent
sampling, native-window checks and exports. [JPL Horizons](https://ssd.jpl.nasa.gov/horizons/manual.html)
is queried only explicitly: 72 dates including 1972/2100 and a daily two-month
sequence, geocentre and five sites including both poles. Airless apparent JPL
output is compared against the documented geometric approximation. Raw
responses remain outside repository/distributions; only original statistics,
request identities and input hashes are retained. Tolerances precede the
comparison, and sampled maxima are not global accuracy guarantees.

```sh
python tools/validate_lunar.py --reference-dir /external/lunar-reference --fetch --output lunar-report.json
python tools/validate_lunar_visual.py --output /external/lunar-review --gpu --native
python -m unittest discover -s tests -p test_lunar_040.py
```

The visual packet includes physical/exaggerated scales, four phase views,
24-hour groundtrack, temporal frames, CPU/GPU PNG, SVG/PDF and own native Tk/Qt
captures when requested. Automation is not human acceptance on every platform.
See [the executable example](../examples/lunar_maps.py).
