"""Body raster isolation, inverse sampling, masks, actual terrain and light."""
from dataclasses import replace
import hashlib,io,math,tempfile,unittest
from pathlib import Path
import azimlib as a

SOURCE=a.BodySource('synthetic:analytic','1','Deterministic pixels, not measured planetary data')
def raster(body=a.MARS,values=((1,2),(3,4)),affine=(1,0,0,0,-1,2),**kwargs):
    return a.PlanetaryRaster(values,affine,a.PlanetaryContext.for_body(body),SOURCE,'BSD-3-Clause',**kwargs)


class BodyRasterTests(unittest.TestCase):
    def test_immutable_units_resolution_and_pixel_corners(self):
        values=[[1,2],[3,4]];r=raster(values=values);values[0][0]=99
        self.assertEqual(r.values[0][0],1);self.assertEqual(r.resolution,(1,1));self.assertEqual(r.bounds,(0,2,0,2))
        self.assertEqual(r.coordinate(0,0,center=True),(.5,1.5));self.assertIs(r.unit,a.METRE)
        self.assertEqual(r.context.datum,a.MARS.datum)

    def test_invalid_grid_masks_budget_and_context(self):
        cases=({'values':[]},{'values':[[1],[2,3]]},{'affine':(0,0,0,0,0,0)},
               {'mask':[[True]]},{'license':''},{'budget':a.RasterBudget(1,1024)})
        for kw in cases:
            with self.subTest(kw=kw),self.assertRaises((ValueError,TypeError)):
                params=dict(values=[[1,2],[3,4]],affine=(1,0,0,0,-1,2),context=a.PlanetaryContext(a.MARS),source=SOURCE,license='BSD-3-Clause');params.update(kw);a.PlanetaryRaster(**params)
        with self.assertRaises(ValueError):raster(projection=a.BodySurface(a.MOON).projection())
        with self.assertRaises(ValueError):raster().resample((10000,10000),extent=(0,2,0,2))

    def test_nodata_mask_interpolation_and_missing_policy(self):
        r=raster(values=[[1,-999],[3,4]],nodata=-999)
        self.assertTrue(r.mask[0][1]);self.assertEqual(r.sample(.5,1.5),1)
        self.assertIsNone(r.sample(1,1,method='bilinear'))
        self.assertAlmostEqual(r.sample(1,1,method='bilinear',missing='renormalize'),8/3)
        self.assertIsNone(r.sample(-1,0));self.assertIsNone(r.sample(2,1))
        m=raster(values=[[math.nan,math.inf],[1,2]],mask=[[False,False],[True,False]])
        self.assertEqual(m.values,((None,None),(None,2)))

    def test_crop_retains_exact_pixels_and_reference(self):
        r=raster(values=[[1,2,3],[4,5,6],[7,8,9]],affine=(1,0,0,0,-1,3));c=r.crop((1,3,0,2))
        self.assertEqual(c.values,((5,6),(8,9)));self.assertEqual(c.bounds,(1,3,0,2));self.assertIs(c.source,r.source)
        self.assertEqual(r.shape,(3,3))
        with self.assertRaises(ValueError):r.crop((10,11,10,11))

    def test_inverse_reprojection_and_body_mismatch(self):
        r=raster(values=[[1,2,3],[4,5,6],[7,8,9]],affine=(1,0,-1.5,0,-1,1.5));p=a.BodySurface(r.context).projection('mercator')
        lo=p.forward(-1.5,-1.5);hi=p.forward(1.5,1.5)
        out=r.resample((3,3),extent=(lo[0],hi[0],lo[1],hi[1]),projection=p)
        self.assertEqual(out.values,r.values)
        back=out.resample((3,3),extent=r.bounds);self.assertEqual(back.values,r.values)
        self.assertEqual(out.provenance,r.provenance)
        with self.assertRaises(ValueError):r.resample((2,2),extent=r.bounds,projection=a.BodySurface(a.MOON).projection())

    def test_mosaic_overlap_and_license_provenance(self):
        left=raster(values=[[1]],affine=(1,0,0,0,-1,1));right=raster(values=[[2]],affine=(1,0,1,0,-1,1))
        out=a.PlanetaryRaster.mosaic([left,right],shape=(1,2),extent=(0,2,0,1),overlap='error')
        self.assertEqual(out.values,((1,2),));self.assertEqual(len(out.provenance),2)
        with self.assertRaises(ValueError):a.PlanetaryRaster.mosaic([left,left],shape=(1,1),extent=(0,1,0,1),overlap='error')
        with self.assertRaises(ValueError):a.PlanetaryRaster.mosaic([left,raster(a.MOON)],shape=(1,1),extent=(0,1,0,1))
        with self.assertRaises(a.UnsupportedBodyOperation):a.PlanetaryRaster.mosaic([left,replace(right,license='other')],shape=(1,2),extent=(0,2,0,1))

    def test_rgba_premultiplication_and_no_scalar_nodata(self):
        r=raster(values=[[(255,0,0,255),(0,0,255,0)]],affine=(1,0,0,0,-1,1),unit='rgba')
        self.assertEqual(r.sample(1,.5,method='bilinear'),(1,0,0,.5))
        with self.assertRaises(ValueError):replace(r,nodata=0)

    def test_explicit_local_image_and_integrity(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'own.png';Image.new('RGB',(2,2),(12,34,56)).save(p)
            source=a.BodySource('synthetic:png','1','Own deterministic test pixels',hashlib.sha256(p.read_bytes()).hexdigest())
            r=a.PlanetaryRaster.from_image(p,context=a.PlanetaryContext(a.MARS),affine=(1,0,0,0,-1,2),source=source,license='BSD-3-Clause')
            self.assertEqual(r.shape,(2,2));self.assertEqual(r.color_mode,'rgba')
            with self.assertRaises(ValueError):a.PlanetaryRaster.from_image(p,context=r.context,affine=r.affine,source=replace(source,sha256='0'*64),license='BSD-3-Clause')

    def test_profile_reports_ground_not_projected_distance(self):
        r=raster(a.MOON,values=[[100]*4]*4,affine=(1,0,0,0,-1,64))
        p=a.BodySurface(r.context).projection('mercator')
        profile=r.profile((.5,61.5),(3.5,61.5),samples=9,projection=p)
        for h in profile.elevation_m:self.assertAlmostEqual(h,100.,delta=1e-7)
        self.assertGreater(profile.projected_distance_m[-1],profile.distance_m[-1]*2)
        self.assertAlmostEqual(profile.distance_m[-1],a.BodySurface(r.context).distance((.5,61.5),(3.5,61.5)),delta=1e-7)
        self.assertEqual(r.values[0],(100,)*4)
        world=raster(a.MOON,values=[[100]*8]*4,affine=(45,0,-180,0,-45,90))
        with self.assertRaises(a.UnsupportedBodyOperation):world.profile((179,0),(-179,0),projection=a.BodySurface(world.context).projection())
        joined=world.profile((179,0),(-179,0),projection=a.BodySurface(world.context).projection(central_longitude=180))
        self.assertLess(joined.projected_distance_m[-1],61000)

    def test_hillshade_sphere_plane_units_and_mask(self):
        r=raster(a.MOON,values=[[0.]*3]*3,affine=(.001,0,-.0015,0,-.001,.0015))
        light=a.GeometricLight(r.context,direction=(1,0,0));shade=r.hillshade(light)
        self.assertGreater(shade.values[1][1],.999999)
        self.assertEqual(r.values[1][1],0);self.assertEqual(shade.unit,'1')
        m=replace(r,values=[[0,0,0],[0,None,0],[0,0,0]])
        self.assertIsNone(m.hillshade(light).values[1][0])
        with self.assertRaises(ValueError):r.hillshade(a.GeometricLight(a.PlanetaryContext(a.MARS),direction=(1,0,0)))
        km=replace(r,unit=a.KILOMETRE,context=replace(r.context,height_unit=a.KILOMETRE))
        self.assertAlmostEqual(km.hillshade(a.GeometricLight(km.context,direction=(1,0,0))).values[1][1],shade.values[1][1],delta=1e-12)


class IlluminationTests(unittest.TestCase):
    def test_known_normals_and_incidence(self):
        for b in a.BODIES.bodies:
            ctx=a.PlanetaryContext.for_body(b);light=a.GeometricLight(ctx,direction=(1,0,0))
            self.assertEqual(light.normal(0,0),(1,0,0));self.assertAlmostEqual(light.incidence(0,0),1,delta=1e-12)
            self.assertAlmostEqual(light.incidence(180,0),-1,delta=1e-12);self.assertAlmostEqual(light.incidence(90,0),0,delta=1e-12)

    def test_terminators_distant_and_finite_sources(self):
        for b in a.BODIES.bodies:
            ctx=a.PlanetaryContext.for_body(b)
            for kwargs in ({'direction':(1,2,3)},{'position':(3*b.axes[0],2*b.axes[0],b.axes[0])}):
                light=a.GeometricLight(ctx,**kwargs);points=light.terminator(samples=41)
                self.assertEqual(len(points),41)
                self.assertLess(math.dist(ctx.to_fixed(*points[0]).xyz,ctx.to_fixed(*points[-1]).xyz),1e-7)
                for p in points:self.assertLess(abs(light.incidence(*p)),1e-10)

    def test_invalid_light_is_not_an_astronomical_model(self):
        ctx=a.PlanetaryContext(a.MARS)
        for kw in ({},{'direction':(0,0,0)},{'position':(0,0,0)},{'direction':(1,0,0),'position':(1e9,0,0)}):
            with self.assertRaises(ValueError):a.GeometricLight(ctx,**kw)


class SurfaceArtistTests(unittest.TestCase):
    def tearDown(self):a.close('all')
    def test_real_scalar_color_exports_and_lifecycle(self):
        f,ax=a.subplots(body=a.MARS);r=raster();layer=ax.raster(r);group=ax.group();group.add(layer)
        self.assertIs(layer.get_body(),a.MARS)
        original=f.to_svg();group.set_visible(False);self.assertNotEqual(f.to_svg(),original);group.set_visible(True)
        self.assertEqual(f.to_svg(),original);f.canvas.draw();layer.set_clim(0,8);self.assertTrue(f.stale)
        color=raster(values=[[(255,0,0),(0,255,0)],[(0,0,255),(255,255,255)]],unit='rgba')
        rgb=ax.raster(color);self.assertIs(rgb.get_body(),a.MARS)
        for fmt,signature in (('png',b'\x89PNG'),('svg',b'<svg'),('pdf',b'%PDF')):
            data=io.StringIO() if fmt=='svg' else io.BytesIO();f.savefig(data,format=fmt)
            value=data.getvalue();value=value.encode() if isinstance(value,str) else value
            self.assertTrue(value.startswith(signature))
        group.remove();self.assertIsNone(layer.axes)

    def test_raster_context_mismatch_preserves_axes(self):
        _,ax=a.subplots(body=a.MARS)
        for r in (raster(a.MOON),a.GeoRaster([[1]],(1,0,0,0,-1,1))):
            with self.assertRaises((ValueError,a.UnsupportedBodyOperation)):ax.raster(r)
            self.assertEqual(ax.layers,[])

    def test_global_and_enu_terrain_preserve_physical_heights(self):
        r=raster(values=[[0,100],[200,300]],affine=(.01,0,-.01,0,-.01,.01))
        f=a.figure(body=a.MARS);ax=f.add_subplot(111,projection='3d');t=ax.terrain(r)
        self.assertIs(t.get_body(),a.MARS);self.assertEqual(t.get_array(),[0,100,200,300])
        original=t.mesh
        with self.assertRaises(a.UnsupportedBodyOperation):ax.set_vertical_exaggeration(5)
        self.assertIs(t.mesh,original);self.assertEqual(ax.vertical_exaggeration,1)
        for j in range(2):
            for i in range(2):self.assertLess(math.dist(t.mesh.vertices[j*2+i],r.context.to_fixed(*r.geographic(i,j,center=True),r.values[j][i]).xyz),1e-7)
        other=a.figure(body=a.MARS);local=other.add_subplot(111,projection='3d');lt=local.terrain(r,origin=(0,0))
        self.assertIsInstance(local.local_frame,a.SurfaceFrame);self.assertNotEqual(lt.mesh.vertices,t.mesh.vertices)
        before=lt.mesh;local.set_vertical_exaggeration(3);self.assertIs(before,lt.mesh)
        self.assertIn('<svg',other.to_svg())

    def test_geometric_shadow_renderer_and_refusals(self):
        r=raster(values=[[0,0,0],[0,300,0],[0,0,0]],affine=(.001,0,-.0015,0,-.001,.0015))
        f=a.figure(body=a.MARS);ax=f.add_subplot(111,projection='3d');t=ax.terrain(r,origin=(0,0))
        light=ax.geometric_light(a.GeometricLight(r.context,direction=(1,0,1)),ambient=.2,diffuse=.8,shadows=True)
        f.canvas.draw();self.assertGreater(light._index.rays,0);self.assertGreater(light._index.tests,0)
        self.assertIsNone(light.model)
        with self.assertRaises(a.UnsupportedBodyOperation):light.set_time('2026-01-01')
        key=t.mesh;ax.set_vertical_exaggeration(4);f.canvas.draw();self.assertIs(t.mesh,key)
        light.remove();self.assertIsNone(ax._solar_lighting)
        with self.assertRaises(a.UnsupportedBodyOperation):ax.geometric_light(a.GeometricLight(r.context,position=(1e8,0,0)))

    def test_metric_projection_context_scale_and_portable_refusal(self):
        f,ax=a.subplots(body=a.MARS);ax.set_extent((-2,2,-2,2));ax.plot([-1,1],[-1,1]);ax.scale_bar(length=10,units='km')
        self.assertTrue(f.to_scene().maps[0]['body']['metric_surface']);self.assertIn('km',f.to_svg())
        with self.assertRaises(ValueError):ax.set_projection(a.BodySurface(a.MOON).projection())
        with self.assertRaises(a.UnsupportedBodyOperation):f.to_html()
        ef,ea=a.subplots();ea.set_projection(a.BodySurface(ea.get_context()).projection('orthographic'))
        with self.assertRaises(a.UnsupportedBodyOperation):ef.to_html()
        route=ea.route([(0,0),(20,30)]);self.assertIs(route.get_body(),a.EARTH)
        _,angular=a.subplots(body=a.MARS,projection='angular')
        with self.assertRaises(a.UnsupportedBodyOperation):angular.scale_bar()

    def test_no_implicit_network_or_scientific_fallback(self):
        from unittest.mock import patch
        with patch('urllib.request.urlopen',side_effect=AssertionError('Implicit download forbidden')):
            r=raster();r.resample((4,4),extent=r.bounds);r.hillshade(a.GeometricLight(r.context,direction=(1,0,0)))
            _,ax=a.subplots(body=a.MARS);ax.route([(0,0),(10,10)])
            with self.assertRaises(a.UnsupportedBodyOperation):ax.sun(None)


if __name__=='__main__':unittest.main()
