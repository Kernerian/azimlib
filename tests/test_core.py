"""Independent numerical, interchange and geometry regression tests."""
import io
import json
import math
from pathlib import Path
import tempfile
import unittest

from azimlib.geometry import (
    EARTH_RADIUS, Feature, FeatureCollection, Geometry, clip_polygon_antimeridian, clip_orthographic_polygon,
    destination, great_circle, haversine, split_antimeridian, wrap_longitude,
)
from azimlib.io import read_geojson, write_geojson
from azimlib.projections import (
    AlbersEqualArea, EqualEarth, Equirectangular, LambertConformalConic,
    Mercator, Orthographic, Projection, get_projection, register_projection,
)
from azimlib.crs import CRS, Transformer, transform, transform_coordinates, transform_geojson


class GeometryTests(unittest.TestCase):
    def test_geometry_freezes_input_and_properties_deeply(self):
        coordinates = [[0, 0], [3, 4]]
        geometry = Geometry("LineString", coordinates)
        coordinates[0][0] = 99
        self.assertEqual(geometry.coordinates[0], (0, 0))
        properties = {"values": [1, {"nested": 2}]}
        feature = Feature(geometry, properties)
        properties["values"][1]["nested"] = 10
        self.assertEqual(feature.properties["values"][1]["nested"], 2)
        with self.assertRaises(TypeError):
            feature.properties["value"] = 1
        with self.assertRaises(TypeError):
            feature.properties["values"][1]["nested"] = 3

    def test_all_geometry_types_and_bounds(self):
        ring = ((0, 0), (4, 0), (4, 4), (0, 0))
        geometries = (
            Geometry("Point", (1, 2, 7)), Geometry("MultiPoint", ((1, 2), (3, 4))),
            Geometry("LineString", ((1, 2), (3, 4))), Geometry("MultiLineString", (((1, 2), (3, 4)),)),
            Geometry("Polygon", (ring,)), Geometry("MultiPolygon", ((ring,),)),
        )
        group = Geometry("GeometryCollection", geometries=geometries)
        collection = FeatureCollection((Feature(None), Feature(group)))
        self.assertEqual(collection.bounds, (0, 0, 4, 4))
        self.assertEqual(read_geojson(collection.to_geojson()), collection)

    def test_empty_geometries(self):
        for kind in ("Point", "LineString", "MultiPoint", "Polygon", "MultiPolygon", "GeometryCollection"):
            with self.subTest(kind=kind):
                self.assertIsNone(Geometry(kind).bounds)
        self.assertIsNone(FeatureCollection().bounds)

    def test_invalid_positions_and_structures(self):
        for coordinates in ((True, 0), (0, float("nan")), (float("inf"), 0), (0, 91), (0,), (0, 0, 0, 0), "00"):
            with self.subTest(coordinates=coordinates), self.assertRaises(ValueError):
                Geometry("Point", coordinates)
        with self.assertRaises(ValueError):
            Geometry("LineString", ((0, 0),))
        with self.assertRaises(ValueError):
            Geometry("Polygon", (((0, 0), (1, 0), (1, 1), (0, 1)),))
        with self.assertRaises(ValueError):
            Geometry("Polygon", ((),))
        with self.assertRaises(ValueError):
            Geometry("GeometryCollection", geometries=(None,))

    def test_holes_and_null_geometry_survive_roundtrip(self):
        outer = ((0, 0), (10, 0), (10, 10), (0, 10), (0, 0))
        hole = ((2, 2), (2, 3), (3, 3), (3, 2), (2, 2))
        data = FeatureCollection((Feature(Geometry("Polygon", (outer, hole)), {"name": "São Paulo"}, "a"), Feature(None)))
        output = io.StringIO()
        text = write_geojson(data, output)
        self.assertEqual(text, output.getvalue())
        self.assertEqual(read_geojson(text), data)
        self.assertIn("São Paulo", text)

    def test_geojson_inputs_and_native_passthrough(self):
        geometry = Geometry("Point", (12, 34))
        class Compatible:
            __geo_interface__ = geometry.to_geojson()
        for source in (geometry, geometry.to_geojson(), Compatible(), json.dumps(geometry.to_geojson()), io.StringIO(json.dumps(geometry.to_geojson()))):
            self.assertEqual(read_geojson(source)[0].geometry, geometry)
        collection = read_geojson(geometry)
        self.assertIs(read_geojson(collection), collection)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"point.geojson"
            write_geojson(geometry, path)
            self.assertEqual(read_geojson(path)[0].geometry, geometry)

    def test_geojson_rejects_bad_structure_and_legacy_crs(self):
        cases = [[], {"type": "FeatureCollection", "features": [None]},
                 {"type": "Feature", "geometry": None},
                 {"type": "Point", "coordinates": [0, 0], "crs": {"name": "EPSG:3857"}},
                 {"type": "Point", "coordinates": [0, 0], "properties": {}},
                 {"type": "GeometryCollection", "geometries": [None]}]
        # Foreign members on otherwise valid geometries are permitted by RFC 7946.
        read_geojson(cases.pop(4))
        for source in cases:
            with self.subTest(source=source), self.assertRaises(ValueError):
                read_geojson(source)

    def test_line_antimeridian_intersection(self):
        parts = split_antimeridian(((170, 10), (-170, 20)))
        self.assertEqual(parts, (((170, 10), (180, 15)), ((-180, 15), (-170, 20))))
        reverse = split_antimeridian(((-170, 20), (170, 10)))
        self.assertEqual(reverse, (((-170, 20), (-180, 15)), ((180, 15), (170, 10))))
        self.assertEqual(len(split_antimeridian(((170, 10), (-170, 20)), 180)), 1)

    def test_polygon_seam_clipping_preserves_area_and_holes(self):
        outer = ((170, -10), (-170, -10), (-170, 10), (170, 10), (170, -10))
        hole = ((175, -2), (-175, -2), (-175, 2), (175, 2), (175, -2))
        polygons = clip_polygon_antimeridian((outer, hole))
        self.assertEqual(len(polygons), 2)
        self.assertEqual([len(p) for p in polygons], [2, 2])
        def area(ring):
            return abs(sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(ring, ring[1:])))/2
        self.assertAlmostEqual(sum(area(p[0])-area(p[1]) for p in polygons), 360)
        self.assertTrue(all(-180 <= point[0] <= 180 for p in polygons for r in p for point in r))

    def test_explicit_polar_cap_clipping(self):
        ring = ((180, -80), (180, -90), (-180, -90), (-180, -80), (-90, -75), (0, -70), (90, -75), (180, -80))
        for center in (0, -60, 90, 180):
            result = clip_polygon_antimeridian((ring,), center)
            self.assertGreaterEqual(len(result), 1)
            for poly in result:
                for closed in poly:
                    self.assertEqual(closed[0], closed[-1])
                    self.assertTrue(all(center-180 <= p[0] <= center+180 for p in closed))

    def test_haversine_and_destination_analytic_reference(self):
        quarter = math.pi*EARTH_RADIUS/2
        self.assertAlmostEqual(haversine((0, 0), (90, 0)), quarter)
        self.assertAlmostEqual(haversine((0, 0), (180, 0)), math.pi*EARTH_RADIUS)
        self.assertEqual(haversine((1, 2), (1, 2)), 0)
        lon, lat = destination(0, 0, 90, quarter)
        self.assertAlmostEqual(lon, 90)
        self.assertAlmostEqual(lat, 0)
        lon, lat = destination(0, 0, 0, quarter/2)
        self.assertAlmostEqual(lon, 0)
        self.assertAlmostEqual(lat, 45)

    def test_orthographic_clipping_follows_horizon_instead_of_chord(self):
        ring = ((70, -20), (110, -20), (110, 20), (70, 20), (70, -20))
        projection = Orthographic(radius=1)
        for original in (ring, tuple(reversed(ring))):
            polygons = clip_orthographic_polygon((original,), projection)
            self.assertEqual(len(polygons), 1)
            self.assertEqual(len(polygons[0]), 1)
            clipped = polygons[0][0]
            self.assertAlmostEqual(max(x for x, y in clipped), 1)
            self.assertTrue(all(math.hypot(x, y) <= 1+1e-12 for x, y in clipped))
            self.assertEqual(clipped[0], clipped[-1])

    def test_orthographic_clipping_retains_regional_holes(self):
        exterior = ((-20, -20), (20, -20), (20, 20), (-20, 20), (-20, -20))
        hole = ((-5, -5), (-5, 5), (5, 5), (5, -5), (-5, -5))
        polygons = clip_orthographic_polygon((exterior, hole), Orthographic(radius=1))
        self.assertEqual(len(polygons), 1)
        self.assertEqual(len(polygons[0]), 2)
        hidden = tuple((lon+180, lat) for lon, lat in exterior)
        self.assertEqual(clip_orthographic_polygon((hidden,), Orthographic(radius=1)), ())

    def test_bundled_world_orthographic_clipping_including_antarctica(self):
        from azimlib.datasets import country
        features = read_geojson(country("world"))
        self.assertGreater(len(features), 150)
        for lon, lat in ((0, 0), (-60, -15), (90, 30), (180, -90)):
            projection = Orthographic(central_longitude=lon, central_latitude=lat, radius=1)
            count = 0
            for feature in features:
                geometry = feature.geometry
                polygons = (geometry.coordinates,) if geometry.type == "Polygon" else geometry.coordinates
                for polygon in polygons:
                    with self.subTest(country=feature.properties.get("name"), view=(lon, lat)):
                        clipped = clip_orthographic_polygon(polygon, projection)
                        for piece in clipped:
                            for ring in piece:
                                self.assertEqual(ring[0], ring[-1])
                                self.assertTrue(all(math.hypot(x, y) <= 1+1e-10 for x, y in ring))
                        count += len(clipped)
            self.assertGreater(count, 50)

    def test_great_circle_equal_segments_and_endpoints(self):
        route = great_circle((-46.63, -23.55), (139.69, 35.68), steps=20)
        self.assertEqual(len(route), 21)
        self.assertEqual(route[0], (-46.63, -23.55))
        self.assertEqual(route[-1], (139.69, 35.68))
        lengths = [haversine(a, b) for a, b in zip(route, route[1:])]
        self.assertLess(max(lengths)-min(lengths), 1e-7)
        self.assertEqual(great_circle((0, 0), (0, 0), 2), ((0, 0),)*3)
        with self.assertRaises(ValueError):
            great_circle((0, 0), (180, 0))
        with self.assertRaises(ValueError):
            great_circle((0, 0), (1, 1), 0)


class ProjectionTests(unittest.TestCase):
    def assertLonLatAlmostEqual(self, a, b, places=7):
        self.assertIsNotNone(a)
        self.assertAlmostEqual(wrap_longitude(a[0]-b[0]), 0, places=places)
        self.assertAlmostEqual(a[1], b[1], places=places)

    def test_equirectangular_analytic_reference(self):
        projection = Equirectangular(radius=1)
        self.assertEqual(projection.forward(0, 0), (0, 0))
        x, y = projection.forward(180, 90)
        self.assertAlmostEqual(x, math.pi)
        self.assertAlmostEqual(y, math.pi/2)
        x, y = Equirectangular(radius=1, standard_parallel=60).forward(90, 0)
        self.assertAlmostEqual(x, math.pi/4)

    def test_mercator_analytic_reference_and_domain(self):
        projection = Mercator(radius=1)
        x, y = projection.forward(90, 45)
        self.assertAlmostEqual(x, math.pi/2)
        self.assertAlmostEqual(y, math.log(1+math.sqrt(2)))
        self.assertIsNone(projection.forward(0, 90))
        self.assertIsNone(projection.inverse(0, 10000))
        self.assertIsNone(projection.inverse(10, 0))

    def test_equalearth_published_unit_sphere_example(self):
        # PROJ's Equal Earth documentation: 122°E,47°N, R=1 -> 1.55,0.89.
        x, y = EqualEarth(radius=1).forward(122, 47)
        self.assertAlmostEqual(x, 1.55, delta=0.005)
        self.assertAlmostEqual(y, 0.89, delta=0.005)
        self.assertIsNone(EqualEarth(radius=1).inverse(4, 0))
        self.assertIsNone(EqualEarth(radius=1).inverse(0, 2))

    def test_orthographic_horizon_and_hidden_hemisphere(self):
        projection = Orthographic(radius=1)
        self.assertEqual(projection.forward(0, 0), (0, 0))
        x, y = projection.forward(90, 0)
        self.assertAlmostEqual(x, 1)
        self.assertAlmostEqual(y, 0)
        self.assertIsNone(projection.forward(91, 0))
        self.assertIsNone(projection.inverse(1.01, 0))
        self.assertLonLatAlmostEqual(projection.inverse(0, 1), (0, 90))

    def test_all_projections_roundtrip_in_both_hemispheres(self):
        for name in ("equirectangular", "mercator", "equalearth", "orthographic", "lambert", "albers"):
            for sign in (-1, 1):
                kwargs = {"central_longitude": -55, "central_latitude": sign*25}
                if name in ("lambert", "albers"):
                    kwargs["standard_parallels"] = (sign*20, sign*50)
                projection = get_projection(name, **kwargs)
                for coordinates in ((-55, sign*25), (-70, sign*45), (-20, sign*12), (-90, sign*60)):
                    with self.subTest(name=name, coordinates=coordinates):
                        xy = projection.forward(*coordinates)
                        self.assertIsNotNone(xy)
                        self.assertLonLatAlmostEqual(projection.inverse(*xy), coordinates)

    def test_all_equal_area_projections_local_jacobian(self):
        # A unit sphere has differential area cos(latitude) dlon dlat.
        for projection in (EqualEarth(radius=1), AlbersEqualArea(radius=1)):
            for latitude in (-50, -10, 30, 70):
                lon, lat, delta = 12, latitude, 1e-4
                x1, y1 = projection.forward(lon-delta, lat)
                x2, y2 = projection.forward(lon+delta, lat)
                x3, y3 = projection.forward(lon, lat-delta)
                x4, y4 = projection.forward(lon, lat+delta)
                h = math.radians(2*delta)
                determinant = ((x2-x1)*(y4-y3)-(x4-x3)*(y2-y1))/(h*h)
                self.assertAlmostEqual(determinant, math.cos(math.radians(lat)), places=7)

    def test_lambert_local_conformality(self):
        projection = LambertConformalConic(radius=1)
        lon, lat, delta = 15, 43, 1e-4
        left, right = projection.forward(lon-delta, lat), projection.forward(lon+delta, lat)
        down, up = projection.forward(lon, lat-delta), projection.forward(lon, lat+delta)
        dx = tuple(b-a for a, b in zip(left, right))
        dy = tuple(b-a for a, b in zip(down, up))
        self.assertAlmostEqual(sum(a*b for a, b in zip(dx, dy)), 0, places=12)
        self.assertAlmostEqual(math.hypot(*dx)/math.cos(math.radians(lat)), math.hypot(*dy), places=12)

    def test_projection_validation_and_registry(self):
        for constructor, kwargs in ((Mercator, {"max_latitude": 90}), (Orthographic, {"radius": 0}),
                                     (EqualEarth, {"central_latitude": 100}), (AlbersEqualArea, {"standard_parallels": (-30, 30)})):
            with self.assertRaises(ValueError):
                constructor(**kwargs)
        with self.assertRaises(ValueError):
            get_projection("unknown")
        class TestProjection(Equirectangular):
            pass
        register_projection("test_registered", TestProjection, replace=True)
        self.assertIsInstance(get_projection("test_registered"), TestProjection)
        with self.assertRaises(ValueError):
            register_projection("test_registered", TestProjection)
        original = Mercator()
        self.assertIs(get_projection(original), original)
        with self.assertRaises(TypeError):
            get_projection(original, radius=1)


class CRSTests(unittest.TestCase):
    def test_webmercator_known_reference(self):
        x, y = transform(180, 0)
        self.assertAlmostEqual(x, 20037508.342789244, places=7)
        self.assertAlmostEqual(y, 0, places=7)
        x, y = transform(10, 45)
        self.assertAlmostEqual(x, 1113194.9079327357, places=7)
        self.assertAlmostEqual(y, 5621521.486192066, places=7)
        self.assertEqual(CRS(4326), CRS("OGC:CRS84"))

    def test_coordinate_transform_roundtrip_and_elevation(self):
        transformer = Transformer.from_crs(4326, 3857)
        point = transformer.transform(-46.63, -23.55)
        back = transform(*point, 3857, 4326)
        self.assertAlmostEqual(back[0], -46.63)
        self.assertAlmostEqual(back[1], -23.55)
        point3 = transform_coordinates(((-46.63, -23.55, 760),))[0]
        self.assertEqual(point3[2], 760)

    def test_projected_geojson_transform_before_validation(self):
        projected = {"type": "Feature", "properties": {"value": 2}, "bbox": [0, 0, 1, 1],
                     "geometry": {"type": "Point", "coordinates": [1113194.9079327357, 5621521.486192066]}}
        geographic = transform_geojson(projected, 3857, 4326)
        self.assertNotIn("bbox", geographic)
        self.assertEqual(projected["bbox"], [0, 0, 1, 1])
        point = read_geojson(geographic)[0].geometry.coordinates
        self.assertAlmostEqual(point[0], 10)
        self.assertAlmostEqual(point[1], 45)

    def test_crs_failures_are_explicit(self):
        for coordinate in ((0, 90), (181, 0), (0, float("nan"))):
            with self.assertRaises(ValueError):
                transform(*coordinate)
        with self.assertRaises(ValueError):
            transform(0, 50_000_000, 3857, 4326)
        with self.assertRaises(ValueError):
            CRS("EPSG:32623")


if __name__ == "__main__":
    unittest.main()
