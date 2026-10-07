# Transforms and composition in 0.3 development

This is an implemented subset of familiar plotting contracts, using Azimlib's
own geometry, projection, scene and renderer. Stable PyPI 0.2.0 is unchanged.

## Coordinate spaces and inverses

`ax.transData` maps longitude/latitude degrees to display; `transProjection`
maps projected X/Y in the projection's units; `transAxes` maps fractions of
the actual equal-aspect map box. `fig.transFigure` uses figure fractions.
Public display coordinates are DPI pixels, origin bottom-left, Y up. The
internal scene uses logical 100-DPI pixels and Y down; conversion is explicit.
`IdentityTransform` means display coordinates. `PhysicalTransform(fig, unit)`
accepts inches, points or mm; `fig.dpi_scale_trans` is inches to display.

```python
from azimlib.transforms import Affine2D, offset_copy, blended_transform_factory

t = Affine2D().scale(2).translate(5, 3)
assert t.inverted().transform_point(t.transform_point((1, 2))) == (1, 2)
ax.text(-50, -20, 'Offset', transform=offset_copy(ax.transData, fig, x=6, y=4, units='points'))
ax.text(-50, .05, 'Mixed', transform=blended_transform_factory(ax.transData, ax.transAxes))
```

`a + b` applies a first, b second. Transform objects compose by reference;
axes limits, figure size and DPI are read live. Affine inversion rejects a
singular matrix. Geographic inverse/forward may return None outside a domain.
Mixed inversion is supported only for known separable transforms; a rotated
or curved geographic blend raises NotImplementedError instead of inventing
an inverse. Cross-figure Artist transforms are rejected before attachment/edit.
This is not a full cache/invalidation graph for arbitrary user transforms.

Existing geometry/scatter/text/path artists accept `set_transform(t)`; text,
line and annotation entry points also accept a Transform. An annotation uses
it for its target and for a data-space text position; offset points remain
relative to the transformed target. Existing offset-pixels Y-down semantics
are retained. Independent xycoords/textcoords Transform objects and general
Figure-text transforms are not yet part of the annotation/text contract.

## Gaps, paths and editable collections

Plot inputs preserve NaN gaps in get_data and editing; masked NumPy scalars
become gaps without making NumPy a core dependency. Infinity is rejected.
This does not relax strict finite geographic Geometry/GeoJSON validation.
`Path` has immutable vertices/codes, MOVETO/LINETO/CURVE3/CURVE4/CLOSEPOLY/STOP
and compound rings. Beziers are flattened deterministically with 24 steps by
default, not adaptively by an error-in-pixels tolerance.

`PathPatch` draws reusable Path geometry under a transform. `Symbol.patch()`
creates a new patch per use. `LineCollection` batches independent paths,
cycles per-segment colors/widths/dashes, and edits segments/styles/array in
one transaction with one notification. Its scalar array must match the segment
count; its norm/cmap drive colors and colorbars. A failed edit leaves data intact.
Collection attachment currently does not auto-fit path/segment bounds; set
the map extent explicitly. Curved transformed paths are flattened before their
transform, rather than using geographic great-circle densification.

Plot, scatter, fill/patch, collections and unmapped quiver have independent
style-cycle cursors. Explicit properties do not consume a row when every
cycle property is already supplied; color-mapped vectors use their mappable.

`HandlerBase.create_artists` receives the familiar legend/handle/dimensions/
fontsize/transform signature. Handlers return fresh Azimlib PathPatch artists;
`HandlerSymbol` supplies a reusable unit-box Symbol. Instance mappings precede
MRO class mappings. Arbitrary foreign artists, images and composite handler
families are outside this initial protocol.

## Numeric scales, dates and graticules

`scale` supplies LinearScale, LogScale, SymLogScale and inverses for numeric
transforms. `dates` supplies UTC days since 1970, date2num/num2date,
DateFormatter, DayLocator, MonthLocator and AutoDateLocator. Date/log locators
and formatters can be installed on scalar colorbar axes; LogNorm remains a
color normalization. MapAxes longitude/latitude stay linear degrees and reject
log/symlog setters. No implicit date-as-latitude or unit converter registry.
LogFormatter variants produce plain-text powers, not a MathText engine.

Curved or rotated graticules sample lines over the supported projection domain,
intersect their segments with the frame and place border ticks at those hits.
Orthographic horizon endpoints are assigned to a border label side. Sampling
is bounded (361 points for intersections), not exact analytic intersection of
every possible projection boundary. Scientific offset artists remain linked
to the formatter and use the same scene as export/layout; CRS values do not change.

## Subfigures, independent grids and layout

```python
fig = azl.figure(figsize=(12, 5), layout='constrained')
left, right = fig.subfigures(1, 2)
a, b = left.subplots(), right.subplots()
left.suptitle('Region A')
right.suptitle('Region B')
```

SubFigure owns its axes/text/grids, shares the root canvas and export, and can
contain subfigures. add_axes/text positions are local fractions; returned
GridSpecs use root fractions, including explicit updates. MapAxes.figure is
the root Figure, while its Artist parent is the SubFigure. Independent roots
must have disjoint explicit regions. The regional solver preserves manual axes,
uses existing weighted/nested-track measurement and rolls all roots back on
failure. Overlapping root regions warn and retain the previous positions.

`layout='compressed'` first solves constrained layout, then compacts measured
fixed-aspect boxes in complete, unspanned grids. Nested or spanning grids keep
their constrained solution. This does not reproduce all reference solver
optimizations. Free Figure/SubFigure text and explicit cax reserve edge strips
when in_layout is true; interior objects stay manual. It is not a universal
collision solver. Manual positions remain unchanged. Simple/nested solvers
retain the existing bounded 16/32 measurement limits and failure rollback.

See [layout](layout.md), [rotation and recommended light view](visual-style.md),
[runnable atlas](../examples/composition_atlas.py) and
[27 integration tests](../tests/test_transforms_composition.py).
