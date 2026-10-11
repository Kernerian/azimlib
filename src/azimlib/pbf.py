"""Own OSM PBF snapshot reader and bounded, disposable SQLite reference index.

No network access. Raw iteration is sequential; indexed extraction resolves
references across arbitrary block order. See docs/osm-pbf.md for the contract.
"""
from contextlib import contextmanager
import hashlib
import io
import json
import math
from numbers import Integral
from pathlib import Path
import re
import shutil
import sqlite3
import struct
import tempfile
import zlib

from ._pbf_wire import Budget, fields, one, chunks, int32, text
from ._pbf_decode import OSMRecord, OSMMember, decode_header, decode_block
from ._readers import assign_holes
from ._contracts import STREAM_BLOCK_BUDGET
from .geometry import Feature, FeatureCollection, Geometry

_BLOCK_BYTES = STREAM_BLOCK_BUDGET.max_bytes


def _limit(value, name, minimum=1):
    if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')
    return int(value)


@contextmanager
def _source(source):
    if isinstance(source, (bytes, bytearray, memoryview)):
        with io.BytesIO(source) as stream:
            yield stream
    elif hasattr(source, 'read'):
        yield source
    else:
        with open(source, 'rb') as stream:
            yield stream


def _read(stream, size, digest, *, eof=False):
    parts = bytearray()
    while len(parts) < size:
        part = stream.read(size - len(parts))
        if not isinstance(part, bytes) or len(part) > size - len(parts):
            raise ValueError('PBF source must return bounded binary reads')
        if not part:
            if eof and not parts:
                return None
            raise ValueError('Truncated PBF framing')
        digest.update(part); parts.extend(part)
    return parts


def _blob(raw):
    message = fields(raw, Budget())
    data_fields = [n for n in (1, 3, 4, 5, 6, 7) if n in message]
    if len(data_fields) != 1:
        raise ValueError('PBF Blob must contain exactly one payload')
    kind = data_fields[0]; payload = one(message, kind, 2)
    declared = one(message, 2, 0, None)
    size = None if declared is None else int32(declared)
    if size is not None and not 0 <= size < _BLOCK_BYTES:
        raise ValueError('PBF raw_size exceeds block budget')
    if kind == 1:
        if len(payload) >= _BLOCK_BYTES or (size is not None and size != len(payload)):
            raise ValueError('PBF raw size mismatch or budget exceeded')
        return payload
    if kind != 3:
        raise ValueError(f'Unsupported PBF compression field {kind}; supported codecs: raw, zlib')
    if size is None:
        raise ValueError('Compressed PBF Blob requires raw_size')
    try:
        decoder = zlib.decompressobj()
        result = decoder.decompress(payload, size + 1)
    except zlib.error as exc:
        raise ValueError('Invalid PBF zlib payload') from exc
    if len(result) != size or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise ValueError('PBF zlib size/stream mismatch')
    return result


class _Reader:
    def __init__(self, source, max_refs, expected_sha256):
        self.source = source; self.max_refs = _limit(max_refs, 'max_refs', 2)
        if expected_sha256 is not None and (not isinstance(expected_sha256, str) or not re.fullmatch('[0-9a-f]{64}', expected_sha256)):
            raise ValueError('expected_sha256 must be a lowercase SHA256 digest')
        self.expected_sha256 = expected_sha256
        self.header = None; self.blocks = 0; self.records = 0; self.sha256 = None
        self.bytes_read = 0

    def __iter__(self):
        digest = hashlib.sha256()
        with _source(self.source) as stream:
            while True:
                prefix = _read(stream, 4, digest, eof=True)
                if prefix is None:
                    break
                size = struct.unpack('>I', prefix)[0]
                if not 0 < size < 64 * 1024:
                    raise ValueError('PBF BlobHeader length outside budget')
                header_raw = _read(stream, size, digest)
                header = fields(header_raw, Budget())
                kind = text(one(header, 1, 2)); size = int32(one(header, 3, 0))
                if not 0 < size <= _BLOCK_BYTES + 64 * 1024:
                    raise ValueError('PBF encoded Blob length outside budget')
                raw = _read(stream, size, digest); self.blocks += 1
                self.bytes_read += 4 + len(header_raw) + len(raw)
                if kind not in ('OSMHeader', 'OSMData'):
                    if self.header is None:
                        raise ValueError('PBF must begin with OSMHeader')
                    continue
                payload = _blob(raw)
                if kind == 'OSMHeader':
                    if self.header is not None or self.blocks != 1:
                        raise ValueError('Duplicate/misplaced PBF OSMHeader')
                    self.header = decode_header(payload)
                else:
                    if self.header is None:
                        raise ValueError('PBF OSMData precedes header')
                    for record in decode_block(payload, self.header, max_refs=self.max_refs):
                        self.records += 1
                        yield record
                # Release the previous block before reading the next one.
                del raw, payload
        if self.header is None:
            raise ValueError('Missing PBF OSMHeader')
        self.sha256 = digest.hexdigest()
        if self.expected_sha256 is not None and self.sha256 != self.expected_sha256:
            raise ValueError('PBF SHA256 integrity mismatch')


def iter_osm_pbf(source, *, max_refs=100_000, expected_sha256=None):
    """Yield immutable OSMRecord snapshots with at most one block in memory.

    Exhaust the iterator to validate framing/hash of the entire input. Streaming
    can yield records before a later error. Use OSMIndex for verified extraction.
    Duplicate IDs/reference existence are checked by OSMIndex, not this iterator.
    Caller-owned streams remain open; close an abandoned iterator explicitly.
    """
    yield from _Reader(source, max_refs, expected_sha256)


class _Missing(ValueError):
    pass


def _rings(segments, max_refs):
    """Join member endpoints by node identity in linear time; reject branches."""
    endpoints = {}; parts = {}; result = []; count = 0
    for index, segment in enumerate(segments):
        count += len(segment)
        if count > max_refs:
            raise ValueError('PBF relation geometry exceeds reference budget')
        parts[index] = segment
        if segment[0] != segment[-1]:
            for node in (segment[0], segment[-1]):
                endpoints.setdefault(node, set()).add(index)
    if any(len(indices) != 2 for indices in endpoints.values()):
        raise ValueError('Open or branched PBF polygon ring')
    while parts:
        index = next(iter(parts)); chain = list(parts.pop(index))
        if chain[0] != chain[-1]:
            endpoints[chain[0]].remove(index); endpoints[chain[-1]].remove(index)
        while chain[-1] != chain[0]:
            matches = endpoints[chain[-1]]
            if len(matches) != 1:
                raise ValueError('Open or branched PBF polygon ring')
            index = next(iter(matches)); part = parts.pop(index)
            endpoints[part[0]].remove(index); endpoints[part[-1]].remove(index)
            if part[-1] == chain[-1]:
                part = part[::-1]
            chain.extend(part[1:])
        if len(chain) < 4 or len(set(chain[:-1])) != len(chain) - 1:
            raise ValueError('Degenerate/self-touching PBF polygon ring')
        result.append(chain)
    return result


class OSMIndex:
    """Disposable disk index; use as a context manager and stream features().

    The input is fully read and SHA256 checked before construction succeeds.
    ``missing='error'`` rejects incomplete references; explicit ``'skip'`` omits
    incomplete ways/derived relations and reports counts in ``statistics``.
    Raw relations remain available, including unsupported semantic types.
    ``max_disk_bytes`` bounds the database; no journal or unbounded temp sort.
    ``reserve_free_bytes`` stops ingestion before consuming reserved free space.
    The input file and other processes' disk usage are outside this index budget.
    """
    def __init__(self, source, *, directory=None, max_disk_bytes=8_000_000_000,
                 reserve_free_bytes=64 * 1024 * 1024, max_refs=100_000,
                 missing='error', expected_sha256=None):
        self._db = None; self._temporary = None
        self._cursors = set()
        self._pending_bytes = 0
        self.max_disk_bytes = _limit(max_disk_bytes, 'max_disk_bytes', 1024 * 1024)
        self.reserve_free_bytes = _limit(reserve_free_bytes, 'reserve_free_bytes', 0)
        self.max_refs = _limit(max_refs, 'max_refs', 2)
        if missing not in ('error', 'skip'):
            raise ValueError('missing must be error or skip')
        self.missing = missing
        self.statistics = {'nodes': 0, 'ways': 0, 'relations': 0, 'missing_ways': 0,
                           'missing_relations': 0, 'polygon_relations': 0, 'restrictions': 0}
        self._temporary = tempfile.TemporaryDirectory(prefix='azimlib-osm-', dir=directory)
        self._path = Path(self._temporary.name) / 'index.sqlite'
        try:
            self._space()
            self._db = sqlite3.connect(self._path)
            self._db.execute('PRAGMA journal_mode=OFF')
            self._db.execute('PRAGMA synchronous=OFF')
            self._db.execute('PRAGMA cache_size=-8192')
            self._db.execute('PRAGMA temp_store=FILE')
            page_size = self._db.execute('PRAGMA page_size').fetchone()[0]
            self._db.execute(f'PRAGMA max_page_count={self.max_disk_bytes // page_size}')
            self._db.executescript('''
                CREATE TABLE nodes(id INTEGER PRIMARY KEY, x REAL, y REAL, tags TEXT, seq INTEGER);
                CREATE TABLE ways(id INTEGER PRIMARY KEY, refs TEXT, tags TEXT, seq INTEGER, valid INTEGER DEFAULT 1);
                CREATE TABLE relations(id INTEGER PRIMARY KEY, members TEXT, tags TEXT, seq INTEGER, valid INTEGER DEFAULT 1, geometry TEXT);
                CREATE TABLE consumed(id INTEGER PRIMARY KEY);
                CREATE INDEX node_sequence ON nodes(seq);
                CREATE INDEX way_sequence ON ways(seq);
                CREATE INDEX relation_sequence ON relations(seq);
            ''')
            reader = _Reader(source, self.max_refs, expected_sha256)
            for seq, record in enumerate(reader):
                tags = json.dumps(dict(record.tags), ensure_ascii=False, separators=(',', ':'))
                self._guard(len(tags.encode('utf8')) + 24 * (len(record.refs) + len(record.members) + len(record.locations)))
                if record.kind == 'node':
                    self._db.execute('INSERT INTO nodes VALUES(?,?,?,?,?)', (record.id, *record.coordinates, tags, seq))
                elif record.kind == 'way':
                    self._db.execute('INSERT INTO ways(id,refs,tags,seq) VALUES(?,?,?,?)',
                                     (record.id, json.dumps(record.refs), tags, seq))
                    # Embedded locations do not substitute for missing nodes.
                    # They are checked against the node index after all blocks.
                    if record.locations:
                        self._db.execute('CREATE TABLE IF NOT EXISTS locations(id INTEGER PRIMARY KEY, coords TEXT)')
                        self._db.execute('INSERT INTO locations VALUES(?,?)', (record.id, json.dumps(record.locations)))
                else:
                    members = [(m.kind, m.id, m.role) for m in record.members]
                    self._db.execute('INSERT INTO relations(id,members,tags,seq) VALUES(?,?,?,?)',
                                     (record.id, json.dumps(members), tags, seq))
                self.statistics[{'node': 'nodes', 'way': 'ways', 'relation': 'relations'}[record.kind]] += 1
                if seq % 512 == 0:
                    self._space(); self._db.commit()
            self.sha256 = reader.sha256; self.header = reader.header
            self.statistics['blocks'] = reader.blocks
            self.statistics['input_bytes_read'] = reader.bytes_read
            self._prepare()
            self._db.commit(); self._space()
            self.statistics['index_bytes'] = self._path.stat().st_size
        except sqlite3.IntegrityError as exc:
            self.close()
            raise ValueError('Duplicate OSM primitive ID') from exc
        except sqlite3.DatabaseError as exc:
            self.close()
            raise ValueError('OSM disk index failed (budget, disk space or SQLite error)') from exc
        except BaseException:
            self.close()
            raise

    def _space(self):
        free = shutil.disk_usage(self._path.parent).free
        # Leave room for the next bounded block/SQLite allocation as well.
        if free < self.reserve_free_bytes + 2 * _BLOCK_BYTES:
            raise ValueError('OSM index would consume reserved free disk space')

    def _guard(self, size):
        if size > 8 * 1024 * 1024:
            raise ValueError('Serialized OSM entity exceeds 8 MiB budget')
        self._pending_bytes += 4 * size + 4096
        if self._pending_bytes >= 8 * 1024 * 1024:
            self._space(); self._pending_bytes = 0

    def _open(self):
        if self._db is None:
            raise ValueError('OSMIndex is closed')

    def close(self):
        for cursor in tuple(self._cursors):
            cursor.close()
        self._cursors.clear()
        if self._db is not None:
            self._db.close(); self._db = None
        if self._temporary is not None:
            self._temporary.cleanup(); self._temporary = None

    def _rows(self, sql):
        self._open()
        cursor = self._db.execute(sql); self._cursors.add(cursor)
        try:
            while True:
                self._open()
                row = cursor.fetchone()
                if row is None:
                    break
                yield row
        finally:
            self._cursors.discard(cursor)
            try:
                cursor.close()
            except sqlite3.ProgrammingError:
                # The owner may have closed the index with an iterator paused.
                pass

    def __enter__(self):
        self._open(); return self

    def __exit__(self, *exc):
        self.close()

    def _coordinates(self, refs):
        result = []
        for ref in refs:
            row = self._db.execute('SELECT x,y FROM nodes WHERE id=?', (ref,)).fetchone()
            if row is None:
                raise _Missing(f'Missing OSM node {ref}')
            result.append(row)
        return result

    def _way(self, identifier):
        row = self._db.execute('SELECT refs,valid FROM ways WHERE id=?', (identifier,)).fetchone()
        if row is None or not row[1]:
            raise _Missing(f'Missing/incomplete OSM way {identifier}')
        return json.loads(row[0])

    def _polygon(self, members, *, boundary=False):
        segments = {'outer': [], 'inner': []}; consumed = set(); total = 0
        for kind, identifier, role in members:
            if boundary and kind == 'relation' and role == 'subarea':
                # Administrative children are metadata, not boundary rings.
                continue
            if kind == 'node' and role in ('label', 'admin_centre'):
                continue
            if kind != 'way' or (role or 'outer') not in segments:
                raise ValueError('Unsupported boundary/multipolygon member type/role')
            if identifier in consumed:
                raise ValueError('Repeated way in polygon relation')
            refs = self._way(identifier); total += len(refs)
            if total > self.max_refs:
                raise ValueError('PBF relation geometry exceeds reference budget')
            consumed.add(identifier); segments[role or 'outer'].append(refs)
        rings = {role: [self._coordinates(refs) for refs in _rings(parts, self.max_refs)]
                 for role, parts in segments.items()}
        groups = assign_holes(rings['outer'], rings['inner'])
        geometry = Geometry('Polygon', groups[0]) if len(groups) == 1 else Geometry('MultiPolygon', groups)
        return geometry, consumed

    def _restriction(self, members, tags):
        roles = {'from': [], 'via': [], 'to': []}
        for kind, identifier, role in members:
            if role not in roles or kind not in ('node', 'way'):
                raise ValueError('Unsupported restriction member type/role')
            roles[role].append((kind, identifier))
            table = 'nodes' if kind == 'node' else 'ways'
            row = self._db.execute(f'SELECT id FROM {table} WHERE id=?' + (' AND valid=1' if kind == 'way' else ''), (identifier,)).fetchone()
            if row is None:
                raise _Missing('Missing OSM restriction member')
        if not all(roles.values()):
            raise _Missing('Incomplete OSM restriction: missing from/via/to members')
        if any(k != 'way' for role in ('from', 'to') for k, _ in roles[role]):
            raise ValueError('Restriction requires from/to ways and via members')
        via = roles['via']
        if len({k for k, _ in via}) != 1 or (via[0][0] == 'node' and len(via) != 1):
            raise ValueError('Restriction via must be one node or an ordered way chain')
        if not any(key == 'restriction' or key.startswith('restriction:') for key in tags):
            raise ValueError('Restriction relation has no restriction tag')

    def _prepare(self):
        embedded = self._db.execute("SELECT 1 FROM sqlite_master WHERE name='locations'").fetchone()
        for count, (identifier, raw) in enumerate(self._rows('SELECT id,refs FROM ways')):
            try:
                coordinates = self._coordinates(json.loads(raw))
                if embedded:
                    row = self._db.execute('SELECT coords FROM locations WHERE id=?', (identifier,)).fetchone()
                    if row is not None and any(tuple(a) != tuple(b) for a, b in zip(json.loads(row[0]), coordinates)):
                        raise ValueError('LocationsOnWays differs from node coordinates')
            except _Missing:
                if self.missing == 'error':
                    raise
                self.statistics['missing_ways'] += 1
                self._db.execute('UPDATE ways SET valid=0 WHERE id=?', (identifier,))
            if count % 512 == 0:
                self._space()
        for count, (identifier, raw, raw_tags) in enumerate(self._rows('SELECT id,members,tags FROM relations')):
            members = json.loads(raw); tags = json.loads(raw_tags); kind = tags.get('type')
            try:
                if kind in ('multipolygon', 'boundary'):
                    geometry, consumed = self._polygon(members, boundary=kind == 'boundary')
                    encoded = json.dumps(geometry.to_geojson())
                    self._guard(len(encoded.encode('utf8')))
                    self._db.execute('UPDATE relations SET geometry=? WHERE id=?', (encoded, identifier))
                    self._db.executemany('INSERT OR IGNORE INTO consumed VALUES(?)', ((ref,) for ref in consumed))
                    self.statistics['polygon_relations'] += 1
                elif kind == 'restriction' or (kind or '').startswith('restriction:'):
                    self._restriction(members, tags); self.statistics['restrictions'] += 1
            except _Missing:
                if self.missing == 'error':
                    raise
                self.statistics['missing_relations'] += 1
                self._db.execute('UPDATE relations SET valid=0 WHERE id=?', (identifier,))
            if count % 128 == 0:
                self._space()

    def relations(self, *, restrictions_only=False, include_incomplete=False):
        """Stream raw members/tags; restrictions retain conditional/except tags.

        This preserves turn semantics for a later router; it does not evaluate
        conditional restrictions or claim that a routable graph was built.
        """
        self._open()
        for identifier, raw, tags, valid in self._rows('SELECT id,members,tags,valid FROM relations'):
            self._open()
            tags = json.loads(tags); kind = tags.get('type', '')
            if not valid and not include_incomplete:
                continue
            if restrictions_only and not (kind == 'restriction' or kind.startswith('restriction:')):
                continue
            yield OSMRecord('relation', identifier, tags,
                            members=tuple(OSMMember(*member) for member in json.loads(raw)))

    def features(self, *, bbox=None, where=None, include_untagged=False):
        """Stream complete geometries whose envelopes intersect bbox, AND tags.

        bbox=(west,south,east,north) in degrees; west>east crosses the dateline.
        Envelope filtering is conservative: geometries are not clipped, and a
        crossing way/polygon may have all vertices outside the selected region.
        Non-geometric relations are available through relations(), not plotted.
        SQL traverses in primitive input order without a global in-memory sort.
        """
        self._open()
        if not isinstance(include_untagged, bool):
            raise ValueError('include_untagged must be bool')
        if where is None:
            where = {}
        if not hasattr(where, 'items') or any(not isinstance(k, str) or not isinstance(v, str) for k, v in where.items()):
            raise ValueError('where must map OSM tag strings to strings')
        where = dict(where)
        windows = None
        if bbox is not None:
            try:
                bbox = tuple(bbox)
                west, south, east, north = bbox
                if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in bbox):
                    raise ValueError()
                if not (-180 <= west <= 180 and -180 <= east <= 180 and -90 <= south <= north <= 90):
                    raise ValueError()
            except (ValueError, TypeError) as exc:
                raise ValueError('bbox must be (west,south,east,north) geographic degrees') from exc
            windows = [(west, south, east, north)] if west <= east else [(west, south, 180, north), (-180, south, east, north)]
        # Three primary scans merged by sequence, avoiding SQL UNION/ORDER temp files.
        # Primary-key order is not sequence order when IDs are unsorted. Explicit
        # disk-backed sequence indexes make the merge correct for arbitrary files.
        cursors = [self._rows(query + ' ORDER BY ' + ('w.seq' if index == 1 else 'seq'))
                   for index, query in enumerate((
                       'SELECT seq,id,tags,x,y FROM nodes INDEXED BY node_sequence',
                       'SELECT w.seq,w.id,w.tags,w.refs,NULL FROM ways w INDEXED BY way_sequence WHERE w.valid=1 AND NOT EXISTS(SELECT 1 FROM consumed c WHERE c.id=w.id)',
                       'SELECT seq,id,tags,geometry,NULL FROM relations INDEXED BY relation_sequence WHERE valid=1 AND geometry IS NOT NULL'))]
        heads = [next(cursor, None) for cursor in cursors]
        while any(row is not None for row in heads):
            self._open()
            index = min((i for i in range(3) if heads[i] is not None), key=lambda i: heads[i][0])
            _, identifier, raw_tags, raw, y = heads[index]
            heads[index] = next(cursors[index], None)
            tags = json.loads(raw_tags)
            if (not tags and not include_untagged) or any(tags.get(k) != v for k, v in where.items()):
                continue
            kind = ('node', 'way', 'relation')[index]
            if index == 0:
                geometry = Geometry('Point', (raw, y))
            elif index == 1:
                refs = json.loads(raw); coordinates = self._coordinates(refs)
                area = tags.get('area') == 'yes' or any(tags.get(k) not in (None, 'no') for k in ('building', 'landuse', 'leisure', 'amenity')) or tags.get('natural') == 'water'
                geometry = Geometry('Polygon', (coordinates,)) if refs[0] == refs[-1] and area and tags.get('area') != 'no' else Geometry('LineString', coordinates)
            else:
                geo = json.loads(raw); geometry = Geometry(geo['type'], geo['coordinates'])
            if windows is not None:
                w, s, e, n = geometry.bounds
                if e - w > 180:
                    # A wrapped path can cross the dateline beyond the ordinary
                    # longitude envelope. Keep candidates rather than miss it.
                    w, e = -180, 180
                if not any(w <= right and e >= left and s <= top and n >= bottom for left, bottom, right, top in windows):
                    continue
            yield Feature(geometry, dict(tags, osm={'type': kind, 'id': str(identifier)}), f'{kind}/{identifier}')

    def audit_references(self):
        """Scan every way/member, including raw relation types, without repair.

        Return counts and a deterministic structural SHA256 (no tag contents).
        Existence checks include invalid/skipped entities; their missing children
        are counted separately. Cycles are not dangling references. This does not
        claim semantic support for all relation types or validate their topology.
        Memory is bounded by one entity; lookups use disk primary-key indexes.
        """
        self._open()
        if self._db.execute('PRAGMA integrity_check').fetchone() != ('ok',):
            raise ValueError('OSM index integrity check failed')
        digest = hashlib.sha256()
        counts = dict(nodes=0, ways=0, relations=0, way_node_references=0,
                      relation_members=0, missing_way_nodes=0, missing_members=0)
        for table, column, key in (('nodes', 'NULL', 'nodes'),
                                   ('ways', 'refs', 'ways'),
                                   ('relations', 'members', 'relations')):
            for identifier, raw in self._rows(f'SELECT id,{column} FROM {table} ORDER BY id'):
                counts[key] += 1
                payload = [] if raw is None else json.loads(raw)
                digest.update((json.dumps([key, identifier, payload], ensure_ascii=True,
                                          separators=(',', ':')) + '\n').encode('ascii'))
                if table == 'ways':
                    for ref in payload:
                        counts['way_node_references'] += 1
                        if self._db.execute('SELECT 1 FROM nodes WHERE id=?', (ref,)).fetchone() is None:
                            counts['missing_way_nodes'] += 1
                elif table == 'relations':
                    for kind, ref, _role in payload:
                        counts['relation_members'] += 1
                        target = {'node': 'nodes', 'way': 'ways', 'relation': 'relations'}[kind]
                        if self._db.execute(f'SELECT 1 FROM {target} WHERE id=?', (ref,)).fetchone() is None:
                            counts['missing_members'] += 1
                if counts[key] % 512 == 0:
                    self._space()
        return dict(counts, structural_sha256=digest.hexdigest(),
                    complete=True, passed=not (counts['missing_way_nodes'] or counts['missing_members']))

    def collection(self, *, max_features=100_000, max_vertices=1_000_000,
                   max_bytes=64 * 1024 * 1024, **filters):
        """Materialize only a bounded selected region for the plotting API."""
        max_features = _limit(max_features, 'max_features'); max_vertices = _limit(max_vertices, 'max_vertices')
        max_bytes = _limit(max_bytes, 'max_bytes')
        features = []; vertices = 0; bytes_used = 0
        for feature in self.features(**filters):
            vertices += sum(1 for _ in feature.geometry.iter_positions())
            bytes_used += len(json.dumps(feature.to_geojson(), ensure_ascii=False).encode('utf8'))
            if len(features) >= max_features or vertices > max_vertices or bytes_used > max_bytes:
                raise ValueError('Selected PBF collection exceeds feature/vertex budget; narrow the filters')
            features.append(feature)
        return FeatureCollection(tuple(features))


def read_osm_pbf(source, *, bbox=None, where=None, include_untagged=False,
                 max_features=100_000, max_vertices=1_000_000,
                 max_bytes=64 * 1024 * 1024, **index_options):
    """Read a bounded collection; for large inputs use OSMIndex.features()."""
    with OSMIndex(source, **index_options) as index:
        return index.collection(bbox=bbox, where=where, include_untagged=include_untagged,
                                max_features=max_features, max_vertices=max_vertices, max_bytes=max_bytes)
