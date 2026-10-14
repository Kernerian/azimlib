# Migration from 0.3 to the unreleased 0.4 development tree

The published stable release remains 0.3.0. These additions require the development
checkout until the [release gates](release-progress-0.4.md) are satisfied.

Both import styles share one figure registry:

```python
import azimlib as azl
import azimlib.pyplot as plt

fig, ax = azl.subplots()
ax.map("brazil")
ax.set_title("Brazil")
assert plt.gcf() is fig
fig.savefig("brazil.svg")
```

Existing figures, style sizes in points, optional legends/grid/north/scale,
visibility/editing, map bearing and separated `savefig()`/`show()` remain. No
minimap or other cartographic decoration becomes mandatory. Prefer the standard
light theme and add only components needed to explain the data.

- **PBF:** choose explicit limits, provenance and missing-reference behavior.
  Small regional trials do not establish full-planet support. Do not bundle
  personal OSM metadata or entire external datasets into application packages.
- **CRS/grids:** declare units, axes, epoch and height frame. Missing grids or
  unsupported operations raise errors; they do not silently substitute a datum.
- **Geocoding/routing:** construct local indexes/graphs with verified source
  metadata. Results are deterministic for the supplied graph, not a guarantee
  of current road legality, traffic or complete global address coverage.
- **Text/TeX:** enable optional engines explicitly and preserve their font/data
  licenses. Missing shaping/TeX providers have explicit capability failures.
- **GPU:** use `fig.show(renderer="gpu")` or `savefig(renderer="gpu")`; stateful
  `azl.show()`/`plt.show()` have no renderer keyword. The backend is experimental. An explicit
  CPU fallback warns. Neither 33 ms exact p95 nor 100 ms complete response is
  guaranteed. See [observed results](observed-validation-0.4.md).
- **3D volumes:** preserve the declared physical/local frame. Camera exaggeration
  and visual body scaling do not change physical solar or shadow calculations.
- **Sun/Moon:** eclipse scientific use remains experimental; no global certified
  prediction/envelope is claimed. Select time policy and observer; consult model validity/error
  budgets. Approximate eclipse visualization requires explicit opt-in and must
  not be interpreted as precise event/contact prediction.

Run [the integration example and validator](integration-0.4.md) against both source
and isolated installed distributions. The [coverage table](integration-0.4.md#coverage-and-explicit-boundaries)
links complete contracts and limits. No external cartographic backend is added.
