"""Own affine georeferencing and GeoTIFF tags; Pillow only decodes pixels."""
from dataclasses import dataclass
from math import isfinite, isnan
from pathlib import Path
from struct import unpack_from, calcsize
import io

from ._readers import binary
from .crs import CRS, transform
from .geometry import _number


@dataclass(frozen=True)
class GeoRaster:
    """Immutable scalar rows and corner affine (a,b,c,d,e,f) in source CRS.

    x=a*column+b*row+c, y=d*column+e*row+f, at pixel CORNERS. Rows follow file
    order. Values equal to NoData, NaN and +/-inf become None. Coordinate
    transforms/extent are separate from rendering; no silent reprojection.
    """
    values: tuple
    affine: tuple
    crs: object = 'EPSG:4326'
    nodata: float | None = None
    pixel_type: str = 'area'

    def __post_init__(self):
        if self.pixel_type not in ('area', 'point'): raise ValueError('pixel_type must be area or point')
        affine = tuple(_number(v, 'affine coefficient') for v in self.affine)
        if len(affine) != 6 or affine[0]*affine[4]-affine[1]*affine[3] == 0:
            raise ValueError('Raster affine requires six finite coefficients and an invertible transform')
        nodata = None if self.nodata is None else float(self.nodata)
        if nodata is not None and not (isfinite(nodata) or isnan(nodata)):
            raise ValueError('NoData must be finite or NaN')
        rows = []
        for row in self.values:
            output = []
            for value in row:
                if value is None: output.append(None); continue
                number = float(value)
                output.append(None if not isfinite(number) or nodata is not None and number == nodata else number)
            rows.append(tuple(output))
        if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
            raise ValueError('Raster requires a nonempty rectangular scalar matrix')
        object.__setattr__(self, 'values', tuple(rows))
        object.__setattr__(self, 'affine', affine)
        object.__setattr__(self, 'crs', CRS.from_user_input(self.crs))
        object.__setattr__(self, 'nodata', nodata)

    @property
    def shape(self): return len(self.values), len(self.values[0])

    def coordinate(self, column, row, *, center=False):
        column, row = _number(column), _number(row)
        if center: column += .5; row += .5
        a, b, c, d, e, f = self.affine
        return a*column+b*row+c, d*column+e*row+f

    @property
    def bounds(self):
        ny, nx = self.shape
        points = [self.coordinate(c, r) for c, r in ((0, 0), (nx, 0), (nx, ny), (0, ny))]
        return min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)

    @property
    def extent(self):
        w, s, e, n = self.bounds
        return w, e, s, n

    def geographic_mesh(self):
        """Return lon/lat edges and south-to-north rows for the own mesh Artist.

        Axis-aligned EPSG:4326/3857 only in this initial renderer integration.
        Rotated/sheared affines remain representable, but plotting rejects them
        until curvilinear meshes are supported. No resampling is performed.
        """
        a, b, c, d, e, f = self.affine
        if self.crs.zone:
            raise ValueError('UTM raster plotting requires a curvilinear mesh; not yet supported')
        if b != 0 or d != 0:
            raise ValueError('Rotated/sheared raster plotting requires a curvilinear mesh; not yet supported')
        ny, nx = self.shape
        x = tuple(transform(c+a*i, f, self.crs, 'EPSG:4326')[0] for i in range(nx+1))
        y = tuple(transform(c, f+e*j, self.crs, 'EPSG:4326')[1] for j in range(ny+1))
        rows = self.values
        if a < 0: x = x[::-1]; rows = tuple(row[::-1] for row in rows)
        if e < 0: y = y[::-1]; rows = rows[::-1]
        return x, y, rows


def read_world_file(source):
    """Convert six world-file values A,D,B,E,C,F (pixel centres) to corner affine."""
    if isinstance(source, str) and ('\n' in source or '\r' in source): text = source
    elif isinstance(source, bytes): text = source.decode('utf-8-sig')
    elif hasattr(source, 'read'):
        text = source.read()
        if isinstance(text, bytes): text = text.decode('utf-8-sig')
    else: text = Path(source).read_text('utf-8-sig')
    fields = text.split()
    if len(fields) != 6: raise ValueError('World file requires exactly six numbers')
    try: a, d, b, e, c, f = (float(v) for v in fields)
    except ValueError as exc: raise ValueError('Invalid world-file number') from exc
    values = (a, b, c-(a+b)/2, d, e, f-(d+e)/2)
    if not all(isfinite(v) for v in values) or a*e-b*d == 0:
        raise ValueError('World-file affine is nonfinite or singular')
    return values


def _pixels(raw, max_pixels):
    if isinstance(max_pixels, bool) or not isinstance(max_pixels, int) or max_pixels < 1:
        raise ValueError('max_pixels must be a positive integer')
    try: from PIL import Image
    except ImportError as exc: raise ImportError('Raster pixel decoding requires azimlib[png] (Pillow)') from exc
    with Image.open(io.BytesIO(raw)) as image:
        if image.width*image.height > max_pixels: raise ValueError('Raster exceeds pixel limit')
        if getattr(image, 'n_frames', 1) != 1: raise ValueError('Only single-image rasters are supported')
        if image.mode not in ('L', 'I', 'F', 'I;16', 'I;16B', 'I;16L'):
            raise ValueError('Initial raster reader supports scalar grayscale/integer/float images, not RGB/palettes')
        image.load()
        # Avoid flattening an entire image through a second optional numerical engine.
        rows = tuple(tuple(image.getpixel((i, j)) for i in range(image.width)) for j in range(image.height))
        return rows, image.size


def _tiff_tags(raw):
    """Read one classic TIFF IFD independently; no geospatial TIFF dependency."""
    if len(raw) < 8 or raw[:2] not in (b'II', b'MM'): raise ValueError('Invalid TIFF byte order')
    endian = '<' if raw[:2] == b'II' else '>'
    if unpack_from(endian+'H', raw, 2)[0] != 42: raise ValueError('Only classic TIFF is supported; BigTIFF is not')
    offset = unpack_from(endian+'I', raw, 4)[0]
    if offset < 8 or offset+2 > len(raw): raise ValueError('Invalid TIFF IFD offset')
    count = unpack_from(endian+'H', raw, offset)[0]
    end = offset+2+12*count
    if end+4 > len(raw) or unpack_from(endian+'I', raw, end)[0] != 0:
        raise ValueError('Truncated or multi-image TIFF IFD')
    formats = {1: 'B', 2: 'c', 3: 'H', 4: 'I', 5: 'II', 6: 'b', 7: 'B', 8: 'h', 9: 'i', 10: 'ii', 11: 'f', 12: 'd'}
    tags = {}
    for cursor in range(offset+2, end, 12):
        tag, kind, length = unpack_from(endian+'HHI', raw, cursor)
        if tag in tags: raise ValueError('Duplicate TIFF tag')
        if kind not in formats: raise ValueError('Unsupported TIFF field type')
        fmt = formats[kind]; size = calcsize(endian+fmt)*length
        address = cursor+8 if size <= 4 else unpack_from(endian+'I', raw, cursor+8)[0]
        if address+size > len(raw): raise ValueError('TIFF tag points outside file')
        payload = raw[address:address+size]
        if kind == 2:
            tags[tag] = payload.rstrip(b'\0').decode('ascii')
        else:
            tags[tag] = unpack_from(endian+fmt*length, payload)
    return tags


def read_geotiff(source, *, crs=None, nodata=None, max_pixels=16_000_000):
    """Classic single-band TIFF, GeoKeys and affine georeference interpreted here.

    TIFF pixels/codecs are decoded by Pillow, not a cartography library. Support
    EPSG:4326/3857, PixelIsArea/Point, PixelScale+Tiepoint or 4x4 affine matrix;
    reject ambiguous CRS, orientation, extra images/bands and unsupported tags.
    Raster coordinates are always normalized to pixel corners.
    """
    raw = binary(source); tags = _tiff_tags(raw)
    def scalar(tag, default=None):
        value = tags.get(tag, (default,))
        if not isinstance(value, tuple) or len(value) != 1: raise ValueError(f'Invalid TIFF scalar tag {tag}')
        return value[0]
    if scalar(277, 1) != 1 or scalar(274, 1) != 1 or scalar(284, 1) != 1:
        raise ValueError('Only one-band, top-left oriented contiguous GeoTIFF is supported')
    if scalar(262, 1) != 1: raise ValueError('Only black-is-zero scalar GeoTIFF is supported')
    keys = {}; directory = tags.get(34735)
    if directory is not None:
        if not isinstance(directory, tuple) or len(directory) < 4 or directory[:2] != (1, 1) or directory[2] not in (0, 1) or len(directory) != 4+4*directory[3]:
            raise ValueError('Invalid GeoKeyDirectory')
        for i in range(4, len(directory), 4):
            key, location, count, value = directory[i:i+4]
            if key in keys: raise ValueError('Duplicate GeoKey')
            if key in (1024, 1025, 2048, 2054, 3072, 3076):
                if location != 0 or count != 1: raise ValueError('Core GeoKeys must use one inline SHORT value')
                keys[key] = value
    code = keys.get(3072) if keys.get(1024) == 1 else keys.get(2048)
    tagged_crs = None if code is None else CRS.from_user_input(code)
    if crs is None and tagged_crs is None: raise ValueError('GeoTIFF requires a supported CRS GeoKey or explicit crs')
    chosen = tagged_crs if crs is None else CRS.from_user_input(crs)
    if tagged_crs is not None and tagged_crs != chosen: raise ValueError('Explicit CRS conflicts with GeoTIFF CRS')
    if keys.get(1024, 2 if chosen.is_geographic else 1) != (2 if chosen.is_geographic else 1):
        raise ValueError('GeoTIFF model type/CRS mismatch')
    if keys.get(2054, 9102) != 9102 or keys.get(3076, 9001) != 9001:
        raise ValueError('Unsupported GeoTIFF angular/linear units')
    pixel = keys.get(1025, 1)
    if pixel not in (1, 2): raise ValueError('Unsupported GeoTIFF raster type')
    if 34264 in tags:
        if 33550 in tags or 33922 in tags: raise ValueError('Conflicting GeoTIFF affine definitions')
        matrix = tags[34264]
        if len(matrix) != 16 or any(matrix[i] != value for i, value in ((2, 0), (6, 0), (8, 0), (9, 0), (12, 0), (13, 0), (14, 0), (15, 1))):
            raise ValueError('Unsupported non-2D/projective GeoTIFF matrix')
        affine = matrix[0], matrix[1], matrix[3], matrix[4], matrix[5], matrix[7]
    else:
        scale, ties = tags.get(33550), tags.get(33922)
        if scale is None or ties is None or len(scale) != 3 or len(ties) < 6 or len(ties) % 6 or scale[0] == 0 or scale[1] == 0:
            raise ValueError('GeoTIFF requires PixelScale and valid Tiepoint tags')
        a, e = scale[0], -scale[1]; i, j, _, x, y, _ = ties[:6]
        affine = a, 0, x-i*a, 0, e, y-j*e
        for k in range(0, len(ties), 6):
            ri, rj, _, rx, ry, _ = ties[k:k+6]
            if abs(affine[2]+a*ri-rx) > 1e-8*max(1, abs(rx)) or abs(affine[5]+e*rj-ry) > 1e-8*max(1, abs(ry)):
                raise ValueError('GeoTIFF tiepoints disagree with affine')
    if pixel == 2:
        a, b, c, d, e, f = affine
        affine = a, b, c-(a+b)/2, d, e, f-(d+e)/2
    tagged_nodata = tags.get(42113)
    if nodata is None and tagged_nodata is not None: nodata = float(tagged_nodata)
    rows, size = _pixels(raw, max_pixels)
    if size != (scalar(256), scalar(257)): raise ValueError('Decoded TIFF dimensions differ from tags')
    return GeoRaster(rows, affine, chosen, nodata, 'area' if pixel == 1 else 'point')


def read_raster(source, *, crs=None, world_file=None, extent=None, nodata=None, max_pixels=16_000_000):
    """Scalar image with an explicit extent/world-file, or embedded GeoTIFF.

    Extent is (west,east,south,north) in the supplied source CRS. Local paths
    discover .tfw/.pgw/.jgw, full-extension-w, or .wld. No .prj guessing; no
    identity georeferencing fallback. Rotation is retained, not flattened.
    """
    if world_file is not None and extent is not None: raise ValueError('Use world_file or extent, not both')
    raw = binary(source)
    if extent is None and world_file is None and raw[:4] in (b'II*\0', b'MM\0*'):
        # Embedded georeferencing takes precedence; override explicitly with a world file.
        tags = _tiff_tags(raw)
        if any(tag in tags for tag in (33550, 33922, 34264)):
            return read_geotiff(raw, crs=crs, nodata=nodata, max_pixels=max_pixels)
    if world_file is None and extent is None and isinstance(source, (str, Path)):
        path = Path(source); suffix = path.suffix
        candidates = [path.with_suffix(suffix+'w'), path.with_suffix('.'+suffix[1]+suffix[-1]+'w') if len(suffix) >= 3 else path.with_suffix(suffix+'w'), path.with_suffix('.wld')]
        found = [p for p in dict.fromkeys(candidates) if p.is_file()]
        if len(found) > 1 and len({p.read_bytes() for p in found}) > 1: raise ValueError('Conflicting world-file sidecars')
        if found: world_file = found[0]
    if crs is None: raise ValueError('Raster extent/world-file requires explicit crs')
    if world_file is None and extent is None: raise ValueError('Raster requires georeferencing, not pixel coordinates')
    rows, (nx, ny) = _pixels(raw, max_pixels)
    if world_file is not None: affine = read_world_file(world_file)
    else:
        w, e, s, n = (_number(v, 'extent') for v in extent)
        if w >= e or s >= n: raise ValueError('Extent must be increasing')
        affine = (e-w)/nx, 0, w, 0, (s-n)/ny, n
    return GeoRaster(rows, affine, crs, nodata)
