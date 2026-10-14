"""Own wire fixtures, disk extraction, corruption and privacy contracts."""
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import tracemalloc
import unittest
from unittest.mock import patch
import zlib

import azimlib as azl
from azimlib._pbf_wire import Budget, fields, varint, numbers, zigzag
from azimlib.pbf import _blob, _rings
from pbf_fixture import field, packed, blob, header, primitive, scene, xml, zz


def tiny(**kwargs):
    return header() + primitive(scene(), **kwargs)


class PBFTests(unittest.TestCase):
    def test_wire_known_bytes_and_unknown_fields(self):
        self.assertEqual(varint(bytes.fromhex('9601'), 0), (150, 2))
        self.assertEqual(zigzag(299), -150)
        message = fields(bytes.fromhex('0896011203010203') + field(77, b'future'), Budget())
        self.assertEqual(list(numbers(message, 2, Budget())), [1, 2, 3])
        self.assertEqual(message[1][0], (0, 150))
        for raw in (b'\x00', b'\x0b', b'\x08\x80', b'\x08' + b'\xff' * 10, b'\x12\x02x', b'\x09x', b'\x0dx'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                fields(raw, Budget())
        with self.assertRaises(ValueError):
            fields(field(1, 1) * 5, Budget(4))

    def test_normal_dense_raw_zlib_packed_unpacked_offsets_equivalence(self):
        expected = azl.read_osm(xml(scene())).to_geojson()
        for dense in (False, True):
            for unpacked in (False, True):
                for compress in (False, True):
                    with self.subTest(dense=dense, unpacked=unpacked, compress=compress):
                        raw = tiny(dense=dense, unpacked=unpacked, compress=compress,
                                   granularity=10, lon_offset=-500_000_000, lat_offset=200_000_000)
                        self.assertEqual(azl.read_osm_pbf(raw).to_geojson(), expected)

    def test_cross_block_unsorted_ids_and_forward_references(self):
        records = scene()
        records = records[9:] + list(reversed(records[:9]))
        raw = header() + b''.join(primitive([record]) for record in records)
        with azl.OSMIndex(raw) as index:
            result = list(index.features())
            self.assertEqual([f.id for f in result], ['way/13', 'relation/20', 'node/1'])
            self.assertEqual(index.statistics['nodes'], 9)
            self.assertEqual(index.sha256, hashlib.sha256(raw).hexdigest())
            restrictions = list(index.relations(restrictions_only=True))
            self.assertEqual(len(restrictions), 1)
            self.assertEqual(restrictions[0].members[1], azl.OSMMember('node', 2, 'via'))
            self.assertIn('restriction:conditional', restrictions[0].tags)
            with self.assertRaises(TypeError):
                restrictions[0].tags['name'] = 'changed'
        with self.assertRaisesRegex(ValueError, 'closed'):
            list(index.features())

    def test_signed_large_ids_deltas_without_float_conversion(self):
        identifier = 2**62 + 17
        records = [dict(kind='node', id=identifier, coordinates=(-179.125, -30.5), tags={'name': 'A'}),
                   dict(kind='node', id=-17, coordinates=(-178, -30)),
                   dict(kind='way', id=-4, refs=(identifier, -17), tags={'highway': 'path'})]
        for dense in (False, True):
            decoded = list(azl.iter_osm_pbf(header() + primitive(records, dense=dense)))
            self.assertEqual(decoded[0].id, identifier)
            self.assertEqual(decoded[2].refs, (identifier, -17))
            self.assertEqual(decoded[0].coordinates, (-179.125, -30.5))

    def test_dense_multiple_nodes_multiple_packed_chunks_and_metadata_discard(self):
        table = field(1, '') + field(1, 'name') + field(1, 'Example') + field(1, 'editor-not-retained')
        info = packed(4, [zz(55), zz(1)]) + packed(5, [zz(3), zz(0)]) + packed(6, [1, 1])
        dense = packed(1, [zz(100)]) + packed(1, [zz(2)]) + packed(8, [zz(-10), zz(3)])
        dense += packed(9, [zz(20), zz(-2)]) + packed(10, [1, 2, 0, 0]) + field(5, info)
        raw = header() + blob('OSMData', field(1, table) + field(2, field(2, dense)))
        records = list(azl.iter_osm_pbf(raw))
        self.assertEqual([r.id for r in records], [100, 102])
        self.assertEqual(records[1].coordinates, (0.0000018, -0.0000007))
        self.assertEqual(dict(records[0].tags), {'name': 'Example'})
        self.assertNotIn('editor-not-retained', repr(records))

    def test_locations_on_ways_declaration_and_index_consistency(self):
        records = [dict(kind='node', id=i + 1, coordinates=(i, i)) for i in range(2)]
        records += [dict(kind='way', id=3, refs=(1, 2), locations=((0, 0), (1, 1)), tags={'highway': 'path'})]
        raw = header(optional=('LocationsOnWays',)) + primitive(records, locations=True)
        self.assertEqual(len(azl.read_osm_pbf(raw)), 1)
        with self.assertRaisesRegex(ValueError, 'undeclared'):
            list(azl.iter_osm_pbf(header() + primitive(records, locations=True)))
        records[-1]['locations'] = ((0, 0), (2, 2))
        with self.assertRaisesRegex(ValueError, 'differs'):
            azl.read_osm_pbf(header(optional=('LocationsOnWays',)) + primitive(records, locations=True))

    def test_short_nonseekable_reads_and_ownership(self):
        class Short(io.BytesIO):
            def read(self, n=-1):
                self.assertion(n)
                return super().read(min(n, 3))
            def assertion(self, n):
                if n < 0:
                    raise AssertionError('unbounded read')
            def seek(self, *args):
                raise AssertionError('seek')
        stream = Short(tiny())
        self.assertEqual(len(azl.read_osm_pbf(stream)), 3)
        self.assertFalse(stream.closed)
        stream = Short(tiny()); iterator = azl.iter_osm_pbf(stream)
        next(iterator); iterator.close(); self.assertFalse(stream.closed)

    def test_framing_truncation_unknown_blocks_features_and_empty_input(self):
        raw = primitive([dict(kind='node', id=1, coordinates=(0, 0))])
        for end in range(1, len(raw)):
            with self.subTest(end=end), self.assertRaises(ValueError):
                list(azl.iter_osm_pbf(header() + raw[:end]))
        for invalid in (b'', raw, header() + header(), struct.pack('>I', 65536),
                        header('OsmSchema-V0.6', 'HistoricalInformation'), header('DenseNodes')):
            with self.assertRaises(ValueError):
                list(azl.iter_osm_pbf(invalid))
        self.assertEqual(len(list(azl.iter_osm_pbf(header() + blob('future', b'ignored') + raw))), 1)

    def test_blob_codecs_sizes_bombs_and_trailing_stream(self):
        for raw in (field(1, b'x') + field(3, zlib.compress(b'x')), field(2, 1),
                    field(1, b'x') + field(2, 2), field(3, zlib.compress(b'x')),
                    field(2, 1) + field(3, zlib.compress(b'x' * 100_000)),
                    field(2, 1) + field(3, zlib.compress(b'x') + b'extra'),
                    field(2, 1) + field(3, b'invalid'), field(2, 32 * 1024 * 1024) + field(3, b'x')):
            with self.subTest(raw=raw[:30]), self.assertRaises(ValueError):
                _blob(raw)
        for codec in (4, 5, 6, 7):
            with self.assertRaisesRegex(ValueError, 'Unsupported PBF compression'):
                _blob(field(2, 1) + field(codec, b'x'))
        self.assertEqual(bytes(_blob(field(1, b'x'))), b'x')

    def test_corrupt_schema_tables_tags_and_members(self):
        table = field(1, '') + field(1, 'name') + field(1, 'A')
        point = field(1, zz(1)) + field(8, 0) + field(9, 0)
        invalid_blocks = [field(1, field(1, 'wrong')),
                          field(1, field(1, '') + field(1, b'\xff')),
                          field(1, table) + field(2, field(1, point + packed(2, [1]))),
                          field(1, table) + field(2, field(1, point + packed(2, [1]) + packed(3, [9]))),
                          field(1, table) + field(2, field(1, point + packed(2, [1, 1]) + packed(3, [2, 2]))),
                          field(1, table) + field(2, field(1, point + field(4, field(6, 0)))),
                          field(1, table) + field(2, field(1, point) + field(3, field(1, 1))),
                          field(1, table) + field(2, field(1, field(1, 0) + field(8, 0) + field(9, 0))),
                          field(1, table) + field(2, field(1, field(1, 2) + field(8, zz(1_000_000_000)) + field(9, 0))),
                          field(1, table) + field(17, 0),
                          field(1, table) + field(2, field(4, field(1, 1) + packed(8, [0]) + packed(9, [2]) + packed(10, [3])))]
        for raw in invalid_blocks:
            with self.subTest(raw=raw[:40]), self.assertRaises(ValueError):
                list(azl.iter_osm_pbf(header() + blob('OSMData', raw)))
        for kv in ([1], [1, 2], [0, 0], [1, 9, 0], [-1, 2, 0]):
            dense = packed(1, [2]) + packed(8, [0]) + packed(9, [0]) + packed(10, kv)
            with self.subTest(kv=kv), self.assertRaises(ValueError):
                list(azl.iter_osm_pbf(header() + blob('OSMData', field(1, table) + field(2, field(2, dense)))))

    def test_missing_reference_policy_and_duplicate_ids(self):
        records = scene(); records = [r for r in records if r['id'] != 9]
        raw = header() + primitive(records)
        with self.assertRaisesRegex(ValueError, 'Missing OSM node'):
            azl.read_osm_pbf(raw)
        with azl.OSMIndex(raw, missing='skip') as index:
            self.assertEqual(index.statistics['missing_ways'], 1)
            self.assertEqual(index.statistics['missing_relations'], 1)
            self.assertEqual(len(list(index.features())), 2)
            self.assertEqual(len(list(index.relations(include_incomplete=True))), 2)
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            azl.read_osm_pbf(header() + primitive(scene() + [scene()[0]]))

    def test_boundary_holes_reversed_members_and_ring_failures(self):
        records = scene()[:-1]; records[-1]['tags']['type'] = 'boundary'
        records[-1]['members'] += (('node', 1, 'admin_centre'),)
        records[-1]['members'] += (('relation', 999, 'subarea'),)
        feature = azl.read_osm_pbf(header() + primitive(records))[-1]
        self.assertEqual(feature.geometry.type, 'Polygon')
        self.assertEqual(len(feature.geometry.coordinates), 2)
        for segments in (((1, 2),), ((1, 2), (2, 3), (2, 1)), ((1, 2, 1),)):
            with self.assertRaises(ValueError):
                _rings(segments, 100)
        with self.assertRaisesRegex(ValueError, 'budget'):
            _rings(((1, 2, 3, 1),), 3)

    def test_bbox_tag_filters_whole_crossing_features_and_collection_budgets(self):
        with azl.OSMIndex(tiny()) as index:
            self.assertEqual([f.id for f in index.features(where={'highway': 'residential'})], ['way/13'])
            self.assertEqual([f.id for f in index.features(bbox=(2.5, 2.5, 3.5, 3.5))], ['relation/20'])
            self.assertEqual(list(index.features(bbox=(100, 20, 110, 30))), [])
            self.assertEqual(list(index.features(bbox=(170, -10, -170, 10))), [])
            for kw in ({'max_features': 1}, {'max_vertices': 2}):
                with self.assertRaisesRegex(ValueError, 'budget'):
                    index.collection(**kw)
            with self.assertRaisesRegex(ValueError, 'budget'):
                index.collection(max_bytes=10)
            for kw in ({'bbox': (0, 4, 2, 1)}, {'bbox': (0, 0, 181, 2)}, {'bbox': (False, 0, 1, 1)}, {'where': {'name': 1}}):
                with self.assertRaises(ValueError):
                    list(index.features(**kw))
            with self.assertRaises(ValueError):
                list(index.features(bbox=iter((False, 0, 1, 1))))

    def test_verified_input_and_cleanup_on_error(self):
        raw = tiny(); digest = hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as folder:
            with azl.OSMIndex(raw, directory=folder, expected_sha256=digest) as index:
                self.assertEqual(len(index.collection()), 3)
                self.assertTrue(list(Path(folder).iterdir()))
            self.assertEqual(list(Path(folder).iterdir()), [])
            for invalid in ('0' * 64, 'not-a-digest'):
                with self.assertRaises(ValueError):
                    azl.OSMIndex(raw, directory=folder, expected_sha256=invalid)
                self.assertEqual(list(Path(folder).iterdir()), [])

    def test_disk_budget_free_space_abort_and_input_validation(self):
        with patch('azimlib.pbf.shutil.disk_usage') as usage:
            usage.return_value.free = 15_000_000_000
            with self.assertRaisesRegex(ValueError, 'reserved'):
                azl.OSMIndex(tiny(), max_disk_bytes=20_000_000_000, reserve_free_bytes=15_000_000_000)
        for kw in ({'max_disk_bytes': True}, {'reserve_free_bytes': -1}, {'max_refs': 1}, {'missing': 'ignore'}):
            with self.assertRaises(ValueError):
                azl.OSMIndex(tiny(), **kw)

    def test_real_sqlite_page_budget_aborts_and_cleans_up(self):
        def nodes(start):
            return [dict(kind='node', id=i, coordinates=(0, 0)) for i in range(start, start + 10_000)]
        raw = header() + b''.join(primitive(nodes(start)) for start in range(1, 50_001, 10_000))
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'disk index failed'):
                with azl.OSMIndex(raw, directory=folder, max_disk_bytes=1024 * 1024):
                    pass
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_close_releases_paused_query_cursors_on_windows(self):
        with tempfile.TemporaryDirectory() as folder:
            index = azl.OSMIndex(tiny(), directory=folder)
            iterator = index.features(); next(iterator)
            relation_iterator = index.relations(); next(relation_iterator)
            index.close()
            self.assertEqual(list(Path(folder).iterdir()), [])
            with self.assertRaisesRegex(ValueError, 'closed'):
                next(iterator)
            iterator.close(); relation_iterator.close()

    def test_dateline_crossing_envelope_is_conservative(self):
        records = [dict(kind='node', id=1, coordinates=(179, 0)),
                   dict(kind='node', id=2, coordinates=(-179, 1)),
                   dict(kind='way', id=3, refs=(1, 2), tags={'highway': 'path'})]
        data = azl.read_osm_pbf(header() + primitive(records), bbox=(179.4, 0, 179.8, 1))
        self.assertEqual([f.id for f in data], ['way/3'])

    def test_partial_restriction_not_silently_claimed_complete(self):
        records = scene(); records[-1]['members'] = records[-1]['members'][1:]
        raw = header() + primitive(records)
        with self.assertRaisesRegex(ValueError, 'Incomplete OSM restriction'):
            azl.read_osm_pbf(raw)
        with azl.OSMIndex(raw, missing='skip') as index:
            self.assertEqual(index.statistics['missing_relations'], 1)
            self.assertEqual(list(index.relations(restrictions_only=True)), [])
            self.assertEqual(len(list(index.relations(include_incomplete=True))), 2)

    def test_raw_non_geometric_nested_relation_preserves_member_identity(self):
        record = dict(kind='relation', id=45, tags={'type': 'route', 'route': 'bus'},
                      members=(('relation', 99, 'forward'), ('node', 123, 'stop')))
        raw = header() + primitive([record])
        self.assertEqual(list(azl.iter_osm_pbf(raw))[0].members[0], azl.OSMMember('relation', 99, 'forward'))
        with azl.OSMIndex(raw) as index:
            self.assertEqual(len(list(index.relations())), 1)
            self.assertEqual(list(index.features()), [])

    def test_no_dense_feature_declaration_and_too_many_entity_references(self):
        with self.assertRaisesRegex(ValueError, 'DenseNodes'):
            list(azl.iter_osm_pbf(header('OsmSchema-V0.6') + primitive(scene())))
        with self.assertRaisesRegex(ValueError, 'count outside budget'):
            list(azl.iter_osm_pbf(tiny(), max_refs=2))

    def test_structural_budget_is_separate_from_packed_numeric_budget(self):
        budget = Budget(); budget.max_fields = 2
        with self.assertRaisesRegex(ValueError, 'structural'):
            fields(field(1, b'') * 3, budget)
        message = fields(packed(1, [1, 2, 3]), Budget())
        self.assertEqual(list(numbers(message, 1, Budget(3))), [1, 2, 3])
        with self.assertRaisesRegex(ValueError, 'decoded item'):
            numbers(message, 1, Budget(2))
        budget = Budget(); budget.max_fields = 2
        fields(field(1, 1) * 2, budget)
        # Separate bounded messages reuse the global item budget, not a spent
        # structural allowance from an already released primitive's fields.
        fields(field(1, 1) * 2, budget)

    def test_acquisition_is_explicit_verified_bounded_and_atomic(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('acquire_osm_pbf', Path(__file__).resolve().parents[1] / 'tools/acquire_osm_pbf.py')
        tool = importlib.util.module_from_spec(spec); spec.loader.exec_module(tool)
        notice = b'Original synthetic notice used only with a mocked license digest.'
        raw = tiny()
        class Response(io.BytesIO):
            headers = {'Content-Length': str(len(raw))}
            def geturl(self):
                return 'https://example.org/map.pbf'
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); license_file = root / 'notice.txt'; license_file.write_bytes(notice)
            options = dict(sha256=hashlib.sha256(raw).hexdigest(), version='1', license_file=license_file,
                           reserve_free_bytes=0)
            with patch.object(tool, '_ODBL_SHA256', hashlib.sha256(notice).hexdigest()):
                with patch.object(tool, 'urlopen', return_value=Response(raw)) as download:
                    result = tool.acquire('https://example.org/map.pbf', root / 'ok', **options)
                    self.assertTrue(result['passed']); self.assertEqual(download.call_count, 1)
                    self.assertEqual(len(azl.DatasetCatalog(root / 'ok/catalog.json').load('osm-extract')), 3)
                for name, updates in (('bad-hash', {'sha256': '0' * 64}), ('too-big', {'max_bytes': 10})):
                    with patch.object(tool, 'urlopen', return_value=Response(raw)), self.assertRaises(ValueError):
                        tool.acquire('https://example.org/map.pbf', root / name, **dict(options, **updates))
                    self.assertFalse((root / name).exists())
                with patch.object(tool, 'urlopen') as download:
                    with self.assertRaises(ValueError):
                        tool.acquire('https://example.org/map.pbf', root / 'ok', **options)
                    download.assert_not_called()
            with patch.object(tool, 'urlopen') as download:
                with self.assertRaisesRegex(ValueError, 'ODbL'):
                    tool.acquire('https://example.org/map.pbf', root / 'invalid-license', **options)
                download.assert_not_called()

    def test_catalog_stream_verification_and_hash_cannot_be_overridden(self):
        raw = tiny()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root / 'map.pbf').write_bytes(raw); (root / 'LICENSE.txt').write_bytes(b'Synthetic original test fixture')
            entry = dict(id='fixture', version='1', format='osm-pbf', file='map.pbf', crs='EPSG:4326',
                         license='BSD-3-Clause', copyright='Kernerian', source='original fixture',
                         attribution='Synthetic fixture', license_file='LICENSE.txt',
                         files={name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in ('map.pbf', 'LICENSE.txt')})
            path = root / 'catalog.json'; path.write_text(json.dumps(dict(schema_version=1, datasets=[entry])), encoding='utf8')
            catalog = azl.DatasetCatalog(path)
            self.assertEqual(catalog.verify()['files_verified'], 2)
            self.assertEqual(len(catalog.load('fixture')), 3)
            with catalog.open_pbf('fixture') as index:
                self.assertEqual(len(index.collection(where={'landuse': 'forest'})), 1)
            with self.assertRaises(ValueError):
                catalog.open_pbf('fixture', expected_sha256='0' * 64)
            (root / 'map.pbf').write_bytes(raw + blob('future', b'changed'))
            with self.assertRaisesRegex(ValueError, 'integrity'):
                catalog.load('fixture')

    def test_large_sequential_stream_does_not_accumulate_records(self):
        class Blocks:
            def __init__(self, count):
                self.count = count; self.index = -1; self.buffer = b''
            def read(self, size):
                if not self.buffer:
                    if self.index >= self.count:
                        return b''
                    self.buffer = header() if self.index == -1 else primitive([dict(kind='node', id=self.index + 1, coordinates=(0, 0))])
                    self.index += 1
                result = self.buffer[:size]; self.buffer = self.buffer[size:]
                return result
        peaks = []
        for count in (100, 5000):
            tracemalloc.start()
            self.assertEqual(sum(1 for _ in azl.iter_osm_pbf(Blocks(count))), count)
            peaks.append(tracemalloc.get_traced_memory()[1]); tracemalloc.stop()
        self.assertLess(peaks[1], peaks[0] + 1024 * 1024)

    def test_plot_urban_layers_and_exports_from_pbf(self):
        data = azl.read_osm_pbf(tiny())
        fig, ax = azl.subplots(figsize=(3, 3)); ax.streets(data.select(where={'highway': 'residential'}))
        ax.set_extent((-1, 6, -1, 5)); ax.geojson(data.select(where={'landuse': 'forest'}), facecolor='#ddeedd')
        output = io.StringIO(); fig.savefig(output, format='svg')
        self.assertIn('<svg', output.getvalue())
        output = io.BytesIO(); fig.savefig(output, format='png')
        self.assertTrue(output.getvalue().startswith(b'\x89PNG'))
        azl.close(fig)


if __name__ == '__main__':
    unittest.main()
