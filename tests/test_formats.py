# Binary/XML/georeference contracts with independent fixtures and failures.
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import azimlib as azl


def shp(records, kind, box=(0, 0, 10, 10)):
    def header(size):
        return struct.pack('>7i', 9994, 0, 0, 0, 0, 0, size//2)+struct.pack('<2i8d', 1000, kind, *box, 0, 0, 0, 0)
    body = b''; index = b''
    for i, record in enumerate(records, 1):
        index += struct.pack('>2i', (100+len(body))//2, len(record)//2)
        body += struct.pack('>2i', i, len(record)//2)+record
    return header(100+len(body))+body, header(100+len(index))+index


def parts_record(kind, parts):
    points = [p for part in parts for p in part]; starts = []; pos = 0
    for part in parts: starts.append(pos); pos += len(part)
    raw = struct.pack('<i4d2i', kind, min(p[0] for p in points), min(p[1] for p in points),
                      max(p[0] for p in points), max(p[1] for p in points), len(parts), len(points))
    raw += struct.pack(f'<{len(starts)}i', *starts)
    raw += b''.join(struct.pack('<2d', *p[:2]) for p in points)
    if kind > 10:
        z = [p[2] for p in points]
        raw += struct.pack('<2d', min(z), max(z))+struct.pack(f'<{len(z)}d', *z)
    return raw


def dbf(rows, fields=(('NAME', 'C', 12, 0),), encoding='utf-8'):
    header_size = 33+32*len(fields); width = 1+sum(f[2] for f in fields)
    header = bytearray(32); header[0] = 3
    struct.pack_into('<IHH', header, 4, len(rows), header_size, width)
    for name, kind, length, decimals in fields:
        descriptor = bytearray(32); descriptor[:len(name)] = name.encode('ascii')
        descriptor[11] = ord(kind); descriptor[16] = length; descriptor[17] = decimals
        header += descriptor
    result = bytes(header)+b'\x0d'
    for deleted, values in rows:
        result += b'*' if deleted else b' '
        for value, (_, kind, length, _) in zip(values, fields):
            raw = value.encode(encoding if kind == 'C' else 'ascii')
            result += raw.ljust(length, b' ') if kind == 'C' else raw.rjust(length, b' ')
    return result+b'\x1a'


class ShapefileTests(unittest.TestCase):
    def test_points_nulls_and_index_validation(self):
        raw, index = shp([struct.pack('<i2d', 1, 1, 2), struct.pack('<i', 0)], 1)
        result = azl.read_shapefile(io.BytesIO(raw), crs=4326, shx=index)
        self.assertEqual(result[0].geometry.coordinates, (1, 2))
        self.assertEqual([f.id for f in result], [1, 2]); self.assertIsNone(result[1].geometry)
        broken = bytearray(index); struct.pack_into('>i', broken, 100, 51)
        with self.assertRaisesRegex(ValueError, 'SHX'): azl.read_shapefile(raw, crs=4326, shx=bytes(broken))

    def test_lines_multipart_z_and_multipoint(self):
        parts = (((1, 2, 9), (3, 4, 8)), ((5, 6, 7), (7, 8, 6)))
        raw, _ = shp([parts_record(13, parts)], 13)
        self.assertEqual(azl.read_shapefile(raw, crs=4326)[0].geometry.coordinates, parts)
        multi = struct.pack('<i4di4d', 8, 1, 2, 3, 4, 2, 1, 2, 3, 4)
        raw, _ = shp([multi], 8)
        self.assertEqual(azl.read_shapefile(raw, crs=4326)[0].geometry.type, 'MultiPoint')
        raw, _ = shp([struct.pack('<i3d', 11, 1, 2, 123)], 11)
        self.assertEqual(azl.read_shapefile(raw, crs=4326)[0].geometry.coordinates, (1, 2, 123))

    def test_polygons_hole_before_shell_and_disjoint_shells(self):
        outer = ((0, 0), (0, 4), (4, 4), (4, 0), (0, 0))
        hole = ((1, 1), (3, 1), (3, 3), (1, 3), (1, 1))
        second = ((6, 0), (6, 2), (8, 2), (8, 0), (6, 0))
        raw, index = shp([parts_record(5, (hole, second, outer))], 5)
        feature = azl.read_shapefile(raw, crs=4326, shx=index)[0]
        self.assertEqual(feature.geometry.type, 'MultiPolygon')
        self.assertEqual([len(p) for p in feature.geometry.coordinates], [1, 2])
        self.assertEqual(feature.bounds, (0, 0, 8, 4))

    def test_deleted_dbf_keeps_physical_shape_alignment(self):
        raw, index = shp([struct.pack('<i2d', 1, i, 1) for i in (1, 2, 3)], 1)
        table = dbf(((False, ('One',)), (True, ('Deleted',)), (False, ('Three',))))
        result = azl.read_shapefile(raw, crs=4326, shx=index, dbf=table, encoding='utf-8')
        self.assertEqual([f.id for f in result], [1, 3])
        self.assertEqual(result[1].properties['NAME'], 'Three')
        self.assertEqual(result[1].geometry.coordinates, (3, 1))
        self.assertEqual(len(azl.read_shapefile(raw, crs=4326, dbf=table, encoding='utf-8', include_deleted=True)), 3)

    def test_sidecar_discovery_stream_ownership_and_explicit_encoding(self):
        raw, index = shp([struct.pack('<i2d', 1, 1, 2)], 1)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'data.shp'; path.write_bytes(raw)
            path.with_suffix('.shx').write_bytes(index)
            path.with_suffix('.dbf').write_bytes(dbf(((False, ('São',)),)))
            with self.assertRaises(ValueError): azl.read_shapefile(path, crs=4326)
            self.assertEqual(azl.read_shapefile(path, crs=4326, encoding='utf-8')[0].properties['NAME'], 'São')
        stream = io.BytesIO(raw); azl.read_shapefile(stream, crs=4326); self.assertFalse(stream.closed)

    def test_projected_input_not_mistaken_for_latitude(self):
        raw, _ = shp([struct.pack('<i2d', 1, 111319.49079327357, 222684.20850554405)], 1,
                      (100000, 200000, 120000, 240000))
        point = azl.read_shapefile(raw, crs=3857)[0].geometry.coordinates
        self.assertAlmostEqual(point[0], 1); self.assertAlmostEqual(point[1], 2)
        with self.assertRaises(ValueError): azl.read_shapefile(raw, crs=4326)

    def test_corrupt_or_unsupported_shapes_are_not_truncated(self):
        valid, index = shp([struct.pack('<i2d', 1, 1, 2)], 1)
        cases = [valid[:99], valid[:-1], b'bad'+valid[3:]]
        for offset, fmt, value in ((24, '>i', 50), (28, '<i', 999), (32, '<i', 31), (100, '>i', 2), (104, '>i', -1), (108, '<i', 3)):
            raw = bytearray(valid); struct.pack_into(fmt, raw, offset, value); cases.append(bytes(raw))
        for raw in cases:
            with self.subTest(size=len(raw)), self.assertRaises(ValueError): azl.read_shapefile(raw, crs=4326)
        with self.assertRaisesRegex(ValueError, 'row count'):
            azl.read_shapefile(valid, crs=4326, dbf=dbf(()), encoding='utf-8')

    def test_invalid_parts_rings_and_orphan_holes(self):
        ring = ((0, 0), (4, 0), (4, 4), (0, 0))  # hole winding without a shell
        for parts in ((ring,), (((0, 0), (0, 4), (4, 4), (4, 0)),)):
            raw, _ = shp([parts_record(5, parts)], 5)
            with self.assertRaises(ValueError): azl.read_shapefile(raw, crs=4326)
        record = bytearray(parts_record(3, (((1, 2), (3, 4)),)))
        struct.pack_into('<i', record, 44, 1)
        raw, _ = shp([bytes(record)], 3)
        with self.assertRaises(ValueError): azl.read_shapefile(raw, crs=4326)


class DBFTests(unittest.TestCase):
    def test_types_nulls_dates_deleted_and_immutability(self):
        fields = (('C', 'C', 8, 0), ('N', 'N', 4, 0), ('F', 'F', 6, 2), ('L', 'L', 1, 0), ('D', 'D', 8, 0))
        raw = dbf(((False, ('São', '12', '2.50', 'T', '20240229')), (True, ('Old', '', '', '?', ''))), fields)
        result = azl.read_dbf(raw, encoding='utf-8', include_deleted=True)
        self.assertEqual(dict(result[0].properties), {'C': 'São', 'N': 12, 'F': 2.5, 'L': True, 'D': '2024-02-29'})
        self.assertTrue(result[1].deleted); self.assertIsNone(result[1].properties['N'])
        self.assertEqual([r.index for r in azl.read_dbf(raw, encoding='utf-8')], [0])
        with self.assertRaises(TypeError): result[0].properties['C'] = 'Changed'

    def test_invalid_dbf_structure_types_values_and_encoding(self):
        valid = dbf(((False, ('Name',)),))
        cases = [valid[:-2], valid+b'junk']
        for offset, value in ((0, 131), (15, 1), (32+11, ord('M')), (32+16, 0), (64, 0), (65, 0)):
            raw = bytearray(valid); raw[offset] = value; cases.append(bytes(raw))
        for raw in cases:
            with self.subTest(offset=len(raw)), self.assertRaises(ValueError): azl.read_dbf(raw, encoding='utf-8')
        for kind, length, value in (('N', 5, 'nan'), ('F', 5, 'inf'), ('L', 1, 'X'), ('D', 8, '20230229')):
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                azl.read_dbf(dbf(((False, (value,)),), (('value', kind, length, 0),)), encoding='utf-8')


KML = '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>{}</Document></kml>'

class XMLTests(unittest.TestCase):
    def test_kml_names_altitude_extended_data_and_multigeometry(self):
        content = KML.format('''<Placemark id="a"><name>Town</name><ExtendedData><Data name="size"><value>12</value></Data></ExtendedData>
        <MultiGeometry><Point><altitudeMode>absolute</altitudeMode><coordinates>1,2,30</coordinates></Point>
        <LineString><coordinates>1,2 3,4</coordinates></LineString></MultiGeometry></Placemark>''')
        feature = azl.read_kml(io.StringIO(content))[0]
        self.assertEqual(feature.id, 'a'); self.assertEqual(feature.properties['name'], 'Town')
        self.assertEqual(feature.properties['extended_data']['size'], '12')
        self.assertEqual(feature.properties['altitude_modes'], ('absolute',))
        self.assertEqual(feature.geometry.geometries[0].coordinates, (1, 2, 30))

    def test_kml_polygon_holes_and_null_placemark(self):
        content = KML.format('''<Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>0,0 4,0 4,4 0,4 0,0</coordinates></LinearRing></outerBoundaryIs>
        <innerBoundaryIs><LinearRing><coordinates>1,1 1,2 2,2 2,1 1,1</coordinates></LinearRing></innerBoundaryIs></Polygon></Placemark>
        <Placemark><name>Empty</name></Placemark>''')
        result = azl.read_kml(content)
        self.assertEqual(len(result[0].geometry.coordinates), 2); self.assertIsNone(result[1].geometry)

    def test_kml_unsupported_bad_tuples_duplicate_ids_and_unclosed_rings(self):
        for body in ('<NetworkLink/>', '<Placemark><Model/></Placemark>', '<Placemark><Point><coordinates>1,2 3,4</coordinates></Point></Placemark>',
                     '<Placemark><Point><coordinates>1,91</coordinates></Point></Placemark>', '<Placemark id="a"/><Placemark id="a"/>',
                     '<Placemark><Point><coordinates>1,2</coordinates></Point><Point><coordinates>1,2</coordinates></Point></Placemark>',
                     '<Placemark><Polygon><outerBoundaryIs><LinearRing><coordinates>0,0 1,0 1,1 0,1</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>'):
            with self.subTest(body=body[:30]), self.assertRaises(ValueError): azl.read_kml(KML.format(body))

    def test_xml_never_resolves_dtd_entities_includes_or_network(self):
        for source in ('<!DOCTYPE kml [<!ENTITY x SYSTEM "file:///missing">]><kml/>',
                       '<kml xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include href="file:///missing"/></kml>', '<kml>'):
            for raw in (source, source.encode('utf-16')):
                with self.subTest(raw_type=type(raw)), self.assertRaises(ValueError): azl.read_kml(raw)

    def test_osm_nodes_lines_areas_ids_and_no_editor_metadata(self):
        raw = '''<osm version="0.6"><node id="1" lon="0" lat="0" user="editor"><tag k="name" v="Station"/></node>
        <node id="2" lon="1" lat="0"/><node id="3" lon="1" lat="1"/>
        <way id="1"><nd ref="1"/><nd ref="2"/><tag k="highway" v="residential"/></way>
        <way id="2"><nd ref="1"/><nd ref="2"/><nd ref="3"/><nd ref="1"/><tag k="building" v="yes"/></way></osm>'''
        result = azl.read_osm(raw)
        self.assertEqual([f.id for f in result], ['node/1', 'way/1', 'way/2'])
        self.assertEqual([f.geometry.type for f in result], ['Point', 'LineString', 'Polygon'])
        self.assertNotIn('user', result[0].properties)
        self.assertEqual(len(azl.read_osm(raw, include_untagged=True)), 5)

    def test_osm_reversed_segments_holes_and_multiple_outer_rings(self):
        nodes = ''.join(f'<node id="{i}" lon="{x}" lat="{y}"/>' for i, (x, y) in enumerate(((0, 0), (4, 0), (4, 4), (0, 4), (1, 1), (2, 1), (2, 2), (1, 2), (6, 0), (8, 0), (8, 2), (6, 2)), 1))
        ways = ''
        segments = ((1, 2, 3), (1, 4, 3), (5, 6, 7, 8, 5), (9, 10, 11, 12, 9))
        for i, refs in enumerate(segments, 1): ways += f'<way id="{i}">'+''.join(f'<nd ref="{r}"/>' for r in refs)+'</way>'
        members = ''.join(f'<member type="way" ref="{i}" role="{role}"/>' for i, role in ((1, 'outer'), (2, 'outer'), (3, 'inner'), (4, 'outer')))
        raw = f'<osm version="0.6">{nodes}{ways}<relation id="7">{members}<tag k="type" v="multipolygon"/><tag k="name" v="Park"/></relation></osm>'
        result = azl.read_osm(raw)
        self.assertEqual(len(result), 1); self.assertEqual(result[0].id, 'relation/7')
        self.assertEqual(result[0].geometry.type, 'MultiPolygon'); self.assertEqual([len(p) for p in result[0].geometry.coordinates], [2, 1])

    def test_osm_incomplete_refs_duplicates_and_area_no(self):
        for body in ('<way id="1"><nd ref="1"/><nd ref="2"/></way>', '<node id="1" lon="0" lat="0"/><node id="1" lon="1" lat="0"/>',
                     '<relation id="1"><member type="way" ref="99" role="outer"/><tag k="type" v="multipolygon"/></relation>'):
            with self.subTest(body=body[:20]), self.assertRaises(ValueError): azl.read_osm(f'<osm version="0.6">{body}</osm>')
        raw = '<osm version="0.6"><node id="1" lon="0" lat="0"/><node id="2" lon="1" lat="1"/><way id="3"><nd ref="1"/><nd ref="2"/><nd ref="1"/><tag k="building" v="yes"/><tag k="area" v="no"/></way></osm>'
        self.assertEqual(azl.read_osm(raw)[0].geometry.type, 'LineString')


class RasterTests(unittest.TestCase):
    def test_world_file_centres_corners_rotation_and_bounds(self):
        affine = azl.read_world_file('2\n0\n0\n-3\n101\n198.5\n')
        self.assertEqual(affine, (2, 0, 100, 0, -3, 200))
        raster = azl.GeoRaster([[1, -999], [float('nan'), 4]], affine, 3857, -999)
        self.assertEqual(raster.bounds, (100, 194, 104, 200))
        self.assertEqual(raster.coordinate(0, 0, center=True), (101, 198.5))
        self.assertEqual(raster.values, ((1, None), (None, 4)))
        rotated = azl.GeoRaster([[1]], (2, 1, 0, 1, -2, 0))
        self.assertEqual(rotated.bounds, (0, -2, 3, 1))
        with self.assertRaisesRegex(ValueError, 'Rotated'): rotated.geographic_mesh()

    def test_flipped_axes_and_invalid_affines_shapes(self):
        raster = azl.GeoRaster([[1, 2], [3, 4]], (-1, 0, 2, 0, 1, 0))
        self.assertEqual(raster.geographic_mesh(), ((0, 1, 2), (0, 1, 2), ((2, 1), (4, 3))))
        for affine in ((1, 0, 0, 0, 0, 0), (1, 0, 0, 0, -1), (float('nan'), 0, 0, 0, -1, 0)):
            with self.assertRaises(ValueError): azl.GeoRaster([[1]], affine)
        with self.assertRaises(ValueError): azl.GeoRaster([[1], [2, 3]], (1, 0, 0, 0, -1, 1))

    def test_mesh_nodata_colorbar_editing_and_failure_before_mutation(self):
        fig, ax = azl.subplots(); ax.set_extent((-1, 3, -1, 3))
        try:
            raster = azl.GeoRaster([[1, None], [3, 4]], (1, 0, 0, 0, -1, 2))
            layer = ax.raster(raster); bar = fig.colorbar(layer)
            layer.set_clim(0, 10); layer.set_visible(False); layer.set_visible(True)
            self.assertEqual(layer.data[2], ((3, 4), (1, None)))
            self.assertEqual(layer.get_clim(), (0, 10)); self.assertIn('<svg', fig.to_svg())
            before = (ax.get_extent(), len(ax.layers))
            with self.assertRaises(ValueError): ax.raster(azl.GeoRaster([[1]], (1, 1, 0, 0, -1, 1)))
            self.assertEqual((ax.get_extent(), len(ax.layers)), before)
        finally: azl.close('all')

    def test_scalar_png_sidecar_and_no_identity_fallback(self):
        try: from PIL import Image
        except ImportError: self.skipTest('Pillow optional')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'a.png'; Image.new('L', (2, 2), 5).save(path)
            path.with_suffix('.pgw').write_text('1\n0\n0\n-1\n.5\n1.5\n')
            result = azl.read_raster(path, crs=4326)
            self.assertEqual(result.extent, (0, 2, 0, 2))
            stream = io.BytesIO(path.read_bytes())
            explicit = azl.read_raster(stream, crs=4326, extent=(0, 2, 0, 2)); self.assertFalse(stream.closed)
            self.assertEqual(result, explicit)
            with self.assertRaises(ValueError): azl.read_raster(path)
            with self.assertRaises(ValueError): azl.read_raster(path.read_bytes(), crs=4326)
            with self.assertRaises(ValueError): azl.read_raster(path, crs=4326, max_pixels=1)

    def test_geotiff_area_point_float_nodata_and_byte_order(self):
        try: from PIL import Image, TiffImagePlugin
        except ImportError: self.skipTest('Pillow optional')
        for pixel in (1, 2):
            for mode in ('I;16', 'I;16B', 'F'):
                info = TiffImagePlugin.ImageFileDirectory_v2()
                info[33550] = (1., 2., 0.); info.tagtype[33550] = 12
                info[33922] = (0., 0., 0., 10., 20., 0.); info.tagtype[33922] = 12
                info[34735] = (1, 1, 0, 3, 1024, 0, 1, 2, 1025, 0, 1, pixel, 2048, 0, 1, 4326)
                info[42113] = '5'
                stream = io.BytesIO(); Image.new(mode, (2, 2), 5).save(stream, format='TIFF', tiffinfo=info)
                with self.subTest(pixel=pixel, mode=mode):
                    raster = azl.read_geotiff(stream.getvalue())
                    self.assertEqual(raster.values, ((None, None), (None, None)))
                    self.assertEqual(raster.extent, (10, 12, 16, 20) if pixel == 1 else (9.5, 11.5, 17, 21))
                    with self.assertRaises(ValueError): azl.read_geotiff(stream.getvalue(), crs=3857)

    def test_tiff_unsupported_and_matrix_georeference(self):
        try: from PIL import Image, TiffImagePlugin
        except ImportError: self.skipTest('Pillow optional')
        info = TiffImagePlugin.ImageFileDirectory_v2()
        info[34264] = (1., 0., 0., 10., 0., -1., 0., 20., 0., 0., 1., 0., 0., 0., 0., 1.); info.tagtype[34264] = 12
        stream = io.BytesIO(); Image.new('L', (2, 2), 7).save(stream, format='TIFF', tiffinfo=info)
        raw = stream.getvalue()
        self.assertEqual(azl.read_geotiff(raw, crs=4326).extent, (10, 12, 18, 20))
        for invalid in (raw[:20], b'II+\0'+raw[4:]):
            with self.assertRaises(ValueError): azl.read_geotiff(invalid, crs=4326)
        with self.assertRaises(ValueError): azl.read_geotiff(raw)
        stream = io.BytesIO(); Image.new('RGB', (1, 1)).save(stream, format='TIFF', tiffinfo=info)
        with self.assertRaises(ValueError): azl.read_geotiff(stream.getvalue(), crs=4326)


class CatalogTests(unittest.TestCase):
    def make(self, folder):
        folder = Path(folder)
        payload = b'{"type":"Point","coordinates":[1,2]}'
        (folder/'points.geojson').write_bytes(payload); (folder/'LICENSE.txt').write_text('Synthetic fixture, BSD-3-Clause.\n')
        entry = dict(id='points', version='1.0', format='geojson', file='points.geojson', crs='EPSG:4326',
                     license='BSD-3-Clause', copyright='2026 Kernerian', source='synthetic test fixture',
                     attribution='Synthetic fixture', license_file='LICENSE.txt',
                     files={name: hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in ('points.geojson', 'LICENSE.txt')})
        path = folder/'catalog.json'; path.write_text(json.dumps({'schema_version': 1, 'datasets': [entry]}))
        return path, entry

    def test_metadata_versions_load_exact_bytes_and_no_download(self):
        with tempfile.TemporaryDirectory() as folder:
            path, entry = self.make(folder); catalog = azl.DatasetCatalog(path)
            with patch('urllib.request.urlopen', side_effect=AssertionError('Network forbidden')):
                self.assertEqual(catalog.verify()['files_verified'], 2)
                self.assertEqual(catalog.load('points')[0].geometry.coordinates, (1, 2))
            detached = catalog.available(); detached[0]['license'] = 'Changed'
            self.assertEqual(catalog.available()[0]['license'], 'BSD-3-Clause')
            entry2 = dict(entry, version='2.0')
            path.write_text(json.dumps({'schema_version': 1, 'datasets': [entry, entry2]}))
            catalog = azl.DatasetCatalog(path)
            with self.assertRaises(ValueError): catalog.load('points')
            self.assertEqual(len(catalog.load('points', version='2.0')), 1)

    def test_tampered_data_or_license_are_rejected(self):
        for name in ('points.geojson', 'LICENSE.txt'):
            with tempfile.TemporaryDirectory() as folder:
                path, entry = self.make(folder); catalog = azl.DatasetCatalog(path)
                (Path(folder)/name).write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'integrity'): catalog.load('points')

    def test_metadata_paths_options_and_duplicates(self):
        for change in ({'file': '../escape'}, {'license': ''}, {'format': 'remote'}, {'options': {'url': 'https://invalid'}},
                       {'files': {'../escape': '0'*64}}, {'crs': 'EPSG:3857'}):
            with tempfile.TemporaryDirectory() as folder:
                path, entry = self.make(folder); entry.update(change)
                path.write_text(json.dumps({'schema_version': 1, 'datasets': [entry]}))
                with self.subTest(change=change), self.assertRaises(ValueError): azl.DatasetCatalog(path)



class RefinementTests(unittest.TestCase):
    def test_deleted_invalid_dbf_fields_are_not_decoded_or_misaligned(self):
        shape_bytes, shx = shp([struct.pack('<idd', 1, 1, 2), struct.pack('<idd', 1, 3, 4)], 1)
        raw = bytearray(dbf(((False,('good',)),(True,('bad',))), fields=(('name','C',4,0),)))
        header = struct.unpack_from('<H', raw, 8)[0]
        raw[header+6] = 255
        data = azl.read_shapefile(shape_bytes, shx=shx, dbf=bytes(raw), crs=4326, encoding='ascii')
        self.assertEqual([f.id for f in data], [1])
        with self.assertRaises(ValueError):
            azl.read_shapefile(shape_bytes, dbf=bytes(raw), crs=4326, encoding='ascii', include_deleted=True)

    def test_unknown_kml_namespaces_fail_and_osm_building_no_stays_line(self):
        with self.assertRaisesRegex(ValueError, 'namespace'):
            azl.read_kml('<kml><Placemark><x:Point xmlns:x="urn:unknown"><x:coordinates>1,2</x:coordinates></x:Point></Placemark></kml>')
        xml = '<osm version="0.6"><node id="1" lon="0" lat="0"/><node id="2" lon="1" lat="0"/><node id="3" lon="0" lat="1"/><way id="4"><nd ref="1"/><nd ref="2"/><nd ref="3"/><nd ref="1"/><tag k="building" v="no"/></way></osm>'
        self.assertEqual(azl.read_osm(xml)[0].geometry.type, 'LineString')

    def test_duplicate_catalog_json_keys_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'catalog.json'
            path.write_text('{"schema_version":1,"schema_version":1,"datasets":[]}')
            with self.assertRaises(ValueError): azl.DatasetCatalog(path)

    def test_catalog_symlink_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder, tempfile.TemporaryDirectory() as external:
            path, entry = CatalogTests().make(folder)
            link = Path(folder)/'link'
            try: link.symlink_to(Path(external), target_is_directory=True)
            except OSError: self.skipTest('Creating symlinks requires platform permission')
            entry['files']['link/escape.txt'] = '0'*64
            path.write_text(json.dumps({'schema_version':1,'datasets':[entry]}))
            with self.assertRaisesRegex(ValueError, 'symlink'): azl.DatasetCatalog(path)

    def test_catalog_dispatches_shp_dbf_xml_and_csv(self):
        shape_bytes, shx = shp([struct.pack('<idd', 1, 1, 2)], 1)
        records = dbf(((False,('Town',)),),fields=(('name','C',4,0),))
        for kind, raw, options in (
            ('shapefile', shape_bytes, {'shx':'index.shx','dbf':'names.dbf','encoding':'ascii'}),
            ('kml', b'<kml><Placemark><Point><coordinates>1,2</coordinates></Point></Placemark></kml>', {}),
            ('osm', b'<osm version="0.6"><node id="1" lon="1" lat="2"><tag k="name" v="Town"/></node></osm>', {}),
            ('csv', b'lon,lat,name\n1,2,Town\n', {}),
        ):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                path, entry = CatalogTests().make(folder)
                (Path(folder)/'payload').write_bytes(raw)
                (Path(folder)/'index.shx').write_bytes(shx)
                (Path(folder)/'names.dbf').write_bytes(records)
                entry.update(format=kind,file='payload',options=options)
                entry['files'] = {name:hashlib.sha256((Path(folder)/name).read_bytes()).hexdigest()
                                  for name in ('payload','LICENSE.txt','index.shx','names.dbf')}
                path.write_text(json.dumps({'schema_version':1,'datasets':[entry]}))
                self.assertEqual(azl.DatasetCatalog(path).load('points')[0].geometry.coordinates, (1,2))

    def test_deflate_tiff_and_catalog_raster_dispatch(self):
        try: from PIL import Image, TiffImagePlugin
        except ImportError: self.skipTest('Pillow optional')
        info = TiffImagePlugin.ImageFileDirectory_v2()
        info[33550] = (1.,1.,0.); info.tagtype[33550] = 12
        info[33922] = (0.,0.,0.,10.,20.,0.); info.tagtype[33922] = 12
        info[34735] = (1,1,0,3,1024,0,1,2,1025,0,1,1,2048,0,1,4326); info.tagtype[34735] = 3
        stream = io.BytesIO(); Image.new('I;16',(2,2),12).save(stream,format='TIFF',tiffinfo=info,compression='tiff_adobe_deflate')
        raw=stream.getvalue()
        self.assertEqual(azl.read_geotiff(raw).values, ((12,12),(12,12)))
        for kind in ('raster','geotiff'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                path, entry = CatalogTests().make(folder)
                (Path(folder)/'terrain.tif').write_bytes(raw)
                entry.update(format=kind,file='terrain.tif')
                entry['files']['terrain.tif'] = hashlib.sha256(raw).hexdigest()
                path.write_text(json.dumps({'schema_version':1,'datasets':[entry]}))
                self.assertEqual(azl.DatasetCatalog(path).load('points').extent, (10,12,18,20))
        for maximum in (0, -1, True, 2.5):
            with self.subTest(maximum=maximum), self.assertRaises(ValueError):
                azl.read_geotiff(raw, max_pixels=maximum)

if __name__ == '__main__': unittest.main()
