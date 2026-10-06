# Geographic readers — 0.3.0 development

These APIs are on `dev/0.3.0`, not the published 0.2.0 package. All geometry,
DBF/XML interpretation, affine georeferencing and GeoTIFF GeoKey interpretation
are implemented in Azimlib. Pillow only decodes scalar image pixels. No GIS
library, Matplotlib backend, automatic download or external XML resource is used.

```python
import azimlib as azl

features = azl.read_shapefile("regions.shp", crs="EPSG:4326", encoding="utf-8")
fig, ax = azl.subplots()
ax.geojson(features)  # accepts the common FeatureCollection, regardless of source format
```

`import azimlib.pyplot as plt` remains available for plotting. Data readers are
available through `azimlib` and `azimlib.io`. Caller-owned streams stay open.
Vector outputs use the same immutable Geometry/Feature/FeatureCollection types
as GeoJSON, so selection, per-feature styling and urban layers remain reusable.

## Supported contracts and explicit limits

| Reader | Implemented | Explicit limits |
| --- | --- | --- |
| `read_shapefile(source, *, crs, dbf=None, shx=None, encoding=None, include_deleted=False)` | Null, Point, MultiPoint, Polyline, Polygon; multipartes; corresponding Z types; SHX exact offsets/lengths; DBF alignment | CRS 4326/3857 only; no .prj guessing, M-only, MultiPatch or topology repair. Optional M values on Z records are not represented. Clean closed shells must be clockwise, holes counterclockwise; hole ordering is independent. |
| `read_dbf(source, *, encoding, include_deleted=False)` | No-memo dBASE III/IV/5, C/N/F/L/D, blank values, ISO dates, physical row indices | No memo, FoxPro or encrypted variants. Encoding is explicit, not inferred from platform or language byte. Deleted rows are omitted without renumbering; their fields are not decoded unless requested. |
| `read_kml(source)` | KML 2.2/2.3 placemarks, names/descriptions, ExtendedData strings, Point/LineString/Polygon/MultiGeometry, optional elevation and altitudeMode | No styles, KMZ, Track, Model, overlays, extension namespaces or external resources. Altitude remains the supplied value, not a ground-height conversion. DTD/entities/XInclude/NetworkLink are rejected. |
| `read_osm(source, *, include_untagged=False)` | Local XML 0.6 tagged POIs, ways, multipolygon assembly by node identity, reverse segments, holes and multiple shells | No PBF, streaming planet files, routing/restriction relations, nested relations or topology repair. Missing references, open/branched/repeated-node rings and reused multipolygon ways fail explicitly. Non-multipolygon relations are ignored. Editor metadata is not retained; arbitrary original tags can still contain personal data and must be audited before redistribution. |
| `read_raster(source, *, crs=None, world_file=None, extent=None, nodata=None, max_pixels=...)` | Scalar grayscale/integer/float images, explicit extent or world-file, automatic local .tfw/.pgw/.jgw/.wld discovery, NoData | No RGB/palettes/multiframe, implicit identity coordinates or .prj guessing. Conflicting sidecars fail. Embedded TIFF georeference takes precedence unless explicitly overridden. |
| `read_geotiff(source, *, crs=None, nodata=None, max_pixels=...)` | Classic TIFF in either byte order; single-band top-left scalar data; PixelScale+Tiepoint or 2D affine matrix; GeoKeys 4326/3857; PixelIsArea/Point; GDAL NoData | No BigTIFF, multiple IFDs/bands, palette/RGB, user-defined CRS, alternate units or 3D/projective transforms. Uncompressed 16-bit/float and deflate scalar fixtures are tested; other codecs depend on the installed Pillow build. Explicit CRS conflicts are errors. |

SHP binary inputs are bounded to 256 MiB; XML is bounded to 64 MiB. Readers load
files in memory. Image decoding defaults to 16 million pixels, independently
of the encoded-byte bound. These limits do not promise resistance to every
adversarial file; reject untrusted oversized data before processing.

OSM area classification uses `area=yes`, or building/landuse/leisure/amenity
tags except `no`, or natural=water; `area=no` takes precedence. Closed highways
otherwise remain lines. Multipolygon member ways are omitted as standalone
features; IDs are namespaced as `node/123`, `way/123`, `relation/123`.

## Affine coordinates and raster Artists

```python
raster = azl.GeoRaster([[1, 2], [3, None]], (1, 0, -48, 0, -1, -20))
fig, ax = azl.subplots()
image = ax.raster(raster, cmap="viridis")
fig.colorbar(image, ax=ax, label="Value")
image.set_clim(0, 5)
```

`GeoRaster` is immutable. Its `(a,b,c,d,e,f)` maps pixel **corners**:
`x=a*column+b*row+c`, `y=d*column+e*row+f`. `coordinate(..., center=True)`
adds half a pixel. `shape` is `(rows, columns)`; `extent` is `(west,east,south,north)`
in the source CRS; `bounds` is `(west,south,east,north)`. NaN/infinity and NoData
become masked `None`. `read_world_file()` converts A,D,B,E,C,F pixel-centre
coefficients to this corner convention, including rotation.

`ax.raster()` uses the own pcolormesh/ScalarMappable Artist: norm, cmap, clim,
colorbar and visibility remain editable. No legend, grid, north arrow or minimap
appears automatically. Axis-aligned 4326/3857 rasters can be drawn; rotated/sheared
affines are preserved by the reader but plotting rejects them before changing
the axes. Curvilinear drawing and resampling belong to later roadmap steps.
PixelIsPoint is normalized by a half-pixel origin shift, not guessed as PixelIsArea.

## Independent implementation references

The readers were implemented from format descriptions, not ported from another
reader's source code. Tests generate original binary/XML fixtures, including
invalid records. An external Natural Earth populated-places SHP/SHX/DBF (243
points) also parsed successfully during local verification; those files are not
vendored. The real OSM example is a separately licensed derivative database.

- [ESRI Shapefile specification](https://www.esri.com/library/whitepapers/pdfs/shapefile.pdf).
- [dBASE format reference](https://www.dbase.com/Knowledgebase/INT/db7_file_fmt.htm)
  and [Library of Congress DBF families](https://www.loc.gov/preservation/digital/formats/fdd/fdd000325.shtml).
- [OGC KML 2.3](https://docs.ogc.org/is/12-007r2/12-007r2.html).
- [OSM XML 0.6](https://wiki.openstreetmap.org/wiki/OSM_XML).
- [OGC GeoTIFF 1.1](https://docs.ogc.org/is/19-008r4/19-008r4.html).
- [ESRI world-file convention](https://doc.esri.com/en/arcgis-pro/latest/help/data/imagery/world-files-for-raster-datasets.html).

See [optional data](optional-data.md), [georaster example](../examples/georaster.py)
and [format tests](../tests/test_formats.py).
