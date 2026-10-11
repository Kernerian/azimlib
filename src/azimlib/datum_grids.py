"""Own bounded NTv2/GTX readers and strict bilinear interpolation.

Only numeric grid data are consumed; no external coordinate engine is used.
NTv2 longitudes/shifts are positive west in the file, east in this public API.
See docs/datum-grids.md for supported variants and model/accuracy contracts.
"""
from dataclasses import dataclass, field
import hashlib
import math
from pathlib import Path
import struct
from types import MappingProxyType

from .geometry import _number


class GridCoverageError(ValueError):
    """No grid tile covers this coordinate; extrapolation is forbidden."""


class GridNoDataError(ValueError):
    """A positive-weight interpolation node is missing; no fallback is applied."""


def _limit(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f'{name} must be a positive integer')
    return value


def _bytes(source, max_bytes):
    _limit(max_bytes, 'max_bytes')
    if isinstance(source, bytes):
        raw = source
    else:
        with Path(source).open('rb') as stream:
            chunks, count = [], 0
            while True:
                chunk = stream.read(min(1024*1024,max_bytes-count+1))
                if not chunk: break
                count += len(chunk)
                if count > max_bytes: raise ValueError('Grid exceeds max_bytes')
                chunks.append(chunk)
            raw = b''.join(chunks)
    if len(raw) > max_bytes:
        raise ValueError('Grid exceeds max_bytes')
    return raw


def _sentinels(values):
    # Match sentinels after the same IEEE float32 quantization as grid nodes.
    try:
        return tuple(struct.unpack('>f', struct.pack('>f', _number(v, 'NoData')))[0]
                     for v in values)
    except OverflowError as exc:
        raise ValueError('NoData must be representable as float32') from exc


@dataclass(frozen=True)
class GridTile:
    """Read-only node geometry; values stay packed, without Python float arrays."""
    name: str
    parent: str
    longitude: float
    latitude: float
    longitude_step: float
    latitude_step: float
    rows: int
    columns: int
    offset: int
    depth: int = 0

    @property
    def bounds(self):
        other = self.longitude + (self.columns-1)*self.longitude_step
        return min(self.longitude, other), self.latitude, max(self.longitude, other), self.latitude+(self.rows-1)*self.latitude_step

    def _indices(self, lon, lat):
        w, s, e, n = self.bounds
        # Resolve equivalent canonical longitude only when it falls IN this tile.
        lon += 360*round(((w+e)/2-lon)/360)
        x = (lon-self.longitude)/self.longitude_step
        y = (lat-self.latitude)/self.latitude_step
        tolerance = 1e-9  # node-index rounding, not an extrapolation margin
        if not -tolerance <= x <= self.columns-1+tolerance or not -tolerance <= y <= self.rows-1+tolerance:
            raise GridCoverageError('Coordinate outside grid coverage')
        return min(self.columns-1, max(0., x)), min(self.rows-1, max(0., y))


@dataclass(frozen=True)
class ShiftGrid:
    """Immutable packed grid. sample returns (east,north) arcsec or (offset,) m.

    Bilinear interpolation preserves all float32 node precision in float64
    arithmetic. Finest nested tile wins, including its NoData; never substitute
    a parent value. Shared sibling edges use the lexically first tile name.
    """
    format: str
    tiles: tuple
    _raw: bytes = field(repr=False)
    _endian: str = field(repr=False)
    nodata: tuple = ()
    metadata: object = field(default_factory=dict)

    def __post_init__(self):
        if self.format not in ('ntv2', 'gtx') or not isinstance(self._raw, bytes):
            raise ValueError('Use read_ntv2/read_gtx to construct a supported grid')
        object.__setattr__(self, 'tiles', tuple(self.tiles))
        object.__setattr__(self, 'nodata', _sentinels(self.nodata))
        object.__setattr__(self, 'metadata', MappingProxyType(dict(self.metadata)))

    @property
    def sha256(self): return hashlib.sha256(self._raw).hexdigest()

    @property
    def units(self): return 'arcseconds' if self.format == 'ntv2' else 'metres'

    def _tile(self, lon, lat):
        lon, lat = _number(lon, 'longitude'), _number(lat, 'latitude')
        if not -180 <= lon <= 180 or not -90 <= lat <= 90:
            raise GridCoverageError('Require canonical lon/lat degrees')
        for tile in sorted(self.tiles, key=lambda t: (-t.depth, abs(t.longitude_step*t.latitude_step), t.name)):
            try:
                tile._indices(lon, lat)
                return tile
            except GridCoverageError:
                pass
        raise GridCoverageError('Coordinate outside grid coverage')

    def _node(self, tile, column, row):
        count = 4 if self.format == 'ntv2' else 1
        values = struct.unpack_from(self._endian+'f'*count, self._raw, tile.offset+count*4*(row*tile.columns+column))
        return values

    def _sample(self, lon, lat, accuracy=False):
        tile = self._tile(lon, lat)
        x, y = tile._indices(lon, lat)
        i, j = min(int(x), tile.columns-2), min(int(y), tile.rows-2)
        u, v = x-i, y-j
        parts = []
        for dx, dy, weight in ((0,0,(1-u)*(1-v)), (1,0,u*(1-v)), (0,1,(1-u)*v), (1,1,u*v)):
            if weight <= 0:
                continue
            node = self._node(tile, i+dx, j+dy)
            values = node[2:] if accuracy else node[:2] if self.format == 'ntv2' else node
            if any(not math.isfinite(value) or value in self.nodata or accuracy and value < 0 for value in values):
                raise GridNoDataError('Interpolation requires missing or unknown grid values')
            parts.append((values, weight))
        result = tuple(math.fsum(values[k]*weight for values, weight in parts) for k in range(len(parts[0][0])))
        return (result[1], result[0]) if accuracy else (-result[1], result[0]) if self.format == 'ntv2' else result

    def sample(self, longitude, latitude):
        return self._sample(longitude, latitude)

    def accuracy(self, longitude, latitude):
        """NTv2 interpolated (lon,lat) accuracy fields, arcsec; not a guarantee."""
        if self.format != 'ntv2':
            raise ValueError('GTX carries no accuracy fields; consult model metadata')
        return self._sample(longitude, latitude, accuracy=True)


def read_gtx(source, *, nodata=(-88.8888,), max_bytes=128*1024*1024, max_nodes=16_000_000):
    """NOAA binary GTX: big-endian 4 doubles, 2 int32, float32 nodes (2009+).

    Positive increments, >=2 nodes per axis. Older float64/ASCII variants fail.
    Units/direction/registration are model metadata, never inferred from suffix.
    """
    raw = _bytes(source, max_bytes); _limit(max_nodes, 'max_nodes')
    if len(raw) < 40:
        raise ValueError('Truncated GTX header')
    lat, lon, dy, dx, rows, cols = struct.unpack_from('>4d2i', raw)
    if not all(math.isfinite(v) for v in (lat,lon,dy,dx)) or dx <= 0 or dy <= 0 or rows < 2 or cols < 2:
        raise ValueError('Invalid GTX geometry')
    if rows*cols > max_nodes or len(raw) != 40+4*rows*cols:
        raise ValueError('GTX size/node limit mismatch or unsupported precision')
    if lat < -90 or lat+(rows-1)*dy > 90+1e-10 or not -360 <= lon <= 360 or (cols-1)*dx > 360+1e-10:
        raise ValueError('GTX geographic extent invalid')
    return ShiftGrid('gtx', (GridTile('GTX', 'NONE', lon,lat,dx,dy,rows,cols,40),), raw, '>', nodata)


def read_ntv2(source, *, nodata=(), max_bytes=128*1024*1024, max_nodes=16_000_000, max_tiles=4096):
    """NTv2 GSB, 11/11-record headers, SECONDS, either endian, nested subgrids.

    Validates header keys, dimensions, parent containment/alignment, hierarchy,
    sibling overlap and trailing records before returning any transformation.
    """
    raw = _bytes(source, max_bytes)
    _limit(max_nodes,'max_nodes'); _limit(max_tiles,'max_tiles')
    if len(raw) < 176 or raw[:8] != b'NUM_OREC':
        raise ValueError('Invalid/truncated NTv2 overview')
    endian = '<' if struct.unpack_from('<i',raw,8)[0] == 11 else '>'
    cursor = 0
    def record(key, kind):
        nonlocal cursor
        if cursor+16 > len(raw) or raw[cursor:cursor+8].decode('ascii',errors='replace').strip() != key:
            raise ValueError(f'Invalid/truncated NTv2 {key} record')
        value = raw[cursor+8:cursor+16]; cursor += 16
        if kind == 's':
            try: return value.decode('ascii').strip()
            except UnicodeError as exc: raise ValueError('Non-ASCII NTv2 header') from exc
        if kind == 'i':
            if value[4:] != b'\0'*4: raise ValueError('Unsupported NTv2 integer layout')
            return struct.unpack_from(endian+'i',value)[0]
        return struct.unpack(endian+'d',value)[0]
    if record('NUM_OREC','i') != 11 or record('NUM_SREC','i') != 11:
        raise ValueError('Only 11/11 NTv2 headers supported')
    count = record('NUM_FILE','i')
    if not 1 <= count <= max_tiles or record('GS_TYPE','s') != 'SECONDS':
        raise ValueError('Unsupported NTv2 units/tile count')
    metadata = {key:record(key,'s') for key in ('VERSION','SYSTEM_F','SYSTEM_T')}
    for key in ('MAJOR_F','MINOR_F','MAJOR_T','MINOR_T'):
        metadata[key] = record(key,'d')
    if any(not math.isfinite(metadata[k]) or metadata[k] <= 0 for k in ('MAJOR_F','MINOR_F','MAJOR_T','MINOR_T')):
        raise ValueError('Invalid NTv2 ellipsoid axes')
    if metadata['MINOR_F'] > metadata['MAJOR_F'] or metadata['MINOR_T'] > metadata['MAJOR_T']:
        raise ValueError('Invalid NTv2 ellipsoid axes')
    tiles, nodes = [], 0
    for _ in range(count):
        name, parent = record('SUB_NAME','s'), record('PARENT','s')
        record('CREATED','s'); record('UPDATED','s')
        south,north,east,west,dy,dx = (record(key,'d') for key in ('S_LAT','N_LAT','E_LONG','W_LONG','LAT_INC','LONG_INC'))
        size = record('GS_COUNT','i')
        if not name or name == 'NONE' or not all(math.isfinite(v) for v in (south,north,east,west,dy,dx)) or dy <= 0 or dx <= 0 or north <= south or west <= east:
            raise ValueError('Invalid NTv2 subgrid geometry')
        nr, nc = (north-south)/dy, (west-east)/dx
        if not math.isfinite(nr) or not math.isfinite(nc) or nr > max_nodes or nc > max_nodes or abs(nr-round(nr)) > 1e-7 or abs(nc-round(nc)) > 1e-7:
            raise ValueError('NTv2 dimensions are not integral')
        rows, cols = round(nr)+1, round(nc)+1
        nodes += size
        if size != rows*cols or size < 4 or nodes > max_nodes or cursor+16*size > len(raw):
            raise ValueError('NTv2 count/size/node limit mismatch')
        if south < -324000 or north > 324000 or abs(east) > 1296000 or abs(west) > 1296000 or west-east > 1296000:
            raise ValueError('NTv2 geographic extent invalid')
        tiles.append(GridTile(name,parent,-east/3600,south/3600,-dx/3600,dy/3600,rows,cols,cursor))
        cursor += 16*size
    trailing = raw[cursor:]
    # The eight-byte END value is unused padding (not necessarily zero).
    if trailing and (len(trailing) != 16 or trailing[:8].strip() != b'END'):
        raise ValueError('Unexpected NTv2 trailing data')
    by_name = {t.name:t for t in tiles}
    if len(by_name) != len(tiles): raise ValueError('Duplicate NTv2 subgrid name')
    depths = {}
    for tile in tiles:
        ancestors, current = set(), tile
        while current.parent != 'NONE':
            if current.name in ancestors or current.parent not in by_name:
                raise ValueError('Cyclic or missing NTv2 parent')
            ancestors.add(current.name); parent = by_name[current.parent]
            w,s,e,n = current.bounds; pw,ps,pe,pn = parent.bounds
            if w < pw-1e-10 or s < ps-1e-10 or e > pe+1e-10 or n > pn+1e-10 or abs(current.longitude_step) > abs(parent.longitude_step) or current.latitude_step > parent.latitude_step:
                raise ValueError('NTv2 child outside/coarser than parent')
            current = parent
        depths[tile.name] = len(ancestors)
    for i,tile in enumerate(tiles):
        for other in tiles[i+1:]:
            if tile.parent != other.parent: continue
            a,b = tile.bounds, other.bounds
            if min(a[2],b[2])-max(a[0],b[0]) > 1e-10 and min(a[3],b[3])-max(a[1],b[1]) > 1e-10:
                raise ValueError('Overlapping NTv2 sibling interiors are ambiguous')
    from dataclasses import replace
    tiles = tuple(replace(t,depth=depths[t.name]) for t in tiles)
    return ShiftGrid('ntv2',tiles,raw,endian,nodata,metadata)
