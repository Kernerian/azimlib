"""Frozen independent projection/geodesic references and adversarial domains."""
import json,math,unittest
from pathlib import Path
from dataclasses import replace
import azimlib as a

FIXTURE=json.loads((Path(__file__).parent/'fixtures/surfaces-050.json').read_text('utf8'))
def surface(body):return a.BodySurface(a.PlanetaryContext.for_body(a.BODIES.get(body),latitude_type='planetographic'))
def angular_error(x,y):return abs((x-y+180)%360-180)


class MetricProjections(unittest.TestCase):
    def test_cspice_normals_and_explicit_geometric_incidence(self):
        for row in FIXTURE['normals']:
            s=surface(row['body']);light=a.GeometricLight(s.context,direction=(1,2,3))
            self.assertLess(math.dist(light.normal(*row['input']),row['normal']),1e-10)
            expected=sum(x*y for x,y in zip(row['normal'],light.direction))
            self.assertAlmostEqual(light.incidence(*row['input']),expected,delta=1e-10)

    def test_cylindrical_crossing_extent_and_mercator_centric_cap(self):
        _,ax=a.subplots(body=a.MARS);ax.set_extent((170,-170,-10,10));ax.plot([175,-175],[0,2])
        self.assertIn('<svg',ax.figure.to_svg())
        p=a.BodySurface(a.MARS).projection('mercator')
        for lat in p.latitude_limits:self.assertIsNotNone(p.forward(0,lat))
        p=a.BodySurface(a.MARS).projection('equirectangular')
        self.assertGreater(p.forward(180,0)[0]-p.forward(-180,0)[0],1e7)

    def test_noncanonical_projection_refuses_instead_of_implicit_conversion(self):
        ctx=replace(a.PlanetaryContext.for_body(a.MARS),longitude=a.LongitudeConvention('west','positive'))
        with self.assertRaises(a.UnsupportedBodyOperation):a.BodySurface(ctx).projection()
        self.assertGreater(a.BodySurface(ctx).distance((0,0),(1,1)),0)

    def test_frozen_independent_xy_and_inverses(self):
        t=FIXTURE['tolerances']
        for row in FIXTURE['projections']:
            with self.subTest(body=row['body'],method=row['method'],position=row['input']):
                s=surface(row['body']);p=s.projection(row['method'],**row['parameters']);q=p.forward(*row['input'])
                if row['xy'] is None or not row['within_declared_domain']:self.assertIsNone(q);continue
                self.assertIsNotNone(q)
                tol=t['tm_xy_m'] if row['method']=='transverse_mercator' else t['sphere_xy_m'] if s.body.shape=='sphere' else t['oblate_xy_m']
                self.assertLessEqual(math.dist(q,row['xy']),tol)
                inverse=p.inverse(*q);self.assertIsNotNone(inverse)
                self.assertLessEqual(angular_error(inverse[0],row['input'][0]),t['inverse_deg'])
                self.assertAlmostEqual(inverse[1],row['input'][1],delta=t['inverse_deg'])

    def test_centric_and_graphic_are_physically_equivalent(self):
        for body in a.BODIES.bodies:
            cent=a.PlanetaryContext.for_body(body);normal=a.PlanetaryContext.for_body(body,latitude_type='planetographic')
            target=cent.convert(40,35,0,target=normal)
            for method in ('equirectangular','mercator','orthographic'):
                p=a.BodySurface(cent).projection(method);q=a.BodySurface(normal).projection(method)
                self.assertLess(math.dist(p.forward(40,35),q.forward(*target[:2])),1e-7)

    def test_models_do_not_receive_spherical_fallback(self):
        tri=a.Body('triaxial',axes=(5000,4000,3000))
        with self.assertRaises(a.UnsupportedBodyOperation):a.BodySurface(tri)
        for method in ('equalearth','lambert_azimuthal_equal_area','azimuthal_equidistant'):
            with self.assertRaises(a.UnsupportedBodyOperation):surface('mars').projection(method)
        with self.assertRaises(a.UnsupportedBodyOperation):surface('mars').projection('stereographic',central_latitude=30)

    def test_projection_reference_surface_cannot_be_replaced(self):
        with self.assertRaises(ValueError):a.SurfaceProjection(context=a.PlanetaryContext(a.MARS),radius=a.MOON.axes[0])
        with self.assertRaises(TypeError):surface('mars').projection(radius=1)

    def test_horizon_and_inverse_outside_ellipse(self):
        for key in ('moon','mars','mercury'):
            p=surface(key).projection('orthographic',central_latitude=30)
            self.assertIsNone(p.forward(180,-30));self.assertIsNone(p.inverse(p.radius*1.001,0))
            self.assertLess(abs(p.visibility(90,0)),1e-12)
            xy=p.forward(0,30);self.assertLess(math.hypot(*xy),1e-8)

    def test_clipped_polygon_and_line_stay_on_ellipsoid_limb(self):
        p=surface('mars').projection('orthographic',central_latitude=35)
        polygons=a.clip_orthographic_polygon((((-20,-20),(120,-20),(120,60),(-20,60),(-20,-20)),),p)
        self.assertTrue(polygons)
        aux,b,offset=p.auxiliary
        for polygon in polygons:
            for ring in polygon:
                self.assertEqual(ring[0],ring[-1])
                for x,y in ring:self.assertLessEqual((x/p.radius)**2+((y+offset)/b)**2,1+1e-9)
        parts=a.clip_orthographic_line([(0,0),(150,0)],p)
        self.assertTrue(parts);x,y=parts[-1][-1]
        self.assertAlmostEqual((x/p.radius)**2+((y+offset)/b)**2,1,delta=1e-10)

    def test_seams_poles_and_singularities(self):
        for key in ('moon','mars','venus','mercury'):
            p=surface(key).projection('equirectangular')
            self.assertLess(p.forward(-180,0)[0],0)
            self.assertAlmostEqual(p.forward(-180,0)[0],-p.forward(180,0)[0],delta=1e-8)
            self.assertAlmostEqual(p.inverse(*p.forward(180,0))[0],-180,delta=1e-8)
            for lat in (-90,90):self.assertAlmostEqual(p.inverse(*p.forward(10,lat))[1],lat,delta=1e-9)
            merc=surface(key).projection('mercator');self.assertIsNone(merc.forward(0,90))
            polar=surface(key).projection('stereographic',central_latitude=-90)
            self.assertIsNone(polar.forward(0,90))
            with self.assertRaises(ValueError):p.forward(0,91)

    def test_tm_is_explicitly_regional(self):
        p=surface('mars').projection('transverse_mercator',central_longitude=20)
        self.assertIsNone(p.forward(23.1,30));self.assertIsNone(p.forward(20,85))


class PhysicalMeasures(unittest.TestCase):
    def test_frozen_geodesic_distances_and_azimuths(self):
        t=FIXTURE['tolerances']
        for row in FIXTURE['geodesics']:
            with self.subTest(body=row['body'],start=row['start'],end=row['end']):
                r=surface(row['body']).inverse(row['start'],row['end'])
                self.assertAlmostEqual(r.distance,row['distance_m'],delta=t['difficult_distance_m'] if row['difficult'] else t['distance_m'])
                if not row['ambiguous']:
                    self.assertLess(angular_error(r.azimuth1,row['azimuth1']),t['azimuth_deg'])
                    self.assertLess(angular_error(r.azimuth2,row['azimuth2']),t['azimuth_deg'])

    def test_frozen_geodesic_polygon_areas(self):
        for row in FIXTURE['areas']:
            with self.subTest(body=row['body'],vertices=row['vertices']):
                self.assertAlmostEqual(surface(row['body']).polygon_area(row['vertices']),row['area_m2'],delta=max(10,1e-7*row['area_m2']))

    def test_surface_chord_and_projected_distance_are_distinct(self):
        s=surface('moon');r=s.a
        self.assertAlmostEqual(s.distance((0,0),(90,0)),math.pi*r/2,delta=1e-7)
        self.assertAlmostEqual(s.chord((0,0),(90,0)),math.sqrt(2)*r,delta=1e-7)
        p=s.projection('mercator');start,end=(0,60),(30,60)
        self.assertGreater(math.dist(p.forward(*start),p.forward(*end)),s.distance(start,end)*1.9)

    def test_route_length_units_and_direct(self):
        for key in ('moon','mars','venus','mercury'):
            s=surface(key);start,end=(170,-20),(-170,30);line=s.route(start,end,samples=17)
            self.assertEqual(len(line),17);self.assertEqual(line[0],start)
            self.assertAlmostEqual(s.length(line),s.distance(start,end),delta=.02)
            self.assertAlmostEqual(s.distance(start,end,unit=a.KILOMETRE)*1000,s.distance(start,end),delta=1e-6)
            target=s.direct(start,s.inverse(start,end).azimuth1,s.distance(start,end))
            self.assertLess(angular_error(target[0],end[0]),1e-8);self.assertAlmostEqual(target[1],end[1],delta=1e-8)

    def test_rectangle_and_geodesic_area_are_not_conflated(self):
        s=surface('moon');expected=2*math.pi*s.a*s.a
        self.assertAlmostEqual(s.rectangle_area((-180,180,0,90)),expected,delta=.02)
        self.assertNotEqual(s.rectangle_area((0,30,0,60)),s.polygon_area([(0,0),(30,0),(30,60),(0,60)]))

    def test_invalid_or_unimplemented_measures_fail(self):
        s=surface('mars')
        for action in (lambda:s.route((0,0),(1,1),samples=1),lambda:s.distance((0,0),(1,1),unit=a.DEGREE),lambda:s.polygon_area([(0,80),(120,80),(-120,80)])):
            with self.assertRaises((ValueError,a.UnsupportedBodyOperation)):action()
        with self.assertRaises(ValueError):surface('moon').polygon_area([(0,0),(10,10),(0,10),(10,0)])


if __name__=='__main__':unittest.main()
