# Lighting and experimental eclipse boundaries — 0.4 development

Local lighting/shadow contracts below remain unchanged. Astronomical eclipse
use (`EclipseGeometry`, occultation/cones, disk conventions, eclipse Artists)
is **experimental**: observed corpus errors do not certify global geometry,
contact discovery or prediction. [Observed evidence](observed-validation-0.4.md)
and [deferred 13.06/13.07](deferred-gates-0.4.md) state current limits.

# Physical illumination and geometric shadows — 0.4 development

This is local development, not part of the published 0.3.0 package. The original
Azimlib implementation prepares the same shaded triangles for CPU and GPU.
Nothing imports Matplotlib or an external ray tracer/ephemeris backend.

## Local terrain and buildings

```python
import azimlib as azl
from azimlib.terrain3d import LocalFrame
from datetime import datetime, timezone

frame = LocalFrame(0, 45)  # east, north, up in physical metres
observer = azl.SolarObserver(0, 45)
model = azl.SolarModel(time_policy="utc-approx")  # explicit illustration clock
instant = datetime(2025, 6, 21, 9, tzinfo=timezone.utc)
fig, ax = azl.subplots(subplot_kw={"projection": "3d"})
ax.plot_surface([-20, 20], [-20, 20], [[0, 0], [0, 0]], color="white")
light = ax.solar_light(model.position(instant, observer), model=model,
                      frame=frame, max_edge_m=2, samples=8, bias_m=.001)
fig.savefig("shadows.png")
```

`SunPosition` connects the bounded [solar model](solar-0.4.md) to the local
frame. Strict TT/UT1 corrections remain the default model contract; the example
explicitly selects approximate UTC. A manual `SunDirection` needs an observer
matching the frame origin and an explicit `angular_radius` (degrees), including
zero for a directional point light. Manual direction never infers a Sun position.
The local approximation treats solar rays as parallel across the bounded ENU
scene; it is not global curved-Earth shadow transport or atmospheric refraction.

Incidence is Lambertian, `ambient + diffuse * max(0, normal·direction)`;
occlusion multiplies diffuse, leaving the declared ambient contribution.
Normals, heights, ray lengths and offsets use physical vertices before camera
transforms and vertical exaggeration. A building is an opaque extruded mesh;
terrain and other buildings can receive/cast shadows. One light is optional per
axes, and global Earth/Moon Artists cannot be mixed with local ENU illumination.

## Accuracy, resolution and bounded resources

- The own median BVH uses slab bounds and double-sided triangle intersection;
  no third-party implementation was copied, translated or adapted.
- Opaque, non-textured surfaces only. Alpha zero is skipped; partial alpha and
  textured shadow occluders fail explicitly rather than pretending transmission.
- Shadows are sampled at triangle centroids. `max_edge_m` refines receiver
  triangles; it controls spatial approximation, **not a guaranteed error bound**.
  Coarse shadows have faceted edges. Compare progressively smaller edges and
  larger `samples` before interpreting small features or a penumbra.
- `bias_m` defaults to 0.001 m, separating self-intersection from true occlusion;
  blockers/features thinner than the bias are not reliable. Relative determinant
  and barycentric tolerances are 1e-12. Check sensitivity when geometry is tiny,
  nearly parallel or translated far from the ENU origin.
- `samples=1` is the central direction. 2–64 samples use deterministic disk
  quadrature; partial visibility is a sampling estimate, not converged radiative
  transfer. Limb darkening, reflections and scattering are unsupported.
- `ShadowBudget` defaults: 20,000 refined triangles, 500,000 rays and 4,000,000
  triangle tests per lighting update. Hard ceilings are 20,000 / 2,000,000 /
  16,000,000. Refinement is checked before allocation; exceeding a budget raises.

`light.set_position(state)`, `set_time(instant)`, `set_visible(bool)` and
`remove()` follow the Artist lifecycle. A time change invalidates illumination
while reusing the physical mesh/BVH. Mesh, material or visibility changes rebuild
the geometry cache. Camera/exaggeration changes do not invalidate physical
shadows. `TemporalSeries.bind(light)` prevalidates states and dates; playback
preserves the current camera. [examples/lighting_maps.py](../examples/lighting_maps.py)
provides daily animation input; seasonal dates use the same explicit solar model.

## Volumes

`light.bind_volume(volume, shadow_steps=4)` requires the same axes and explicit
`VolumeField.frame`. It connects direction and time to the existing optional
volume self-attenuation model. Visibility/removal restore the previous light.
It does **not** implement mesh-to-volume, volume-to-mesh or multiple-scattering
transport. Scalar transfer functions remain explicit. PNG/PDF support volume
rendering; SVG embeds a raster volume layer when Pillow is installed, and fails
explicitly without that provider. Other figure elements retain vector output.

## Finite source and occultation geometry

`ShadowSphere.from_xyz(xyz, radius_m=...)` represents an Earth-fixed sphere in
metres. `EclipseGeometry(sun, moon, source=...)` requires input provenance and
separates physical sizes/distances from display magnification.
`geometry.solar(observer)`, `lunar()` and `at(point, occulter=...)` report angular
separation, disk radii, visible fraction, and clear/umbra/penumbra/antumbra.
`solar_cone` and `lunar_cone` provide exact finite-sphere tangent cones, apex
distance and signed umbra/penumbra radii at an axial distance. There are no
event-specific rules that force an eclipse.

Angular boundary tests use `asin(radius/distance)`. Partial disk area uses an
analytic **tangent angular-disk approximation**, restricted to radii <=2°;
it is not exact spherical solid-angle irradiance. Independent chord integration
tests the planar formula. Earth shadow uses an enclosing equatorial sphere,
not the oblate atmosphere; Sun/Moon are spheres without terrain/limb structure.
Declared fraction intervals vary angular separation only. They are sensitivity
intervals, **not certified confidence bounds** incorporating all radii, clocks,
Earth shape or model errors.

`ax.eclipse_shadow(geometry, step=2)` adds an optional scalar map/colorbar target.
Cells sample their centres (minimum step 2°); this cannot resolve a narrow
totality path and is not a contour/contact solver. `mode="possible"` visualizes
angular sensitivity. A global `earth_moon` Artist accepts
`set_eclipse_geometry(geometry)`, evaluating physical illumination before
distance/radius display scales. Both layers are toggleable; eclipse maps bind
to `TemporalSeries`, and calculated Earth–Moon states update their geometry.

## Real-event precision remains pending: 13.06 and 13.07

`EclipseGeometry.from_moon(state)` uses the bounded low-precision Sun/Moon models,
with an angular budget over 0.5°. It requires **`allow_approximate=True`** at a
visualization boundary. Synthetic coordinates must identify themselves as such.
`events()` always raises `NotImplementedError`; no precise path, contact time,
eclipse magnitude or observation-planning claim is supported.

The independent [NASA/GSFC 2024-04-08 central-line table](https://eclipse.gsfc.nasa.gov/SEhistory/SEpath/SE2024Apr08Tpath.html)
provides an actual counterexample: all 96 evaluated central-line locations miss
totality with this approximate model. The preset angular, residual-light and
model-budget gates fail. This does not invalidate the generic geometry, but
prevents closing the real solar/lunar event items. A precise, audited ephemeris,
consistent time/frame reductions and independent path/contact validation are
required before revisiting them; lunar event timing is also unvalidated.

## Reproduce local validation

```bash
python tools/validate_lighting_visual.py --output REVIEW_DIR --gpu --native
python tools/validate_eclipse_precision.py --reference-dir EXTERNAL_DIR --fetch --output REPORT.json
```

The precision tool exits **3 when the scientific gate fails**; successful fetching
does not pass the gate. Raw NASA inputs stay outside the checkout and packages.
The visual tool exports original urban/synthetic eclipse/volume scenes, CPU/GPU,
PNG/SVG/PDF as supported, three daily GIF frames, source/asset hashes and optional
verified own-window Tk/Qt captures. Automated Windows captures do not constitute
human Linux/macOS acceptance or a real-time viewer performance guarantee.

See [numerical/provenance definitions](lighting-model-0.4.json),
[local evidence](lighting-validation-0.4.json) and
[the unchanged release gates](release-progress-0.4.md).
