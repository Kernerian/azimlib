# Interação e integração — desenvolvimento 0.3.0

O runtime continua próprio. Tk é o viewer padrão; Qt, notebook e uma sessão
HTTP **explicitamente local** são opcionais. A versão publicada 0.2.0 não muda.
Para usar estes recursos, instale o checkout 0.3 com `python -m pip install ".[qt,notebook]"`
(ou somente o extra desejado). O pacote estável 0.2.0 ainda não contém esses extras.

`savefig()` sempre produz PNG/SVG/PDF estáticos, sem controls ou scripts.
Nenhum minimapa, seletor, slider ou painel de camadas é criado por padrão.

## Picking e seleção

```python
import azimlib as azl
from azimlib.widgets import FeatureSelector

fig, ax = azl.subplots()
stations = ax.scatter([-47, -44], [-22, -19], label='Stations')
stations.set_picker(5)  # physical display pixels, NOT points
cid = fig.canvas.mpl_connect('pick_event', lambda event: print(event.ind))
selection = FeatureSelector(ax, stations, lambda indices: print(indices))
fig.show()
```

`Artist.contains(mouseevent)` returns `(hit, {'ind': [...], 'features': [...]})`.
`features` contains the immutable geographic Features for geometry layers;
scatter uses original point indices. Set picker to True, False/None, a finite
nonnegative radius, or a callable `(artist, event) -> (bool, properties)`.
`set_pickradius()` is also in **physical display pixels**. This deliberately
differs from Matplotlib's picker-radius points. DPI, clip rectangles, holes,
visible primitives, reprojection, bearing and insets are accounted for.
Line picking tests the painted path's centerline, including dash gaps; text,
mesh cells, vectors and picking individual segments within LineCollection
are not implemented. No implicit selection or geo-coordinate snapping occurs.

FeatureSelector stores validated immutable index tuples, exposes get_features,
and draws an optional interactive highlight; it does not recolor/modify source
data. Disconnect restores the previous picker. Geometry replacement can change
indices; no identity matching across unrelated new data is inferred.
Button/motion events expose bottom-up physical `x/y`, geographic `xdata/ydata`
or None, `inaxes`, `button`, `buttons`, `key`, and `canvas`. Pick callbacks are
delivered when navigation is inactive; explicit canvas.pick works separately.

## Optional controls

```python
from azimlib.widgets import Slider, LayerControl, RectangleSelector

size = Slider(fig.add_axes((.2, .02, .5, .07)), 'Area', 10, 100, 36, valstep=2)
size.on_changed(lambda value: stations.set_sizes([value]))
layers = LayerControl(fig.add_axes((.8, .65, .18, .2)), [stations], ['Stations'])
box = RectangleSelector(ax, lambda press, release: print(press.xdata, release.xdata),
                        minspanx=8, minspany=8)
```

Slider supports horizontal/vertical orientation, finite ranges, clamping,
positive scalar step, set_val/reset/on_changed/disconnect. CheckButtons provides
get_status/set_active(index)/on_clicked; LayerControl binds those states to owned
Artists and observes external visibility changes during repaint. Controls need
distinct empty axes. `.active` controls event handling, get/set_visible controls
appearance, eventson controls user callbacks, drawon controls redraw scheduling.
RectangleSelector uses pixel minspans and geographic endpoint events; its four
extents are endpoint longitude/latitude bounds, not a spherical polygon or exact
geographic bounds of an arbitrarily projected rectangular box. No blitting,
lasso, dragging existing selection corners or universal widget toolkit is claimed.
Keep references to controls/selectors. clear/close/disconnect releases subscriptions.
The interactive scene can be inspected with `fig.to_scene(interactive=True)`;
ordinary static save/to_svg/to_html omit controls.

## Viewers and lifecycle

| Backend | Installation | Ownership / event loop |
|---|---|---|
| tk (default) | `azimlib[gui]` and system Tk | Existing own native window/worker; blocking pyplot.show |
| qt | `azimlib[qt]` | Own QWidget/toolbar, Pillow pixels, Qt main thread/QTimer; no Qt plotting backend |
| browser | core | Offline HTML snapshot, existing limited JavaScript navigation |
| browser-live | core (PNG download needs Pillow) | Loopback server + original client; Python recomposition on creating thread |
| notebook | `azimlib[notebook]` | Public IPython display handle/post_run_cell hook; updatable SVG |

`fig.show(backend='qt', block=True)` uses own Navigation for pan/rectangle zoom,
wheel, Home/Back/Forward, save PNG/SVG/PDF, optional Subplots dialog and cursor
coordinates. Device pixel ratio is respected. Repeated views coalesce before
composition/raster; the worker only receives an owned Scene. It never translates
a clipped bitmap with old ticks/spines. Settled frames use exact rasterization.
This is an initial QWidget integration, not all Qt canvas/backend APIs.
Close the active viewer before changing backend. Standalone FigureCanvas remains
available; subscriptions transfer to the new viewer. Qt must use the GUI thread;
Tk retains its existing thread contract. Do not mutate Figures from worker threads.

```python
viewer = fig.show(backend='browser-live', open_browser=False)
print(viewer.url)            # ephemeral localhost token; do not publish it
stations.set_offsets([[-48, -23], [-44, -19]])
ax.set_projection('mercator')
fig.canvas.draw_idle()
fig.canvas.flush_events()    # required pump in nonblocking scripts
viewer.close()
```

With block=True the live viewer pumps its own owner-thread queue. With
block=False the application must periodically call flush_events on that thread;
an idle script cannot magically execute Python callbacks. Client input uses a
bounded/coalesced queue; callbacks, data updates, components and projection
changes run in Python. All nine built-in projections have recomposition tests;
the underlying domain/singularity/seam limits still apply. set_projection validates
the domain before mutation, retains geographic limits/bearing and rejects axes
sharing or noncylindrical wrapped limits. Custom Python projections can work when
their renderer domain permits them; no JavaScript port is required by the bridge.

The bridge binds only 127.0.0.1 on an ephemeral port, verifies Host/token and
same Origin for POST, exposes a fixed input vocabulary, caps requests at 4096
bytes and queues at 256. Connections have a two-second I/O timeout so incomplete
requests cannot indefinitely block shutdown. Resize is bounded to 60..4096 pixels. It never executes
client Python, reads server files or decodes network pickle. Errors sent to clients
name only the exception type; API arguments/resources remain local. Keep the
session token private; this is not an authenticated multiuser/cloud web service.
Close joins the server and closes the listening socket. Offline HTML is unchanged.

`fig.show(backend='notebook')` creates one updatable SVG display_id, reuses its
handle, flushes dirty Figures after cells and unregisters its hook on close.
Draw_idle coalesces until cell completion/flush_events; no additional thread or
private IPython backend/event-loop API is used. The automatic _repr_svg_ remains
a static representation. The notebook SVG output is not a DOM-event widget,
does not provide live mouse picking/pan, and does not validate all Jupyter frontends.
Use a local live/browser/native viewer for mouse interaction. Qt/Tk and notebook
integration have separate lifecycles; no hidden global auto-backend switch occurs.

## Simplification and performance

`simplify_path(XY, tolerance)` returns a subsequence under iterative
Douglas–Peucker, bounding original vertex distance to each retained segment.
Finite XY values and nonnegative pixel tolerance are required. Transformed,
nonlinear source geometry must first be densified/projected; this is a polyline
error bound, not a geodesic/projection approximation theorem.

`line.set_simplify(.35)` opts a plain geometry-line layer into screen-error
simplification; zero is the default. Curves, arrows, dashed lines and contour cuts
retain their original paths. Markers retain original positions. Packed-path
indices/coordinates reuse across translations and styles; scale/projection/source
changes invalidate appropriately. Its LRU is bounded to 4 MiB. Static savefig,
to_svg and offline HTML always retain full line geometry, including custom DPI.

`simplify_boundaries(collection, ax.transData, tolerance)` explicitly processes
regional 2D Polygon/MultiPolygon data. Exact shared input edge chains are reduced
once and reused in reverse, preserving IDs/properties and ring direction. Holes,
minimum cardinality, planar topology and interchain crossings are checked;
invalid proposals return the original collection. Crossings, differently
vertexized shared edges, altitude/seams and >10000 vertices fail explicitly.
No snapping, boolean overlay, repair, arbitrary tolerance of different source
vertexizations or universal regional containment preservation is promised.

Circle rasterization integrates true disk/unit-square area analytically; regular
stroke annuli use the difference of disk areas. This replaces repeated polygon
stroke integration for ordinary circles; dashed/crisp circle styles retain the
previous generic path. Exact exports retain fractional centers/radii and alpha.
During navigation only, circle centers quantize to 1/16 supersample pixel
(at most 1/32 pixel at 1x) to reuse marker tiles. Radii/stroke widths do not change;
settled frames/exports are exact. Viewer tiles retain at most 512 entries/16 MiB
(default standalone TileCache remains 128); large primitive tiles are excluded.
This preview policy is explicit, not a claim of pixel-identical preview/export.

[benchmark_interaction.py](../tools/benchmark_interaction.py) records first
composition/raster, pan p95/median, with/without labels, separate Python allocation
peak, cache payload and PNG/SVG/PDF time/size. Default synthetic cases use 400
streets and 5000 points at 640×480. Tracemalloc runs separately from timing;
native/Pillow/Qt memory, human-input latency and hardware-independent FPS are
not inferred. There is no performance promise for 500000 points or dense labels.

See [example](../examples/interactive_layers.py), [integration tests](../tests/test_interaction_integration.py),
[Tk smoke](../tools/smoke_interaction_tk.py), [Qt smoke](../tools/smoke_interaction_qt.py),
[IPython smoke](../tools/smoke_notebook.py), [client protocol test](../tools/check_live_viewer.js)
and [dependency terms](dependencies.md). Native Windows is checked locally;
Linux/macOS and frontend/native human acceptance must only be claimed from
their actual executions, never from an offscreen fixture.

## Recorded local batch

The [reproducible gallery](_static/interaction/README.md) separates explicit UI
controls from static exports. [Benchmark measurements](interaction-benchmark-0.3.json)
record this Windows run, not an FPS guarantee. Median whole-scene pan was about
261 ms (400 synthetic streets) and 309 ms (5000 synthetic points); initial painting
remains about six seconds in both scenarios. First-frame and label work still need
optimization; cache speed does not mean a zero-cost first render.

Legacy buffer/band regression fixtures still compare exact bytes against the
frozen own renderer using the same polygonized circle geometry. Analytic-circle
coverage is verified separately against disk-area mathematics; image/PNG and
full/banded composition must still match byte for byte. This deliberate circle
geometry change is not hidden by replacing the frozen baseline or broadening
an arbitrary visual tolerance.
