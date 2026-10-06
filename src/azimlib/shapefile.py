"""Own ESRI SHP/SHX and dBASE III/IV/5 readers, without a GIS backend."""
from dataclasses import dataclass
from datetime import date
from math import isfinite
from pathlib import Path
from struct import unpack_from
from types import MappingProxyType

from ._readers import binary, area, assign_holes
from .crs import CRS, transform_coordinates
from .geometry import Feature, FeatureCollection, Geometry


@dataclass(frozen=True)
class DBFRecord:
    index: int
    properties: object
    deleted: bool = False

    def __post_init__(self):
        object.__setattr__(self, 'properties', MappingProxyType(dict(self.properties)))


def read_dbf(source, *, encoding, include_deleted=False):
    """Return DBFRecords with physical zero-based indices; explicit encoding.

    Support C/N/F/L/D in no-memo dBASE III/IV/5. Dates become ISO strings,
    blanks become None. Deleted rows are omitted by default without renumbering.
    Memo/FoxPro/encrypted variants are rejected rather than guessed.
    """
    if not isinstance(encoding, str) or not encoding:
        raise ValueError('Supply an explicit DBF encoding')
    raw = binary(source)
    if len(raw) < 33 or raw[0] not in (3, 4, 5) or raw[15]:
        raise ValueError('Unsupported or truncated no-memo DBF header')
    count, header, width = unpack_from('<IHH', raw, 4)
    if header < 33 or (header-33) % 32 or header > len(raw) or raw[header-1] != 13:
        raise ValueError('Invalid DBF field descriptors')
    if width < 1 or header+count*width > len(raw) or raw[header+count*width:] not in (b'', b'\x1a'):
        raise ValueError('DBF record length/count or EOF mismatch')
    fields = []
    for offset in range(32, header-1, 32):
        entry = raw[offset:offset+32]
        name = entry[:11].split(b'\0')[0].decode(encoding)
        kind, length, decimals = chr(entry[11]), entry[16], entry[17]
        if not name or name in [f[0] for f in fields] or kind not in 'CNFLD' or not length:
            raise ValueError('Unsupported/duplicate DBF field')
        if kind == 'L' and length != 1 or kind == 'D' and length != 8:
            raise ValueError('Invalid DBF logical/date width')
        fields.append((name, kind, length, decimals))
    if 1+sum(f[2] for f in fields) != width:
        raise ValueError('DBF field widths do not match record width')
    records = []
    for index in range(count):
        row = raw[header+index*width:header+(index+1)*width]
        if row[:1] not in (b' ', b'*'):
            raise ValueError(f'DBF record {index}: invalid deletion flag')
        deleted = row[:1] == b'*'
        if deleted and not include_deleted:
            continue
        properties = {}; position = 1
        for name, kind, length, decimals in fields:
            value = row[position:position+length]; position += length
            try:
                text = value.decode(encoding if kind == 'C' else 'ascii').strip()
                if kind == 'C':
                    result = value.decode(encoding).rstrip(' \0')
                elif not text or kind == 'L' and text == '?':
                    result = None
                elif kind in 'NF':
                    result = int(text) if kind == 'N' and decimals == 0 else float(text)
                    if not isfinite(result):
                        raise ValueError('Nonfinite DBF number')
                elif kind == 'L':
                    if text.upper() not in ('T', 'Y', 'F', 'N'):
                        raise ValueError('Invalid logical value')
                    result = text.upper() in ('T', 'Y')
                else:
                    result = date(int(text[:4]), int(text[4:6]), int(text[6:])).isoformat()
            except (ValueError, UnicodeError, OverflowError) as exc:
                raise ValueError(f'DBF record {index}, field {name}: invalid value') from exc
            properties[name] = result
        records.append(DBFRecord(index, properties, deleted))
    return tuple(records)


def _header(raw):
    if len(raw) < 100 or unpack_from('>i', raw)[0] != 9994 or raw[4:24] != b'\0'*20:
        raise ValueError('Invalid SHP/SHX header')
    if unpack_from('>i', raw, 24)[0]*2 != len(raw) or unpack_from('<i', raw, 28)[0] != 1000:
        raise ValueError('SHP/SHX declared length/version mismatch')
    kind = unpack_from('<i', raw, 32)[0]
    if kind not in (0, 1, 3, 5, 8, 11, 13, 15, 18):
        raise ValueError('Unsupported shape type; M-only and MultiPatch are not implemented')
    bounds = unpack_from('<8d', raw, 36)
    if not all(isfinite(v) for v in bounds) or bounds[0] > bounds[2] or bounds[1] > bounds[3]:
        raise ValueError('Invalid SHP/SHX bounding box')
    return kind


def _shape(raw, expected, crs):
    if len(raw) < 4:
        raise ValueError('Truncated shape record')
    kind = unpack_from('<i', raw)[0]
    if kind == 0:
        if len(raw) != 4:
            raise ValueError('Invalid null shape length')
        return None
    if kind != expected:
        raise ValueError('Record type differs from SHP header')
    base = kind-10 if kind >= 11 else kind
    z = kind >= 11
    if base == 1:
        end = 28 if z else 20
        if len(raw) not in ((28, 36) if z else (20,)):
            raise ValueError('Invalid Point record length')
        coords = unpack_from('<3d' if z else '<2d', raw, 4)
        return Geometry('Point', transform_coordinates((coords,), crs, 'EPSG:4326')[0])
    if len(raw) < (40 if base == 8 else 44):
        raise ValueError('Truncated multipart shape')
    bounds = unpack_from('<4d', raw, 4)
    if not all(isfinite(v) for v in bounds) or bounds[0] > bounds[2] or bounds[1] > bounds[3]:
        raise ValueError('Invalid record bounds')
    if base == 8:
        count = unpack_from('<i', raw, 36)[0]; parts = None; start = 40
    else:
        nparts, count = unpack_from('<2i', raw, 36)
        if nparts < 1 or count < nparts or 44+4*nparts > len(raw):
            raise ValueError('Invalid part count')
        parts = unpack_from(f'<{nparts}i', raw, 44); start = 44+4*nparts
        if parts[0] != 0 or any(a >= b for a, b in zip(parts, parts[1:])) or parts[-1] >= count:
            raise ValueError('Invalid part offsets')
    if count < 1 or start+16*count > len(raw):
        raise ValueError('Invalid point count')
    coords = [unpack_from('<2d', raw, start+16*i) for i in range(count)]
    end = start+16*count
    if z:
        if end+16+8*count > len(raw):
            raise ValueError('Missing Z array')
        elevations = unpack_from(f'<{count}d', raw, end+16)
        coords = [point+(height,) for point, height in zip(coords, elevations)]
        end += 16+8*count
    if len(raw) not in ((end, end+16+8*count) if z else (end,)):
        raise ValueError('Unexpected shape trailing data')
    if any(not all(isfinite(v) for v in p) for p in coords):
        raise ValueError('Nonfinite shape coordinate')
    if any(not bounds[0] <= p[0] <= bounds[2] or not bounds[1] <= p[1] <= bounds[3] for p in coords):
        raise ValueError('Coordinates outside declared record bounds')
    if base == 8:
        return Geometry('MultiPoint', transform_coordinates(coords, crs, 'EPSG:4326'))
    chunks = [coords[a:b] for a, b in zip(parts, (*parts[1:], count))]
    if base == 3:
        lines = [transform_coordinates(line, crs, 'EPSG:4326') for line in chunks]
        return Geometry('LineString', lines[0]) if len(lines) == 1 else Geometry('MultiLineString', lines)
    if any(len(ring) < 4 or ring[0] != ring[-1] or area(ring) == 0 for ring in chunks):
        raise ValueError('Polygon rings must be closed and nondegenerate')
    groups = assign_holes([r for r in chunks if area(r) < 0], [r for r in chunks if area(r) > 0])
    # Shapefile shells are clockwise; geographic shells are emitted CCW.
    groups = [[tuple(reversed(transform_coordinates(ring, crs, 'EPSG:4326'))) for ring in group] for group in groups]
    return Geometry('Polygon', groups[0]) if len(groups) == 1 else Geometry('MultiPolygon', groups)


def read_shapefile(source, *, crs, dbf=None, shx=None, encoding=None, include_deleted=False):
    """Read SHP plus optional SHX/DBF; source CRS is always explicit.

    Local paths discover same-stem .shx/.dbf. Streams stay open. SHX offsets
    must agree with every SHP record; DBF physical rows must align one-to-one.
    IDs are one-based SHP record numbers. Z is retained; optional M measures
    on Z records are not represented. Clean clockwise-shell polygons only.
    .prj is never guessed; unsupported CRS/types fail explicitly.
    """
    crs = CRS.from_user_input(crs)
    if isinstance(source, (str, Path)):
        path = Path(source)
        if dbf is None and path.with_suffix('.dbf').is_file(): dbf = path.with_suffix('.dbf')
        if shx is None and path.with_suffix('.shx').is_file(): shx = path.with_suffix('.shx')
    raw = binary(source); kind = _header(raw)
    records = []; offsets = []; cursor = 100
    while cursor < len(raw):
        if cursor+8 > len(raw): raise ValueError('Truncated SHP record header')
        number, words = unpack_from('>2i', raw, cursor)
        size = words*2
        if number != len(records)+1 or words < 2 or cursor+8+size > len(raw):
            raise ValueError('Invalid SHP record number/length')
        offsets.append((cursor//2, words))
        records.append(_shape(raw[cursor+8:cursor+8+size], kind, crs))
        cursor += 8+size
    if shx is not None:
        index = binary(shx)
        if _header(index) != kind or (len(index)-100) % 8 or index[36:100] != raw[36:100]:
            raise ValueError('SHX type/bounds/length mismatch')
        entries = [unpack_from('>2i', index, p) for p in range(100, len(index), 8)]
        if entries != offsets: raise ValueError('SHX entries do not match SHP records')
    rows = None
    if dbf is not None:
        dbf_raw = binary(dbf)
        parsed = read_dbf(dbf_raw, encoding=encoding, include_deleted=include_deleted)
        if unpack_from('<I', dbf_raw, 4)[0] != len(records):
            raise ValueError('DBF/SHP row count mismatch')
        rows = {row.index: row for row in parsed}
    features = []
    for index, geometry in enumerate(records):
        row = None if rows is None else rows.get(index)
        if rows is not None and row is None: continue
        properties = {} if row is None else dict(row.properties)
        features.append(Feature(geometry, properties, index+1))
    return FeatureCollection(tuple(features))
