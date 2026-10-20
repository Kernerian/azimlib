"""Static model contracts, independent analytic fixtures and explicit refusals."""
from dataclasses import FrozenInstanceError,replace
import json,math,unittest
from pathlib import Path
from unittest.mock import patch
import azimlib as azl
from azimlib._frames import Body as InternalBody,Coordinates,ReferenceFrame,GeodeticFrame


class Bodies050(unittest.TestCase):
    def test_one_body_implementation_and_legacy_constructor(self):
        self.assertIs(azl.Body,InternalBody)
        custom=azl.Body('sphere',azl.Ellipsoid(1000000,0))
        self.assertEqual(custom.shape,'sphere')
        self.assertEqual(custom.axes,(1000000,)*3)
        with self.assertRaises(FrozenInstanceError):custom.name='changed'

    def test_five_presets_and_provenance(self):
        expected={'earth':('ellipsoid',6378137),'moon':('sphere',1737400),
                  'mars':('ellipsoid',3396190),'venus':('sphere',6051800),'mercury':('ellipsoid',2440530)}
        for key,(shape,a) in expected.items():
            body=azl.BODIES.get(key)
            self.assertEqual((body.shape,body.axes[0]),(shape,a))
            self.assertTrue(body.provenance and body.frame and body.datum)
        self.assertIs(azl.EARTH.ellipsoid,azl.WGS84)
        self.assertEqual(azl.MARS.axes[2],3376200)
        self.assertEqual(azl.MERCURY.axes[2],2438260)

    def test_invalid_models_and_parameters(self):
        cases=({'name':''},{'name':'x','axes':(1,2,1)},{'name':'x','axes':(True,1,1)},
               {'name':'x','axes':(math.inf,1,1)},{'name':'x','axes':(0,0,0)},
               {'name':'x','axes':(1,1)},{'name':'x','axes':(1,1,1),'shape':'triaxial'},
               {'name':'x','axes':(1,1,1),'unit':azl.KILOMETRE},
               {'name':'x','axes':(1,1,1),'prime_meridian':181},
               {'name':'x','axes':(1,1,1),'metadata':(('x','a'),('x','b'))})
        for kwargs in cases:
            with self.subTest(kwargs=kwargs),self.assertRaises((ValueError,TypeError)):azl.Body(**kwargs)

    def test_registry_is_local_and_no_identifier_replacement(self):
        custom=azl.Body('Custom',axes=(10,10,10),identifier='custom')
        registry=azl.BODIES.with_body(custom)
        self.assertIs(registry.get('custom'),custom)
        with self.assertRaises(KeyError):azl.BODIES.get('custom')
        with self.assertRaises(ValueError):registry.with_body(custom)

    def test_explicit_irregular_mesh_and_limits(self):
        source=azl.BodySource('synthetic','1','Analytic triangle, not a closed surface')
        mesh=azl.SurfaceMesh([(1,0,0),(0,1,0),(0,0,1)],[(0,1,2)],source)
        body=azl.Body('Mesh',mesh=mesh)
        self.assertEqual(body.shape,'irregular');self.assertIsInstance(mesh.vertices,tuple)
        with self.assertRaises(azl.UnsupportedBodyOperation):body.ellipsoid
        with self.assertRaises(azl.UnsupportedBodyOperation):azl.PlanetaryContext(body).to_fixed(0,0)
        with self.assertRaises(ValueError):azl.SurfaceMesh(mesh.vertices,[(0,1,3)],source)
        with self.assertRaises(ValueError):azl.SurfaceMesh([(0,0,0),(1,0,0),(2,0,0)],[(0,1,2)],source)
        with self.assertRaises(ValueError):azl.SurfaceMesh([(1e308,0,0),(-1e308,0,0),(0,0,0)],[(0,1,2)],source)

    def test_capability_states_and_unknowns(self):
        self.assertEqual(azl.MARS.capability('planetocentric').status,'supported')
        self.assertEqual(azl.MARS.capability('angular_map').status,'experimental')
        self.assertEqual(azl.MARS.capability('irregular_geodesy').status,'research')
        self.assertEqual(azl.MARS.capability('temporal_orientation').status,'not_implemented')
        with self.assertRaises(azl.UnsupportedBodyOperation):azl.MARS.capability('angular_map').require()
        azl.MARS.capability('angular_map').require(experimental=True)
        with self.assertRaises(ValueError):azl.MARS.capability('made-up')
        with self.assertRaises(azl.UnsupportedBodyOperation):azl.MARS.capability('groups',backend='gpu').require()


class Coordinates050(unittest.TestCase):
    def test_cardinal_radial_and_normal_on_every_preset(self):
        for body in azl.BODIES.bodies:
            for kind in ('planetocentric','planetographic'):
                ctx=azl.PlanetaryContext.for_body(body,latitude_type=kind)
                for lon,lat,expected in ((0,0,(body.axes[0],0,0)),(90,0,(0,body.axes[1],0)),(0,90,(0,0,body.axes[2]))):
                    with self.subTest(body=body.name,kind=kind,lon=lon):
                        for a,b in zip(ctx.to_fixed(lon,lat).xyz,expected):self.assertAlmostEqual(a,b,delta=1e-7)

    def test_cspice_frozen_independent_fixtures(self):
        fixture=json.loads((Path(__file__).parent/'fixtures/planetary-050.json').read_text('utf8'))
        self.assertEqual(fixture['tolerances'],{'metres':1e-7,'degrees':1e-10})
        for row in fixture['cases']:
            ctx=azl.PlanetaryContext.for_body(azl.BODIES.get(row['body']),latitude_type='planetographic')
            with self.subTest(body=row['body'],position=row['input']):
                for a,b in zip(ctx.to_fixed(*row['input']).xyz,row['fixed']):self.assertAlmostEqual(a,b,delta=1e-7)
                result=ctx.from_fixed(Coordinates(tuple(row['fixed']),ReferenceFrame(ctx.frame,ctx.body)))
                for a,b,tol in zip(result,row['input'],(1e-10,1e-10,1e-7)):self.assertAlmostEqual(a,b,delta=tol)

    def test_triaxial_radial_exact_surface_and_no_normal_fallback(self):
        body=azl.Body('triaxial',axes=(5,4,3))
        ctx=azl.PlanetaryContext(body)
        coordinate=Coordinates((3,3.2,0),ReferenceFrame(body.frame,body))
        lon,lat,h=ctx.from_fixed(coordinate)
        self.assertAlmostEqual(h,0,delta=1e-12)
        actual=ctx.to_fixed(lon,lat,h)
        for a,b in zip(actual.xyz,coordinate.xyz):self.assertAlmostEqual(a,b,delta=1e-12)
        normal=azl.PlanetaryContext.for_body(body,latitude_type='planetographic')
        with self.assertRaises(azl.UnsupportedBodyOperation):normal.to_fixed(0,0)
        with self.assertRaises(azl.UnsupportedBodyOperation):GeodeticFrame(coordinate.frame).to_fixed(0,0)

    def test_west_positive_meridian_and_units(self):
        body=azl.Body('analytic',axes=(1000,)*3)
        ctx=azl.PlanetaryContext(body,longitude=azl.LongitudeConvention('west','positive'),prime_meridian=30,height_unit=azl.KILOMETRE)
        fixed=ctx.to_fixed(120,0,1)
        self.assertAlmostEqual(fixed.xyz[0],0,delta=1e-10);self.assertAlmostEqual(fixed.xyz[1],-2000,delta=1e-10)
        self.assertEqual(tuple(round(v,10) for v in ctx.from_fixed(fixed)),(120,0,1))
        rad=replace(ctx,angle_unit=azl.RADIAN)
        for a,b in zip(rad.to_fixed(math.radians(120),0,1).xyz,fixed.xyz):self.assertAlmostEqual(a,b,delta=1e-10)

    def test_unsupported_datum_frame_epoch_body_and_vertical(self):
        ctx=azl.PlanetaryContext(azl.MARS)
        for kwargs in ({'frame':'J2000'},{'datum':'other'},{'vertical':'areoid'}):
            with self.subTest(kwargs=kwargs),self.assertRaises((ValueError,azl.UnsupportedBodyOperation)):replace(ctx,**kwargs)
        for target in (replace(ctx,epoch='J2000'),azl.PlanetaryContext(azl.EARTH)):
            with self.assertRaises(azl.UnsupportedBodyOperation):ctx.convert(0,0,target=target)
        dated=replace(ctx,epoch='declared static snapshot')
        with self.assertRaises(ValueError):ctx.from_fixed(dated.to_fixed(0,0))

    def test_invalid_domain_and_no_network(self):
        ctx=azl.PlanetaryContext(azl.MARS)
        for args in ((181,0),(0,91),(0,math.nan),(0,0,-4000000)):
            with self.subTest(args=args),self.assertRaises(ValueError):ctx.to_fixed(*args)
        with self.assertRaises(ValueError):ctx.from_fixed(Coordinates((0,0,0),ReferenceFrame(ctx.frame,ctx.body)))
        with patch('urllib.request.urlopen',side_effect=AssertionError('Implicit network forbidden')):
            self.assertEqual(ctx.from_fixed(ctx.to_fixed(45,30))[0],45)


class PlotContext050(unittest.TestCase):
    def tearDown(self):azl.close('all')
    def test_standalone_axes_preserve_earth_default(self):
        ax=azl.MapAxes(None,(0,0,1,1))
        self.assertIs(ax.get_body(),azl.EARTH)
        ax.map('brazil');self.assertTrue(ax.layers)
    def test_earth_default_and_two_body_isolation(self):
        f=azl.figure();earth=f.add_subplot(121);mars=f.add_subplot(122,body=azl.MARS)
        self.assertIs(f.get_body(),azl.EARTH);self.assertIs(mars.get_body(),azl.MARS)
        line,=mars.plot([0,10],[0,10]);text=mars.text(0,0,'Mars')
        self.assertIs(line.get_body(),azl.MARS);self.assertIs(text.get_body(),azl.MARS)
        mars.set_title('Mars chart');self.assertIs(mars._title.get_body(),azl.MARS)
        self.assertIs(mars.inset().get_body(),azl.MARS)
        earth.map('brazil');earth.scale_bar();svg=f.to_svg();self.assertIn('Mars',svg)
        metadata=f.to_scene().maps
        self.assertTrue(any(m['body']['metric_surface'] for m in metadata))
        self.assertTrue(all(m['body']['metric_surface'] for m in metadata))
        angular=azl.figure(body=azl.MARS).add_subplot(111,projection='angular')
        self.assertFalse(angular.figure.to_scene().maps[0]['body']['metric_surface'])
        with self.assertRaises(ValueError):mars.sharex(earth)

    def test_figure_and_subplot_kw_and_import_facade(self):
        import azimlib.pyplot as plt
        f,ax=plt.subplots(body=azl.MARS);self.assertIs(ax.get_body(),azl.MARS)
        with self.assertRaises(ValueError):plt.figure(f,body=azl.EARTH)
        other,ax2=plt.subplots(subplot_kw={'body':azl.MOON});self.assertIs(ax2.get_body(),azl.MOON)
        self.assertIs(other.get_body(),azl.EARTH)

    def test_noncanonical_earth_context_is_not_silently_plotted(self):
        for ctx in (azl.PlanetaryContext(azl.EARTH),
                    replace(azl.PlanetaryContext.for_body(azl.EARTH,latitude_type='planetographic'),
                            longitude=azl.LongitudeConvention('west','positive'))):
            fig=azl.figure(context=ctx)
            with self.assertRaises(azl.UnsupportedBodyOperation):fig.add_subplot(111)
            self.assertEqual(fig.axes,[])

    def test_geographic_transforms_cannot_mix_bodies_in_same_figure(self):
        from azimlib.transforms import Affine2D,blended_transform_factory
        fig=azl.figure();earth=fig.add_subplot(121);mars=fig.add_subplot(122,body=azl.MARS)
        line,=mars.plot([0,1],[0,1])
        for transform in (earth.transData,earth.transData.inverted(),Affine2D()+earth.transData,
                          blended_transform_factory(earth.transData,mars.transAxes)):
            for setter in (line.set_transform,lambda tr:line.set(transform=tr)):
                with self.assertRaises(ValueError):setter(transform)
            before=len(mars.layers)
            with self.assertRaises(ValueError):mars.text(0,0,'Foreign context',transform=transform)
            self.assertEqual(len(mars.layers),before)
        line.set_transform(mars.transData)
        line.set_transform(earth.transAxes)  # Fractions are layout, not geography.

    def test_explicit_earth_terrain_in_mars_figure_keeps_earth_context(self):
        fig=azl.figure(body=azl.MARS)
        ax=fig.add_subplot(111,projection='3d',body=azl.EARTH)
        self.assertIs(ax.get_body(),azl.EARTH)

    def test_non_earth_refusals_before_attachment(self):
        f,ax=azl.subplots(body=azl.MARS)
        for action in (lambda:ax.map('brazil'),lambda:ax.overview(),
                       lambda:ax.set_projection('equalearth'),lambda:ax.sun('2024-01-01')):
            before=len(ax.layers)
            with self.subTest(action=action),self.assertRaises(azl.UnsupportedBodyOperation):action()
            self.assertEqual(len(ax.layers),before)
        with self.assertRaises(azl.UnsupportedBodyOperation):f.savefig('unused.png',renderer='gpu')
        ax.route([(0,0),(1,1)],geodesic=False)
        ax.route([(0,0),(1,1)]);ax.set_projection('mercator')
        ax.imshow([[1]],extent=(0,1,0,1));ax.scale_bar()
        terrain=f.add_subplot(111,projection='3d');self.assertIs(terrain.get_body(),azl.MARS)

    def test_explicit_planetary_geojson_and_wrong_body_are_not_stripped(self):
        source={'type':'LineString','coordinates':[[0,0],[10,10]]}
        earth=azl.read_geojson(source);ctx=azl.PlanetaryContext(azl.MARS)
        data=azl.read_geojson(source,context=ctx)
        f,ax=azl.subplots(body=azl.MARS)
        with self.assertRaises(ValueError):ax.geojson(earth)
        layer=ax.geojson(data);self.assertIs(layer.get_body(),azl.MARS)
        with self.assertRaises(ValueError):azl.read_geojson(data)
        _,ea=azl.subplots()
        with self.assertRaises(ValueError):ea.geojson(data)
        layer.remove()
        with self.assertRaises(ValueError):ea.add_collection(layer)
        self.assertIsNone(layer.axes)


if __name__=='__main__':unittest.main()
