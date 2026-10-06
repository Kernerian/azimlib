"""Urban data interchange, immutable selection and existing Artist lifecycle."""
import io
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

import azimlib as azl
import azimlib.pyplot as plt
from azimlib.io import read_csv


def sample():
    return azl.FeatureCollection((
        azl.Feature(azl.Geometry('Point', (1, 2)), {'name': 'A', 'class': 'town', 'rank': 2}, 'a'),
        azl.Feature(azl.Geometry('Point', (3, 4)), {'name': 'B', 'class': 'town', 'rank': 1, 'note': None}, 'b'),
        azl.Feature(azl.Geometry('LineString', ((0, 0), (2, 2))), {'class': 'street'}, 'c'),
        azl.Feature(None, {'class': 'town'}, 'd'),
    ))


class SelectionTests(unittest.TestCase):
    def test_preserves_identity_ids_order_and_original_bounds(self):
        original = sample()
        original_bounds = original.bounds
        selected = original.select({'class': 'town'}, predicate=lambda f: f.geometry is not None)
        self.assertEqual([f.id for f in selected], ['a', 'b'])
        self.assertIs(selected[0], original[0])
        self.assertIs(selected[1], original[1])
        self.assertEqual(selected.bounds, (1, 2, 3, 4))
        self.assertEqual(original.bounds, original_bounds)
        self.assertEqual(len(original), 4)
        self.assertEqual(azl.read_geojson(selected.to_geojson()), selected)

    def test_nested_json_values_are_matched_after_freezing(self):
        properties = {'tags': ['town', {'rank': 2}]}
        feature = azl.Feature(azl.Geometry('Point', (0, 0)), properties)
        collection = azl.FeatureCollection((feature,))
        self.assertIs(collection.select(properties)[0], feature)
        with self.assertRaises(ValueError):
            collection.select({'tags': {1}})

    def test_missing_property_does_not_match_null(self):
        self.assertEqual([f.id for f in sample().select({'note': None})], ['b'])

    def test_filters_combine_and_predicate_receives_feature(self):
        seen = []
        result = sample().select({'class': 'town'}, geometry_types=('Point',),
                                 predicate=lambda f: seen.append(f.id) or f.properties['rank'] >= 2)
        self.assertEqual(seen, ['a', 'b'])
        self.assertEqual([f.id for f in result], ['a'])

    def test_empty_and_unfiltered_collections(self):
        self.assertEqual(sample().select(), sample())
        self.assertIsNone(sample().select({'missing': 1}).bounds)
        self.assertEqual(len(sample().select(geometry_types=())), 0)
        self.assertEqual(azl.FeatureCollection().select(), azl.FeatureCollection())
        self.assertEqual([f.id for f in sample().select(geometry_types='Point')], ['a', 'b'])

    def test_geometry_collection_filter_matches_top_level_only(self):
        geom = azl.Geometry('GeometryCollection', geometries=(azl.Geometry('Point', (0, 0)),))
        collection = azl.FeatureCollection((azl.Feature(geom),))
        self.assertEqual(len(collection.select(geometry_types='Point')), 0)
        self.assertEqual(len(collection.select(geometry_types='GeometryCollection')), 1)

    def test_invalid_filters_and_predicate_errors_are_explicit(self):
        for options, error in (({'where': []}, TypeError), ({'where': {1: 2}}, TypeError),
                               ({'predicate': 1}, TypeError), ({'geometry_types': ['Unknown']}, ValueError),
                               ({'geometry_types': 1}, TypeError)):
            with self.subTest(options=options), self.assertRaises(error):
                sample().select(**options)
        def fail(feature):
            raise RuntimeError('predicate error')
        with self.assertRaisesRegex(RuntimeError, 'predicate error'):
            sample().select(predicate=fail)


class CSVTests(unittest.TestCase):
    def test_bom_custom_columns_ids_and_converters(self):
        raw = '\ufeffkey;name;x;y;count\n01;"Station; A";-46.6;-23.5;12\n02;B;-43.1;-22.9;4\n'
        result = read_csv(raw.encode('utf-8'), longitude='x', latitude='y', id_column='key',
                          delimiter=';', converters={'count': int})
        self.assertIs(azl.read_csv, read_csv)
        self.assertEqual([f.id for f in result], ['01', '02'])
        self.assertEqual(result[0].geometry.coordinates, (-46.6, -23.5))
        self.assertEqual(result[0].properties['name'], 'Station; A')
        self.assertEqual(result[0].properties['count'], 12)
        self.assertEqual(result[0].properties['x'], -46.6)
        self.assertEqual(azl.read_geojson(result.to_geojson()), result)

    def test_files_and_caller_streams_preserve_ownership(self):
        raw = 'lon,lat,name\r\n1,2,A\r\n'
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'points.csv'
            path.write_text(raw, encoding='utf-8')
            expected = read_csv(path)
            self.assertEqual(read_csv(str(path)), expected)
            for stream in (io.StringIO(raw), io.BytesIO(raw.encode())):
                self.assertEqual(read_csv(stream), expected)
                self.assertFalse(stream.closed)

    def test_strings_do_not_infer_property_types_or_ids(self):
        result = read_csv('lon,lat,id,count\n1,2,001,12\n')
        self.assertEqual(result[0].properties['count'], '12')
        self.assertEqual(result[0].properties['id'], '001')
        self.assertIsNone(result[0].id)

    def test_explicit_numeric_id(self):
        result = read_csv('lon,lat,id\n1,2,01\n', id_column='id', converters={'id': int})
        self.assertEqual(result[0].id, 1)

    def test_header_only_and_empty_lines(self):
        self.assertEqual(len(read_csv('lon,lat\n')), 0)
        self.assertEqual(len(read_csv('lon,lat\n\n1,2\n\n')), 1)
        with self.assertRaisesRegex(ValueError, 'column'):
            read_csv(io.StringIO(''))

    def test_quoted_multiline_record_and_physical_error_line(self):
        result = read_csv('lon,lat,name\n1,2,"Line one\nLine two"\n')
        self.assertEqual(result[0].properties['name'], 'Line one\nLine two')
        with self.assertRaisesRegex(ValueError, 'line 5'):
            read_csv('lon,lat,name\n1,2,"Line one\nLine two"\n\n3,91,B\n')

    def test_bad_headers_missing_columns_and_field_counts(self):
        for raw in ('lon,lat,lon\n1,2,3\n', 'lon,lat,\n1,2,3\n', 'x,y\n1,2\n',
                    'lon,lat\n1\n', 'lon,lat\n1,2,3\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                read_csv(raw)
        with self.assertRaisesRegex(ValueError, 'required'):
            read_csv('lon,lat\n', id_column='id')
        with self.assertRaisesRegex(ValueError, 'required'):
            read_csv('lon,lat\n', converters={'unknown': int})

    def test_invalid_coordinates_fail_without_partial_result(self):
        for lon, lat in (('nan', '2'), ('inf', '2'), ('1', '-91'), ('1', 'nan'), ('a', '2'), ('', '2')):
            with self.subTest(lon=lon, lat=lat), self.assertRaisesRegex(ValueError, 'line 3'):
                read_csv(f'lon,lat\n1,2\n{lon},{lat}\n')
        self.assertEqual(read_csv('lon,lat\n181,90\n')[0].geometry.coordinates, (181, 90))

    def test_bad_quoting_is_not_silently_accepted(self):
        for raw in ('lon,lat,name\n1,2,"unclosed\n', 'lon,lat,name\n1,2,"name"x\n'):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, 'malformed'):
                read_csv(raw)

    def test_converters_must_produce_json_properties_and_valid_ids(self):
        for converter in (lambda value: {1}, lambda value: float('nan'), int):
            with self.subTest(converter=converter), self.assertRaisesRegex(ValueError, 'line 2'):
                read_csv('lon,lat,value\n1,2,a\n', converters={'value': converter})
        with self.assertRaisesRegex(ValueError, 'line 2'):
            read_csv('lon,lat,id\n1,2,a\n', id_column='id', converters={'id': lambda value: True})

    def test_invalid_options_and_sources(self):
        for options, error in (({'longitude': ''}, ValueError), ({'latitude': 'lon'}, ValueError),
                               ({'id_column': False}, ValueError), ({'delimiter': '::'}, ValueError),
                               ({'delimiter': '\n'}, ValueError), ({'converters': []}, TypeError),
                               ({'converters': {'name': 'float'}}, TypeError),
                               ({'converters': {'lon': float}}, ValueError)):
            with self.subTest(options=options), self.assertRaises(error):
                read_csv('lon,lat,name\n1,2,A\n', **options)
        with self.assertRaises(TypeError):
            read_csv({})


class UrbanArtistTests(unittest.TestCase):
    def setUp(self):
        self.fig, self.ax = azl.subplots()
        self.ax.set_extent((-10, 10, -10, 10))
        self.point = sample().select(geometry_types='Point')
        self.line = sample().select(geometry_types='LineString')
        ring = ((0, 0), (1, 0), (1, 1), (0, 0))
        self.polygon = azl.FeatureCollection((azl.Feature(azl.Geometry('Polygon', (ring,)), {'zone': 'mixed'}, 'p'),))

    def tearDown(self):
        azl.close('all')

    def test_default_components_are_optional_and_both_imports_work(self):
        self.assertIs(plt.subplots, azl.subplots)
        layer = self.ax.cities(self.point, fit=False)
        self.assertEqual(self.ax.layers, [layer])
        self.assertIsNone(self.ax.get_legend())
        self.assertEqual(self.ax._get_extent(), (-10, -10, 10, 10))

    def test_mixed_wrong_geometries_leave_view_layers_and_stale_unchanged(self):
        for method, wrong in ((self.ax.cities, self.line), (self.ax.streets, self.polygon),
                              (self.ax.neighborhoods, self.point), (self.ax.buildings, self.point)):
            self.fig.canvas.draw()
            before = (self.ax._get_extent(), tuple(self.ax.layers), self.fig.stale)
            with self.subTest(method=method.__name__), self.assertRaisesRegex(ValueError, 'geometries'):
                method(wrong)
            self.assertEqual((self.ax._get_extent(), tuple(self.ax.layers), self.fig.stale), before)

    def test_none_empty_null_and_unknown_styles(self):
        for method in (self.ax.cities, self.ax.streets, self.ax.neighborhoods, self.ax.buildings):
            with self.subTest(method=method.__name__), self.assertRaisesRegex(ValueError, 'not bundled'):
                method()
            empty = method(azl.FeatureCollection())
            self.assertEqual(len(empty.data), 0)
            self.assertEqual(self.ax._get_extent(), (-10, -10, 10, 10))
        null = self.ax.cities(azl.FeatureCollection((azl.Feature(None),)))
        self.assertIsNone(null.data.bounds)
        count = len(self.ax.layers)
        with self.assertRaises(TypeError):
            self.ax.cities(self.point, not_a_property=1)
        self.assertEqual(len(self.ax.layers), count)
        self.assertEqual(self.ax._get_extent(), (-10, -10, 10, 10))

    def test_multipart_geometries(self):
        groups = ((self.ax.cities, 'MultiPoint', ((0, 0), (1, 1))),
                  (self.ax.streets, 'MultiLineString', (((0, 0), (1, 1)),)),
                  (self.ax.neighborhoods, 'MultiPolygon', ((((0, 0), (1, 0), (1, 1), (0, 0)),),)),
                  (self.ax.buildings, 'MultiPolygon', ((((0, 0), (1, 0), (1, 1), (0, 0)),),)))
        for method, kind, coords in groups:
            with self.subTest(kind=kind):
                collection = azl.FeatureCollection((azl.Feature(azl.Geometry(kind, coords)),))
                layer = method(collection, fit=False)
                self.assertEqual(layer.data, collection)

    def test_attribute_filter_and_aliases_before_fit(self):
        layer = self.ax.cities(sample(), where={'name': 'A'}, ms=8, c='red', label='A')
        self.assertEqual([f.id for f in layer.data], ['a'])
        self.assertEqual(layer.style['markersize'], 8)
        self.assertEqual(layer.get_color(), 'red')
        before = self.ax._get_extent()
        empty = self.ax.cities(sample(), where={'unknown': 'value'})
        self.assertEqual(len(empty.data), 0)
        self.assertEqual(self.ax._get_extent(), before)

    def test_visibility_edit_remove_stale_and_callbacks(self):
        layer = self.ax.buildings(self.polygon, fit=False, label='Buildings')
        seen = []
        layer.add_callback(lambda item: seen.append(item.get_visible()))
        self.fig.canvas.draw()
        layer.set(visible=False, linewidth=1.5)
        self.assertTrue(self.fig.stale)
        self.assertEqual(seen, [False])
        self.assertEqual(layer.get_linewidth(), 1.5)
        layer.set_visible(True)
        layer.remove()
        self.assertNotIn(layer, self.ax.layers)

    def test_feature_styles_and_labels_reuse_renderer(self):
        layer = self.ax.buildings(self.polygon, fit=False,
                                 style=lambda feature: {'facecolor': '#ff0000'}, label='Blocks')
        self.ax.set_extent((-.5, 1.5, -.5, 1.5))
        self.ax.labels(layer, field='zone', halo='white')
        self.ax.legend()
        stream = io.StringIO()
        self.fig.savefig(stream, format='svg')
        root = ET.fromstring(stream.getvalue())
        self.assertTrue(any(node.get('fill') == '#ff0000' for node in root.iter()))
        self.assertIn('mixed', [node.text for node in root.iter('{http://www.w3.org/2000/svg}text')])

    def test_explicit_mercator_source_crs(self):
        projected = {'type': 'Point', 'coordinates': [111319.49079327357, 222684.20850554405]}
        layer = self.ax.cities(projected, crs='EPSG:3857', fit=False)
        self.assertAlmostEqual(layer.data[0].geometry.coordinates[0], 1, places=8)
        self.assertAlmostEqual(layer.data[0].geometry.coordinates[1], 2, places=8)
        with self.assertRaises(ValueError):
            self.ax.cities(projected, crs='EPSG:9999')

    def test_export_png_svg_without_cartographic_imports(self):
        self.ax.neighborhoods(self.polygon, fit=False)
        self.ax.streets(self.line, fit=False, linestyle='--')
        self.ax.buildings(self.polygon, fit=False, hatch='//')
        self.ax.cities(self.point, fit=False)
        svg = io.StringIO()
        self.fig.savefig(svg, format='svg')
        self.assertEqual(ET.fromstring(svg.getvalue()).tag, '{http://www.w3.org/2000/svg}svg')
        try:
            from PIL import Image
        except ImportError:
            return  # SVG/core contract does not require PNG dependencies.
        png = io.BytesIO()
        self.fig.savefig(png, format='png')
        png.seek(0)
        with Image.open(png) as image:
            self.assertEqual(image.size, (640, 480))
            self.assertGreater(len(image.convert('RGB').getcolors(image.width * image.height)), 10)


if __name__ == '__main__':
    unittest.main()
