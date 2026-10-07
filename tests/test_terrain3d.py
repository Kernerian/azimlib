"""Independent camera, homogeneous clipping, depth, metric mesh and integration contracts."""
import io,math,unittest,tempfile,sys,zlib,re,base64
from pathlib import Path
from dataclasses import replace
import azimlib as azl
from azimlib.terrain3d import Camera,Mesh,LocalFrame,clip_triangle,rasterize,transform_point,length_unit
from azimlib.terrain_axes import surface_mesh,triangulate_ring
from azimlib.scene import Raster3D,Scene
from azimlib.raster import GeoRaster
from azimlib.interaction import Interaction
from azimlib.navigation import Navigation

RED=(255,0,0,255);BLUE=(0,0,255,255)
def triangle(z=0):return ((-.8,-.8,z,1),(.8,-.8,z,1),(0,.8,z,1))
def footprint(points=None,**properties):
    points=points or [(0,0),(100,0),(100,100),(0,100),(0,0)]
    return {'type':'FeatureCollection','features':[{'type':'Feature','id':'building','properties':properties,'geometry':{'type':'Polygon','coordinates':[points]}}]}

class NumericTests(unittest.TestCase):
    def test_length_units(self):
        self.assertEqual(length_unit('km').to_si,1000);self.assertEqual(length_unit('ft').to_si,.3048)
        from azimlib.geodesy import DEGREE
        with self.assertRaises(ValueError):length_unit(DEGREE)
    def test_local_origin_and_axis_direction(self):
        frame=LocalFrame(-46,-23);self.assertEqual(frame.horizontal(-46,-23),(0,0))
        east,north=frame.horizontal(-45.99,-23);self.assertGreater(east,1000);self.assertLess(abs(north),1)
        east,north=frame.horizontal(-46,-22.99);self.assertLess(abs(east),1e-6);self.assertGreater(north,1000)
    def test_local_region_limit(self):
        with self.assertRaises(ValueError):LocalFrame(0,0).horizontal(20,0)
        with self.assertRaises(ValueError):LocalFrame(0,90)
    def test_camera_center_and_perspective_distance(self):
        for projection in ('ortho','persp'):
            camera=Camera(projection=projection);q=transform_point(camera.matrix((0,2,0,2,0,2)),(1,1,1))
            self.assertAlmostEqual(q[0],0);self.assertAlmostEqual(q[1],0);self.assertTrue(-q[3]<=q[2]<=q[3])
            self.assertEqual(q[3],1 if projection=='ortho' else 4)
    def test_zoom_and_roll(self):
        b=(0,2,0,2,0,2);p=(2,1,1)
        a=transform_point(Camera().matrix(b),p);c=transform_point(Camera(zoom=2).matrix(b),p)
        self.assertAlmostEqual(c[0],a[0]*2);self.assertAlmostEqual(c[1],a[1]*2)
        rolled=transform_point(Camera(roll=90).matrix(b),p);self.assertAlmostEqual(rolled[0],a[1]);self.assertAlmostEqual(rolled[1],-a[0])
    def test_invalid_camera_and_bounds(self):
        for kw in ({'projection':'foo'},{'zoom':0},{'elev':90},{'near':5},{'far':2},{'azim':math.nan}):
            with self.subTest(kw=kw),self.assertRaises(ValueError):Camera(**kw)
        with self.assertRaises(ValueError):Camera().matrix((0,0,0,1,0,1))
    def test_clip_all_halfspaces(self):
        for axis in range(3):
            for sign in (-1,1):
                pts=[list(p) for p in triangle()];pts[0][axis]=sign*2
                result=clip_triangle(pts);self.assertTrue(result)
                self.assertTrue(all(-p[3]-1e-12<=p[k]<=p[3]+1e-12 for t in result for p in t for k in range(3)))
    def test_clip_behind_and_nonfinite(self):
        self.assertFalse(clip_triangle(((0,0,0,-1),(1,0,0,-1),(0,1,0,-1))))
        with self.assertRaises(ValueError):clip_triangle(((math.nan,0,0,1),*triangle()[1:]))
    def test_depth_near_wins_regardless_of_order(self):
        near=(triangle(-.5),RED);far=(triangle(.5),BLUE)
        a=rasterize((near,far),32,32);b=rasterize((far,near),32,32)
        self.assertEqual(a.rgba,b.rgba);self.assertEqual(a.rgba[(16*32+16)*4:(16*32+16+1)*4],bytes(RED))
    def test_intersecting_triangles_need_per_pixel_depth(self):
        a=(((-.8,-.8,-.8,1),(.8,-.8,.8,1),(0,.8,0,1)),RED)
        b=(((-.8,-.8,.8,1),(.8,-.8,-.8,1),(0,.8,0,1)),BLUE)
        result=rasterize((a,b),40,40)
        self.assertEqual(result.rgba[(25*40+12)*4:(25*40+13)*4],bytes(RED))
        self.assertEqual(result.rgba[(25*40+28)*4:(25*40+29)*4],bytes(BLUE))
    def test_top_left_no_seam_full_square(self):
        a=((-1,-1,0,1),(1,-1,0,1),(1,1,0,1));b=((-1,-1,0,1),(1,1,0,1),(-1,1,0,1))
        for accelerate in (False,True):self.assertEqual(rasterize(((a,RED),(b,RED)),17,13,accelerate=accelerate).rgba,bytes(RED)*17*13)
    def test_numpy_fallback_exact_pixels(self):
        tris=((triangle(-.4),RED),(((0,-2,.7,1),(2,.5,.2,1),(-.3,.8,-.8,1)),BLUE))
        self.assertEqual(rasterize(tris,39,27,accelerate=False).rgba,rasterize(tris,39,27).rgba)
    def test_transparency_and_tie(self):
        a=rasterize(((triangle(),RED),(triangle(),BLUE)),8,8)
        self.assertEqual(a.rgba[4*(4*8+4):4*(4*8+5)],bytes(RED))
        self.assertFalse(any(rasterize(((triangle(),(0,0,0,0)),),8,8).rgba))
        with self.assertRaises(ValueError):rasterize(((triangle(),(0,0,0,128)),),8,8)
    def test_raster_limits_and_cancel(self):
        for size in ((0,8),(True,3),(4000,4000)):
            with self.assertRaises(ValueError):rasterize((),*size)
        with self.assertRaises(ValueError):rasterize(((triangle(),(300,0,0,255)),),8,8)
        with self.assertRaises(ValueError):rasterize(((triangle(),RED),)*100,2000,2000)
        def cancel():raise RuntimeError('cancelled')
        with self.assertRaises(RuntimeError):rasterize(((triangle(),RED),),8,8,check=cancel)
    def test_mesh_freeze_bounds_unused_and_indices(self):
        vertices=[[0,0,0],[1,0,2],[0,1,1],[100,100,100]];mesh=Mesh(vertices,[[0,1,2]])
        vertices[0][0]=30;self.assertEqual(mesh.bounds,(0,1,0,1,0,2))
        with self.assertRaises(ValueError):Mesh(mesh.vertices,((0,1,9),))
    def test_units_masks_and_upward_normals(self):
        mesh=surface_mesh([0,1],[1,0],[[3,4],[5,6]],'km','ft')
        self.assertEqual(mesh.bounds,(0,1000,0,1000,3*.3048,6*.3048))
        for t in mesh.triangles:
            a,b,c=(mesh.vertices[i] for i in t);self.assertGreater((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]),0)
        mesh=surface_mesh([0,1,2],[0,1,2],[[None,1,2],[1,2,3],[2,3,4]],'m','m');self.assertEqual(len(mesh.triangles),6)
    def test_surface_shape_and_empty_reject(self):
        for args in (([0,1],[0,1],[[None,None],[None,None]]),([0],[0,1],[[1,2],[3,4]]),([0,0],[0,1],[[1,2],[3,4]])):
            with self.assertRaises(ValueError):surface_mesh(*args,'m','m')
    def test_concave_ear_clipping_and_bad_ring(self):
        p,t=triangulate_ring(((0,0),(2,0),(2,2),(1,1),(0,2),(0,0)));self.assertEqual(len(t),3)
        self.assertEqual(len(triangulate_ring(tuple(reversed(p)))[1]),3)
        with self.assertRaises(ValueError):triangulate_ring(((0,0),(2,2),(0,2),(2,0)))

class TerrainTests(unittest.TestCase):
    def setUp(self):self.fig,self.ax=azl.subplots(figsize=(4,3),subplot_kw={'projection':'3d'});self.a=self.ax.plot_surface([0,100,200],[0,100,200],[[0,20,0],[20,80,20],[0,20,0]])
    def tearDown(self):azl.close('all')
    def test_artist_visibility_remove_stale(self):
        self.assertIs(self.a.axes,self.ax);self.fig.canvas.draw();self.a.set_visible(False);self.assertTrue(self.fig.stale)
        self.assertFalse(next(i for i in self.fig.to_scene().items if isinstance(i,Raster3D)).triangles)
        self.a.remove();self.assertIsNone(self.a.axes);self.assertFalse(self.ax.layers)
    def test_exaggeration_keeps_physical_data(self):
        before=self.a.mesh;self.ax.set_vertical_exaggeration(5);self.assertEqual(self.a.mesh,before);self.assertEqual(self.ax.get_zlim(),(0,80))
        with self.assertRaises(ValueError):self.ax.set_vertical_exaggeration(0)
        self.assertEqual(self.ax.vertical_exaggeration,5)
    def test_camera_edit_is_atomic(self):
        original=self.ax.camera
        with self.assertRaises(ValueError):self.ax.view_init(elev=90)
        self.assertEqual(self.ax.camera,original);self.ax.view_init(elev=20,azim=30,roll=10);self.assertEqual(self.ax.camera.elev,20)
        self.ax.set_proj_type('ortho');self.assertEqual(self.ax.camera.projection,'ortho')
    def test_explicit_metric_limits(self):
        self.ax.set_xlim(1000,4000);self.ax.set_zlim(-100,200);self.assertEqual(self.ax.get_xlim(),(1000,4000));self.assertEqual(self.ax.get_zlim(),(-100,200))
        with self.assertRaises(ValueError):self.ax.set_ylim(5,4)
    def test_norm_colorbar_and_shade_edit(self):
        bar=self.fig.colorbar(self.a,label='Elevation');self.a.set_clim(-20,150);self.assertEqual(bar.mappable.get_clim(),(-20,150))
        self.a.set_cmap('viridis');self.a.set_shade(False);scene=self.fig.to_scene();self.assertTrue(any(isinstance(i,Raster3D) for i in scene.items))
        with self.assertRaises(ValueError):self.a.set_color((1,0,0,.5))
        self.assertIsNone(self.a.color)
    def test_scalar_array_edits_colors_not_elevation(self):
        geometry=self.a.mesh
        self.a.set_array([100]*len(geometry.vertices));self.assertEqual(self.a.get_array(),[100]*len(geometry.vertices));self.assertEqual(self.a.mesh,geometry)
        self.a.set_array([None]*len(geometry.vertices));self.assertFalse(next(i for i in self.fig.to_scene().items if isinstance(i,Raster3D)).triangles)
        with self.assertRaises(ValueError):self.a.set_array([1])
        self.assertEqual(len(self.a.get_array()),len(geometry.vertices))
    def test_georaster_affine_units_and_reference(self):
        raster=GeoRaster(((1,2),(3,4)),(.01,.002,-46,0,-.01,-23))
        a=self.ax.terrain(raster,origin=(-46,-23),elevation_unit='ft',elevation_reference='source DEM')
        self.assertEqual(a.mesh.bounds[-2:],(.3048,1.2192));self.assertEqual(a.elevation_reference,'source DEM')
        self.assertEqual(self.ax.local_frame,LocalFrame(-46,-23))
        with self.assertRaises(ValueError):self.ax.terrain(raster,origin=(-45,-23))
    def test_georaster_outside_region_does_not_attach(self):
        before=len(self.ax.layers)
        with self.assertRaises(ValueError):self.ax.terrain(GeoRaster(((1,2),(3,4)),(10,0,0,0,10,0)),origin=(0,0))
        self.assertEqual(len(self.ax.layers),before);self.assertIsNone(self.ax.local_frame)
    def test_extrusion_physical_height_and_id(self):
        a=self.ax.buildings(footprint(height=40),height='height',base=10)
        self.assertEqual(a.mesh.bounds,(0,100,0,100,10,50));self.assertEqual(a.feature_ids,('building',));self.assertEqual(len(a.mesh.triangles),12)
    def test_geographic_extrusion_requires_local_frame(self):
        with self.assertRaises(ValueError):self.ax.buildings(footprint(),height=10,coordinates='geographic')
        self.ax.terrain(GeoRaster(((0,0),(0,0)),(.01,0,-46,0,-.01,-23)),origin=(-46,-23))
        a=self.ax.buildings(footprint([(-46,-23),(-45.999,-23),(-45.999,-22.999),(-46,-22.999),(-46,-23)]),height=10,coordinates='geographic')
        self.assertAlmostEqual(a.mesh.bounds[-1],10)
    def test_invalid_building_preserves_layers(self):
        count=len(self.ax.layers)
        for h in (0,-1,math.nan):
            with self.assertRaises(ValueError):self.ax.buildings(footprint(),height=h)
            self.assertEqual(len(self.ax.layers),count)
        data=footprint();data['features'][0]['geometry']['coordinates'].append([(20,20),(40,20),(40,40),(20,20)])
        with self.assertRaises(ValueError):self.ax.buildings(data,height=10)
    def test_camera_history_and_2d_remain_distinct(self):
        geographic=self.fig.add_axes((.02,.02,.1,.1));geographic.set_extent((-5,5,-5,5));nav=Navigation(self.fig);initial=self.ax.camera
        self.ax.view_init(20,30);geographic.set_extent((-2,2,-2,2));nav.push();nav.home();self.assertEqual(self.ax.camera,initial);self.assertEqual(geographic.get_extent(),(-5,5,-5,5))
        nav.back();self.assertEqual(self.ax.camera.elev,20);nav.forward();self.assertEqual(self.ax.camera,initial)
    def test_drag_orbit_wheel_reset_no_fake_geolocation(self):
        controller=Interaction(self.fig.canvas);self.fig.canvas.scene=self.fig.canvas.draw();x,y,w,h=self.fig.canvas.scene.maps[0]['box'];initial=self.ax.camera
        controller.command('pan');event=controller.event('button_press_event',x+w/2,y+h/2,button=1);self.assertIsNone(event.xdata)
        controller.event('motion_notify_event',x+w/2+20,y+h/2+10,buttons=[1]);controller.event('button_release_event',x+w/2+20,y+h/2+10,button=1)
        self.assertNotEqual(self.ax.camera,initial);controller.command('home');self.assertEqual(self.ax.camera,initial)
        controller.event('scroll_event',x+w/2,y+h/2,step=1);self.assertGreater(self.ax.camera.zoom,1)
    def test_lost_button_and_zoom_tool(self):
        controller=Interaction(self.fig.canvas);self.fig.canvas.scene=self.fig.canvas.draw();x,y,w,h=self.fig.canvas.scene.maps[0]['box'];controller.command('zoom')
        controller.event('button_press_event',x+w/2,y+h/2,button=1);controller.event('button_release_event',x+w/2,y+h/2-20,button=1);self.assertGreater(self.ax.camera.zoom,1)
        controller.command('pan');controller.event('button_press_event',x+w/2,y+h/2,button=1);controller.event('motion_notify_event',x,y,buttons=[]);self.assertIsNone(controller.drag)
    def test_frame_cache_changes_with_camera_and_scalar_colors(self):
        from azimlib.backends._raster_cache import scene_key
        a=scene_key(self.fig.to_scene());self.ax.view_init(20,15);b=scene_key(self.fig.to_scene());self.assertNotEqual(a,b)
        self.a.set_color('red');self.assertNotEqual(b,scene_key(self.fig.to_scene()))
    def test_scene_scaled_and_static_html(self):
        scene=self.fig.to_scene();image=next(i for i in scene.items if isinstance(i,Raster3D));scaled=next(i for i in scene.scaled(2).items if isinstance(i,Raster3D))
        self.assertEqual(scaled.width,image.width*2);self.assertEqual(scaled.triangles,image.triangles)
        html=self.fig.to_html();self.assertIn('data:image/png;base64,',html);self.assertNotIn('"terrain3d": true',html)
    def test_png_svg_pdf_embedded_pixels_orientation(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Pillow optional encoder')
        from azimlib.renderers.svg import render_svg
        from azimlib.renderers.pdf import render_pdf
        from azimlib.renderers.pillow import render_image
        # Non-symmetric triangle permits exact embedded image comparison.
        scene=Scene(24,16,background=None);item=Raster3D(0,0,24,16,((triangle(-.5),RED),));scene.add(item)
        expected=rasterize(item.triangles,24,16).rgba
        with Image.open(io.BytesIO(base64.b64decode(re.search(r'data:image/png;base64,([^\"]+)',render_svg(scene)).group(1)))) as im:self.assertEqual(im.tobytes(),expected)
        pdf=render_pdf(scene);self.assertIn(b'/SMask',pdf);self.assertIn(b'24 0 0 -16 0 16 cm /Im0 Do',pdf)
        streams=re.findall(rb'stream\n(.*?)\nendstream',pdf,re.S);decoded=[]
        for s in streams:
            try:decoded.append(zlib.decompress(s))
            except zlib.error:pass
        self.assertIn(expected[3::4],decoded);self.assertIn(bytes(c for i,c in enumerate(expected) if i%4!=3),decoded)
        try:import aggdraw
        except ImportError:
            # PNG fallback supersamples; use Pillow BOX as an independent
            # composition reference for the already-tested depth pixels.
            high=rasterize(item.triangles,72,48).rgba
            with Image.frombytes('RGBA',(72,48),high) as reference:
                expected_png=reference.resize((24,16),Image.Resampling.BOX).tobytes()
        else:expected_png=expected
        with render_image(scene,_interactive=True) as im:self.assertEqual(im.tobytes(),expected_png)
    def test_clear_detaches_surface_and_resets_camera(self):
        self.ax.view_init(10,20);self.ax.clear();self.assertEqual(self.ax.camera,Camera());self.assertIsNone(self.a.axes)
    def test_unsupported_geographic_operation_rejected(self):
        for call in (lambda:self.ax.set_extent((-1,1,-1,1)),lambda:self.ax.north_arrow(),lambda:self.ax.geojson(footprint())):
            with self.assertRaises(NotImplementedError):call()
        with self.assertRaises(ValueError):self.fig.add_axes((.1,.1,.3,.3),projection='3d',sharex=self.ax)
        geographic=self.fig.add_axes((.02,.02,.1,.1));original=geographic.get_extent()
        for call in (lambda:geographic.sharex(self.ax),lambda:self.ax.sharey(geographic)):
            with self.assertRaises(ValueError):call()
        self.assertEqual(geographic.get_extent(),original)
        self.assertFalse(geographic.get_shared_x_axes().joined(geographic,self.ax))

if __name__=='__main__':unittest.main()
