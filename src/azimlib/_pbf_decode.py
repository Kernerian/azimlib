"""OSM snapshot protocol interpretation; field numbers are interoperability facts.

Implemented from the published format descriptions; no schema, generated code
or implementation from OSM-binary/protobuf is incorporated. See docs/osm-pbf.md.
"""
from dataclasses import dataclass
from types import MappingProxyType

from ._pbf_wire import (Budget, fields, one, chunks, numbers, deltas, signed,
                        zigzag, int32, text)


@dataclass(frozen=True)
class OSMMember:
    kind: str
    id: int
    role: str


@dataclass(frozen=True)
class OSMRecord:
    """One snapshot primitive, excluding editor identities and edit metadata.

    Coordinates are (longitude, latitude) degrees; IDs remain int64 integers.
    ``refs`` are way node IDs; ``members`` retain relation order and roles.
    Tags are unchanged OSM strings and can themselves contain personal data.
    """
    kind: str
    id: int
    tags: object
    coordinates: tuple = ()
    refs: tuple = ()
    members: tuple = ()
    locations: tuple = ()

    def __post_init__(self):
        object.__setattr__(self, 'tags', MappingProxyType(dict(self.tags)))
        for name in ('coordinates', 'refs', 'members'):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        object.__setattr__(self, 'locations', tuple(tuple(p) for p in self.locations))


def _identifier(value):
    if not value:
        raise ValueError('OSM ID/reference must be nonzero')
    return value


def _coordinate(lon, lat, granularity, lon_offset, lat_offset):
    x = lon_offset + granularity * lon; y = lat_offset + granularity * lat
    if not -180_000_000_000 <= x <= 180_000_000_000 or not -90_000_000_000 <= y <= 90_000_000_000:
        raise ValueError('PBF coordinate outside geographic range')
    return x / 1e9, y / 1e9


def _tag(tags, key, value):
    if not key or key == 'osm' or key in tags:
        raise ValueError('Empty, duplicate or reserved OSM tag key')
    tags[key] = value


def decode_header(raw):
    budget = Budget(); message = fields(raw, budget)
    required = tuple(text(value) for value in chunks(message, 4))
    optional = tuple(text(value) for value in chunks(message, 5))
    if 'OsmSchema-V0.6' not in required:
        raise ValueError('PBF header must require OsmSchema-V0.6')
    if set(required) - {'OsmSchema-V0.6', 'DenseNodes'}:
        raise ValueError('Unsupported PBF required feature (history/diffs are not snapshots)')
    bbox = one(message, 1, 2, None)
    if bbox is not None:
        m = fields(bbox, budget)
        left, right, top, bottom = (zigzag(one(m, n, 0)) for n in range(1, 5))
        bbox = _coordinate(left, bottom, 1, 0, 0) + _coordinate(right, top, 1, 0, 0)
        if left > right or bottom > top:
            raise ValueError('Invalid PBF header bounding box')
    # Do not retain free-form writer/source/replication URLs or edit metadata.
    return {'required_features': required, 'optional_features': optional, 'bbox': bbox}


def decode_block(raw, header, *, max_refs=100_000):
    budget = Budget(); block = fields(raw, budget)
    table = fields(one(block, 1, 2), budget)
    strings = []
    for value in chunks(table, 1):
        if len(strings) >= 100_000:
            raise ValueError('PBF string table exceeds item budget')
        strings.append(text(value))
    if not strings or strings[0] != '':
        raise ValueError('PBF string table must start with the empty string')
    granularity = int32(one(block, 17, 0, 100))
    if granularity <= 0 or int32(one(block, 18, 0, 1000)) <= 0:
        raise ValueError('Invalid PBF coordinate/date granularity')
    lat_offset = signed(one(block, 19, 0, 0)); lon_offset = signed(one(block, 20, 0, 0))

    def string(index):
        if not 0 <= index < len(strings):
            raise ValueError('PBF string index outside table')
        return strings[index]

    def coord(lon, lat):
        return _coordinate(lon, lat, granularity, lon_offset, lat_offset)

    def tags(message):
        keys = numbers(message, 2, budget); values = numbers(message, 3, budget)
        if len(keys) != len(values):
            raise ValueError('PBF tag arrays differ in length')
        result = {}
        for key, value in zip(keys, values):
            if key >= 2**32 or value >= 2**32:
                raise ValueError('PBF tag index overflows uint32')
            _tag(result, string(key), string(value))
        info = one(message, 4, 2, None)
        if info is not None and one(fields(info, budget), 6, 0, 1) != 1:
            raise ValueError('Deleted OSM objects are unsupported')
        return result

    for raw_group in chunks(block, 2):
        group = fields(raw_group, budget)
        kinds = [number for number in range(1, 6) if number in group]
        if len(kinds) > 1 or 5 in kinds:
            raise ValueError('Mixed primitive group or unsupported changeset group')
        if not kinds:
            continue
        kind = kinds[0]
        if kind == 2:
            if 'DenseNodes' not in header['required_features']:
                raise ValueError('DenseNodes used without required feature declaration')
            dense = fields(one(group, 2, 2), budget)
            ids = deltas(numbers(dense, 1, budget, zigzag))
            lats = deltas(numbers(dense, 8, budget, zigzag))
            lons = deltas(numbers(dense, 9, budget, zigzag))
            if len(ids) != len(lats) or len(ids) != len(lons):
                raise ValueError('PBF dense coordinate arrays differ in length')
            dense_info = one(dense, 5, 2, None)
            if dense_info is not None:
                visible = numbers(fields(dense_info, budget), 6, budget)
                if visible and (len(visible) != len(ids) or any(v != 1 for v in visible)):
                    raise ValueError('Invalid/deleted dense OSM objects')
            kv = numbers(dense, 10, budget, int32); cursor = 0
            for identifier, lat, lon in zip(ids, lats, lons):
                attributes = {}
                if kv:
                    while True:
                        if cursor >= len(kv):
                            raise ValueError('Unterminated dense PBF tags')
                        key = kv[cursor]; cursor += 1
                        if key == 0:
                            break
                        if cursor >= len(kv):
                            raise ValueError('Odd dense PBF tag pair')
                        _tag(attributes, string(key), string(kv[cursor])); cursor += 1
                yield OSMRecord('node', _identifier(identifier), attributes, coord(lon, lat))
            if cursor != len(kv):
                raise ValueError('Trailing dense PBF tags')
            continue
        for raw_item in chunks(group, kind):
            item = fields(raw_item, budget)
            identifier = _identifier((zigzag if kind == 1 else signed)(one(item, 1, 0)))
            attributes = tags(item)
            if kind == 1:
                yield OSMRecord('node', identifier, attributes,
                                coord(zigzag(one(item, 9, 0)), zigzag(one(item, 8, 0))))
            elif kind == 3:
                refs = deltas(numbers(item, 8, budget, zigzag))
                if not 2 <= len(refs) <= max_refs:
                    raise ValueError('PBF way reference count outside budget')
                for ref in refs:
                    _identifier(ref)
                lats = deltas(numbers(item, 9, budget, zigzag))
                lons = deltas(numbers(item, 10, budget, zigzag))
                if lats or lons:
                    if 'LocationsOnWays' not in header['optional_features'] or len(lats) != len(refs) or len(lons) != len(refs):
                        raise ValueError('Invalid/undeclared LocationsOnWays')
                locations = tuple(coord(lon, lat) for lon, lat in zip(lons, lats))
                yield OSMRecord('way', identifier, attributes, refs=tuple(refs), locations=locations)
            else:
                roles = numbers(item, 8, budget, int32)
                refs = deltas(numbers(item, 9, budget, zigzag)); types = numbers(item, 10, budget)
                if len(refs) > max_refs or len(roles) != len(refs) or len(types) != len(refs):
                    raise ValueError('PBF relation member arrays/count outside budget')
                members = []
                for ref, role, member_type in zip(refs, roles, types):
                    if member_type not in (0, 1, 2):
                        raise ValueError('Unknown PBF relation member type')
                    members.append(OSMMember(('node', 'way', 'relation')[member_type], _identifier(ref), string(role)))
                yield OSMRecord('relation', identifier, attributes, members=tuple(members))
