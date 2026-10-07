# Referência pública da Azimlib

Gerada por `python tools/api_reference.py` a partir dos objetos reais.
Assinaturas descrevem a implementação atual, não compatibilidade integral
com Matplotlib. Veja [guia científico](scientific.md),
[componentes](components.md), [limites de compatibilidade](compatibility.md)
e [matemática](math.md).

Coordenadas: longitude/latitude em graus. figsize: polegadas; linewidth,
fontes e espaçamentos: pontos; s: pontos². set_extent/extent:
(west, east, south, north). Arquivos PNG/SVG não incluem controles de UI.

## azimlib

### `cla()`

### `clf()`

### `clip_orthographic_line(coordinates, projection, *, step=2.0)`

Projected-metre line parts ending exactly on the visible horizon.

### `clip_orthographic_polygon(rings, projection, *, step=2.0)`

Clip small spherical polygons to an Orthographic view, including its limb.

### `close(fig=None)`

Close current, numbered/named/explicit figure, or 'all', without creation.

### `cycler(*args, **kwargs)`

Create zipped properties or combine cycles with + (zip) / * (product).

### `destination(lon, lat, bearing, distance, radius=6371008.8)`

Destination at a bearing clockwise from true north and metres of travel.

### `fignum_exists(num)`

### `figure(num=None, *, figsize=None, dpi=None, facecolor=None, layout=None, clear=False)`

Create/reactivate an own figure by number, label or managed Figure.

### `gca()`

### `gcf()`

### `get_figlabels()`

### `get_fignums()`

### `get_projection(projection='equirectangular', **kwargs)`

Resolve a registered name or reuse a Projection object.

### `getp(artist, property=None)`

### `great_circle(start, end, steps=100)`

Sample the shorter spherical arc; return steps+1 positions.

### `haversine(start, end, radius=6371008.8)`

Great-circle distance in metres on a sphere.

### `ioff()`

### `ion()`

### `isinteractive()`

### `longitude_bounds(longitudes)`

Shortest circular interval, returned increasing, possibly east>180.

### `orientation(a, b, c)`

Exact sign of the binary-float 2D determinant: -1, 0 or 1.

### `rc(group, **kwargs)`

### `rc_context(rc=None)`

### `rcdefaults()`

### `read_csv(source, *, longitude='lon', latitude='lat', id_column=None, converters=None, delimiter=',', encoding='utf-8-sig', crs=None)`

Read a local CSV into immutable Point features, without guessing a CRS.

### `read_dbf(source, *, encoding, include_deleted=False)`

Return DBFRecords with physical zero-based indices; explicit encoding.

### `read_geojson(source, *, crs=None)`

Read a path, JSON string, mapping, text stream or __geo_interface__.

### `read_geotiff(source, *, crs=None, nodata=None, max_pixels=16000000)`

Classic single-band TIFF, GeoKeys and affine georeference interpreted here.

### `read_kml(source)`

Local KML 2.2/2.3 Point/LineString/Polygon/MultiGeometry placemarks.

### `read_osm(source, *, include_untagged=False)`

Interpret local OSM 0.6 nodes/ways and multipolygon relations strictly.

### `read_raster(source, *, crs=None, world_file=None, extent=None, nodata=None, max_pixels=16000000)`

Scalar image with an explicit extent/world-file, or embedded GeoTIFF.

### `read_shapefile(source, *, crs, dbf=None, shx=None, encoding=None, include_deleted=False)`

Read SHP plus optional SHX/DBF; source CRS is always explicit.

### `read_world_file(source)`

Convert six world-file values A,D,B,E,C,F (pixel centres) to corner affine.

### `register_projection(name, projection_class, *, replace=False)`

Register an independently implemented Projection subclass.

### `ring_orientation(ring)`

### `savefig(path, **kwargs)`

### `sca(ax)`

Select an axes and its managed figure without reordering Figure.axes.

### `segment_intersection(a, b, c, d)`

Return none, point or overlap, including endpoints and zero-length edges.

### `setp(artists, *args, **kwargs)`

Set properties on an artist or nested sequence of artists.

### `show(*, block=True, backend='tk', open_browser=True)`

Show own viewers; desktop event loop blocks only when requested.

### `subplot(*args, **kwargs)`

Select/reuse a subplot; explicit projection options can create another.

### `subplot_mosaic(mosaic, *, projection='equirectangular', projection_kw=None, figsize=None, dpi=None, facecolor=None, layout=None, num=None, clear=False, subplot_kw=None, per_subplot_kw=None, gridspec_kw=None, width_ratios=None, height_ratios=None, empty_sentinel='.', sharex=False, sharey=False)`

Return (figure, dict of named axes) for a rectangular or nested mosaic.

### `subplots(nrows=1, ncols=1, *, projection='equirectangular', figsize=None, dpi=None, facecolor=None, squeeze=True, projection_kw=None, subplot_kw=None, layout=None, gridspec_kw=None, width_ratios=None, height_ratios=None, num=None, clear=False, sharex=False, sharey=False)`

### `transform(x, y, source='EPSG:4326', target='EPSG:3857')`

Transform one coordinate pair, always using longitude before latitude.

### `utm_crs(longitude, latitude)`

### `utm_zone(longitude, latitude)`

### `validate_geometry(geometry, *, require_winding=False)`

Check rings/holes and multipolygon interiors in a regional lon/lat plane.

### `validate_ring(ring, *, winding=None)`

### `write_geojson(data, destination=None, *, indent=2)`

Serialize native objects or validated input; optionally write a path/stream.

## azimlib.pyplot

### `annotate(*args, **kwargs)`

### `autoscale(enable=True, axis='both', tight=None)`

### `cla()`

### `clabel(*args, **kwargs)`

### `clf()`

### `close(fig=None)`

Close current, numbered/named/explicit figure, or 'all', without creation.

### `colorbar(mappable, *, ax=None, cax=None, **kwargs)`

### `contour(*args, **kwargs)`

### `cycler(*args, **kwargs)`

Create zipped properties or combine cycles with + (zip) / * (product).

### `draw()`

### `fignum_exists(num)`

### `figtext(x, y, text, **kwargs)`

### `figure(num=None, *, figsize=None, dpi=None, facecolor=None, layout=None, clear=False)`

Create/reactivate an own figure by number, label or managed Figure.

### `gca()`

### `gcf()`

### `get_figlabels()`

### `get_fignums()`

### `getp(artist, property=None)`

### `grid(*args, **kwargs)`

### `imshow(*args, **kwargs)`

### `ioff()`

### `ion()`

### `isinteractive()`

### `legend(*args, **kwargs)`

### `margins(*args, **kwargs)`

### `minorticks_off()`

### `minorticks_on()`

### `pcolormesh(*args, **kwargs)`

### `plot(*args, **kwargs)`

### `quiver(*args, **kwargs)`

### `rc(group, **kwargs)`

### `rc_context(rc=None)`

### `rcdefaults()`

### `savefig(path, **kwargs)`

### `sca(ax)`

Select an axes and its managed figure without reordering Figure.axes.

### `scatter(*args, **kwargs)`

### `setp(artists, *args, **kwargs)`

Set properties on an artist or nested sequence of artists.

### `show(*, block=True, backend='tk', open_browser=True)`

Show own viewers; desktop event loop blocks only when requested.

### `subplot(*args, **kwargs)`

Select/reuse a subplot; explicit projection options can create another.

### `subplot_mosaic(mosaic, *, projection='equirectangular', projection_kw=None, figsize=None, dpi=None, facecolor=None, layout=None, num=None, clear=False, subplot_kw=None, per_subplot_kw=None, gridspec_kw=None, width_ratios=None, height_ratios=None, empty_sentinel='.', sharex=False, sharey=False)`

Return (figure, dict of named axes) for a rectangular or nested mosaic.

### `subplots(nrows=1, ncols=1, *, projection='equirectangular', figsize=None, dpi=None, facecolor=None, squeeze=True, projection_kw=None, subplot_kw=None, layout=None, gridspec_kw=None, width_ratios=None, height_ratios=None, num=None, clear=False, sharex=False, sharey=False)`

### `subplots_adjust(**kwargs)`

### `suptitle(text, **kwargs)`

### `text(*args, **kwargs)`

### `tick_params(**kwargs)`

### `ticklabel_format(**kwargs)`

### `tight_layout(*, pad=1.08, w_pad=None, h_pad=None, rect=(0, 0, 1, 1))`

### `title(label, **kwargs)`

### `xlabel(label, **kwargs)`

### `xlim(*args, **kwargs)`

### `xticks(ticks=None, labels=None, **kwargs)`

### `ylabel(label, **kwargs)`

### `ylim(*args, **kwargs)`

### `yticks(ticks=None, labels=None, **kwargs)`

## azimlib.colors

### `get_cmap(value='viridis')`

### `sample_color(cmap, t)`

## azimlib.cm

### `get_cmap(value='viridis')`

## azimlib.fields

### `contour_levels(valid, levels)`

Validate explicit levels; deduplicate float rounding in automatic levels.

### `contour_segments(x, y, z, level)`

### `grid_data(x, y, z)`

### `hillshade(z, *, dx=1, dy=1, azdeg=315, altdeg=45, vert_exag=1)`

Lambertian illumination; dx/dy and elevation use consistent units.

## azimlib.io

### `read_csv(source, *, longitude='lon', latitude='lat', id_column=None, converters=None, delimiter=',', encoding='utf-8-sig', crs=None)`

Read a local CSV into immutable Point features, without guessing a CRS.

### `read_dbf(source, *, encoding, include_deleted=False)`

Return DBFRecords with physical zero-based indices; explicit encoding.

### `read_geojson(source, *, crs=None)`

Read a path, JSON string, mapping, text stream or __geo_interface__.

### `read_geotiff(source, *, crs=None, nodata=None, max_pixels=16000000)`

Classic single-band TIFF, GeoKeys and affine georeference interpreted here.

### `read_kml(source)`

Local KML 2.2/2.3 Point/LineString/Polygon/MultiGeometry placemarks.

### `read_osm(source, *, include_untagged=False)`

Interpret local OSM 0.6 nodes/ways and multipolygon relations strictly.

### `read_raster(source, *, crs=None, world_file=None, extent=None, nodata=None, max_pixels=16000000)`

Scalar image with an explicit extent/world-file, or embedded GeoTIFF.

### `read_shapefile(source, *, crs, dbf=None, shx=None, encoding=None, include_deleted=False)`

Read SHP plus optional SHX/DBF; source CRS is always explicit.

### `read_world_file(source)`

Convert six world-file values A,D,B,E,C,F (pixel centres) to corner affine.

### `write_geojson(data, destination=None, *, indent=2)`

Serialize native objects or validated input; optionally write a path/stream.

## azimlib.projections

### `available_projections()`

Return the registered projection names, including aliases.

### `get_projection(projection='equirectangular', **kwargs)`

Resolve a registered name or reuse a Projection object.

### `position(value)`

Validate and freeze a two- or three-dimensional geographic position.

### `register_projection(name, projection_class, *, replace=False)`

Register an independently implemented Projection subclass.

### `tm_forward(lon, lat, *, central_longitude=0, central_latitude=0, scale_factor=0.9996, false_easting=0, false_northing=0, ellipsoid=Ellipsoid(semi_major_axis=6378137.0, inverse_flattening=298.257223563, name='WGS84'))`

### `tm_inverse(x, y, *, central_longitude=0, central_latitude=0, scale_factor=0.9996, false_easting=0, false_northing=0, ellipsoid=Ellipsoid(semi_major_axis=6378137.0, inverse_flattening=298.257223563, name='WGS84'))`

### `wrap_longitude(longitude, central_longitude=0.0)`

Wrap longitude into the central meridian's closed +/-180° interval.

## azimlib.crs

### `position(value)`

Validate and freeze a two- or three-dimensional geographic position.

### `tm_forward(lon, lat, *, central_longitude=0, central_latitude=0, scale_factor=0.9996, false_easting=0, false_northing=0, ellipsoid=Ellipsoid(semi_major_axis=6378137.0, inverse_flattening=298.257223563, name='WGS84'))`

### `tm_inverse(x, y, *, central_longitude=0, central_latitude=0, scale_factor=0.9996, false_easting=0, false_northing=0, ellipsoid=Ellipsoid(semi_major_axis=6378137.0, inverse_flattening=298.257223563, name='WGS84'))`

### `transform(x, y, source='EPSG:4326', target='EPSG:3857')`

Transform one coordinate pair, always using longitude before latitude.

### `transform_coordinates(coordinates, source='EPSG:4326', target='EPSG:3857')`

Transform a sequence of 2D/3D positions, preserving optional elevation.

### `transform_geojson(data, source='EPSG:4326', target='EPSG:3857')`

Transform raw GeoJSON coordinates before geographic geometry validation.

### `utm_crs(longitude, latitude)`

### `utm_zone(longitude, latitude)`

## azimlib.datasets

### `catalog() -> 'dict'`

Return a new mapping of offline layer names to coverage and provenance.

### `country(name: 'str') -> 'dict'`

Return a country FeatureCollection by English/Portuguese name or ISO code.

### `load(name: 'str', country: 'str | None' = None) -> 'dict'`

Load ``countries``, ``states``, ``rivers``, ``lakes``, or ``coastlines``.

### `provenance() -> 'dict'`

Return source URLs, pinned commit, license, processing, and SHA-256 hashes.

### `state(name: 'str') -> 'dict'`

Return one bundled Brazilian state by name, postal code or ISO code.

## azimlib.geodesy

### `haversine(start, end, radius=6371008.8)`

Great-circle distance in metres on a sphere.

### `position(value)`

Validate and freeze a two- or three-dimensional geographic position.

### `wrap_longitude(longitude, central_longitude=0.0)`

Wrap longitude into the central meridian's closed +/-180° interval.

## azimlib.topology

### `orientation(a, b, c)`

Exact sign of the binary-float 2D determinant: -1, 0 or 1.

### `position(value)`

Validate and freeze a two- or three-dimensional geographic position.

### `ring_orientation(ring)`

### `segment_intersection(a, b, c, d)`

Return none, point or overlap, including endpoints and zero-length edges.

### `validate_geometry(geometry, *, require_winding=False)`

Check rings/holes and multipolygon interiors in a regional lon/lat plane.

### `validate_ring(ring, *, winding=None)`

### `wrap_longitude(longitude, central_longitude=0.0)`

Wrap longitude into the central meridian's closed +/-180° interval.

## azimlib.transverse

### `position(value)`

Validate and freeze a two- or three-dimensional geographic position.

### `tm_forward(lon, lat, *, central_longitude=0, central_latitude=0, scale_factor=0.9996, false_easting=0, false_northing=0, ellipsoid=Ellipsoid(semi_major_axis=6378137.0, inverse_flattening=298.257223563, name='WGS84'))`

### `tm_inverse(x, y, *, central_longitude=0, central_latitude=0, scale_factor=0.9996, false_easting=0, false_northing=0, ellipsoid=Ellipsoid(semi_major_axis=6378137.0, inverse_flattening=298.257223563, name='WGS84'))`

### `utm_crs(longitude, latitude)`

### `utm_zone(longitude, latitude)`

### `wrap_longitude(longitude, central_longitude=0.0)`

Wrap longitude into the central meridian's closed +/-180° interval.

## azimlib.transforms

### `blended_transform_factory(x_transform, y_transform)`

### `offset_copy(transform, fig=None, x=0, y=0, units='inches')`

### `scene_point(transform, p, figure)`

## azimlib.dates

### `date2num(value)`

### `num2date(value, tz=datetime.timezone.utc)`

## azimlib.scale

### `scale_factory(name, **kwargs)`

## azimlib.legend_handler

### `get_handler(mapping, handle)`

## azimlib.path.Path

`Path(vertices, codes=None)`

### `to_polylines(steps=24)`

### `transformed(transform)`

## azimlib.patches.PathPatch

`PathPatch(path, **kwargs)`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `findobj(match=None, include_self=True)`

### `get_alpha()`

### `get_antialiased()`

### `get_array()`

### `get_children()`

### `get_clim()`

### `get_clip_on()`

### `get_cmap()`

### `get_color()`

### `get_dash_capstyle()`

### `get_dash_joinstyle()`

### `get_data()`

### `get_edgecolor()`

### `get_facecolor()`

### `get_figure(root=False)`

### `get_fontsize()`

### `get_fontweight()`

### `get_in_layout()`

### `get_label()`

### `get_linestyle()`

### `get_linewidth()`

### `get_marker()`

### `get_markeredgecolor()`

### `get_markeredgewidth()`

### `get_markerfacecolor()`

### `get_markersize()`

### `get_norm()`

### `get_path()`

### `get_rotation()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_color(value)`

### `set_dash_capstyle(value)`

### `set_dash_joinstyle(value)`

### `set_data(*args)`

Replace a geographic plot series; explicit map limits stay unchanged.

### `set_edgecolor(value)`

### `set_facecolor(value)`

### `set_fontsize(value)`

### `set_fontweight(value)`

### `set_in_layout(value)`

### `set_label(value)`

### `set_linestyle(value)`

### `set_linewidth(value)`

### `set_marker(value)`

### `set_markeredgecolor(value)`

### `set_markeredgewidth(value)`

### `set_markerfacecolor(value)`

### `set_markersize(value)`

### `set_norm(value)`

### `set_path(path)`

### `set_rotation(value)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `update(props)`

## azimlib.patches.Symbol

`Symbol(path)`

### `patch(**kwargs)`

## azimlib.collections.LineCollection

`LineCollection(segments, *, colors=None, linewidths=None, linestyles=None, transform=None, **kwargs)`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `findobj(match=None, include_self=True)`

### `get_alpha()`

### `get_antialiased()`

### `get_array()`

### `get_children()`

### `get_clim()`

### `get_clip_on()`

### `get_cmap()`

### `get_color()`

### `get_colors()`

### `get_dash_capstyle()`

### `get_dash_joinstyle()`

### `get_data()`

### `get_edgecolor()`

### `get_facecolor()`

### `get_figure(root=False)`

### `get_fontsize()`

### `get_fontweight()`

### `get_in_layout()`

### `get_label()`

### `get_linestyle()`

### `get_linestyles()`

### `get_linewidth()`

### `get_linewidths()`

### `get_marker()`

### `get_markeredgecolor()`

### `get_markeredgewidth()`

### `get_markerfacecolor()`

### `get_markersize()`

### `get_norm()`

### `get_rotation()`

### `get_segments()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_color(value)`

### `set_colors(value)`

### `set_dash_capstyle(value)`

### `set_dash_joinstyle(value)`

### `set_data(*args)`

Replace a geographic plot series; explicit map limits stay unchanged.

### `set_edgecolor(value)`

### `set_facecolor(value)`

### `set_fontsize(value)`

### `set_fontweight(value)`

### `set_in_layout(value)`

### `set_label(value)`

### `set_linestyle(value)`

### `set_linestyles(value)`

### `set_linewidth(value)`

### `set_linewidths(value)`

### `set_marker(value)`

### `set_markeredgecolor(value)`

### `set_markeredgewidth(value)`

### `set_markerfacecolor(value)`

### `set_markersize(value)`

### `set_norm(value)`

### `set_rotation(value)`

### `set_segments(value)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `update(props)`

## azimlib.subfigure.SubFigure

`SubFigure(figure, position, parent=None)`

### `add_axes(rect=(0.125, 0.11, 0.775, 0.77), **kwargs)`

### `add_callback(func)`

### `add_gridspec(nrows=1, ncols=1, **kwargs)`

### `add_subplot(*args, **kwargs)`

### `clear()`

### `colorbar(mappable, *, ax=None, **kwargs)`

### `findobj(match=None, include_self=True)`

### `get_children()`

### `get_clip_on()`

### `get_dpi()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_size_inches()`

### `get_transform()`

### `pchanged()`

### `properties()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_transform(transform)`

### `subfigures(*args, **kwargs)`

### `subplots(nrows=1, ncols=1, *, gridspec_kw=None, width_ratios=None, height_ratios=None, **kwargs)`

### `suptitle(text, **kwargs)`

### `supxlabel(text, **kwargs)`

### `supylabel(text, **kwargs)`

### `text(x, y, text, **kwargs)`

### `update(props)`

## azimlib.transforms.Transform

`Transform()`

### `inverted()`

### `owners()`

### `transform(values)`

### `transform_point(point)`

## azimlib.transforms.CompositeTransform

`CompositeTransform(first, second)`

### `inverted()`

### `owners()`

### `transform(values)`

### `transform_point(p)`

## azimlib.transforms.AxesTransform

`AxesTransform(axes, space='axes')`

### `inverted()`

### `owners()`

### `transform(values)`

### `transform_point(p)`

## azimlib.transforms.FigureTransform

`FigureTransform(figure)`

### `inverted()`

### `owners()`

### `transform(values)`

### `transform_point(p)`

## azimlib.transforms.OffsetTransform

`OffsetTransform(source, figure, x, y, unit)`

### `inverted()`

### `owners()`

### `transform(values)`

### `transform_point(p)`

## azimlib.transforms.IdentityTransform

`IdentityTransform()`

### `inverted()`

### `owners()`

### `transform(values)`

### `transform_point(p)`

## azimlib.transforms.Affine2D

`Affine2D(matrix=None)`

### `clear()`

### `get_matrix()`

### `inverted()`

### `owners()`

### `rotate(theta)`

### `rotate_deg(degrees)`

### `rotate_deg_around(x, y, degrees)`

### `scale(sx, sy=None)`

### `transform(values)`

### `transform_point(p)`

### `translate(tx, ty)`

## azimlib.transforms.PhysicalTransform

`PhysicalTransform(figure, unit='inches')`

### `inverted()`

### `owners()`

### `transform(values)`

### `transform_point(p)`

## azimlib.transforms.BlendedTransform

`BlendedTransform(x_transform, y_transform)`

### `inverted()`

### `owners()`

### `transform(values)`

### `transform_point(p)`

## azimlib.dates.DateFormatter

`DateFormatter(fmt='%Y-%m-%d', tz=datetime.timezone.utc)`

### `fix_minus(text)`

### `format_data(value)`

### `format_data_short(value)`

### `format_ticks(values)`

### `get_offset()`

### `set_axis(axis)`

### `set_locs(locs)`

## azimlib.dates.DayLocator

`DayLocator(interval=1)`

### `raise_if_exceeds(locs)`

### `set_axis(axis)`

### `tick_values(vmin, vmax)`

## azimlib.dates.MonthLocator

`MonthLocator(interval=1)`

### `raise_if_exceeds(locs)`

### `set_axis(axis)`

### `tick_values(vmin, vmax)`

## azimlib.dates.AutoDateLocator

`AutoDateLocator(maxticks=9)`

### `raise_if_exceeds(locs)`

### `set_axis(axis)`

### `tick_values(vmin, vmax)`

## azimlib.scale.ScaleTransform

`ScaleTransform(scale, inverse=False)`

### `inverted()`

### `owners()`

### `transform(values)`

### `transform_point(p)`

## azimlib.scale.LinearScale

`LinearScale()`

### `forward(value)`

### `get_transform()`

### `inverse(value)`

## azimlib.scale.LogScale

`LogScale(base=10)`

### `forward(value)`

### `get_transform()`

### `inverse(value)`

## azimlib.scale.SymLogScale

`SymLogScale(base=10, linthresh=1)`

### `forward(value)`

### `get_transform()`

### `inverse(value)`

## azimlib.legend_handler.HandleBox

`HandleBox(legend, scene, box)`

### `add_artist(artist)`

### `get_transform()`

## azimlib.legend_handler.HandlerBase

`HandlerBase()`

### `create_artists(legend, orig_handle, xdescent, ydescent, width, height, fontsize, transform)`

### `legend_artist(legend, orig_handle, fontsize, handlebox)`

## azimlib.legend_handler.HandlerSymbol

`HandlerSymbol(**style)`

### `create_artists(legend, orig_handle, xdescent, ydescent, width, height, fontsize, transform)`

### `legend_artist(legend, orig_handle, fontsize, handlebox)`

## azimlib.ticker.LogFormatter

`LogFormatter(base=10, labelOnlyBase=False)`

### `fix_minus(text)`

### `format_data(value)`

### `format_data_short(value)`

### `format_ticks(values)`

### `get_offset()`

### `set_axis(axis)`

### `set_locs(locs)`

## azimlib.ticker.LogFormatterExponent

`LogFormatterExponent(base=10, labelOnlyBase=False)`

### `fix_minus(text)`

### `format_data(value)`

### `format_data_short(value)`

### `format_ticks(values)`

### `get_offset()`

### `set_axis(axis)`

### `set_locs(locs)`

## azimlib.ticker.LogFormatterSciNotation

`LogFormatterSciNotation(base=10, labelOnlyBase=False)`

### `fix_minus(text)`

### `format_data(value)`

### `format_data_short(value)`

### `format_ticks(values)`

### `get_offset()`

### `set_axis(axis)`

### `set_locs(locs)`

## azimlib.geodesy.Unit

`Unit(name: str, symbol: str, to_si: float, quantity: str = 'length') -> None`

### `convert(value, target)`

## azimlib.geodesy.Ellipsoid

`Ellipsoid(semi_major_axis: float = 6378137.0, inverse_flattening: float = 298.257223563, name: str = 'WGS84') -> None`

## azimlib.geodesy.Datum

`Datum(name: str = 'WGS84', ellipsoid: azimlib.geodesy.Ellipsoid = Ellipsoid(semi_major_axis=6378137.0, inverse_flattening=298.257223563, name='WGS84'), prime_meridian: float = 0) -> None`

## azimlib.geodesy.Geodesic

`Geodesic(ellipsoid=Ellipsoid(semi_major_axis=6378137.0, inverse_flattening=298.257223563, name='WGS84'))`

### `direct(longitude, latitude, azimuth, distance)`

### `inverse(longitude1, latitude1, longitude2, latitude2)`

### `line(start, end, *, steps=100)`

## azimlib.geodesy.GeodesicResult

`GeodesicResult(longitude: float, latitude: float, distance: float, azimuth1: float, azimuth2: float, iterations: int, method: str) -> None`

## azimlib.topology.Intersection

`Intersection(kind: str, points: tuple = ()) -> None`

## azimlib.topology.TopologyReport

`TopologyReport(issues: tuple) -> None`

### `raise_if_invalid()`

## azimlib.topology.ValidationIssue

`ValidationIssue(code: str, path: tuple, message: str) -> None`

## azimlib.projections.TransverseMercator

`TransverseMercator(central_longitude: 'float' = 0.0, central_latitude: 'float' = 0.0, radius: 'float' = 6371008.8, ellipsoid: 'Ellipsoid' = Ellipsoid(semi_major_axis=6378137.0, inverse_flattening=298.257223563, name='WGS84'), scale_factor: 'float' = 0.9996, false_easting: 'float' = 0, false_northing: 'float' = 0) -> None`

### `forward(lon, lat)`

### `inverse(x, y)`

## azimlib.projections.Stereographic

`Stereographic(central_longitude: 'float' = 0.0, central_latitude: 'float' = 0.0, radius: 'float' = 6371008.8) -> None`

### `forward(lon, lat)`

### `inverse(x, y)`

## azimlib.projections.AzimuthalEquidistant

`AzimuthalEquidistant(central_longitude: 'float' = 0.0, central_latitude: 'float' = 0.0, radius: 'float' = 6371008.8) -> None`

### `forward(lon, lat)`

### `inverse(x, y)`

## azimlib.raster.GeoRaster

`GeoRaster(values: tuple, affine: tuple, crs: object = 'EPSG:4326', nodata: float | None = None, pixel_type: str = 'area') -> None`

### `coordinate(column, row, *, center=False)`

### `geographic_mesh()`

Return lon/lat edges and south-to-north rows for the own mesh Artist.

## azimlib.catalog.DatasetCatalog

`DatasetCatalog(manifest)`

### `available()`

Return detached metadata; editing it does not change the catalog.

### `load(identifier, *, version=None)`

### `verify(identifier=None, *, version=None)`

## azimlib.shapefile.DBFRecord

`DBFRecord(index: int, properties: object, deleted: bool = False) -> None`

## azimlib.artist.Artist

`Artist(parent=None)`

### `add_callback(func)`

### `findobj(match=None, include_self=True)`

### `get_children()`

### `get_clip_on()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_transform()`

### `pchanged()`

### `properties()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_transform(transform)`

### `update(props)`

## azimlib.callbacks.CallbackRegistry

`CallbackRegistry(signals=None)`

### `blocked(*, signal=None)`

### `connect(signal, callback)`

### `disconnect(cid)`

### `process(signal, *args, **kwargs)`

## azimlib.spatial.BoundsIndex

`BoundsIndex(entries=(), *, leaf_size=12)`

### `query(bounds)`

Sorted keys of envelopes intersecting the closed query rectangle.

## azimlib.figure.Figure

`Figure(figsize=None, dpi=None, facecolor=None, layout=None)`

### `add_axes(rect=(0.06, 0.07, 0.88, 0.86), *, projection='equirectangular', projection_kw=None, sharex=None, sharey=None)`

Add axes at figure fractions (left,bottom,width,height).

### `add_callback(func)`

### `add_gridspec(nrows=1, ncols=1, **kwargs)`

Create a GridSpec owned by this figure, with ratios/margins/gaps.

### `add_subplot(*args, projection='equirectangular', projection_kw=None, sharex=None, sharey=None)`

Add a subplot using a SubplotSpec, 111 or (rows, columns, index).

### `clear()`

Detach contents, retaining size, DPI, identity and layout engine.

### `clf()`

Detach contents, retaining size, DPI, identity and layout engine.

### `close()`

### `colorbar(mappable, *, ax=None, cax=None, **kwargs)`

### `delaxes(ax)`

### `findobj(match=None, include_self=True)`

### `gca()`

### `get_children()`

### `get_clip_on()`

### `get_dpi()`

### `get_figheight()`

### `get_figure(root=False)`

### `get_figwidth()`

### `get_in_layout()`

### `get_label()`

### `get_layout_engine()`

### `get_size_inches()`

### `get_suptitle()`

### `get_supxlabel()`

### `get_supylabel()`

### `get_transform()`

### `pchanged()`

### `properties()`

### `remove_callback(oid)`

### `save(path, *, format=None, dpi=None)`

Export static .svg or .png without UI; streams require format.

### `savefig(path, *, format=None, dpi=None)`

Export static .svg or .png without UI; streams require format.

### `sca(ax)`

Select an existing axes without changing Figure.axes creation order.

### `set(**kwargs)`

### `set_clip_on(value)`

### `set_dpi(val)`

### `set_figheight(val, forward=True)`

### `set_figwidth(val, forward=True)`

### `set_in_layout(value)`

### `set_label(label)`

### `set_layout_engine(layout=None, **kwargs)`

### `set_size_inches(w, h=None, forward=True)`

Set physical figure size; optionally resize an existing desktop canvas.

### `set_transform(transform)`

### `show(*, backend='tk', block=False, open_browser=True, path=None)`

Display a native figure, or explicitly request the browser viewer.

### `subfigures(*args, **kwargs)`

### `subplot_mosaic(mosaic, *, projection='equirectangular', projection_kw=None, empty_sentinel='.', subplot_kw=None, per_subplot_kw=None, gridspec_kw=None, width_ratios=None, height_ratios=None, sharex=False, sharey=False)`

Create named maps in a root/nested grid hierarchy; empty slots create no axes.

### `subplots(nrows=1, ncols=1, *, projection='equirectangular', projection_kw=None, squeeze=True, subplot_kw=None, gridspec_kw=None, width_ratios=None, height_ratios=None, sharex=False, sharey=False)`

### `subplots_adjust(*, left=None, bottom=None, right=None, top=None, wspace=None, hspace=None)`

Adjust a regular grid using Matplotlib's fraction/gap vocabulary.

### `suptitle(text, **kwargs)`

### `supxlabel(text, **kwargs)`

Add/reuse a shared longitude label at the bottom of the Figure.

### `supylabel(text, **kwargs)`

Add/reuse a shared latitude label at the left of the Figure.

### `text(x, y, text, **kwargs)`

### `tight_layout(*, pad=1.08, w_pad=None, h_pad=None, rect=(0, 0, 1, 1))`

Adjust once using measured decoration bounds; padding is font units.

### `to_html(title=None)`

### `to_scene(*, cull=False)`

Compose a scene; optionally omit safely invisible geometry.

### `to_svg()`

### `update(props)`

## azimlib.gridspec.GridSpec

`GridSpec(nrows, ncols, figure=None, *, left=None, bottom=None, right=None, top=None, wspace=None, hspace=None, width_ratios=None, height_ratios=None)`

### `get_geometry()`

### `get_grid_positions(fig=None)`

Return bottoms, tops, lefts, rights as immutable tuples.

### `get_height_ratios()`

### `get_subplot_params(figure=None)`

Return a copied mapping (also supporting attribute access).

### `get_width_ratios()`

### `locally_modified_subplot_params()`

### `set_height_ratios(height_ratios)`

### `set_width_ratios(width_ratios)`

### `subplots(*, projection='equirectangular', projection_kw=None, squeeze=True, subplot_kw=None, sharex=False, sharey=False)`

Create one axes per cell in the owning Figure.

### `update(**kwargs)`

Edit explicit margins/gaps; None restores inheritance from the figure.

## azimlib.gridspec.GridSpecFromSubplotSpec

`GridSpecFromSubplotSpec(nrows, ncols, subplot_spec, *, wspace=None, hspace=None, width_ratios=None, height_ratios=None)`

### `get_geometry()`

### `get_grid_positions(fig=None)`

Return bottoms, tops, lefts, rights as immutable tuples.

### `get_height_ratios()`

### `get_subplot_params(figure=None)`

Return a copied mapping (also supporting attribute access).

### `get_topmost_subplotspec()`

### `get_width_ratios()`

### `locally_modified_subplot_params()`

### `set_height_ratios(height_ratios)`

### `set_width_ratios(width_ratios)`

### `subplots(*, projection='equirectangular', projection_kw=None, squeeze=True, subplot_kw=None, sharex=False, sharey=False)`

Create one axes per cell in the owning Figure.

### `update(**kwargs)`

Own convenience: edit child gaps; margins always follow the parent.

## azimlib.gridspec.SubplotSpec

`SubplotSpec(gridspec, num1, num2=None)`

### `get_geometry()`

### `get_gridspec()`

### `get_position(figure=None)`

### `get_topmost_subplotspec()`

### `is_first_col()`

### `is_first_row()`

### `is_last_col()`

### `is_last_row()`

### `subgridspec(nrows, ncols, **kwargs)`

Subdivide this rectangular selection using independent child tracks.

## azimlib.gridspec.SubplotBox

`SubplotBox(left, bottom, width, height)`

## azimlib.figure.FigureCanvas

`FigureCanvas(figure)`

### `draw()`

### `draw_idle()`

### `flush_events()`

### `get_width_height()`

### `mpl_connect(event, callback)`

### `mpl_disconnect(cid)`

## azimlib.axes.MapAxes

`MapAxes(figure, position, projection='equirectangular', projection_kw=None)`

### `add_callback(func)`

### `add_collection(collection, autolim=True)`

### `add_geometries(data, *, style=None, fit=True, crs=None, **kwargs)`

Read GeoJSON; style(feature) can override appearance per feature.

### `add_patch(patch)`

### `annotate(text, xy, xytext=None, *, textcoords='offset pixels', arrow=True, **kwargs)`

### `autoscale(enable=True, axis='both', tight=None)`

### `autoscale_view(tight=None, scalex=True, scaley=True)`

Fit data bounds on automatic axes; explicit limits remain fixed.

### `borders(**kwargs)`

### `buildings(data=None, *, where=None, crs=None, **kwargs)`

Draw supplied building footprints; heights do not imply extrusion.

### `callout(text, xy, xytext=None, *, textcoords='offset pixels', arrow=True, **kwargs)`

### `categorical(data, values, *, key=None, colors=None, missing_color='#dce1e0', **kwargs)`

### `choropleth(data, values, *, key=None, cmap='ocean', vmin=None, vmax=None, bins=5, scheme='equal_interval', missing_color='#dce1e0', norm=None, **kwargs)`

### `cities(data=None, *, where=None, crs=None, **kwargs)`

Draw supplied city/POI centres, not administrative boundaries.

### `clabel(contour, levels=None, *, fmt='%g', **kwargs)`

Return editable line-label handles; inline=True cuts the displayed path.

### `clear()`

Remove artists and decoration while preserving projection and position.

### `coastlines(**kwargs)`

### `colorbar(layer, **kwargs)`

### `compass(*, loc='upper left', size=36, color='black')`

Add an eight-point compass rose independently of the north arrow.

### `contour(lon, lat, values, levels=7, *, cmap='viridis', norm=None, vmin=None, vmax=None, colors=None, linewidths=None, linestyles=None, **kwargs)`

### `countries(**kwargs)`

### `density(lon, lat, *, bins=24, smoothing=1, cmap='sunset', **kwargs)`

A regular lon/lat count grid with optional Gaussian cell smoothing.

### `fill(lon, lat, **kwargs)`

### `findobj(match=None, include_self=True)`

### `fit_extent(data=None, *, margin=0.05)`

Fit point samples using the shortest circular longitude interval.

### `geojson(data, *, style=None, fit=True, crs=None, **kwargs)`

Read GeoJSON; style(feature) can override appearance per feature.

### `get_autoscale_on()`

### `get_autoscalex_on()`

### `get_autoscaley_on()`

### `get_axisbelow()`

### `get_bearing()`

### `get_children()`

### `get_clip_on()`

### `get_extent()`

### `get_facecolor()`

### `get_figure(root=False)`

### `get_gridspec()`

### `get_in_layout()`

### `get_label()`

### `get_legend()`

### `get_shared_x_axes()`

### `get_shared_y_axes()`

### `get_subplotspec()`

Return the cell selection, or None for manually positioned axes.

### `get_title(loc='center')`

### `get_transform()`

### `get_visible()`

### `get_xaxis()`

### `get_xlabel()`

### `get_xlim()`

Return (west, east) geographic longitude limits in degrees.

### `get_xmargin()`

### `get_xscale()`

### `get_xticks(*, minor=False)`

### `get_yaxis()`

### `get_ylabel()`

### `get_ylim()`

Return (south, north) geographic latitude limits in degrees.

### `get_ymargin()`

### `get_yscale()`

### `get_yticks(*, minor=False)`

### `graticule(visible=None, which='major', axis='both', *, step=None, labels=None, **kwargs)`

Toggle with no arguments; styling arguments imply visible=True.

### `grid(visible=None, which='major', axis='both', *, step=None, labels=None, **kwargs)`

Toggle with no arguments; styling arguments imply visible=True.

### `imshow(values, *, extent, origin='upper', cmap='viridis', norm=None, vmin=None, vmax=None, **kwargs)`

Scalar geographic image; extent=(west,east,south,north).

### `info_box(text, *, position=(0.025, 0.975), **kwargs)`

### `inset(bounds=(0.68, 0.66, 0.28, 0.28), *, projection='equirectangular', projection_kw=None)`

### `inset_axes(bounds=(0.68, 0.66, 0.28, 0.28), *, projection='equirectangular', projection_kw=None)`

### `label_outer(remove_inner_ticks=False)`

Hide inner labels; optionally hide ticks, using the local SubplotSpec.

### `labels(data, field='name', *, avoid_overlap=True, padding=2, offsets=None, leader=False, placement='auto', priority_field='priority', min_span=0, max_span=None, **kwargs)`

Place feature labels with collision avoidance and local line tangents.

### `lakes(**kwargs)`

### `legend(handles=None, labels=None, *, title=None, loc=None, fontsize=None, frameon=True, facecolor=None, edgecolor=None, framealpha=None, title_fontsize=None, borderpad=0.4, labelspacing=0.5, handlelength=2, handletextpad=0.8, borderaxespad=0.5, ncols=None, ncol=None, columnspacing=2, bbox_to_anchor=None, bbox_transform='axes', mode=None, handler_map=None)`

### `line(coordinates, **kwargs)`

### `map(region='world', **kwargs)`

### `margins(*margins, x=None, y=None, tight=True)`

### `minorticks_off()`

### `minorticks_on()`

Enable automatic minor ticks without enabling any grid.

### `municipalities(data=None, **kwargs)`

### `neighborhoods(data=None, *, where=None, crs=None, **kwargs)`

Draw supplied neighborhood polygons; where filters properties.

### `north_arrow(*, loc='upper right', size=36, color='black')`

Add a north arrow without replacing the compass rose.

### `ocean(color='#e5f1f4')`

### `overview(visible=True, *, loc='upper right', context=None, extent=None, width=145, shade_alpha=0.45)`

Add a locator with a fixed context and highlighted current viewport.

### `pan(dlon, dlat)`

Move the geographic viewport in degrees, preserving its size.

### `pchanged()`

### `pcolormesh(lon, lat, values, *, cmap='viridis', norm=None, vmin=None, vmax=None, shading='flat', antialiased=False, **kwargs)`

Lon/lat edges and scalar cells; own projected quadrilateral mesh.

### `plot(*args, data=None, **kwargs)`

Plot one/many lon/lat series, columns and named data; return handles.

### `polygon(coordinates, *, holes=None, **kwargs)`

### `properties()`

### `quiver(lon, lat, u, v, C=None, *, scale=None, cmap='viridis', norm=None, vmin=None, vmax=None, **kwargs)`

East/north vectors; scale is data units per axes width.

### `raster(data, *, crs=None, world_file=None, extent=None, nodata=None, **kwargs)`

Draw an explicit GeoRaster or read a locally georeferenced scalar image.

### `relim(visible_only=False)`

Recompute geographic data bounds without moving the current view.

### `remove()`

### `remove_callback(oid)`

### `rivers(**kwargs)`

### `roads(data=None, **kwargs)`

### `route(coordinates, *, geodesic=True, steps=64, ellipsoid=None, **kwargs)`

### `scale_bar(*, length=None, units='km', loc='lower left', fontsize=9, frameon=True, facecolor='white', edgecolor='#cccccc', framealpha=0.8, color='black')`

### `scatter(lon, lat, *, s=36, c=None, cmap='viridis', norm=None, vmin=None, vmax=None, **kwargs)`

### `set(**kwargs)`

### `set_autoscale_on(value)`

### `set_autoscalex_on(value)`

### `set_autoscaley_on(value)`

### `set_axis_off()`

### `set_axis_on()`

### `set_axisbelow(value)`

### `set_bearing(angle)`

### `set_clip_on(value)`

### `set_extent(extent)`

Set (west, east, south, north), matching common map plotting APIs.

### `set_facecolor(color='#e5f1f4')`

### `set_in_layout(value)`

### `set_label(label)`

### `set_prop_cycle(*args, **kwargs)`

Set future line/scatter defaults; does not restyle existing Artists.

### `set_title(text, fontdict=None, loc=None, pad=None, **kwargs)`

Set one of three independent titles; pad is measured in points.

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xlabel(label, *, labelpad=None, **kwargs)`

Set the horizontal geographic axis label.

### `set_xlim(left=None, right=None, *, emit=True, auto=False)`

Set longitude limits; accept ``(left, right)`` or separate values.

### `set_xmargin(value)`

### `set_xscale(value, **kwargs)`

### `set_xticks(ticks, labels=None, *, minor=False, **kwargs)`

### `set_ylabel(label, *, labelpad=None, **kwargs)`

Set the vertical geographic axis label.

### `set_ylim(bottom=None, top=None, *, emit=True, auto=False)`

Set latitude limits; accept ``(bottom, top)`` or separate values.

### `set_ymargin(value)`

### `set_yscale(value, **kwargs)`

### `set_yticks(ticks, labels=None, *, minor=False, **kwargs)`

### `sharex(other)`

### `sharey(other)`

### `state(name, **kwargs)`

Draw and fit one Brazilian state by name, postal code or BR-XX.

### `states(country=None, **kwargs)`

### `streets(data=None, *, where=None, crs=None, **kwargs)`

Draw supplied street lines, with linewidth in points, not metres.

### `subtitle(text, **kwargs)`

### `text(lon, lat, text, *, transform='data', **kwargs)`

### `tick_params(axis='both', which='major', **kwargs)`

### `ticklabel_format(*, axis='both', style=None, scilimits=None, useOffset=None, useLocale=None, useMathText=None)`

Configure ScalarFormatter on the requested major axes atomically.

### `title(text, **kwargs)`

Fluent geographic shorthand; set_title returns the text artist.

### `update(props)`

### `zoom(factor=2, center=None)`

Zoom geographic limits by a positive factor (>1 zooms in).

## azimlib.figure.AxesGrid

`AxesGrid(matrix, squeeze=True)`

### `flatten()`

## azimlib.layers.Layer

`Layer(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `findobj(match=None, include_self=True)`

### `get_alpha()`

### `get_antialiased()`

### `get_array()`

### `get_children()`

### `get_clim()`

### `get_clip_on()`

### `get_cmap()`

### `get_color()`

### `get_dash_capstyle()`

### `get_dash_joinstyle()`

### `get_data()`

### `get_edgecolor()`

### `get_facecolor()`

### `get_figure(root=False)`

### `get_fontsize()`

### `get_fontweight()`

### `get_in_layout()`

### `get_label()`

### `get_linestyle()`

### `get_linewidth()`

### `get_marker()`

### `get_markeredgecolor()`

### `get_markeredgewidth()`

### `get_markerfacecolor()`

### `get_markersize()`

### `get_norm()`

### `get_rotation()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_color(value)`

### `set_dash_capstyle(value)`

### `set_dash_joinstyle(value)`

### `set_data(*args)`

Replace a geographic plot series; explicit map limits stay unchanged.

### `set_edgecolor(value)`

### `set_facecolor(value)`

### `set_fontsize(value)`

### `set_fontweight(value)`

### `set_in_layout(value)`

### `set_label(value)`

### `set_linestyle(value)`

### `set_linewidth(value)`

### `set_marker(value)`

### `set_markeredgecolor(value)`

### `set_markeredgewidth(value)`

### `set_markerfacecolor(value)`

### `set_markersize(value)`

### `set_norm(value)`

### `set_rotation(value)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `update(props)`

## azimlib.collections.ScatterCollection

`ScatterCollection(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `findobj(match=None, include_self=True)`

### `get_alpha()`

### `get_antialiased()`

### `get_array()`

### `get_children()`

### `get_clim()`

### `get_clip_on()`

### `get_cmap()`

### `get_color()`

### `get_dash_capstyle()`

### `get_dash_joinstyle()`

### `get_data()`

### `get_edgecolor()`

### `get_facecolor()`

### `get_figure(root=False)`

### `get_fontsize()`

### `get_fontweight()`

### `get_in_layout()`

### `get_label()`

### `get_linestyle()`

### `get_linewidth()`

### `get_marker()`

### `get_markeredgecolor()`

### `get_markeredgewidth()`

### `get_markerfacecolor()`

### `get_markersize()`

### `get_norm()`

### `get_offsets()`

### `get_rotation()`

### `get_sizes()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit points, areas and color data together before notifying observers.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_color(value)`

### `set_dash_capstyle(value)`

### `set_dash_joinstyle(value)`

### `set_data(*args)`

Replace a geographic plot series; explicit map limits stay unchanged.

### `set_edgecolor(value)`

### `set_facecolor(value)`

### `set_fontsize(value)`

### `set_fontweight(value)`

### `set_in_layout(value)`

### `set_label(value)`

### `set_linestyle(value)`

### `set_linewidth(value)`

### `set_marker(value)`

### `set_markeredgecolor(value)`

### `set_markeredgewidth(value)`

### `set_markerfacecolor(value)`

### `set_markersize(value)`

### `set_norm(value)`

### `set_offsets(values)`

### `set_rotation(value)`

### `set_sizes(sizes, dpi=72.0)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `update(props)`

## azimlib.field_artists.MeshCollection

`MeshCollection(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `findobj(match=None, include_self=True)`

### `get_alpha()`

### `get_antialiased()`

### `get_array()`

### `get_children()`

### `get_clim()`

### `get_clip_on()`

### `get_cmap()`

### `get_color()`

### `get_coordinates()`

### `get_dash_capstyle()`

### `get_dash_joinstyle()`

### `get_data()`

### `get_edgecolor()`

### `get_facecolor()`

### `get_figure(root=False)`

### `get_fontsize()`

### `get_fontweight()`

### `get_in_layout()`

### `get_label()`

### `get_linestyle()`

### `get_linewidth()`

### `get_marker()`

### `get_markeredgecolor()`

### `get_markeredgewidth()`

### `get_markerfacecolor()`

### `get_markersize()`

### `get_norm()`

### `get_rotation()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_color(value)`

### `set_dash_capstyle(value)`

### `set_dash_joinstyle(value)`

### `set_data(*args)`

Replace a geographic plot series; explicit map limits stay unchanged.

### `set_edgecolor(value)`

### `set_facecolor(value)`

### `set_fontsize(value)`

### `set_fontweight(value)`

### `set_in_layout(value)`

### `set_label(value)`

### `set_linestyle(value)`

### `set_linewidth(value)`

### `set_marker(value)`

### `set_markeredgecolor(value)`

### `set_markeredgewidth(value)`

### `set_markerfacecolor(value)`

### `set_markersize(value)`

### `set_norm(value)`

### `set_rotation(value)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `update(props)`

## azimlib.field_artists.ScalarImage

`ScalarImage(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `findobj(match=None, include_self=True)`

### `get_alpha()`

### `get_antialiased()`

### `get_array()`

### `get_children()`

### `get_clim()`

### `get_clip_on()`

### `get_cmap()`

### `get_color()`

### `get_coordinates()`

### `get_dash_capstyle()`

### `get_dash_joinstyle()`

### `get_data()`

### `get_edgecolor()`

### `get_extent()`

### `get_facecolor()`

### `get_figure(root=False)`

### `get_fontsize()`

### `get_fontweight()`

### `get_in_layout()`

### `get_label()`

### `get_linestyle()`

### `get_linewidth()`

### `get_marker()`

### `get_markeredgecolor()`

### `get_markeredgewidth()`

### `get_markerfacecolor()`

### `get_markersize()`

### `get_norm()`

### `get_rotation()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_color(value)`

### `set_dash_capstyle(value)`

### `set_dash_joinstyle(value)`

### `set_data(values)`

Replace a geographic plot series; explicit map limits stay unchanged.

### `set_edgecolor(value)`

### `set_extent(extent)`

### `set_facecolor(value)`

### `set_fontsize(value)`

### `set_fontweight(value)`

### `set_in_layout(value)`

### `set_label(value)`

### `set_linestyle(value)`

### `set_linewidth(value)`

### `set_marker(value)`

### `set_markeredgecolor(value)`

### `set_markeredgewidth(value)`

### `set_markerfacecolor(value)`

### `set_markersize(value)`

### `set_norm(value)`

### `set_rotation(value)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `update(props)`

## azimlib.field_artists.VectorCollection

`VectorCollection(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `findobj(match=None, include_self=True)`

### `get_UVC()`

### `get_alpha()`

### `get_antialiased()`

### `get_array()`

### `get_children()`

### `get_clim()`

### `get_clip_on()`

### `get_cmap()`

### `get_color()`

### `get_dash_capstyle()`

### `get_dash_joinstyle()`

### `get_data()`

### `get_edgecolor()`

### `get_facecolor()`

### `get_figure(root=False)`

### `get_fontsize()`

### `get_fontweight()`

### `get_in_layout()`

### `get_label()`

### `get_linestyle()`

### `get_linewidth()`

### `get_marker()`

### `get_markeredgecolor()`

### `get_markeredgewidth()`

### `get_markerfacecolor()`

### `get_markersize()`

### `get_norm()`

### `get_offsets()`

### `get_rotation()`

### `get_scale()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_UVC(U, V, C=None)`

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_color(value)`

### `set_dash_capstyle(value)`

### `set_dash_joinstyle(value)`

### `set_data(*args)`

Replace a geographic plot series; explicit map limits stay unchanged.

### `set_edgecolor(value)`

### `set_facecolor(value)`

### `set_fontsize(value)`

### `set_fontweight(value)`

### `set_in_layout(value)`

### `set_label(value)`

### `set_linestyle(value)`

### `set_linewidth(value)`

### `set_marker(value)`

### `set_markeredgecolor(value)`

### `set_markeredgewidth(value)`

### `set_markerfacecolor(value)`

### `set_markersize(value)`

### `set_norm(value)`

### `set_offsets(values)`

### `set_rotation(value)`

### `set_scale(value)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `update(props)`

## azimlib.contours.ContourSet

`ContourSet(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `clabel(levels=None, **kwargs)`

### `findobj(match=None, include_self=True)`

### `get_alpha()`

### `get_antialiased()`

### `get_array()`

### `get_children()`

### `get_clim()`

### `get_clip_on()`

### `get_cmap()`

### `get_color()`

### `get_dash_capstyle()`

### `get_dash_joinstyle()`

### `get_data()`

### `get_edgecolor()`

### `get_edgecolors()`

### `get_facecolor()`

### `get_figure(root=False)`

### `get_fontsize()`

### `get_fontweight()`

### `get_in_layout()`

### `get_label()`

### `get_linestyle()`

### `get_linestyles()`

### `get_linewidth()`

### `get_linewidths()`

### `get_marker()`

### `get_markeredgecolor()`

### `get_markeredgewidth()`

### `get_markerfacecolor()`

### `get_markersize()`

### `get_norm()`

### `get_rotation()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_color(value)`

### `set_dash_capstyle(value)`

### `set_dash_joinstyle(value)`

### `set_data(*args)`

Replace a geographic plot series; explicit map limits stay unchanged.

### `set_edgecolor(value)`

### `set_edgecolors(values)`

### `set_facecolor(value)`

### `set_fontsize(value)`

### `set_fontweight(value)`

### `set_in_layout(value)`

### `set_label(value)`

### `set_linestyle(value)`

### `set_linestyles(values)`

### `set_linewidth(value)`

### `set_linewidths(values)`

### `set_marker(value)`

### `set_markeredgecolor(value)`

### `set_markeredgewidth(value)`

### `set_markerfacecolor(value)`

### `set_markersize(value)`

### `set_norm(value)`

### `set_rotation(value)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `update(props)`

## azimlib.contours.ContourLabel

`ContourLabel(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `findobj(match=None, include_self=True)`

### `get_alpha()`

### `get_antialiased()`

### `get_array()`

### `get_children()`

### `get_clim()`

### `get_clip_on()`

### `get_cmap()`

### `get_color()`

### `get_dash_capstyle()`

### `get_dash_joinstyle()`

### `get_data()`

### `get_edgecolor()`

### `get_facecolor()`

### `get_figure(root=False)`

### `get_fontsize()`

### `get_fontweight()`

### `get_in_layout()`

### `get_inline()`

### `get_inline_spacing()`

### `get_label()`

### `get_linestyle()`

### `get_linewidth()`

### `get_marker()`

### `get_markeredgecolor()`

### `get_markeredgewidth()`

### `get_markerfacecolor()`

### `get_markersize()`

### `get_norm()`

### `get_rotation()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_color(value)`

### `set_dash_capstyle(value)`

### `set_dash_joinstyle(value)`

### `set_data(*args)`

Replace a geographic plot series; explicit map limits stay unchanged.

### `set_edgecolor(value)`

### `set_facecolor(value)`

### `set_fontsize(value)`

### `set_fontweight(value)`

### `set_in_layout(value)`

### `set_inline(value)`

### `set_inline_spacing(value)`

### `set_label(value)`

### `set_linestyle(value)`

### `set_linewidth(value)`

### `set_marker(value)`

### `set_markeredgecolor(value)`

### `set_markeredgewidth(value)`

### `set_markerfacecolor(value)`

### `set_markersize(value)`

### `set_norm(value)`

### `set_rotation(value)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `update(props)`

## azimlib.contours.ContourLabels

`ContourLabels(iterable=(), /)`

### `get_visible()`

### `remove()`

Remove first occurrence of value.

### `set(**kwargs)`

### `set_visible(value)`

## azimlib.axis.Axis

`Axis(owner, name)`

### `get_major_formatter()`

### `get_major_locator()`

### `get_majorticklocs()`

### `get_minor_formatter()`

### `get_minor_locator()`

### `get_minorticklocs()`

### `get_offset_text()`

### `get_scale()`

### `get_tick_space()`

### `get_view_interval()`

### `set_major_formatter(formatter)`

### `set_major_locator(locator)`

### `set_minor_formatter(formatter)`

### `set_minor_locator(locator)`

### `set_tick_params(**kwargs)`

### `set_ticks(ticks, labels=None, *, minor=False, **kwargs)`

## azimlib.components.AxisComponents

`AxisComponents(parent=None)`

### `add_callback(func)`

### `findobj(match=None, include_self=True)`

### `get_children()`

### `get_clip_on()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_transform()`

### `get_xaxis()`

### `get_xticks(*, minor=False)`

### `get_yaxis()`

### `get_yticks(*, minor=False)`

### `label_outer(remove_inner_ticks=False)`

Hide inner labels; optionally hide ticks, using the local SubplotSpec.

### `minorticks_off()`

### `minorticks_on()`

Enable automatic minor ticks without enabling any grid.

### `pchanged()`

### `properties()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_axis_off()`

### `set_axis_on()`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_transform(transform)`

### `set_xticks(ticks, labels=None, *, minor=False, **kwargs)`

### `set_yticks(ticks, labels=None, *, minor=False, **kwargs)`

### `tick_params(axis='both', which='major', **kwargs)`

### `ticklabel_format(*, axis='both', style=None, scilimits=None, useOffset=None, useLocale=None, useMathText=None)`

Configure ScalarFormatter on the requested major axes atomically.

### `update(props)`

## azimlib.components.TextArtist

`TextArtist(text='', _owner=None, _slot=None, **style)`

### `add_callback(func)`

### `findobj(match=None, include_self=True)`

### `get_alpha()`

### `get_children()`

### `get_clip_on()`

### `get_color()`

### `get_figure(root=False)`

### `get_fontfamily()`

### `get_fontsize()`

### `get_fontstyle()`

### `get_fontweight()`

### `get_ha()`

### `get_horizontalalignment()`

### `get_in_layout()`

### `get_rotation()`

### `get_rotation_mode()`

### `get_size()`

### `get_text()`

### `get_transform()`

### `get_va()`

### `get_verticalalignment()`

### `get_visible()`

### `get_weight()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_alpha(value)`

### `set_clip_on(value)`

### `set_color(value)`

### `set_fontfamily(value)`

### `set_fontsize(value)`

### `set_fontstyle(value)`

### `set_fontweight(value)`

### `set_ha(value)`

### `set_horizontalalignment(value)`

### `set_in_layout(value)`

### `set_rotation(value)`

### `set_rotation_mode(value)`

### `set_size(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_va(value)`

### `set_verticalalignment(value)`

### `set_visible(value)`

### `set_weight(value)`

### `update(props)`

## azimlib.text_artists.MapText

`MapText(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `findobj(match=None, include_self=True)`

### `get_alpha()`

### `get_antialiased()`

### `get_array()`

### `get_children()`

### `get_clim()`

### `get_clip_on()`

### `get_cmap()`

### `get_color()`

### `get_dash_capstyle()`

### `get_dash_joinstyle()`

### `get_data()`

### `get_edgecolor()`

### `get_facecolor()`

### `get_figure(root=False)`

### `get_fontfamily()`

### `get_fontsize()`

### `get_fontstyle()`

### `get_fontweight()`

### `get_ha()`

### `get_horizontalalignment()`

### `get_in_layout()`

### `get_label()`

### `get_linestyle()`

### `get_linewidth()`

### `get_marker()`

### `get_markeredgecolor()`

### `get_markeredgewidth()`

### `get_markerfacecolor()`

### `get_markersize()`

### `get_norm()`

### `get_position()`

### `get_rotation()`

### `get_rotation_mode()`

### `get_size()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_va()`

### `get_verticalalignment()`

### `get_visible()`

### `get_weight()`

### `get_x()`

### `get_xdata()`

### `get_y()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_color(value)`

### `set_dash_capstyle(value)`

### `set_dash_joinstyle(value)`

### `set_data(*args)`

Replace a geographic plot series; explicit map limits stay unchanged.

### `set_edgecolor(value)`

### `set_facecolor(value)`

### `set_fontfamily(value)`

### `set_fontsize(value)`

### `set_fontstyle(value)`

### `set_fontweight(value)`

### `set_ha(value)`

### `set_horizontalalignment(value)`

### `set_in_layout(value)`

### `set_label(value)`

### `set_linestyle(value)`

### `set_linewidth(value)`

### `set_marker(value)`

### `set_markeredgecolor(value)`

### `set_markeredgewidth(value)`

### `set_markerfacecolor(value)`

### `set_markersize(value)`

### `set_norm(value)`

### `set_position(value)`

### `set_rotation(value)`

### `set_rotation_mode(value)`

### `set_size(value)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_va(value)`

### `set_verticalalignment(value)`

### `set_visible(visible)`

### `set_weight(value)`

### `set_x(value)`

### `set_xdata(value)`

### `set_y(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `update(props)`

## azimlib.text_artists.Annotation

`Annotation(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `findobj(match=None, include_self=True)`

### `get_alpha()`

### `get_anncoords()`

### `get_antialiased()`

### `get_array()`

### `get_children()`

### `get_clim()`

### `get_clip_on()`

### `get_cmap()`

### `get_color()`

### `get_dash_capstyle()`

### `get_dash_joinstyle()`

### `get_data()`

### `get_edgecolor()`

### `get_facecolor()`

### `get_figure(root=False)`

### `get_fontfamily()`

### `get_fontsize()`

### `get_fontstyle()`

### `get_fontweight()`

### `get_ha()`

### `get_horizontalalignment()`

### `get_in_layout()`

### `get_label()`

### `get_linestyle()`

### `get_linewidth()`

### `get_marker()`

### `get_markeredgecolor()`

### `get_markeredgewidth()`

### `get_markerfacecolor()`

### `get_markersize()`

### `get_norm()`

### `get_position()`

### `get_rotation()`

### `get_rotation_mode()`

### `get_size()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_va()`

### `get_verticalalignment()`

### `get_visible()`

### `get_weight()`

### `get_x()`

### `get_xdata()`

### `get_y()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_anncoords(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_color(value)`

### `set_dash_capstyle(value)`

### `set_dash_joinstyle(value)`

### `set_data(*args)`

Replace a geographic plot series; explicit map limits stay unchanged.

### `set_edgecolor(value)`

### `set_facecolor(value)`

### `set_fontfamily(value)`

### `set_fontsize(value)`

### `set_fontstyle(value)`

### `set_fontweight(value)`

### `set_ha(value)`

### `set_horizontalalignment(value)`

### `set_in_layout(value)`

### `set_label(value)`

### `set_linestyle(value)`

### `set_linewidth(value)`

### `set_marker(value)`

### `set_markeredgecolor(value)`

### `set_markeredgewidth(value)`

### `set_markerfacecolor(value)`

### `set_markersize(value)`

### `set_norm(value)`

### `set_position(value)`

### `set_rotation(value)`

### `set_rotation_mode(value)`

### `set_size(value)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_va(value)`

### `set_verticalalignment(value)`

### `set_visible(visible)`

### `set_weight(value)`

### `set_x(value)`

### `set_xdata(value)`

### `set_y(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `update(props)`

## azimlib.figure_text.FigureTextArtist

`FigureTextArtist(x, y, text='', **kwargs)`

### `add_callback(func)`

### `findobj(match=None, include_self=True)`

### `get_alpha()`

### `get_children()`

### `get_clip_on()`

### `get_color()`

### `get_figure(root=False)`

### `get_fontfamily()`

### `get_fontsize()`

### `get_fontstyle()`

### `get_fontweight()`

### `get_ha()`

### `get_horizontalalignment()`

### `get_in_layout()`

### `get_position()`

### `get_rotation()`

### `get_rotation_mode()`

### `get_size()`

### `get_text()`

### `get_transform()`

### `get_va()`

### `get_verticalalignment()`

### `get_visible()`

### `get_weight()`

### `get_x()`

### `get_y()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_alpha(value)`

### `set_clip_on(value)`

### `set_color(value)`

### `set_fontfamily(value)`

### `set_fontsize(value)`

### `set_fontstyle(value)`

### `set_fontweight(value)`

### `set_ha(value)`

### `set_horizontalalignment(value)`

### `set_in_layout(value)`

### `set_position(value)`

### `set_rotation(value)`

### `set_rotation_mode(value)`

### `set_size(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_va(value)`

### `set_verticalalignment(value)`

### `set_visible(value)`

### `set_weight(value)`

### `set_x(value)`

### `set_y(value)`

### `update(props)`

## azimlib.cycles.Cycler

`Cycler(rows)`

### `by_key()`

## azimlib.components.MapComponent

`MapComponent(*, axes=None, slot=None, **options)`

### `add_callback(func)`

### `findobj(match=None, include_self=True)`

### `get_children()`

### `get_clip_on()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_transform()`

### `get_visible()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_transform(transform)`

### `set_visible(value)`

## azimlib.components.Spine

`Spine(visible: bool = True, color: str = 'black', linewidth: float = 0.8) -> None`

### `add_callback(func)`

### `findobj(match=None, include_self=True)`

### `get_children()`

### `get_clip_on()`

### `get_color()`

### `get_edgecolor()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_linewidth()`

### `get_transform()`

### `get_visible()`

### `pchanged()`

### `properties()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_clip_on(value)`

### `set_color(value)`

### `set_edgecolor(value)`

### `set_in_layout(value)`

### `set_linewidth(value)`

### `set_transform(transform)`

### `set_visible(value)`

### `update(props)`

## azimlib.components.Legend

`Legend(**options)`

### `add_callback(func)`

### `findobj(match=None, include_self=True)`

### `get_children()`

### `get_clip_on()`

### `get_figure(root=False)`

### `get_frame()`

### `get_frame_on()`

### `get_in_layout()`

### `get_texts()`

### `get_title()`

### `get_transform()`

### `get_visible()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_bbox_to_anchor(value, transform=None)`

### `set_clip_on(value)`

### `set_frame_on(value)`

### `set_in_layout(value)`

### `set_loc(value)`

### `set_ncols(value)`

### `set_title(text, **kwargs)`

### `set_transform(transform)`

### `set_visible(value)`

## azimlib.components.LegendFrame

`LegendFrame(legend)`

### `add_callback(func)`

### `findobj(match=None, include_self=True)`

### `get_alpha()`

### `get_children()`

### `get_clip_on()`

### `get_edgecolor()`

### `get_facecolor()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_linewidth()`

### `get_transform()`

### `get_visible()`

### `pchanged()`

### `properties()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_alpha(value)`

### `set_clip_on(value)`

### `set_edgecolor(value)`

### `set_facecolor(value)`

### `set_in_layout(value)`

### `set_linewidth(value)`

### `set_transform(transform)`

### `set_visible(value)`

### `update(props)`

## azimlib.components.OrientationIndicator

`OrientationIndicator(*, axes, slot, loc, size, color, compass=False)`

### `add_callback(func)`

### `findobj(match=None, include_self=True)`

### `get_angle()`

### `get_children()`

### `get_clip_on()`

### `get_color()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_loc()`

### `get_size()`

### `get_transform()`

### `get_visible()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_clip_on(value)`

### `set_color(value)`

### `set_in_layout(value)`

### `set_loc(value)`

### `set_size(value)`

### `set_transform(transform)`

### `set_visible(value)`

## azimlib.components.ScaleBar

`ScaleBar(*, axes=None, slot=None, **options)`

### `add_callback(func)`

### `findobj(match=None, include_self=True)`

### `get_children()`

### `get_clip_on()`

### `get_color()`

### `get_figure(root=False)`

### `get_fontsize()`

### `get_frame_on()`

### `get_in_layout()`

### `get_length()`

### `get_loc()`

### `get_transform()`

### `get_units()`

### `get_visible()`

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_clip_on(value)`

### `set_color(value)`

### `set_edgecolor(value)`

### `set_facecolor(value)`

### `set_fontsize(value)`

### `set_frame_on(value)`

### `set_in_layout(value)`

### `set_length(value)`

### `set_loc(value)`

### `set_transform(transform)`

### `set_units(value)`

### `set_visible(value)`

## azimlib.colorbar.Colorbar

`Colorbar(axes, mappable, *, orientation=None, location=None, label=None, fraction=0.15, shrink=1, aspect=20, pad=None, ticks=None, format=None, extend='neither', extendfrac=0.05, spacing='uniform', drawedges=False, alpha=1)`

### `add_callback(func)`

### `findobj(match=None, include_self=True)`

### `get_children()`

### `get_clip_on()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_ticks(*, minor=False)`

### `get_transform()`

### `get_visible()`

### `minorticks_off()`

### `minorticks_on()`

Enable subdivisions on the long axis; the short axis remains empty.

### `pchanged()`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_alpha(value)`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_label(text, *, labelpad=None, loc=None, **kwargs)`

### `set_ticklabels(labels, *, minor=False, **kwargs)`

### `set_ticks(ticks, labels=None, *, minor=False, **kwargs)`

### `set_transform(transform)`

### `set_visible(value)`

### `update_normal(mappable)`

### `update_ticks()`

## azimlib.colorbar.ColorbarAxes

`ColorbarAxes(bar)`

### `get_visible()`

### `get_xaxis()`

### `get_xticks(*, minor=False)`

### `get_yaxis()`

### `get_yticks(*, minor=False)`

### `minorticks_off()`

### `minorticks_on()`

### `set_visible(value)`

### `set_xlabel(text, **kwargs)`

### `set_xticks(ticks, labels=None, *, minor=False, **kwargs)`

### `set_ylabel(text, **kwargs)`

### `set_yticks(ticks, labels=None, *, minor=False, **kwargs)`

### `tick_params(axis='both', which='major', **kwargs)`

### `ticklabel_format(**kwargs)`

## azimlib.cm.ScalarMappable

`ScalarMappable(norm=None, cmap='viridis')`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `get_array()`

### `get_clim()`

### `get_cmap()`

### `get_norm()`

### `set_array(values)`

### `set_clim(vmin=None, vmax=None)`

### `set_cmap(value)`

### `set_norm(value)`

### `to_color(value)`

## azimlib.colors.Normalize

`Normalize(vmin=None, vmax=None, clip=False)`

### `autoscale(values)`

### `autoscale_None(values)`

### `inverse(value)`

### `scaled()`

## azimlib.colors.NoNorm

`NoNorm(vmin=None, vmax=None, clip=False)`

### `autoscale(values)`

### `autoscale_None(values)`

### `inverse(value)`

### `scaled()`

## azimlib.colors.LogNorm

`LogNorm(vmin=None, vmax=None, clip=False)`

### `autoscale(values)`

### `autoscale_None(values)`

### `inverse(value)`

### `scaled()`

## azimlib.colors.TwoSlopeNorm

`TwoSlopeNorm(vcenter, vmin=None, vmax=None)`

### `autoscale(values)`

### `autoscale_None(values)`

### `inverse(value)`

### `scaled()`

## azimlib.colors.BoundaryNorm

`BoundaryNorm(boundaries, ncolors=None, clip=False)`

### `autoscale(values)`

### `autoscale_None(values)`

### `inverse(value)`

### `scaled()`

## azimlib.colors.Colormap

`Colormap(name='viridis', colors=None)`

### `reversed(name=None)`

### `set_bad(color)`

### `set_over(color)`

### `set_under(color)`

## azimlib.colors.ListedColormap

`ListedColormap(colors, name='from_list')`

### `reversed(name=None)`

### `set_bad(color)`

### `set_over(color)`

### `set_under(color)`

## azimlib.geometry.Geometry

`Geometry(type: 'str', coordinates: 'tuple' = (), geometries: 'tuple' = ()) -> None`

### `iter_positions()`

### `to_geojson()`

## azimlib.geometry.Feature

`Feature(geometry: 'Geometry | None', properties: 'Mapping' = <factory>, id: 'str | int | float | None' = None) -> None`

### `to_geojson()`

## azimlib.geometry.FeatureCollection

`FeatureCollection(features: 'tuple' = ()) -> None`

### `select(where=None, *, predicate=None, geometry_types=None)`

Return a new collection, preserving feature objects, IDs and order.

### `to_geojson()`

## azimlib.crs.CRS

`CRS(code: 'str' = 'EPSG:4326') -> None`

### `transform_to(target, x, y)`

## azimlib.crs.Transformer

`Transformer(source: 'CRS', target: 'CRS') -> None`

### `transform(x, y)`

## azimlib.ticker.Locator

`Locator()`

### `raise_if_exceeds(locs)`

### `set_axis(axis)`

### `tick_values(vmin, vmax)`

## azimlib.ticker.FixedLocator

`FixedLocator(locs)`

### `raise_if_exceeds(locs)`

### `set_axis(axis)`

### `tick_values(vmin, vmax)`

## azimlib.ticker.NullLocator

`NullLocator()`

### `raise_if_exceeds(locs)`

### `set_axis(axis)`

### `tick_values(vmin, vmax)`

## azimlib.ticker.MultipleLocator

`MultipleLocator(base=1.0, offset=0.0)`

### `raise_if_exceeds(locs)`

### `set_axis(axis)`

### `set_params(*, base=None, offset=None)`

### `tick_values(vmin, vmax)`

## azimlib.ticker.MaxNLocator

`MaxNLocator(nbins=10, *, steps=None, integer=False, prune=None)`

### `raise_if_exceeds(locs)`

### `set_axis(axis)`

### `set_params(**kwargs)`

### `tick_values(vmin, vmax)`

## azimlib.ticker.AutoLocator

`AutoLocator()`

### `raise_if_exceeds(locs)`

### `set_axis(axis)`

### `set_params(**kwargs)`

### `tick_values(vmin, vmax)`

## azimlib.ticker.LogLocator

`LogLocator(base=10.0, subs=(1.0,))`

### `raise_if_exceeds(locs)`

### `set_axis(axis)`

### `tick_values(vmin, vmax)`

## azimlib.ticker.Formatter

`Formatter()`

### `fix_minus(text)`

### `format_data(value)`

### `format_data_short(value)`

### `format_ticks(values)`

### `get_offset()`

### `set_axis(axis)`

### `set_locs(locs)`

## azimlib.ticker.AutoMinorLocator

`AutoMinorLocator(n=None)`

### `raise_if_exceeds(locs)`

### `set_axis(axis)`

### `tick_values(vmin, vmax)`

## azimlib.ticker.ScalarFormatter

`ScalarFormatter(useOffset=None, useMathText=None, useLocale=None, *, usetex=None)`

### `fix_minus(text)`

### `format_data(value)`

### `format_data_short(value)`

### `format_ticks(values)`

### `get_offset()`

### `get_useLocale()`

### `get_useMathText()`

### `get_useOffset()`

### `get_usetex()`

### `set_axis(axis)`

### `set_locs(locs)`

### `set_powerlimits(lims)`

### `set_scientific(value)`

### `set_useLocale(value)`

### `set_useMathText(value)`

### `set_useOffset(value)`

### `set_usetex(value)`

## azimlib.ticker.EngFormatter

`EngFormatter(unit='', places=None, sep=' ', *, usetex=None, useMathText=None, useOffset=False)`

### `fix_minus(text)`

### `format_data(value)`

### `format_data_short(value)`

### `format_eng(value)`

### `format_ticks(values)`

### `get_offset()`

### `set_axis(axis)`

### `set_locs(locs)`

## azimlib.ticker.NullFormatter

`NullFormatter()`

### `fix_minus(text)`

### `format_data(value)`

### `format_data_short(value)`

### `format_ticks(values)`

### `get_offset()`

### `set_axis(axis)`

### `set_locs(locs)`

## azimlib.ticker.FixedFormatter

`FixedFormatter(seq)`

### `fix_minus(text)`

### `format_data(value)`

### `format_data_short(value)`

### `format_ticks(values)`

### `get_offset()`

### `set_axis(axis)`

### `set_locs(locs)`

## azimlib.ticker.FuncFormatter

`FuncFormatter(func)`

### `fix_minus(text)`

### `format_data(value)`

### `format_data_short(value)`

### `format_ticks(values)`

### `get_offset()`

### `set_axis(axis)`

### `set_locs(locs)`

## azimlib.ticker.FormatStrFormatter

`FormatStrFormatter(fmt)`

### `fix_minus(text)`

### `format_data(value)`

### `format_data_short(value)`

### `format_ticks(values)`

### `get_offset()`

### `set_axis(axis)`

### `set_locs(locs)`

## azimlib.ticker.StrMethodFormatter

`StrMethodFormatter(fmt)`

### `fix_minus(text)`

### `format_data(value)`

### `format_data_short(value)`

### `format_ticks(values)`

### `get_offset()`

### `set_axis(axis)`

### `set_locs(locs)`

## azimlib.ticker.LongitudeFormatter

`LongitudeFormatter(*, direction_label=True, degree_symbol='°', number_format='g', dms=False, zero_direction_label=False, dateline_direction_label=False)`

### `fix_minus(text)`

### `format_data(value)`

### `format_data_short(value)`

### `format_ticks(values)`

### `get_offset()`

### `set_axis(axis)`

### `set_locs(locs)`

## azimlib.ticker.LatitudeFormatter

`LatitudeFormatter(*, direction_label=True, degree_symbol='°', number_format='g', dms=False, zero_direction_label=False, dateline_direction_label=False)`

### `fix_minus(text)`

### `format_data(value)`

### `format_data_short(value)`

### `format_ticks(values)`

### `get_offset()`

### `set_axis(axis)`

### `set_locs(locs)`

## azimlib.projections.Projection

`Projection(central_longitude: 'float' = 0.0, central_latitude: 'float' = 0.0, radius: 'float' = 6371008.8) -> None`

### `forward(lon, lat)`

### `inverse(x, y)`

## azimlib.projections.Equirectangular

`Equirectangular(central_longitude: 'float' = 0.0, central_latitude: 'float' = 0.0, radius: 'float' = 6371008.8, standard_parallel: 'float' = 0.0) -> None`

### `forward(lon, lat)`

### `inverse(x, y)`

## azimlib.projections.Mercator

`Mercator(central_longitude: 'float' = 0.0, central_latitude: 'float' = 0.0, radius: 'float' = 6371008.8, max_latitude: 'float' = 85.0511287798066) -> None`

### `forward(lon, lat)`

### `inverse(x, y)`

## azimlib.projections.EqualEarth

`EqualEarth(central_longitude: 'float' = 0.0, central_latitude: 'float' = 0.0, radius: 'float' = 6371008.8) -> None`

### `forward(lon, lat)`

### `inverse(x, y)`

## azimlib.projections.Orthographic

`Orthographic(central_longitude: 'float' = 0.0, central_latitude: 'float' = 0.0, radius: 'float' = 6371008.8) -> None`

### `forward(lon, lat)`

### `inverse(x, y)`

### `visibility(lon, lat)`

Signed cosine of angular distance to the view centre (>=0 visible).

## azimlib.projections.LambertConformalConic

`LambertConformalConic(central_longitude: 'float' = 0.0, central_latitude: 'float' = 0.0, radius: 'float' = 6371008.8, standard_parallels: 'tuple' = (20.0, 50.0)) -> None`

### `forward(lon, lat)`

### `inverse(x, y)`

## azimlib.projections.AlbersEqualArea

`AlbersEqualArea(central_longitude: 'float' = 0.0, central_latitude: 'float' = 0.0, radius: 'float' = 6371008.8, standard_parallels: 'tuple' = (20.0, 50.0)) -> None`

### `forward(lon, lat)`

### `inverse(x, y)`

## azimlib.layout_engine.LayoutEngine

`LayoutEngine()`

### `execute(figure)`

### `get()`

## azimlib.layout_engine.TightLayoutEngine

`TightLayoutEngine(*, pad=1.08, w_pad=None, h_pad=None, rect=(0, 0, 1, 1))`

### `execute(figure)`

### `get()`

### `set(**kwargs)`

## azimlib.layout_engine.ConstrainedLayoutEngine

`ConstrainedLayoutEngine(*, w_pad=0.041666666666666664, h_pad=0.041666666666666664, wspace=0.02, hspace=0.02, rect=(0, 0, 1, 1))`

### `execute(figure)`

### `get()`

### `set(**kwargs)`

## azimlib.layout_engine.PlaceHolderLayoutEngine

`PlaceHolderLayoutEngine(adjust_compatible=True)`

### `execute(figure)`

### `get()`

## azimlib.layout_engine.CompressedLayoutEngine

`CompressedLayoutEngine(*, w_pad=0.041666666666666664, h_pad=0.041666666666666664, wspace=0.02, hspace=0.02, rect=(0, 0, 1, 1))`

### `execute(figure)`

### `get()`

### `set(**kwargs)`
