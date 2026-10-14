"""Original tiny snapshot encoder for tests, not a production PBF writer.

Only protocol facts are shared with the reader. No schema/generated/vendor code.
Real independently produced extracts are validated separately by the benchmark.
"""
import struct
import zlib


def varint(value):
    value &= (1 << 64) - 1
    output = bytearray()
    while value >= 128:
        output.append((value & 127) | 128); value >>= 7
    return bytes(output + bytes((value,)))


def zz(value):
    return 2 * value if value >= 0 else -2 * value - 1


def field(number, value):
    if isinstance(value, int):
        return varint(number << 3) + varint(value)
    if isinstance(value, str):
        value = value.encode('utf8')
    return varint((number << 3) | 2) + varint(len(value)) + value


def packed(number, values, *, unpacked=False):
    values = list(values)
    if unpacked:
        return b''.join(field(number, value) for value in values)
    return field(number, b''.join(varint(value) for value in values))


def delta(values):
    previous = 0
    for value in values:
        yield zz(value - previous); previous = value


def blob(kind, payload, *, compress=True):
    encoded = field(2, len(payload)) + field(3, zlib.compress(payload)) if compress else field(1, payload)
    header = field(1, kind) + field(3, len(encoded))
    return struct.pack('>I', len(header)) + header + encoded


def header(*required, optional=()):
    features = required or ('OsmSchema-V0.6', 'DenseNodes')
    return blob('OSMHeader', b''.join(field(4, name) for name in features) + b''.join(field(5, name) for name in optional))


def primitive(records, *, dense=True, unpacked=False, granularity=100,
              lon_offset=0, lat_offset=0, compress=True, locations=False):
    strings = ['']; lookup = {'': 0}
    def sid(value):
        if value not in lookup:
            lookup[value] = len(strings); strings.append(value)
        return lookup[value]
    def tags(values):
        pairs = [(sid(k), sid(v)) for k, v in values.items()]
        return packed(2, (k for k, v in pairs), unpacked=unpacked) + packed(3, (v for k, v in pairs), unpacked=unpacked)
    def coordinate(record, index):
        return round((record['coordinates'][index] * 1e9 - (lon_offset if index == 0 else lat_offset)) / granularity)
    groups = []
    # Each group is homogeneous, but group order follows the supplied records.
    for record in records:
        kind = record['kind']; identifier = record['id']; attributes = record.get('tags', {})
        if kind == 'node' and dense:
            kv = [value for k, v in attributes.items() for value in (sid(k), sid(v))] + [0]
            item = packed(1, [zz(identifier)], unpacked=unpacked)
            item += packed(8, [zz(coordinate(record, 1))], unpacked=unpacked)
            item += packed(9, [zz(coordinate(record, 0))], unpacked=unpacked)
            item += packed(10, kv, unpacked=unpacked)
            groups.append(field(2, item)); continue
        item = field(1, zz(identifier) if kind == 'node' else identifier) + tags(attributes)
        if kind == 'node':
            item += field(8, zz(coordinate(record, 1))) + field(9, zz(coordinate(record, 0)))
        elif kind == 'way':
            item += packed(8, delta(record['refs']), unpacked=unpacked)
            if locations:
                coords = record['locations']
                item += packed(9, delta(round((p[1] * 1e9 - lat_offset) / granularity) for p in coords))
                item += packed(10, delta(round((p[0] * 1e9 - lon_offset) / granularity) for p in coords))
        else:
            members = record['members']
            item += packed(8, (sid(role) for kind, ref, role in members), unpacked=unpacked)
            item += packed(9, delta(ref for kind, ref, role in members), unpacked=unpacked)
            item += packed(10, (('node', 'way', 'relation').index(kind) for kind, ref, role in members), unpacked=unpacked)
        groups.append(field({'node': 1, 'way': 3, 'relation': 4}[kind], item))
    table = b''.join(field(1, value) for value in strings)
    block = field(1, table) + b''.join(field(2, group) for group in groups)
    block += field(17, granularity) + field(19, lat_offset) + field(20, lon_offset)
    return blob('OSMData', block, compress=compress)


def scene():
    nodes = [dict(kind='node', id=i + 1, coordinates=p) for i, p in enumerate(
        ((0, 0), (4, 0), (4, 4), (0, 4), (1, 1), (1, 2), (2, 2), (2, 1), (5, 0)))]
    nodes[0]['tags'] = {'name': 'Ponto sintético', 'amenity': 'bench'}
    ways = [dict(kind='way', id=10, refs=(1, 2, 3)), dict(kind='way', id=11, refs=(1, 4, 3)),
            dict(kind='way', id=12, refs=(5, 6, 7, 8, 5)),
            dict(kind='way', id=13, refs=(2, 9), tags={'highway': 'residential', 'name': 'Via sintética'})]
    relations = [dict(kind='relation', id=20, tags={'type': 'multipolygon', 'landuse': 'forest'},
                      members=(('way', 10, 'outer'), ('way', 11, 'outer'), ('way', 12, 'inner'))),
                 dict(kind='relation', id=21, tags={'type': 'restriction', 'restriction': 'no_right_turn',
                                                  'except': 'bicycle', 'restriction:conditional': 'no_right_turn @ (Mo-Fr)'},
                      members=(('way', 10, 'from'), ('node', 2, 'via'), ('way', 13, 'to')))]
    return nodes + ways + relations


def xml(records):
    from xml.etree.ElementTree import Element, SubElement, tostring
    root = Element('osm', version='0.6')
    for record in records:
        element = SubElement(root, record['kind'], id=str(record['id']))
        if record['kind'] == 'node':
            element.set('lon', str(record['coordinates'][0])); element.set('lat', str(record['coordinates'][1]))
        for ref in record.get('refs', ()):
            SubElement(element, 'nd', ref=str(ref))
        for kind, ref, role in record.get('members', ()):
            SubElement(element, 'member', type=kind, ref=str(ref), role=role)
        for key, value in record.get('tags', {}).items():
            SubElement(element, 'tag', k=key, v=value)
    return tostring(root)
