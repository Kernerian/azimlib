# Azimlib 0.4.0 — unpublished candidate API

GPU selection (`Figure.show(renderer="gpu")`, Figure/root/pyplot
`savefig(renderer="gpu")`, `GpuRenderer`/`GpuConfig`) is experimental.
Stateful root/pyplot `show()` has no renderer keyword. Astronomical eclipses,
finite-source geometry and disk conventions are experimental, not certified
forecasts. Private ephemeris APIs remain internal. PBF has regional real-data
validation, not proven planet scale. CPU defaults and explicit refusals remain.
[Policy](api-stability.md), [scope](deferred-gates-0.4.md),
[observed evidence](observed-validation-0.4.md).

# Referência pública da Azimlib

Gerada por `python tools/api_reference.py` a partir dos objetos reais.
Assinaturas descrevem a implementação atual, não compatibilidade integral
com Matplotlib. Veja [guia científico](scientific.md),
[componentes](components.md), [limites de compatibilidade](compatibility.md)
e [matemática](math.md).

Coordenadas: longitude/latitude em graus. figsize: polegadas; linewidth,
fontes e espaçamentos: pontos; s: pontos². set_extent/extent:
(west, east, south, north). Arquivos PNG/SVG não incluem controles de UI.

## azimlib.solar_artists

### `artist_mutation(method)`

Coalesce nested setters on one artist; failed edits do not notify.

### `attach_night(axes, value, **options)`

### `attach_path(axes, path, *, visual_radius=1000.0, width=8.0, color='#d77924')`

### `attach_sun(axes, value, **options)`

### `collection(value, role, samples)`

### `state(value, model=None, observer=None, offsets=None)`

### `style_dict(values=None, **kwargs)`

### `text_style(style)`

## azimlib.lunar_artists

### `artist_mutation(method)`

Coalesce nested setters on one artist; failed edits do not notify.

### `attach_earth_moon(axes, value, **options)`

### `attach_moon(axes, value, **options)`

### `attach_path(axes, path, *, distance_scale=1.0, width=500000.0, color='#a576bf', **style)`

### `collection(value)`

### `state(value, model=None, observer=None, offsets=None)`

### `style_dict(values=None, **kwargs)`

### `text_style(style)`

### `to_rgba(color, alpha=None)`

Dependency-free basic CSS/hex or normalized RGB(A) conversion.

### `transform_point(matrix, point)`

## azimlib.eclipse_artists

### `artist_mutation(method)`

Coalesce nested setters on one artist; failed edits do not notify.

### `attach_eclipse(axes, geometry, **options)`

### `style_dict(values=None, **kwargs)`

## azimlib.volume_artist

### `artist_mutation(method)`

Coalesce nested setters on one artist; failed edits do not notify.

### `finite(value)`

### `inverse_matrix(matrix)`

Own bounded Gauss-Jordan inversion, row major.

### `isosurface_mesh(field, level)`

Original marching tetrahedra, fixed shared cube diagonal; bounded output.

### `normalized(a)`

### `slice_mesh(field, axis, position)`

### `to_rgba(color, alpha=None)`

Dependency-free basic CSS/hex or normalized RGB(A) conversion.

### `trace_ray(layers, origin, direction, maximum=inf, *, samplers=None, pick=False)`

Reference midpoint integration; overlapping fields mix optical depth.

## azimlib.pbf

### `assign_holes(outers, holes)`

### `chunks(message, number)`

### `decode_block(raw, header, *, max_refs=100000)`

### `decode_header(raw)`

### `fields(data, budget)`

### `int32(value)`

### `iter_osm_pbf(source, *, max_refs=100000, expected_sha256=None)`

Yield immutable OSMRecord snapshots with at most one block in memory.

### `one(message, number, wire, default=<object object at 0x000001B9EF940C10>)`

### `read_osm_pbf(source, *, bbox=None, where=None, include_untagged=False, max_features=100000, max_vertices=1000000, max_bytes=67108864, **index_options)`

Read a bounded collection; for large inputs use OSMIndex.features().

### `text(value)`

## azimlib.coordinate_operations

### `vector3(value)`

### `wrap_longitude(longitude, central_longitude=0.0)`

Wrap longitude into the central meridian's closed +/-180° interval.

## azimlib.datum_grids

### `read_gtx(source, *, nodata=(-88.8888,), max_bytes=134217728, max_nodes=16000000)`

NOAA binary GTX: big-endian 4 doubles, 2 int32, float32 nodes (2009+).

### `read_ntv2(source, *, nodata=(), max_bytes=134217728, max_nodes=16000000, max_tiles=4096)`

NTv2 GSB, 11/11-record headers, SECONDS, either endian, nested subgrids.

## azimlib.grid_operations

### `vector3(value)`

### `wrap_longitude(longitude, central_longitude=0.0)`

Wrap longitude into the central meridian's closed +/-180° interval.

## overlay

## azimlib.geocoding

### `edit_distance(a, b, limit=2)`

Own bounded Levenshtein dynamic program, over Unicode code points.

### `normalize_name(value, *, accents=False)`

### `records_from_features(features, source, *, include_addresses=False)`

Allowlisted OSM/GeoJSON tags; aliases/language names retain display text.

### `tokens(value)`

## azimlib.routing

### `allowed(tags, profile)`

### `budget(value, name)`

### `directions(tags, profile)`

### `haversine(start, end, radius=6371008.8)`

Great-circle distance in metres on a sphere.

### `identifier(value)`

### `kept_tags(tags)`

### `node_open(tags, profile)`

### `positive(value, name, *, zero=False)`

### `restriction_value(tags, profile)`

### `speed(tags, profile, direction)`

### `xml_records(source)`

Bounded, entity-free XML snapshot primitives with original IDs/references.

## azimlib.text_engine

### `cache_token(text, style)`

### `cluster_units(text, style)`

### `current_defaults()`

### `figure_defaults(method)`

Recompose auto-generated components with the figure's captured controls.

### `is_shaped(style)`

### `register_font(path, *, family, source, license_id, license_text, allow_outlines=False)`

Register an immutable font snapshot with explicit redistribution provenance.

### `scene_options(style)`

### `shape_text(text, style)`

### `text_commands(item)`

### `text_context(*, engine='harfbuzz', direction='auto', language='und', fallback=(), features=())`

Defaults captured by newly composed Artists; reset on exit, thread-local.

### `text_options(options)`

Validate the public opt-in controls without loading optional engines.

### `with_text_notices(scene)`

Return a shallow scene view with deduplicated font provenance; no paths.

## azimlib.tex

### `clear_tex_cache()`

Discard prepared fragments and force rehashing of tools/resources.

### `composition_resources()`

One verified tool/font snapshot per composition, never a time-based TTL.

### `tex_cache_info()`

Read prepared-fragment cache counts and measured retained payload.

### `tex_context(config)`

Capture real TeX defaults in new figures/Artists; reset on exit.

### `tex_layout(text, style)`

### `text_commands(item)`

## azimlib.solar

### `solar_events(day, observer, *, model=None, offsets=None, zone=datetime.timezone.utc, center_altitude=-0.8333333333333334)`

Events in a civil day, fixed geometric center threshold plus local horizon.

### `wrap_longitude(longitude, central_longitude=0.0)`

Wrap longitude into the central meridian's closed +/-180° interval.

## azimlib.lunar

### `wrap_longitude(longitude, central_longitude=0.0)`

Wrap longitude into the central meridian's closed +/-180° interval.

## azimlib.lighting

### `artist_mutation(method)`

Coalesce nested setters on one artist; failed edits do not notify.

### `attach_light(axes, value, *, frame=None, **options)`

### `dot(a, b)`

### `finite(value)`

### `subdivide(points, max_edge, depth=0)`

## azimlib.eclipse

### `disk_overlap(a, b, d)`

Area of two planar disks, independent analytic circle intersection.

### `occultation(point, source, occulter, *, uncertainty_degrees=0.0)`

## azimlib.solar_disk

### `compare_disks(evaluator, conventions)`

Report every selected model. Never choose the one closest to a reference.

## azimlib.volume

### `finite(value)`

### `length_unit(unit)`

### `read_volume(path, *, budget=None, sha256=None)`

Verify every AZV brick in bounded memory; retain only its file descriptor.

### `write_volume(path, field=None, *, shape=None, bricks=None, brick_size=16, origin=(0, 0, 0), spacing=(1, 1, 1), components=1, value_unit='1', frame=None, budget=None)`

Write atomic AZV1; a streaming producer yields ordered (XYZ brick, LE f32).

## azimlib.renderers.gpu

### `render_gpu_image(scene, scale=1, *, fallback='raise', config=None, cancel=None)`

### `render_gpu_png(scene, path_or_stream, scale=1, *, fallback='raise', config=None)`

## azimlib

### `cla()`

### `clear_tex_cache()`

Discard prepared fragments and force rehashing of tools/resources.

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

### `difference(left, right, **kwargs)`

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

### `intersection(left, right, **kwargs)`

### `ioff()`

### `ion()`

### `isinteractive()`

### `iter_osm_pbf(source, *, max_refs=100000, expected_sha256=None)`

Yield immutable OSMRecord snapshots with at most one block in memory.

### `longitude_bounds(longitudes)`

Shortest circular interval, returned increasing, possibly east>180.

### `occultation(point, source, occulter, *, uncertainty_degrees=0.0)`

### `orientation(a, b, c)`

Exact sign of the binary-float 2D determinant: -1, 0 or 1.

### `overlay(left, right, operation='intersection', *, domain='planar', max_segments=20000, max_pairs=2000000, max_edges=100000)`

Return geometry and a shared noded graph with source-edge lineage.

### `overlay_features(left, right, operation='intersection', **kwargs)`

Keep both property namespaces/IDs; never silently overwrite a field.

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

Classic scalar/RGB/RGBA TIFF, GeoKeys and affine georeference interpreted here.

### `read_gtx(source, *, nodata=(-88.8888,), max_bytes=134217728, max_nodes=16000000)`

NOAA binary GTX: big-endian 4 doubles, 2 int32, float32 nodes (2009+).

### `read_kml(source)`

Local KML 2.2/2.3 Point/LineString/Polygon/MultiGeometry placemarks.

### `read_ntv2(source, *, nodata=(), max_bytes=134217728, max_nodes=16000000, max_tiles=4096)`

NTv2 GSB, 11/11-record headers, SECONDS, either endian, nested subgrids.

### `read_osm(source, *, include_untagged=False)`

Interpret local OSM 0.6 nodes/ways and multipolygon relations strictly.

### `read_osm_pbf(source, *, bbox=None, where=None, include_untagged=False, max_features=100000, max_vertices=1000000, max_bytes=67108864, **index_options)`

Read a bounded collection; for large inputs use OSMIndex.features().

### `read_raster(source, *, crs=None, world_file=None, extent=None, nodata=None, max_pixels=16000000)`

Scalar or RGB/RGBA image with an explicit extent/world-file, or embedded GeoTIFF.

### `read_shapefile(source, *, crs, dbf=None, shx=None, encoding=None, include_deleted=False)`

Read SHP plus optional SHX/DBF; source CRS is always explicit.

### `read_svg_symbol(path, *, provenance)`

Read a local SVG geometry subset; caller supplies legal provenance.

### `read_volume(path, *, budget=None, sha256=None)`

Verify every AZV brick in bounded memory; retain only its file descriptor.

### `read_world_file(source)`

Convert six world-file values A,D,B,E,C,F (pixel centres) to corner affine.

### `records_from_features(features, source, *, include_addresses=False)`

Allowlisted OSM/GeoJSON tags; aliases/language names retain display text.

### `register_font(path, *, family, source, license_id, license_text, allow_outlines=False)`

Register an immutable font snapshot with explicit redistribution provenance.

### `register_projection(name, projection_class, *, replace=False)`

Register an independently implemented Projection subclass.

### `repair_geometry(geometry, *, method='normalize', max_segments=20000, max_pairs=2000000, max_edges=100000)`

Explicit planar deduplication/winding, optionally even-odd polygonization.

### `ring_orientation(ring)`

### `savefig(path, **kwargs)`

Static export; renderer="gpu" forwards experimental PNG selection.

### `sca(ax)`

Select an axes and its managed figure without reordering Figure.axes.

### `segment_intersection(a, b, c, d)`

Return none, point or overlap, including endpoints and zero-length edges.

### `setp(artists, *args, **kwargs)`

Set properties on an artist or nested sequence of artists.

### `show(*, block=True, backend='tk', open_browser=True)`

Show own CPU viewers; desktop loop blocks only when requested.

### `simplify_boundaries(data, transform, tolerance)`

Simplify exact shared chains once; preserve IDs/properties/ring direction.

### `simplify_path(points, tolerance)`

### `solar_events(day, observer, *, model=None, offsets=None, zone=datetime.timezone.utc, center_altitude=-0.8333333333333334)`

Events in a civil day, fixed geometric center threshold plus local horizon.

### `subplot(*args, **kwargs)`

Select/reuse a subplot; explicit projection options can create another.

### `subplot_mosaic(mosaic, *, projection='equirectangular', projection_kw=None, figsize=None, dpi=None, facecolor=None, layout=None, num=None, clear=False, subplot_kw=None, per_subplot_kw=None, gridspec_kw=None, width_ratios=None, height_ratios=None, empty_sentinel='.', sharex=False, sharey=False)`

Return (figure, dict of named axes) for a rectangular or nested mosaic.

### `subplots(nrows=1, ncols=1, *, projection='equirectangular', figsize=None, dpi=None, facecolor=None, squeeze=True, projection_kw=None, subplot_kw=None, layout=None, gridspec_kw=None, width_ratios=None, height_ratios=None, num=None, clear=False, sharex=False, sharey=False)`

### `symmetric_difference(left, right, **kwargs)`

### `tex_context(config)`

Capture real TeX defaults in new figures/Artists; reset on exit.

### `text_context(*, engine='harfbuzz', direction='auto', language='und', fallback=(), features=())`

Defaults captured by newly composed Artists; reset on exit, thread-local.

### `transform(x, y, source='EPSG:4326', target='EPSG:3857')`

Transform one coordinate pair, always using longitude before latitude.

### `union(left, right, **kwargs)`

### `utm_crs(longitude, latitude)`

### `utm_zone(longitude, latitude)`

### `validate_geometry(geometry, *, require_winding=False)`

Check rings/holes and multipolygon interiors in a regional lon/lat plane.

### `validate_ring(ring, *, winding=None)`

### `validate_topology(geometry, *, domain='planar')`

Diagnose the new overlay contract without modifying any coordinates.

### `write_geojson(data, destination=None, *, indent=2)`

Serialize native objects or validated input; optionally write a path/stream.

### `write_volume(path, field=None, *, shape=None, bricks=None, brick_size=16, origin=(0, 0, 0), spacing=(1, 1, 1), components=1, value_unit='1', frame=None, budget=None)`

Write atomic AZV1; a streaming producer yields ordered (XYZ brick, LE f32).

## azimlib.pyplot

### `annotate(*args, **kwargs)`

### `autoscale(enable=True, axis='both', tight=None)`

### `cla()`

### `clabel(*args, **kwargs)`

### `clear_tex_cache()`

Discard prepared fragments and force rehashing of tools/resources.

### `clf()`

### `close(fig=None)`

Close current, numbered/named/explicit figure, or 'all', without creation.

### `colorbar(mappable, *, ax=None, cax=None, **kwargs)`

### `contour(*args, **kwargs)`

### `contourf(*args, **kwargs)`

### `cycler(*args, **kwargs)`

Create zipped properties or combine cycles with + (zip) / * (product).

### `draw()`

### `fignum_exists(num)`

### `figtext(x, y, text, **kwargs)`

### `figure(num=None, *, figsize=None, dpi=None, facecolor=None, layout=None, clear=False)`

Create/reactivate an own figure by number, label or managed Figure.

### `flow(*args, **kwargs)`

### `gca()`

### `gcf()`

### `get_figlabels()`

### `get_fignums()`

### `getp(artist, property=None)`

### `grid(*args, **kwargs)`

### `heatmap(*args, **kwargs)`

### `hist2d(*args, **kwargs)`

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

### `register_font(path, *, family, source, license_id, license_text, allow_outlines=False)`

Register an immutable font snapshot with explicit redistribution provenance.

### `savefig(path, **kwargs)`

Static export; renderer="gpu" forwards experimental PNG selection.

### `sca(ax)`

Select an axes and its managed figure without reordering Figure.axes.

### `scatter(*args, **kwargs)`

### `setp(artists, *args, **kwargs)`

Set properties on an artist or nested sequence of artists.

### `show(*, block=True, backend='tk', open_browser=True)`

Show own CPU viewers; desktop loop blocks only when requested.

### `subplot(*args, **kwargs)`

Select/reuse a subplot; explicit projection options can create another.

### `subplot_mosaic(mosaic, *, projection='equirectangular', projection_kw=None, figsize=None, dpi=None, facecolor=None, layout=None, num=None, clear=False, subplot_kw=None, per_subplot_kw=None, gridspec_kw=None, width_ratios=None, height_ratios=None, empty_sentinel='.', sharex=False, sharey=False)`

Return (figure, dict of named axes) for a rectangular or nested mosaic.

### `subplots(nrows=1, ncols=1, *, projection='equirectangular', figsize=None, dpi=None, facecolor=None, squeeze=True, projection_kw=None, subplot_kw=None, layout=None, gridspec_kw=None, width_ratios=None, height_ratios=None, num=None, clear=False, sharex=False, sharey=False)`

### `subplots_adjust(**kwargs)`

### `suptitle(text, **kwargs)`

### `tex_context(config)`

Capture real TeX defaults in new figures/Artists; reset on exit.

### `text(*args, **kwargs)`

### `text_context(*, engine='harfbuzz', direction='auto', language='und', fallback=(), features=())`

Defaults captured by newly composed Artists; reset on exit, thread-local.

### `tick_params(**kwargs)`

### `ticklabel_format(**kwargs)`

### `tight_layout(*, pad=1.08, w_pad=None, h_pad=None, rect=(0, 0, 1, 1))`

### `title(label, **kwargs)`

### `tricontourf(*args, **kwargs)`

### `tripcolor(*args, **kwargs)`

### `xlabel(label, **kwargs)`

### `xlim(*args, **kwargs)`

### `xticks(ticks=None, labels=None, **kwargs)`

### `ylabel(label, **kwargs)`

### `ylim(*args, **kwargs)`

### `yticks(ticks=None, labels=None, **kwargs)`

## azimlib.temporal

### `bounded(value)`

### `freeze(value)`

### `normalizer(template, values, *, rescale)`

### `time_key(value, kind)`

## azimlib.animation

### `bounded(value)`

### `fps_value(value)`

### `frame_index(value, length)`

### `freeze(value)`

## azimlib.colors

### `get_cmap(value='viridis')`

### `sample_color(cmap, t)`

### `to_rgba(color, alpha=None)`

Dependency-free basic CSS/hex or normalized RGB(A) conversion.

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

Classic scalar/RGB/RGBA TIFF, GeoKeys and affine georeference interpreted here.

### `read_kml(source)`

Local KML 2.2/2.3 Point/LineString/Polygon/MultiGeometry placemarks.

### `read_osm(source, *, include_untagged=False)`

Interpret local OSM 0.6 nodes/ways and multipolygon relations strictly.

### `read_raster(source, *, crs=None, world_file=None, extent=None, nodata=None, max_pixels=16000000)`

Scalar or RGB/RGBA image with an explicit extent/world-file, or embedded GeoTIFF.

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

Transform positions; actual XYZ conversion for explicit 3D CRS.

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

## azimlib.tri

### `scalar(value)`

Normalize missing/nonfinite/masked scalars without importing NumPy.

## azimlib.widgets

## azimlib.simplify

### `segment_distance(p, a, b)`

### `simplify_boundaries(data, transform, tolerance)`

Simplify exact shared chains once; preserve IDs/properties/ring direction.

### `simplify_indices(points, tolerance)`

Iterative Douglas-Peucker; bounds each input vertex against its kept chord.

### `simplify_path(points, tolerance)`

## azimlib.temporal.TemporalSeries

`TemporalSeries(times, values, *, unit=None, name='')`

### `at(time, *, method='nearest')`

### `bind(artist, *, scale='global', norm=None)`

### `count(value)`

S.count(value) -> integer -- return number of occurrences of value

### `index(value, start=0, stop=None)`

S.index(value, [start, [stop]]) -> integer -- return first index of value.
Raises ValueError if the value is not present.

### `index_at(time, *, method='nearest')`

## azimlib.temporal.Frame

`Frame(time: object, data: object) -> None`

## azimlib.temporal.ScalarBinding

`ScalarBinding(series, artist, *, scale='global', norm=None)`

### `apply(index)`

## azimlib.atlas.Atlas

`Atlas(pages, *, labels=None)`

### `save(path)`

### `save_pages(directory, *, format='png', dpi=None)`

### `savefig(path)`

## azimlib.atlas.Region

`Region(name: str, extent: tuple) -> None`

## azimlib.timers.Timer

`Timer(figure, interval=200, callbacks=None)`

### `add_callback(func, *args, **kwargs)`

### `close()`

### `remove_callback(func, *args, **kwargs)`

### `start(interval=None)`

### `stop()`

## azimlib.backends.backend_pdf.PdfPages

`PdfPages(filename)`

### `close()`

### `get_pagecount()`

### `savefig(figure=None)`

## azimlib.animation.FuncAnimation

`FuncAnimation(fig, func, frames, *, init_func=None, fargs=(), interval=200, repeat=True, event_source=None, autoplay=True)`

### `add_controls(slider_ax, play_ax=None, *, label='Frame')`

### `close()`

### `pause()`

### `resume()`

### `save(filename, *, writer=None, fps=None, dpi=None)`

Write GIF by default; a video encoder must be explicitly supplied.

### `save_frames(directory, *, prefix='frame', dpi=None)`

### `seek(index, *, draw=True)`

### `set_interval(milliseconds)`

### `step()`

## azimlib.animation.PlaybackControls

`PlaybackControls(animation, slider_ax, play_ax=None, *, label='Frame')`

### `close()`

### `sync()`

## azimlib.animation.PillowWriter

`PillowWriter()`

### `abort()`

### `finish()`

### `setup(path, width, height, fps, count)`

### `write_frame(image)`

## azimlib.animation.FFMpegWriter

`FFMpegWriter(*, executable='ffmpeg')`

### `abort()`

### `finish()`

### `setup(path, width, height, fps, count)`

### `write_frame(image)`

## azimlib.terrain_axes.TerrainAxes

`TerrainAxes(figure, position, *, elev=35, azim=-60, roll=0, proj_type='persp', vertical_exaggeration=1)`

### `add_callback(func)`

### `add_collection(*args, **kwargs)`

### `add_geometries(data, *, style=None, fit=True, crs=None, **kwargs)`

Read GeoJSON; style(feature) can override appearance per feature.

### `add_patch(patch)`

### `annotate(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `autoscale(enable=True, axis='both', tight=None)`

### `autoscale_view(tight=None, scalex=True, scaley=True)`

Fit data bounds on automatic axes; explicit limits remain fixed.

### `borders(**kwargs)`

### `buildings(data, *, height, base=0, coordinates='world', unit='m', color='#aab1b8', shade=True)`

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

### `compass(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `compass_rose(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `contains(mouseevent)`

### `contour(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `contourf(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `countries(**kwargs)`

### `density(lon, lat, *, bins=24, smoothing=1, cmap='sunset', weights=None, extent=None, normalization=None, **kwargs)`

A regular lon/lat count grid with optional Gaussian cell smoothing.

### `earth_moon(position, **kwargs)`

### `eclipse_shadow(geometry, **kwargs)`

Experimental sampled eclipse visualization, not certified event prediction.

### `fill(lon, lat, **kwargs)`

### `findobj(match=None, include_self=True)`

### `fit_extent(data=None, *, margin=0.05)`

Fit point samples using the shortest circular longitude interval.

### `flow(origins, destinations, values, *, geodesic=True, ellipsoid=None, steps=32, minwidth=0.5, maxwidth=4, cmap='viridis', norm=None, vmin=None, vmax=None, **kwargs)`

Own batched geodesic flows: scalar colors, widths in physical points.

### `geojson(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

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

### `get_picker()`

### `get_pickradius()`

### `get_projection()`

### `get_shared_x_axes()`

### `get_shared_y_axes()`

### `get_subplotspec()`

Return the cell selection, or None for manually positioned axes.

### `get_title(loc='center')`

### `get_transform()`

### `get_visible()`

### `get_world_bounds()`

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

### `get_zlim()`

### `graticule(visible=None, which='major', axis='both', *, step=None, labels=None, **kwargs)`

Toggle with no arguments; styling arguments imply visible=True.

### `grid(visible=None, **kwargs)`

Toggle with no arguments; styling arguments imply visible=True.

### `heatmap(values, *, extent, origin='lower', **kwargs)`

Scalar geographic heatmap with imshow's editable image/colorbar contract.

### `hillshade(values, *, extent, dx=1, dy=1, azdeg=315, altdeg=45, vert_exag=1, origin='lower', **kwargs)`

Own Lambertian hillshade; spacing and height must use consistent units.

### `hist2d(lon, lat, *, weights=None, bins=24, extent=None, density=False, **kwargs)`

Weighted histogram; returns (counts,xedges,yedges,mesh).

### `imshow(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `info_box(text, *, position=(0.025, 0.975), **kwargs)`

### `inset(bounds=(0.68, 0.66, 0.28, 0.28), *, projection='equirectangular', projection_kw=None)`

### `inset_axes(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `isosurface(field, level, **style)`

### `label_outer(remove_inner_ticks=False)`

Hide inner labels; optionally hide ticks, using the local SubplotSpec.

### `labels(data, field='name', *, avoid_overlap=True, padding=2, offsets=None, leader=False, placement='auto', repeat=None, priority_field='priority', min_span=0, max_span=None, **kwargs)`

Place feature labels with collision avoidance and local line tangents.

### `lakes(**kwargs)`

### `legend(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `line(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `map(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `margins(*margins, x=None, y=None, tight=True)`

### `minorticks_off()`

### `minorticks_on()`

Enable automatic minor ticks without enabling any grid.

### `moon(position, **kwargs)`

Optional sublunar marker, or finite Earth-fixed lunar body in 3D.

### `moon_path(path, **kwargs)`

### `municipalities(data=None, **kwargs)`

### `neighborhoods(data=None, *, where=None, crs=None, **kwargs)`

Draw supplied neighborhood polygons; where filters properties.

### `nightshade(position, **kwargs)`

### `north_arrow(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `ocean(color='#e5f1f4')`

### `overview(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `pan(dlon, dlat)`

Move the geographic viewport in degrees, preserving its size.

### `pchanged()`

### `pcolormesh(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `pick(mouseevent)`

### `plot(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `plot_surface(X, Y, Z, *, horizontal_unit='m', vertical_unit='m', cmap='terrain', norm=None, color=None, shade=True, light=(1, -1, 2), elevation_reference='unspecified', texture=None, uv=None)`

### `plot_volume(field, *, region=None, **style)`

### `polygon(coordinates, *, holes=None, **kwargs)`

### `properties()`

### `quiver(lon, lat, u, v, C=None, *, scale=None, cmap='viridis', norm=None, vmin=None, vmax=None, **kwargs)`

East/north vectors; scale is data units per axes width.

### `raster(data, *, crs=None, world_file=None, extent=None, nodata=None, **kwargs)`

Draw an explicit GeoRaster or read a locally georeferenced scalar or RGB/RGBA image.

### `region(region, **kwargs)`

Optional spherical region, with explicit fill/boundary resolution.

### `relim(visible_only=False)`

Recompute geographic data bounds without moving the current view.

### `remove()`

### `remove_callback(oid)`

### `rivers(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `roads(data=None, **kwargs)`

### `route(coordinates, *, geodesic=True, steps=64, ellipsoid=None, **kwargs)`

### `scale_bar(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `scatter(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `set(**kwargs)`

### `set_autoscale_on(value)`

### `set_autoscalex_on(value)`

### `set_autoscaley_on(value)`

### `set_axis_off()`

### `set_axis_on()`

### `set_axisbelow(value)`

### `set_bearing(angle)`

### `set_camera(camera)`

### `set_clip_on(value)`

### `set_extent(*args, **kwargs)`

Set (west, east, south, north), matching common map plotting APIs.

### `set_facecolor(color='#e5f1f4')`

### `set_in_layout(value)`

### `set_label(label)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_proj_type(proj_type, *, fov=None)`

### `set_projection(*args, **kwargs)`

Replace projection after domain checks; keep geographic view/data/bearing.

### `set_prop_cycle(*args, **kwargs)`

Set future line/scatter defaults; does not restyle existing Artists.

### `set_title(text, fontdict=None, loc=None, pad=None, **kwargs)`

Set one of three independent titles; pad is measured in points.

### `set_transform(transform)`

### `set_vertical_exaggeration(value)`

### `set_visible(visible)`

### `set_xlabel(text, **style)`

Set the horizontal geographic axis label.

### `set_xlim(left, right=None, **kwargs)`

Set longitude limits; accept ``(left, right)`` or separate values.

### `set_xmargin(value)`

### `set_xscale(value, **kwargs)`

### `set_xticks(ticks, labels=None, *, minor=False, **kwargs)`

### `set_ylabel(text, **style)`

Set the vertical geographic axis label.

### `set_ylim(bottom, top=None, **kwargs)`

Set latitude limits; accept ``(bottom, top)`` or separate values.

### `set_ymargin(value)`

### `set_yscale(value, **kwargs)`

### `set_yticks(ticks, labels=None, *, minor=False, **kwargs)`

### `set_zlabel(text, **style)`

### `set_zlim(bottom, top=None)`

### `sharex(other)`

### `sharey(other)`

### `solar_light(position, **kwargs)`

### `solar_terminator(position, **kwargs)`

### `state(name, **kwargs)`

Draw and fit one Brazilian state by name, postal code or BR-XX.

### `states(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `streets(data=None, *, where=None, crs=None, **kwargs)`

Draw supplied street lines, with linewidth in points, not metres.

### `subtitle(text, **kwargs)`

### `sun(position, **kwargs)`

Optional subsolar marker, or explicit local sky marker on 3D axes.

### `sun_path(path, **kwargs)`

### `terrain(raster, *, origin, elevation_unit='m', elevation_reference='unspecified', **style)`

Hypsometric RGB illumination plus a separate elevation ScalarMappable.

### `text(*args, **kwargs)`

Add a north arrow without replacing the compass rose.

### `tick_params(axis='both', which='major', **kwargs)`

### `ticklabel_format(*, axis='both', style=None, scilimits=None, useOffset=None, useLocale=None, useMathText=None)`

Configure ScalarFormatter on the requested major axes atomically.

### `title(text, **kwargs)`

Fluent geographic shorthand; set_title returns the text artist.

### `tricontourf(triangulation, values, levels=7, **kwargs)`

Fill an own regional Triangulation; masks exclude whole triangles.

### `tripcolor(triangulation, values, *, cmap='viridis', norm=None, vmin=None, vmax=None, shading='flat', **kwargs)`

Flat triangle colors from nodal means; masked nodes/triangles omitted.

### `update(props)`

### `view_init(elev=None, azim=None, roll=None)`

### `volume_slice(field, *, axis='z', position, **style)`

### `zoom(factor=2, center=None)`

Zoom geographic limits by a positive factor (>1 zooms in).

## azimlib.terrain_axes.SurfaceArtist

`SurfaceArtist(mesh, *, norm=None, cmap='terrain', color=None, shade=True, light=(1, -1, 2), elevation_reference='unspecified')`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

### `faces(camera, bounds, aspect, exaggeration, *, with_uv=False)`

### `findobj(match=None, include_self=True)`

### `get_array()`

### `get_children()`

### `get_clim()`

### `get_clip_on()`

### `get_cmap()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_label()`

### `get_norm()`

### `get_picker()`

### `get_pickradius()`

### `get_texture()`

### `get_texture_uv()`

### `get_transform()`

### `get_visible()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_array(values)`

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_color(value)`

### `set_in_layout(value)`

### `set_norm(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_shade(value)`

### `set_texture(texture, uv=None)`

### `set_transform(transform)`

### `set_visible(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.terrain3d.Camera

`Camera(elev: float = 35, azim: float = -60, roll: float = 0, projection: str = 'persp', zoom: float = 1, fov: float = 35, near: float = 0.1, far: float = 100) -> None`

### `matrix(bounds, aspect=1, vertical_exaggeration=1)`

## azimlib.terrain3d.Mesh

`Mesh(vertices: tuple, triangles: tuple) -> None`

## azimlib.terrain3d.LocalFrame

`LocalFrame(lon: float, lat: float) -> None`

### `horizontal(lon, lat)`

## azimlib.widgets.AxesWidget

`AxesWidget(ax, *, occupy=True)`

### `add_callback(func)`

### `connect_event(name, callback)`

### `contains(mouseevent)`

### `disconnect_events()`

### `findobj(match=None, include_self=True)`

### `get_active()`

### `get_children()`

### `get_clip_on()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_picker()`

### `get_pickradius()`

### `get_transform()`

### `get_visible()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_active(value)`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_transform(transform)`

### `set_visible(value)`

### `update(props)`

## azimlib.widgets.Slider

`Slider(ax, label, valmin, valmax, valinit=None, *, valstep=None, orientation='horizontal')`

### `add_callback(func)`

### `connect_event(name, callback)`

### `contains(mouseevent)`

### `disconnect(cid)`

### `disconnect_events()`

### `findobj(match=None, include_self=True)`

### `get_active()`

### `get_children()`

### `get_clip_on()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_picker()`

### `get_pickradius()`

### `get_transform()`

### `get_visible()`

### `on_changed(callback)`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove_callback(oid)`

### `reset()`

### `set(**kwargs)`

### `set_active(value)`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_transform(transform)`

### `set_val(value)`

### `set_visible(value)`

### `update(props)`

## azimlib.widgets.CheckButtons

`CheckButtons(ax, labels, actives=None)`

### `add_callback(func)`

### `connect_event(name, callback)`

### `contains(mouseevent)`

### `disconnect(cid)`

### `disconnect_events()`

### `findobj(match=None, include_self=True)`

### `get_active()`

### `get_children()`

### `get_clip_on()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_picker()`

### `get_pickradius()`

### `get_status()`

### `get_transform()`

### `get_visible()`

### `on_clicked(callback)`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_active(index)`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_transform(transform)`

### `set_visible(value)`

### `update(props)`

## azimlib.widgets.LayerControl

`LayerControl(ax, layers, labels=None)`

### `add_callback(func)`

### `connect_event(name, callback)`

### `contains(mouseevent)`

### `disconnect(cid)`

### `disconnect_events()`

### `findobj(match=None, include_self=True)`

### `get_active()`

### `get_children()`

### `get_clip_on()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_picker()`

### `get_pickradius()`

### `get_status()`

### `get_transform()`

### `get_visible()`

### `on_clicked(callback)`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_active(index)`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_transform(transform)`

### `set_visible(value)`

### `update(props)`

## azimlib.widgets.RectangleSelector

`RectangleSelector(ax, onselect, *, minspanx=0, minspany=0)`

### `add_callback(func)`

### `connect_event(name, callback)`

### `contains(mouseevent)`

### `disconnect_events()`

### `findobj(match=None, include_self=True)`

### `get_active()`

### `get_children()`

### `get_clip_on()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_picker()`

### `get_pickradius()`

### `get_transform()`

### `get_visible()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_active(value)`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_transform(transform)`

### `set_visible(value)`

### `update(props)`

## azimlib.widgets.FeatureSelector

`FeatureSelector(ax, layer, onselect=None, *, tolerance=5)`

### `add_callback(func)`

### `connect_event(name, callback)`

### `contains(mouseevent)`

### `disconnect_events()`

### `findobj(match=None, include_self=True)`

### `get_active()`

### `get_children()`

### `get_clip_on()`

### `get_features()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_picker()`

### `get_pickradius()`

### `get_selection()`

### `get_transform()`

### `get_visible()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_active(value)`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_selection(indices)`

### `set_transform(transform)`

### `set_visible(value)`

### `update(props)`

## azimlib.patterns.Provenance

`Provenance(source: str, license: str, copyright: str, attribution: str = '', sha256: str = '', license_text: str = '') -> None`

## azimlib.patterns.HatchPattern

`HatchPattern(paths: tuple, provenance: azimlib.patterns.Provenance) -> None`

## azimlib.scientific_artists.ColorImage

`ColorImage(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

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

### `get_picker()`

### `get_pickradius()`

### `get_rotation()`

### `get_simplify()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

### `set_clim(*args, **kwargs)`

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_rotation(value)`

### `set_simplify(tolerance)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.scientific_artists.FilledContourSet

`FilledContourSet(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

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

### `get_legend_entries()`

### `get_linestyle()`

### `get_linewidth()`

### `get_marker()`

### `get_markeredgecolor()`

### `get_markeredgewidth()`

### `get_markerfacecolor()`

### `get_markersize()`

### `get_norm()`

### `get_picker()`

### `get_pickradius()`

### `get_rotation()`

### `get_simplify()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

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

### `set_levels(levels)`

### `set_linestyle(value)`

### `set_linewidth(value)`

### `set_marker(value)`

### `set_markeredgecolor(value)`

### `set_markeredgewidth(value)`

### `set_markerfacecolor(value)`

### `set_markersize(value)`

### `set_norm(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_rotation(value)`

### `set_simplify(tolerance)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.scientific_artists.FlowCollection

`FlowCollection(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

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

### `get_legend_entries()`

### `get_linestyle()`

### `get_linewidth()`

### `get_marker()`

### `get_markeredgecolor()`

### `get_markeredgewidth()`

### `get_markerfacecolor()`

### `get_markersize()`

### `get_norm()`

### `get_picker()`

### `get_pickradius()`

### `get_rotation()`

### `get_simplify()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_rotation(value)`

### `set_simplify(tolerance)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.tri.Triangulation

`Triangulation(x, y, triangles=None, mask=None)`

### `field(values)`

### `set_mask(mask)`

## azimlib.tri.LinearTriInterpolator

`LinearTriInterpolator(triangulation, z)`

## azimlib.path.Path

`Path(vertices, codes=None)`

### `to_polylines(steps=24, *, tolerance=None, transform=None, max_depth=16)`

### `transformed(transform)`

## azimlib.patches.PathPatch

`PathPatch(path, **kwargs)`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

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

### `get_picker()`

### `get_pickradius()`

### `get_rotation()`

### `get_simplify()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_rotation(value)`

### `set_simplify(tolerance)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

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

### `contains(mouseevent)`

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

### `get_picker()`

### `get_pickradius()`

### `get_rotation()`

### `get_segments()`

### `get_simplify()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_rotation(value)`

### `set_segments(value)`

### `set_simplify(tolerance)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.subfigure.SubFigure

`SubFigure(figure, position, parent=None)`

### `add_axes(rect=(0.125, 0.11, 0.775, 0.77), **kwargs)`

### `add_callback(func)`

### `add_gridspec(nrows=1, ncols=1, **kwargs)`

### `add_subplot(*args, **kwargs)`

### `clear()`

### `colorbar(mappable, *, ax=None, **kwargs)`

### `contains(mouseevent)`

### `findobj(match=None, include_self=True)`

### `get_children()`

### `get_clip_on()`

### `get_dpi()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_picker()`

### `get_pickradius()`

### `get_size_inches()`

### `get_transform()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_picker(value)`

### `set_pickradius(value)`

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

`GeoRaster(values: tuple, affine: tuple, crs: object = 'EPSG:4326', nodata: float | None = None, pixel_type: str = 'area', color_mode: str = 'auto', mask: object = None, height_frame: object = None) -> None`

### `coordinate(column, row, *, center=False)`

### `geographic_mesh()`

Return lon/lat edges and south-to-north rows for the own mesh Artist.

### `mask_region(region, *, domain='planar', invert=False)`

Return a geographic region mask sampled at pixel centres; no warp.

### `resample(shape, *, extent=None, affine=None, crs=None, method='nearest', missing='strict')`

Own inverse-affine/CRS sampling at destination pixel centres.

### `sample(x, y, *, crs=None, method='nearest', missing='strict')`

Sample one coordinate; outside coverage is missing/transparent.

## azimlib.catalog.DatasetCatalog

`DatasetCatalog(manifest)`

### `available()`

Return detached metadata; editing it does not change the catalog.

### `grid_operation(identifier, *, version=None)`

Load an exact declared grid operation, verifying data and legal notices.

### `load(identifier, *, version=None)`

### `open_pbf(identifier, *, version=None, **index_options)`

Open a verified disk index; caller must close it (prefer ``with``).

### `verify(identifier=None, *, version=None)`

## azimlib.shapefile.DBFRecord

`DBFRecord(index: int, properties: object, deleted: bool = False) -> None`

## azimlib.artist.Artist

`Artist(parent=None)`

### `add_callback(func)`

### `contains(mouseevent)`

### `findobj(match=None, include_self=True)`

### `get_children()`

### `get_clip_on()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_picker()`

### `get_pickradius()`

### `get_transform()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_picker(value)`

### `set_pickradius(value)`

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

### `contains(mouseevent)`

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

### `get_picker()`

### `get_pickradius()`

### `get_size_inches()`

### `get_suptitle()`

### `get_supxlabel()`

### `get_supylabel()`

### `get_transform()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove_callback(oid)`

### `save(path, *, format=None, dpi=None, renderer='cpu', gpu_fallback='raise', gpu_config=None)`

Export static .svg, .png or vector .pdf without UI; streams require format.

### `savefig(path, *, format=None, dpi=None, renderer='cpu', gpu_fallback='raise', gpu_config=None)`

Export static .svg, .png or vector .pdf without UI; streams require format.

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_size_inches(w, h=None, forward=True)`

Set physical figure size; optionally resize an existing desktop canvas.

### `set_transform(transform)`

### `show(*, backend='tk', block=False, open_browser=True, path=None, renderer='cpu', gpu_fallback='raise', gpu_config=None)`

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

### `to_scene(*, cull=False, interactive=False, simplify=True)`

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

### `new_timer(interval=200, callbacks=None)`

### `pick(mouseevent)`

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

### `contains(mouseevent)`

### `contour(lon, lat, values, levels=7, *, cmap='viridis', norm=None, vmin=None, vmax=None, colors=None, linewidths=None, linestyles=None, **kwargs)`

### `contourf(lon, lat, values, levels=7, **kwargs)`

Own filled scalar bands; whole cells adjoining missing nodes are masked.

### `countries(**kwargs)`

### `density(lon, lat, *, bins=24, smoothing=1, cmap='sunset', weights=None, extent=None, normalization=None, **kwargs)`

A regular lon/lat count grid with optional Gaussian cell smoothing.

### `earth_moon(position, **kwargs)`

### `eclipse_shadow(geometry, **kwargs)`

Experimental sampled eclipse visualization, not certified event prediction.

### `fill(lon, lat, **kwargs)`

### `findobj(match=None, include_self=True)`

### `fit_extent(data=None, *, margin=0.05)`

Fit point samples using the shortest circular longitude interval.

### `flow(origins, destinations, values, *, geodesic=True, ellipsoid=None, steps=32, minwidth=0.5, maxwidth=4, cmap='viridis', norm=None, vmin=None, vmax=None, **kwargs)`

Own batched geodesic flows: scalar colors, widths in physical points.

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

### `get_picker()`

### `get_pickradius()`

### `get_projection()`

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

### `heatmap(values, *, extent, origin='lower', **kwargs)`

Scalar geographic heatmap with imshow's editable image/colorbar contract.

### `hillshade(values, *, extent, dx=1, dy=1, azdeg=315, altdeg=45, vert_exag=1, origin='lower', **kwargs)`

Own Lambertian hillshade; spacing and height must use consistent units.

### `hist2d(lon, lat, *, weights=None, bins=24, extent=None, density=False, **kwargs)`

Weighted histogram; returns (counts,xedges,yedges,mesh).

### `imshow(values, *, extent, origin='upper', cmap='viridis', norm=None, vmin=None, vmax=None, **kwargs)`

Scalar or RGB/RGBA geographic image; extent=(west,east,south,north).

### `info_box(text, *, position=(0.025, 0.975), **kwargs)`

### `inset(bounds=(0.68, 0.66, 0.28, 0.28), *, projection='equirectangular', projection_kw=None)`

### `inset_axes(bounds=(0.68, 0.66, 0.28, 0.28), *, projection='equirectangular', projection_kw=None)`

### `label_outer(remove_inner_ticks=False)`

Hide inner labels; optionally hide ticks, using the local SubplotSpec.

### `labels(data, field='name', *, avoid_overlap=True, padding=2, offsets=None, leader=False, placement='auto', repeat=None, priority_field='priority', min_span=0, max_span=None, **kwargs)`

Place feature labels with collision avoidance and local line tangents.

### `lakes(**kwargs)`

### `legend(handles=None, labels=None, *, title=None, loc=None, fontsize=None, frameon=True, facecolor=None, edgecolor=None, framealpha=None, title_fontsize=None, borderpad=0.4, labelspacing=0.5, handlelength=2, handletextpad=0.8, borderaxespad=0.5, ncols=None, ncol=None, columnspacing=2, bbox_to_anchor=None, bbox_transform='axes', mode=None, handler_map=None)`

### `line(coordinates, **kwargs)`

### `map(region='world', **kwargs)`

### `margins(*margins, x=None, y=None, tight=True)`

### `minorticks_off()`

### `minorticks_on()`

Enable automatic minor ticks without enabling any grid.

### `moon(position, **kwargs)`

Optional sublunar marker, or finite Earth-fixed lunar body in 3D.

### `moon_path(path, **kwargs)`

### `municipalities(data=None, **kwargs)`

### `neighborhoods(data=None, *, where=None, crs=None, **kwargs)`

Draw supplied neighborhood polygons; where filters properties.

### `nightshade(position, **kwargs)`

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

### `pick(mouseevent)`

### `plot(*args, data=None, **kwargs)`

Plot one/many lon/lat series, columns and named data; return handles.

### `polygon(coordinates, *, holes=None, **kwargs)`

### `properties()`

### `quiver(lon, lat, u, v, C=None, *, scale=None, cmap='viridis', norm=None, vmin=None, vmax=None, **kwargs)`

East/north vectors; scale is data units per axes width.

### `raster(data, *, crs=None, world_file=None, extent=None, nodata=None, **kwargs)`

Draw an explicit GeoRaster or read a locally georeferenced scalar or RGB/RGBA image.

### `region(region, **kwargs)`

Optional spherical region, with explicit fill/boundary resolution.

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_projection(projection, **parameters)`

Replace projection after domain checks; keep geographic view/data/bearing.

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

### `solar_light(position, **kwargs)`

### `solar_terminator(position, **kwargs)`

### `state(name, **kwargs)`

Draw and fit one Brazilian state by name, postal code or BR-XX.

### `states(country=None, **kwargs)`

### `streets(data=None, *, where=None, crs=None, **kwargs)`

Draw supplied street lines, with linewidth in points, not metres.

### `subtitle(text, **kwargs)`

### `sun(position, **kwargs)`

Optional subsolar marker, or explicit local sky marker on 3D axes.

### `sun_path(path, **kwargs)`

### `terrain(values, *, extent, dx, dy, azdeg=315, altdeg=45, vert_exag=1, origin='lower', cmap='terrain', norm=None, vmin=None, vmax=None, shade=0.65, **kwargs)`

Hypsometric RGB illumination plus a separate elevation ScalarMappable.

### `text(lon, lat, text, *, transform='data', **kwargs)`

### `tick_params(axis='both', which='major', **kwargs)`

### `ticklabel_format(*, axis='both', style=None, scilimits=None, useOffset=None, useLocale=None, useMathText=None)`

Configure ScalarFormatter on the requested major axes atomically.

### `title(text, **kwargs)`

Fluent geographic shorthand; set_title returns the text artist.

### `tricontourf(triangulation, values, levels=7, **kwargs)`

Fill an own regional Triangulation; masks exclude whole triangles.

### `tripcolor(triangulation, values, *, cmap='viridis', norm=None, vmin=None, vmax=None, shading='flat', **kwargs)`

Flat triangle colors from nodal means; masked nodes/triangles omitted.

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

### `contains(mouseevent)`

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

### `get_picker()`

### `get_pickradius()`

### `get_rotation()`

### `get_simplify()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_rotation(value)`

### `set_simplify(tolerance)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.collections.ScatterCollection

`ScatterCollection(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

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

### `get_picker()`

### `get_pickradius()`

### `get_rotation()`

### `get_simplify()`

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

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit points, areas and color data together before notifying observers.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_rotation(value)`

### `set_simplify(tolerance)`

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

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.field_artists.MeshCollection

`MeshCollection(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

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

### `get_picker()`

### `get_pickradius()`

### `get_rotation()`

### `get_simplify()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_rotation(value)`

### `set_simplify(tolerance)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.field_artists.ScalarImage

`ScalarImage(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

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

### `get_picker()`

### `get_pickradius()`

### `get_rotation()`

### `get_simplify()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_rotation(value)`

### `set_simplify(tolerance)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.field_artists.VectorCollection

`VectorCollection(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

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

### `get_picker()`

### `get_pickradius()`

### `get_rotation()`

### `get_scale()`

### `get_simplify()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `legend_elements(num=3)`

Own magnitude proxies: fixed arrow markers, labels in vector units.

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_UVC(U, V, C=None)`

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_rotation(value)`

### `set_scale(value)`

### `set_simplify(tolerance)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.contours.ContourSet

`ContourSet(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `clabel(levels=None, **kwargs)`

### `contains(mouseevent)`

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

### `get_picker()`

### `get_pickradius()`

### `get_rotation()`

### `get_simplify()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_rotation(value)`

### `set_simplify(tolerance)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.contours.ContourLabel

`ContourLabel(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

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

### `get_picker()`

### `get_pickradius()`

### `get_rotation()`

### `get_simplify()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_rotation(value)`

### `set_simplify(tolerance)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

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

### `contains(mouseevent)`

### `findobj(match=None, include_self=True)`

### `get_children()`

### `get_clip_on()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_picker()`

### `get_pickradius()`

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

### `pick(mouseevent)`

### `properties()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_axis_off()`

### `set_axis_on()`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_picker(value)`

### `set_pickradius(value)`

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

### `contains(mouseevent)`

### `findobj(match=None, include_self=True)`

### `get_alpha()`

### `get_children()`

### `get_clip_on()`

### `get_color()`

### `get_direction()`

### `get_figure(root=False)`

### `get_fontfallback()`

### `get_fontfamily()`

### `get_fontfeatures()`

### `get_fontsize()`

### `get_fontstyle()`

### `get_fontweight()`

### `get_ha()`

### `get_horizontalalignment()`

### `get_in_layout()`

### `get_language()`

### `get_picker()`

### `get_pickradius()`

### `get_rotation()`

### `get_rotation_mode()`

### `get_size()`

### `get_texconfig()`

### `get_text()`

### `get_textengine()`

### `get_transform()`

### `get_va()`

### `get_verticalalignment()`

### `get_visible()`

### `get_weight()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_alpha(value)`

### `set_clip_on(value)`

### `set_color(value)`

### `set_direction(value)`

### `set_fontfallback(value)`

### `set_fontfamily(value)`

### `set_fontfeatures(value)`

### `set_fontsize(value)`

### `set_fontstyle(value)`

### `set_fontweight(value)`

### `set_ha(value)`

### `set_horizontalalignment(value)`

### `set_in_layout(value)`

### `set_language(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_rotation(value)`

### `set_rotation_mode(value)`

### `set_size(value)`

### `set_texconfig(value)`

### `set_text(value)`

### `set_textengine(value)`

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

### `contains(mouseevent)`

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

### `get_direction()`

### `get_edgecolor()`

### `get_facecolor()`

### `get_figure(root=False)`

### `get_fontfallback()`

### `get_fontfamily()`

### `get_fontfeatures()`

### `get_fontsize()`

### `get_fontstyle()`

### `get_fontweight()`

### `get_ha()`

### `get_horizontalalignment()`

### `get_in_layout()`

### `get_label()`

### `get_language()`

### `get_linestyle()`

### `get_linewidth()`

### `get_marker()`

### `get_markeredgecolor()`

### `get_markeredgewidth()`

### `get_markerfacecolor()`

### `get_markersize()`

### `get_norm()`

### `get_picker()`

### `get_pickradius()`

### `get_position()`

### `get_rotation()`

### `get_rotation_mode()`

### `get_simplify()`

### `get_size()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_texconfig()`

### `get_text()`

### `get_textengine()`

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

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_color(value)`

### `set_dash_capstyle(value)`

### `set_dash_joinstyle(value)`

### `set_data(*args)`

Replace a geographic plot series; explicit map limits stay unchanged.

### `set_direction(value)`

### `set_edgecolor(value)`

### `set_facecolor(value)`

### `set_fontfallback(value)`

### `set_fontfamily(value)`

### `set_fontfeatures(value)`

### `set_fontsize(value)`

### `set_fontstyle(value)`

### `set_fontweight(value)`

### `set_ha(value)`

### `set_horizontalalignment(value)`

### `set_in_layout(value)`

### `set_label(value)`

### `set_language(value)`

### `set_linestyle(value)`

### `set_linewidth(value)`

### `set_marker(value)`

### `set_markeredgecolor(value)`

### `set_markeredgewidth(value)`

### `set_markerfacecolor(value)`

### `set_markersize(value)`

### `set_norm(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_position(value)`

### `set_rotation(value)`

### `set_rotation_mode(value)`

### `set_simplify(tolerance)`

### `set_size(value)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_texconfig(value)`

### `set_text(value)`

### `set_textengine(value)`

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

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.text_artists.Annotation

`Annotation(kind: 'str', data: 'object', style: 'dict' = <factory>, options: 'dict' = <factory>, visible: 'bool' = True, legend_entries: 'list' = <factory>, _axes: 'object' = None) -> None`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

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

### `get_direction()`

### `get_edgecolor()`

### `get_facecolor()`

### `get_figure(root=False)`

### `get_fontfallback()`

### `get_fontfamily()`

### `get_fontfeatures()`

### `get_fontsize()`

### `get_fontstyle()`

### `get_fontweight()`

### `get_ha()`

### `get_horizontalalignment()`

### `get_in_layout()`

### `get_label()`

### `get_language()`

### `get_linestyle()`

### `get_linewidth()`

### `get_marker()`

### `get_markeredgecolor()`

### `get_markeredgewidth()`

### `get_markerfacecolor()`

### `get_markersize()`

### `get_norm()`

### `get_picker()`

### `get_pickradius()`

### `get_position()`

### `get_rotation()`

### `get_rotation_mode()`

### `get_simplify()`

### `get_size()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_texconfig()`

### `get_text()`

### `get_textengine()`

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

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_anncoords(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_color(value)`

### `set_dash_capstyle(value)`

### `set_dash_joinstyle(value)`

### `set_data(*args)`

Replace a geographic plot series; explicit map limits stay unchanged.

### `set_direction(value)`

### `set_edgecolor(value)`

### `set_facecolor(value)`

### `set_fontfallback(value)`

### `set_fontfamily(value)`

### `set_fontfeatures(value)`

### `set_fontsize(value)`

### `set_fontstyle(value)`

### `set_fontweight(value)`

### `set_ha(value)`

### `set_horizontalalignment(value)`

### `set_in_layout(value)`

### `set_label(value)`

### `set_language(value)`

### `set_linestyle(value)`

### `set_linewidth(value)`

### `set_marker(value)`

### `set_markeredgecolor(value)`

### `set_markeredgewidth(value)`

### `set_markerfacecolor(value)`

### `set_markersize(value)`

### `set_norm(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_position(value)`

### `set_rotation(value)`

### `set_rotation_mode(value)`

### `set_simplify(tolerance)`

### `set_size(value)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_texconfig(value)`

### `set_text(value)`

### `set_textengine(value)`

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

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.figure_text.FigureTextArtist

`FigureTextArtist(x, y, text='', **kwargs)`

### `add_callback(func)`

### `contains(mouseevent)`

### `findobj(match=None, include_self=True)`

### `get_alpha()`

### `get_children()`

### `get_clip_on()`

### `get_color()`

### `get_direction()`

### `get_figure(root=False)`

### `get_fontfallback()`

### `get_fontfamily()`

### `get_fontfeatures()`

### `get_fontsize()`

### `get_fontstyle()`

### `get_fontweight()`

### `get_ha()`

### `get_horizontalalignment()`

### `get_in_layout()`

### `get_language()`

### `get_picker()`

### `get_pickradius()`

### `get_position()`

### `get_rotation()`

### `get_rotation_mode()`

### `get_size()`

### `get_texconfig()`

### `get_text()`

### `get_textengine()`

### `get_transform()`

### `get_va()`

### `get_verticalalignment()`

### `get_visible()`

### `get_weight()`

### `get_x()`

### `get_y()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_alpha(value)`

### `set_clip_on(value)`

### `set_color(value)`

### `set_direction(value)`

### `set_fontfallback(value)`

### `set_fontfamily(value)`

### `set_fontfeatures(value)`

### `set_fontsize(value)`

### `set_fontstyle(value)`

### `set_fontweight(value)`

### `set_ha(value)`

### `set_horizontalalignment(value)`

### `set_in_layout(value)`

### `set_language(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_position(value)`

### `set_rotation(value)`

### `set_rotation_mode(value)`

### `set_size(value)`

### `set_texconfig(value)`

### `set_text(value)`

### `set_textengine(value)`

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

### `contains(mouseevent)`

### `findobj(match=None, include_self=True)`

### `get_children()`

### `get_clip_on()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_picker()`

### `get_pickradius()`

### `get_transform()`

### `get_visible()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_transform(transform)`

### `set_visible(value)`

## azimlib.components.Spine

`Spine(visible: bool = True, color: str = 'black', linewidth: float = 0.8) -> None`

### `add_callback(func)`

### `contains(mouseevent)`

### `findobj(match=None, include_self=True)`

### `get_children()`

### `get_clip_on()`

### `get_color()`

### `get_edgecolor()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_linewidth()`

### `get_picker()`

### `get_pickradius()`

### `get_transform()`

### `get_visible()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_clip_on(value)`

### `set_color(value)`

### `set_edgecolor(value)`

### `set_in_layout(value)`

### `set_linewidth(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_transform(transform)`

### `set_visible(value)`

### `update(props)`

## azimlib.components.Legend

`Legend(**options)`

### `add_callback(func)`

### `contains(mouseevent)`

### `findobj(match=None, include_self=True)`

### `get_children()`

### `get_clip_on()`

### `get_figure(root=False)`

### `get_frame()`

### `get_frame_on()`

### `get_in_layout()`

### `get_picker()`

### `get_pickradius()`

### `get_texts()`

### `get_title()`

### `get_transform()`

### `get_visible()`

### `pchanged()`

### `pick(mouseevent)`

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_title(text, **kwargs)`

### `set_transform(transform)`

### `set_visible(value)`

## azimlib.components.LegendFrame

`LegendFrame(legend)`

### `add_callback(func)`

### `contains(mouseevent)`

### `findobj(match=None, include_self=True)`

### `get_alpha()`

### `get_children()`

### `get_clip_on()`

### `get_edgecolor()`

### `get_facecolor()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_linewidth()`

### `get_picker()`

### `get_pickradius()`

### `get_transform()`

### `get_visible()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_alpha(value)`

### `set_clip_on(value)`

### `set_edgecolor(value)`

### `set_facecolor(value)`

### `set_in_layout(value)`

### `set_linewidth(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_transform(transform)`

### `set_visible(value)`

### `update(props)`

## azimlib.components.OrientationIndicator

`OrientationIndicator(*, axes, slot, loc, size, color, compass=False)`

### `add_callback(func)`

### `contains(mouseevent)`

### `findobj(match=None, include_self=True)`

### `get_angle()`

### `get_children()`

### `get_clip_on()`

### `get_color()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_loc()`

### `get_picker()`

### `get_pickradius()`

### `get_size()`

### `get_transform()`

### `get_visible()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_clip_on(value)`

### `set_color(value)`

### `set_in_layout(value)`

### `set_loc(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_size(value)`

### `set_transform(transform)`

### `set_visible(value)`

## azimlib.components.ScaleBar

`ScaleBar(*, axes=None, slot=None, **options)`

### `add_callback(func)`

### `contains(mouseevent)`

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

### `get_picker()`

### `get_pickradius()`

### `get_transform()`

### `get_units()`

### `get_visible()`

### `pchanged()`

### `pick(mouseevent)`

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_transform(transform)`

### `set_units(value)`

### `set_visible(value)`

## azimlib.colorbar.Colorbar

`Colorbar(axes, mappable, *, orientation=None, location=None, label=None, fraction=0.15, shrink=1, aspect=20, pad=None, ticks=None, format=None, extend='neither', extendfrac=0.05, spacing='uniform', drawedges=False, alpha=1)`

### `add_callback(func)`

### `contains(mouseevent)`

### `findobj(match=None, include_self=True)`

### `get_children()`

### `get_clip_on()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_picker()`

### `get_pickradius()`

### `get_ticks(*, minor=False)`

### `get_transform()`

### `get_visible()`

### `minorticks_off()`

### `minorticks_on()`

Enable subdivisions on the long axis; the short axis remains empty.

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_alpha(value)`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_label(text, *, labelpad=None, loc=None, **kwargs)`

### `set_picker(value)`

### `set_pickradius(value)`

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

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

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

### `clip(region, **kwargs)`

Explicit planar overlay; retain source IDs/properties and order.

### `select(where=None, *, predicate=None, geometry_types=None)`

Return a new collection, preserving feature objects, IDs and order.

### `spatial_select(region, **kwargs)`

Select intersecting features without modifying their geometry.

### `to_geojson()`

## azimlib.crs.CRS

`CRS(code: 'str' = 'EPSG:4326') -> None`

### `to_dict()`

### `to_string()`

### `transform_to(target, x, y, z=None)`

## azimlib.crs.Transformer

`Transformer(source: 'CRS', target: 'CRS') -> None`

### `inverse()`

### `transform(x, y, z=None)`

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

## azimlib.solar_artists.SkySunArtist

`SkySunArtist(value, *, model=None, observer=None, offsets=None, visual_radius=1000.0, symbol_radius=40.0, color='#eea52d')`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

### `faces(camera, bounds, aspect, exaggeration, *, with_uv=False)`

### `findobj(match=None, include_self=True)`

### `get_array()`

### `get_children()`

### `get_clim()`

### `get_clip_on()`

### `get_cmap()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_label()`

### `get_norm()`

### `get_picker()`

### `get_pickradius()`

### `get_position()`

### `get_texture()`

### `get_texture_uv()`

### `get_transform()`

### `get_visible()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_array(values)`

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_color(value)`

### `set_in_layout(value)`

### `set_norm(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_position(value)`

### `set_shade(value)`

### `set_texture(texture, uv=None)`

### `set_time(instant, *, offsets=None)`

### `set_transform(transform)`

### `set_visible(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.solar_artists.SolarBinding

`SolarBinding(series, artist, *, scale='global', norm=None)`

### `apply(index)`

## azimlib.solar_artists.SolarNightshade

`SolarNightshade(value, *, model=None, observer=None, offsets=None, step=5.0, color='#192b45', alpha=0.28, zorder=3)`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

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

### `get_picker()`

### `get_pickradius()`

### `get_position()`

### `get_rotation()`

### `get_simplify()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_position(value)`

### `set_rotation(value)`

### `set_simplify(tolerance)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_time(instant, *, offsets=None)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.solar_artists.SunArtist

`SunArtist(value, *, model=None, observer=None, offsets=None, role='point', samples=361, annotation=None, annotation_style=None, **style)`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

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

### `get_picker()`

### `get_pickradius()`

### `get_position()`

### `get_rotation()`

### `get_simplify()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_annotation(text)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

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

### `set_manual(azimuth, elevation)`

### `set_marker(value)`

### `set_markeredgecolor(value)`

### `set_markeredgewidth(value)`

### `set_markerfacecolor(value)`

### `set_markersize(value)`

### `set_norm(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_position(value)`

### `set_rotation(value)`

### `set_simplify(tolerance)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_time(instant, *, offsets=None)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.lunar_artists.EarthMoonArtist

`EarthMoonArtist(value, *, model=None, observer=None, offsets=None, include_earth=True, distance_scale=1.0, moon_radius_scale=1.0, earth_color='#47869b', moon_color='#c3c5ca', ambient=0.12, shade=True)`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

### `faces(camera, bounds, aspect, exaggeration, *, with_uv=False)`

### `findobj(match=None, include_self=True)`

### `get_array()`

### `get_children()`

### `get_clim()`

### `get_clip_on()`

### `get_cmap()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_label()`

### `get_norm()`

### `get_picker()`

### `get_pickradius()`

### `get_position()`

### `get_texture()`

### `get_texture_uv()`

### `get_transform()`

### `get_visible()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_array(values)`

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_color(value)`

### `set_eclipse_geometry(geometry, *, allow_approximate=False)`

### `set_in_layout(value)`

### `set_manual(azimuth, elevation, distance_m)`

### `set_norm(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_position(value)`

### `set_scales(*, distance_scale=None, moon_radius_scale=None)`

### `set_shade(value)`

### `set_texture(texture, uv=None)`

### `set_time(instant, *, offsets=None)`

### `set_transform(transform)`

### `set_visible(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.lunar_artists.LunarBinding

`LunarBinding(series, artist, *, scale='global', norm=None)`

### `apply(index)`

## azimlib.lunar_artists.LunarHandle

`LunarHandle()`

### `get_position()`

### `set_manual(azimuth, elevation, distance_m)`

### `set_time(instant, *, offsets=None)`

## azimlib.lunar_artists.MoonArtist

`MoonArtist(value, *, model=None, observer=None, offsets=None, annotation=None, annotation_style=None, **style)`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

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

### `get_picker()`

### `get_pickradius()`

### `get_position()`

### `get_rotation()`

### `get_simplify()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_annotation(text)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

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

### `set_manual(azimuth, elevation, distance_m)`

### `set_marker(value)`

### `set_markeredgecolor(value)`

### `set_markeredgewidth(value)`

### `set_markerfacecolor(value)`

### `set_markersize(value)`

### `set_norm(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_position(value)`

### `set_rotation(value)`

### `set_simplify(tolerance)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_time(instant, *, offsets=None)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.eclipse_artists.EclipseBinding

`EclipseBinding(series, artist, *, scale='global', norm=None)`

### `apply(index)`

## azimlib.eclipse_artists.EclipseMapArtist

`EclipseMapArtist(geometry, *, allow_approximate=False, step=4.0, mode='estimate', cmap='viridis', alpha=0.75, zorder=4)`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

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

### `get_geometry()`

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

### `get_picker()`

### `get_pickradius()`

### `get_rotation()`

### `get_simplify()`

### `get_solid_capstyle()`

### `get_solid_joinstyle()`

### `get_text()`

### `get_transform()`

### `get_visible()`

### `get_xdata()`

### `get_ydata()`

### `get_zorder()`

### `pchanged()`

### `pick(mouseevent)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

Edit supported data/text, styles and colors after batch validation.

### `set_alpha(value)`

### `set_antialiased(value)`

### `set_array(values)`

### `set_classes(bins=5, *, scheme='equal_interval')`

Reclassify an own choropleth; geometry/feature IDs remain unchanged.

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

### `set_geometry(geometry)`

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

### `set_picker(value)`

### `set_pickradius(value)`

### `set_rotation(value)`

### `set_simplify(tolerance)`

### `set_solid_capstyle(value)`

### `set_solid_joinstyle(value)`

### `set_text(value)`

### `set_transform(transform)`

### `set_visible(visible)`

### `set_xdata(value)`

### `set_ydata(value)`

### `set_zorder(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.volume_artist.VolumeArtist

`VolumeArtist(field, *, norm=None, cmap='viridis', opacity=None, step=None, reference_length=None, density=1.0, light=None)`

### `add_callback(func)`

### `autoscale()`

### `autoscale_None()`

### `changed()`

### `contains(mouseevent)`

### `findobj(match=None, include_self=True)`

### `get_array()`

### `get_children()`

### `get_clim()`

### `get_clip_on()`

### `get_cmap()`

### `get_data()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_label()`

### `get_norm()`

### `get_opacity()`

### `get_picker()`

### `get_pickradius()`

### `get_transform()`

### `get_visible()`

### `get_zorder()`

### `layer(matrix)`

### `pchanged()`

### `pick(mouseevent)`

### `pick_ray(origin, direction, *, maximum=inf)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_array(field)`

### `set_clim(vmin=None, vmax=None)`

### `set_clip_on(value)`

### `set_cmap(value)`

### `set_data(field)`

### `set_density(value)`

### `set_in_layout(value)`

### `set_light(value)`

### `set_norm(norm)`

### `set_opacity(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_reference_length(value)`

### `set_step(value)`

### `set_transform(transform)`

### `set_visible(value)`

### `to_color(value)`

### `to_rgba(values, alpha=None, bytes=False, norm=True)`

Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

### `update(props)`

## azimlib.volume_artist.VolumeBinding

`VolumeBinding(series, artist, *, scale='global', norm=None)`

### `apply(index)`

## azimlib.pbf.OSMIndex

`OSMIndex(source, *, directory=None, max_disk_bytes=8000000000, reserve_free_bytes=67108864, max_refs=100000, missing='error', expected_sha256=None)`

### `audit_references()`

Scan every way/member, including raw relation types, without repair.

### `close()`

### `collection(*, max_features=100000, max_vertices=1000000, max_bytes=67108864, **filters)`

Materialize only a bounded selected region for the plotting API.

### `features(*, bbox=None, where=None, include_untagged=False)`

Stream complete geometries whose envelopes intersect bbox, AND tags.

### `relations(*, restrictions_only=False, include_incomplete=False)`

Stream raw members/tags; restrictions retain conditional/except tags.

## azimlib.coordinate_operations.CoordinateFrame

`CoordinateFrame(name: str, kind: str, datum: azimlib.geodesy.Datum = Datum(name='WGS84', ellipsoid=Ellipsoid(semi_major_axis=6378137.0, inverse_flattening=298.257223563, name='WGS84'), prime_meridian=0.0), height_reference: str = 'ellipsoidal') -> None`

## azimlib.coordinate_operations.CoordinatePipeline

`CoordinatePipeline(steps: tuple) -> None`

### `inverse()`

### `then(operation)`

### `transform(x, y, z=None, *, epoch=None)`

## azimlib.coordinate_operations.GeodeticConversion

`GeodeticConversion(source: azimlib.coordinate_operations.CoordinateFrame, target: azimlib.coordinate_operations.CoordinateFrame) -> None`

### `inverse()`

### `transform(x, y, z, *, epoch=None)`

## azimlib.coordinate_operations.Helmert

`Helmert(source: azimlib.coordinate_operations.CoordinateFrame, target: azimlib.coordinate_operations.CoordinateFrame, parameters: tuple, convention: str, rates: tuple = None, reference_epoch: float = None, valid_epochs: tuple = None, area_of_use: tuple = None) -> None`

### `inverse()`

### `transform(x, y, z, *, epoch=None)`

## azimlib.datum_grids.GridCoverageError

`GridCoverageError(...)`

## azimlib.datum_grids.GridNoDataError

`GridNoDataError(...)`

## azimlib.datum_grids.GridTile

`GridTile(name: str, parent: str, longitude: float, latitude: float, longitude_step: float, latitude_step: float, rows: int, columns: int, offset: int, depth: int = 0) -> None`

## azimlib.datum_grids.ShiftGrid

`ShiftGrid(format: str, tiles: tuple, _raw: bytes, _endian: str, nodata: tuple = (), metadata: object = <factory>) -> None`

### `accuracy(longitude, latitude)`

NTv2 interpolated (lon,lat) accuracy fields, arcsec; not a guarantee.

### `sample(longitude, latitude)`

## azimlib.grid_operations.GridOperation

`GridOperation(source: azimlib.coordinate_operations.CoordinateFrame, target: azimlib.coordinate_operations.CoordinateFrame, grid: azimlib.datum_grids.ShiftGrid, kind: str, factor: float = 1.0, valid_epochs: tuple = None) -> None`

### `inverse()`

### `transform(x, y, z, *, epoch=None)`

### `transform_raster(raster, *, epoch=None)`

Explicit scalar-height correction at pixel centres; strict grid coverage.

## azimlib.grid_operations.InverseGridOperation

`InverseGridOperation(operation: azimlib.grid_operations.GridOperation) -> None`

### `inverse()`

### `transform(x, y, z, *, epoch=None)`

### `transform_raster(raster, *, epoch=None)`

## azimlib.grid_operations.OperationSet

`OperationSet(operations)`

### `select(source, target, x, y, z, *, epoch=None, name=None)`

## azimlib.geocoding.Address

`Address(house_number: 'str' = '', street: 'str' = '', neighborhood: 'str' = '', city: 'str' = '', state: 'str' = '', country: 'str' = '', postcode: 'str' = '') -> None`

### `as_dict()`

### `display()`

## azimlib.geocoding.AddressRange

`AddressRange(record: 'GeocodingRecord', start_id: 'str', end_id: 'str', step: 'int' = 1) -> None`

## azimlib.geocoding.ExternalGeocoder

`ExternalGeocoder(search, reverse=None)`

### `reverse(*args, **kwargs)`

### `search(*args, **kwargs)`

## azimlib.geocoding.GeocodingLimitError

`GeocodingLimitError(...)`

## azimlib.geocoding.GeocodingRecord

`GeocodingRecord(id: 'str', kind: 'str', names: 'tuple[str, ...]', geometry: 'Geometry', source: 'str', address: 'Address' = <factory>, category: 'str' = '', accuracy_m: 'float | None' = None) -> None`

### `as_dict()`

## azimlib.geocoding.GeocodingResult

`GeocodingResult(record: 'GeocodingRecord', source: 'GeocodingSource', coordinate: 'tuple[float, float]', precision: 'str', score: 'float' = 0.0, match: 'str' = 'exact', distance_m: 'float | None' = None, contains: 'bool' = False, range_ids: 'tuple[str, ...]' = ()) -> None`

### `to_feature(*, boundary=False)`

Normal layer/picking/labels integration; no contacts or query history.

## azimlib.geocoding.GeocodingResults

`GeocodingResults(items: 'tuple[GeocodingResult, ...]', total: 'int', ambiguous: 'bool', truncated: 'bool', diagnostics: 'tuple[str, ...]' = ()) -> None`

### `to_features(*, boundary=False)`

## azimlib.geocoding.GeocodingSource

`GeocodingSource(id: 'str', version: 'str', license: 'str', copyright: 'str', attribution: 'str', origin: 'str', sha256: 'str', notices: 'tuple[str, ...]' = ()) -> None`

### `as_dict()`

## azimlib.geocoding.LocalGeocoder

`LocalGeocoder(directory, *, max_candidates=5000)`

### `close()`

### `reverse(lon, lat, *, radius_m=1000.0, kinds=None, filters=None, limit=10)`

Nearest imported objects/containing regional boundaries, in spherical metres.

### `search(query='', *, filters=None, kinds=None, bbox=None, near=None, radius_m=5000.0, fuzzy=False, prefix=False, interpolate=False, limit=10)`

Own exact/prefix/fuzzy token ranking; score is not a probability.

## azimlib.routing.NetworkSnap

`NetworkSnap(coordinate: 'tuple', distance_m: 'float', node: 'int | None', segment: 'tuple | None', fraction: 'float', _network: 'object') -> None`

## azimlib.routing.RoadEdge

`RoadEdge(id: 'str', way_id: 'int', segment_index: 'int', start: 'int', end: 'int', direction: 'int', geometry: 'tuple', distance_m: 'float', speed_kmh: 'float', tags: 'object') -> None`

## azimlib.routing.RoadGraph

`RoadGraph()`

### `route(origin, destination, *, via=(), objective='distance', algorithm='astar', snap_radius_m=1000, max_states=250000, max_candidates=10000, cancel=None)`

Globally optimal path through ordered stops, retaining turn history.

### `save(directory, *, max_bytes=134217728, reserve_free_bytes=67108864)`

Atomic new-directory JSON index, SHA-256 manifest and original notices.

### `snap(location, *, radius_m=1000, max_candidates=10000)`

Nearest physical edge; ties at disconnected coincident roads are errors.

### `submit(executor, origin, destination, **options)`

Caller-owned executor; no worker touches Artists or opens a viewer.

## azimlib.routing.RoadNode

`RoadNode(id: 'int', coordinate: 'tuple') -> None`

## azimlib.routing.RoadRoute

`RoadRoute(steps: 'tuple', stops: 'tuple', source: 'RoutingSource', profile: 'RoutingProfile', objective: 'str', algorithm: 'str', expanded_states: 'int') -> None`

### `playback(ax, *, frames=100, interval=100, autoplay=False, **marker_style)`

Own FuncAnimation edits one marker on the viewer thread; hold the handle.

### `sample(seconds)`

Clamped estimated-time position; spherical interpolation, not a GPS fix.

### `to_features()`

Editable/pickable source-edge features, without query logs or input addresses.

## azimlib.routing.RouteInstruction

`RouteInstruction(maneuver: 'str', coordinate: 'tuple', way_id: 'int | None', name: 'str', distance_m: 'float', duration_s: 'float') -> None`

## azimlib.routing.RouteStep

`RouteStep(edge: 'RoadEdge', start_fraction: 'float', end_fraction: 'float', geometry: 'tuple') -> None`

## azimlib.routing.RoutingSource

`RoutingSource(id: 'str', version: 'str', license: 'str', copyright: 'str', attribution: 'str', origin: 'str', sha256: 'str', notices: 'tuple[str, ...]' = ()) -> None`

### `as_dict()`

## azimlib.routing.RoutingTask

`RoutingTask(future, event)`

### `cancel()`

### `done()`

### `draw(ax, **style)`

### `result(timeout=None)`

## azimlib.text_engine.ClusterText

`ClusterText(text, layout)`

### `replace(old, new, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

### `split(sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

## azimlib.text_engine.FontPermissionError

`FontPermissionError(...)`

## azimlib.text_engine.FontRecord

`FontRecord(family: str, sha256: str, source: str, license_id: str, license_text: str, copyright: str, coverage: tuple) -> None`

### `notice()`

## azimlib.text_engine.Glyph

`Glyph(font: str, glyph: int, start: int, end: int, x: float, y: float, advance: float, outline: tuple, ink: tuple | None) -> None`

## azimlib.text_engine.MissingGlyphError

`MissingGlyphError(...)`

## azimlib.text_engine.ShapedLine

`ShapedLine(text: str, glyphs: tuple, runs: tuple, width: float, ascent: float, descent: float, ink: tuple, engines: tuple, notices: tuple, signature: tuple) -> None`

## azimlib.text_engine.TextEngineError

`TextEngineError(...)`

## azimlib.text_engine.TextRun

`TextRun(start: int, end: int, direction: str, script: str, font: str, glyph_start: int, glyph_end: int) -> None`

## azimlib.tex.TexConfig

`TexConfig(executable: str = 'tectonic', converter: str = 'pdftocairo', cache_dir: object = None, temp_root: object = None, preamble: str = '\\usepackage{amsmath}', font_notices: tuple = (), resource_files: tuple = (), trusted: bool = False, allow_outlines: bool = False, timeout: float = 30, max_memory_bytes: int = 1073741824, max_temp_bytes: int = 67108864, max_cache_bytes: int = 268435456, fallback: object = None) -> None`

## azimlib.tex.TexError

`TexError(...)`

## azimlib.tex.TexLayout

`TexLayout(width: float, ascent: float, descent: float, commands: tuple, notices: tuple, identity: str, metrics: tuple = (), engine: str = 'tectonic') -> None`

## azimlib.tex.TexResourceError

`TexResourceError(...)`

## azimlib.tex.TexText

`TexText(text, layout)`

### `replace(old, new, count=-1)`

Return a copy with all occurrences of substring old replaced by new.

### `split(sep=None, maxsplit=-1)`

Return a list of the substrings in the string, using sep as the separator string.

## azimlib.tex.TexUnavailableError

`TexUnavailableError(...)`

## azimlib.solar.SolarEvents

`SolarEvents(start: datetime.datetime, end: datetime.datetime, rises: tuple, sets: tuple, transits: tuple, status: str, center_altitude: float, estimated_model_timing_seconds: tuple) -> None`

## azimlib.solar.SolarModel

`SolarModel(time_policy: str = 'strict', aberration: bool = True, parallax: bool = True, refraction: azimlib.solar.SolarRefraction | None = None) -> None`

### `events(day, observer, *, offsets=None, zone=datetime.timezone.utc, center_altitude=-0.8333333333333334)`

### `path(instants, observer, *, offsets=None)`

### `position(instant, observer=None, *, offsets=None)`

### `seasons(year, *, offsets=None)`

## azimlib.solar.SolarPath

`SolarPath(positions: tuple, observer: azimlib._frames.Observer) -> None`

### `mesh(*, visual_radius=1000.0, width=8.0)`

ENU ribbon on a visual sky sphere, not physical Sun-distance geometry.

## azimlib.solar.SolarRefraction

`SolarRefraction(pressure_hpa: float = 1010.0, temperature_c: float = 10.0) -> None`

### `correction(elevation)`

## azimlib.solar.SunDirection

`SunDirection(azimuth: float, elevation: float, observer: azimlib._frames.Observer | None = None) -> None`

## azimlib.solar.SunPosition

`SunPosition(instant: azimlib._timescales.Instant, right_ascension: float, declination: float, distance_m: float, ecliptic_longitude: float, sidereal_angle: float, equation_of_time_minutes: float, fixed: azimlib._frames.Coordinates, observer: azimlib._frames.Observer | None, azimuth: float | None, geometric_elevation: float | None, elevation: float | None, refraction_degrees: float, parallax: bool, aberration: bool, time_policy: str, angular_budget_degrees: float, model: str = 'azim-usno-approx-v1') -> None`

### `night_region()`

### `terminator(*, samples=361)`

## azimlib.lunar.LunarModel

`LunarModel(time_policy: str = 'strict', parallax: bool = True, refraction: azimlib.solar.SolarRefraction | None = None) -> None`

### `path(instants, observer=None, *, offsets=None)`

### `position(instant, observer=None, *, offsets=None)`

## azimlib.lunar.LunarPath

`LunarPath(positions: tuple) -> None`

### `mesh(*, distance_scale=1.0, width=500000.0)`

## azimlib.lunar.MoonDirection

`MoonDirection(azimuth: float, elevation: float, distance_m: float, observer: azimlib._frames.Observer) -> None`

## azimlib.lunar.MoonPosition

`MoonPosition(instant: azimlib._timescales.Instant, right_ascension: float, declination: float, distance_m: float, ecliptic_longitude: float, ecliptic_latitude: float, sidereal_angle: float, fixed: azimlib._frames.Coordinates, sun: azimlib.solar.SunPosition, observer: azimlib._frames.Observer | None, topocentric_right_ascension: float | None, topocentric_declination: float | None, topocentric_distance_m: float | None, azimuth: float | None, geometric_elevation: float | None, elevation: float | None, refraction_degrees: float, parallax: bool, time_policy: str, angular_budget_degrees: float, distance_budget_m: float = 5000000.0, model: str = 'azim-almanac-short-v1') -> None`

## azimlib.lighting.LightingBinding

`LightingBinding(series, artist, *, scale='global', norm=None)`

### `apply(index)`

## azimlib.lighting.ShadowBudget

`ShadowBudget(max_triangles: int = 20000, max_rays: int = 500000, max_triangle_tests: int = 4000000) -> None`

## azimlib.lighting.ShadowIndex

`ShadowIndex(triangles, budget, bias)`

### `blocked(origin, direction, maximum=inf, ignore=None)`

### `reset()`

## azimlib.lighting.SolarLighting

`SolarLighting(axes, value, *, frame, model=None, offsets=None, ambient=0.25, diffuse=0.75, shadows=True, samples=1, angular_radius=None, bias_m=0.001, max_edge_m=None, budget=None)`

### `add_callback(func)`

### `bind_volume(artist, *, shadow_steps=0)`

### `contains(mouseevent)`

### `faces(artist, camera, bounds, aspect, exaggeration, *, with_uv=False)`

### `findobj(match=None, include_self=True)`

### `get_children()`

### `get_clip_on()`

### `get_figure(root=False)`

### `get_in_layout()`

### `get_picker()`

### `get_pickradius()`

### `get_position()`

### `get_transform()`

### `get_visible()`

### `pchanged()`

### `pick(mouseevent)`

### `prepare(artists)`

### `properties()`

### `remove()`

### `remove_callback(oid)`

### `set(**kwargs)`

### `set_clip_on(value)`

### `set_in_layout(value)`

### `set_picker(value)`

### `set_pickradius(value)`

### `set_position(value)`

### `set_time(instant, *, offsets=None)`

### `set_transform(transform)`

### `set_visible(value)`

### `update(props)`

### `volume_light(*, shadow_steps=0)`

## azimlib.eclipse.EclipseGeometry

`EclipseGeometry(sun: azimlib.eclipse.ShadowSphere, moon: azimlib.eclipse.ShadowSphere, source: str, instant: object = None, angular_uncertainty_degrees: float = 0.0, earth_radius_m: float = 6378137.0) -> None`

### `at(point, *, occulter='moon')`

### `compare_solar_disks(observer, conventions)`

### `events(*args, **kwargs)`

### `lunar()`

### `require_visual_permission(allow_approximate)`

### `solar(observer, *, solar_disk=None)`

## azimlib.eclipse.Occultation

`Occultation(visible_fraction: float, classification: str, separation_degrees: float, source_radius_degrees: float, occulter_radius_degrees: float, fraction_bounds: tuple, uncertainty_degrees: float) -> None`

## azimlib.eclipse.ShadowCone

`ShadowCone(source: azimlib.eclipse.ShadowSphere, occulter: azimlib.eclipse.ShadowSphere) -> None`

### `radii(distance_m)`

## azimlib.eclipse.ShadowSphere

`ShadowSphere(center: azimlib._frames.Coordinates, radius_m: float) -> None`

## azimlib.solar_disk.SolarDiskComparison

`SolarDiskComparison(results: tuple) -> None`

## azimlib.solar_disk.SolarDiskConvention

`SolarDiskConvention(name: str, radius_m: float, definition: str, source: str) -> None`

## azimlib.volume.BrickStore

`BrickStore(path: pathlib.Path, shape: tuple, components: int, brick_size: int, header_bytes: int, signature: tuple, sha256: str, summary: dict) -> None`

### `brick(index)`

## azimlib.volume.VolumeBudget

`VolumeBudget(max_dense_bytes: int = 33554432, max_cache_bytes: int = 16777216, max_file_bytes: int = 20000000000, max_samples: int = 64000000, max_steps: int = 512, max_pixels: int = 1000000) -> None`

## azimlib.volume.VolumeField

`VolumeField(shape: tuple, values: bytes | None, origin: tuple = (0.0, 0.0, 0.0), spacing: tuple = (1.0, 1.0, 1.0), components: int = 1, value_unit: str = '1', frame: azimlib.terrain3d.LocalFrame | None = None, store: object = None, budget: azimlib.volume.VolumeBudget = VolumeBudget(max_dense_bytes=33554432, max_cache_bytes=16777216, max_file_bytes=20000000000, max_samples=64000000, max_steps=512, max_pixels=1000000)) -> None`

### `component(component)`

### `iter_bricks(*, brick_size=16)`

### `sample(x, y, z, *, method='linear')`

### `sampler()`

### `select(bounds)`

Copy a bounded nodal ROI, including interpolation support at its edges.

## azimlib.volume.VolumeSampler

`VolumeSampler(field)`

### `node(x, y, z)`

### `sample(p, method='linear')`

## azimlib.renderers.gpu.GpuCancelled

`GpuCancelled(...)`

## azimlib.renderers.gpu.GpuConfig

`GpuConfig(context_backend: str | None = None, max_surface_bytes: int = 268435456, max_cache_bytes: int = 33554432, max_vertices: int = 2000000) -> None`

## azimlib.renderers.gpu.GpuError

`GpuError(...)`

## azimlib.renderers.gpu.GpuRenderer

`GpuRenderer(config=None)`

### `close()`

### `render(scene, scale=1, *, cancel=None, generation=None)`

## azimlib.renderers.gpu.GpuResourceError

`GpuResourceError(...)`

## azimlib.renderers.gpu.GpuUnavailableError

`GpuUnavailableError(...)`

## azimlib.projections.LambertAzimuthalEqualArea

`LambertAzimuthalEqualArea(central_longitude: 'float' = 0.0, central_latitude: 'float' = 0.0, radius: 'float' = 6371008.8) -> None`

### `forward(lon, lat)`

### `inverse(x, y)`

## azimlib.simplify.SimplificationCache

`SimplificationCache(max_bytes=4194304)`

### `clear()`

### `indices(packed, scale, tolerance)`

### `info()`

### `path(packed, scale, tolerance)`
