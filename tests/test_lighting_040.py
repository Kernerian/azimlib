"""Analytic shadow/occultation invariants and owned Artist integration."""
import math,tempfile,unittest
from datetime import datetime,timedelta,timezone
from pathlib import Path
from dataclasses import replace
import azimlib as azl
from azimlib._frames import Coordinates,EARTH_FIXED
from azimlib.terrain3d import LocalFrame
from azimlib.lighting import ShadowIndex
from azimlib.eclipse import disk_overlap,SUN_RADIUS_M
T=datetime(2025,1,7,12,tzinfo=timezone.utc)
O=azl.SolarObserver(0,0);FRAME=LocalFrame(0,0)
def point(xyz):return Coordinates(tuple(xyz),EARTH_FIXED)
def sphere(xyz,r):return azl.ShadowSphere.from_xyz(xyz,radius_m=r)
def scene():
    fig,ax=azl.subplots(subplot_kw={'projection':'3d'},figsize=(2,2))
    ground=ax.plot_surface([-20,20],[-20,20],[[0,0],[0,0]],color='white')
    data=azl.FeatureCollection((azl.Feature(azl.Geometry('Polygon',(((-2,-2),(2,-2),(2,2),(-2,2),(-2,-2)),)),{}),))
    building=ax.buildings(data.to_geojson(),height=10)
    light=ax.solar_light(azl.SunDirection(90,45,O),frame=FRAME,angular_radius=.2666,max_edge_m=4)
    return fig,ax,ground,building,light

class ShadowNumeric(unittest.TestCase):
    def test_ray_triangle_translation_edges_and_double_sided(self):
        for shift in (0,1e6):
            tri=tuple((x+shift,y,5) for x,y in ((-5,-5),(5,-5),(0,5)))
            for face in (tri,tuple(reversed(tri))):
                index=ShadowIndex(((1,face),),azl.ShadowBudget(),.001)
                self.assertTrue(index.blocked((shift,0,0),(0,0,1)))
                self.assertFalse(index.blocked((shift+10,0,0),(0,0,1)))
                self.assertFalse(index.blocked((shift,0,0),(0,0,1),maximum=4))
                self.assertFalse(index.blocked((shift,0,0),(0,0,1),ignore=1))
    def test_ray_budget_fails_explicitly(self):
        index=ShadowIndex((),azl.ShadowBudget(max_rays=1),.001);index.blocked((0,0,0),(0,0,1))
        with self.assertRaises(ValueError):index.blocked((0,0,0),(0,0,1))
    def test_budget_types_and_limits(self):
        for kw in ({'max_rays':True},{'max_triangles':20001},{'max_triangle_tests':0}):
            with self.assertRaises(ValueError):azl.ShadowBudget(**kw)
    def test_triangle_shadow_length_analytic(self):
        tri=((0,-2,0),(0,2,0),(0,0,10));index=ShadowIndex(((1,tri),),azl.ShadowBudget(),.00001)
        d=(math.sqrt(.5),0,math.sqrt(.5))
        self.assertTrue(index.blocked((-5,0,.0001),d));self.assertFalse(index.blocked((-11,0,.0001),d))
    def test_disk_area_closed_cases_and_symmetry(self):
        self.assertEqual(disk_overlap(2,1,3),0);self.assertAlmostEqual(disk_overlap(2,1,0),math.pi)
        self.assertAlmostEqual(disk_overlap(1,1,1),2*math.pi/3-math.sqrt(3)/2)
        for d in (.5,1,2):self.assertAlmostEqual(disk_overlap(2,1,d),disk_overlap(1,2,d))
    def test_disk_area_independent_vertical_slice_quadrature(self):
        # Integrate intersecting vertical chords; no inverse-cosine formula.
        for a,b,d in ((1,1,1),(1,.75,.8),(1,1.5,.7),(1,.5,1.4)):
            lo,hi=max(-a,d-b),min(a,d+b);n=20000;dx=(hi-lo)/n
            numerical=sum(2*min(math.sqrt(max(0,a*a-x*x)),math.sqrt(max(0,b*b-(x-d)**2)))*dx for x in (lo+(i+.5)*dx for i in range(n)))
            self.assertAlmostEqual(disk_overlap(a,b,d),numerical,delta=2e-6)
    def test_umbra_antumbra_penumbra_without_event_specific_rules(self):
        sun=sphere((1e6,0,0),1000)
        self.assertEqual(azl.occultation(point((0,0,0)),sun,sphere((1e4,0,0),20)).classification,'umbra')
        self.assertEqual(azl.occultation(point((0,0,0)),sun,sphere((1e4,0,0),5)).classification,'antumbra')
        q=azl.occultation(point((0,0,0)),sun,sphere((1e4,10,0),10))
        self.assertEqual(q.classification,'penumbra');self.assertTrue(0<q.visible_fraction<1)
        self.assertEqual(azl.occultation(point((0,0,0)),sun,sphere((2e6,0,0),1000)).visible_fraction,1)
    def test_uncertainty_changes_bounds_not_estimate(self):
        sun=sphere((1e6,0,0),1000);moon=sphere((1e4,10,0),10)
        a=azl.occultation(point((0,0,0)),sun,moon);b=azl.occultation(point((0,0,0)),sun,moon,uncertainty_degrees=.1)
        self.assertEqual(a.visible_fraction,b.visible_fraction);self.assertLessEqual(b.fraction_bounds[0],a.visible_fraction);self.assertGreaterEqual(b.fraction_bounds[1],a.visible_fraction)
    def test_cone_tangency_apex_and_antumbra(self):
        c=azl.ShadowCone(sphere((-1e6,0,0),1000),sphere((0,0,0),10))
        self.assertAlmostEqual(c.radii(c.apex_distance_m)[0],0,places=10)
        self.assertLess(c.radii(c.apex_distance_m*2)[0],0)
        self.assertGreater(c.radii(1000)[1],c.radii(0)[1]);self.assertEqual(c.axis,(1,0,0))
    def test_small_angle_contract_and_point_outside_bodies(self):
        with self.assertRaises(ValueError):azl.occultation(point((0,0,0)),sphere((100,0,0),20),sphere((50,0,0),1))
        with self.assertRaises(ValueError):azl.occultation(point((0,0,0)),sphere((1e6,0,0),1000),sphere((0,0,0),1))
    def test_calculated_eclipse_optin_and_prediction_refusal(self):
        g=azl.EclipseGeometry.from_moon(azl.LunarModel(time_policy='utc-approx').position(T))
        self.assertGreater(g.angular_uncertainty_degrees,.5)
        with self.assertRaises(ValueError):g.require_visual_permission(False)
        with self.assertRaises(NotImplementedError):g.events(T)

class LightingArtists(unittest.TestCase):
    def test_physical_shadows_and_cache_on_camera_and_exaggeration(self):
        fig,ax,ground,building,light=scene();fig.to_scene();factors=light._factors[id(ground)];builds=(light.geometry_builds,light.lighting_builds)
        self.assertIn(.25,factors);self.assertTrue(any(v>.6 for v in factors))
        ax.view_init(elev=50,azim=15);ax.vertical_exaggeration=3;fig.to_scene()
        self.assertEqual(light._factors[id(ground)],factors);self.assertEqual((light.geometry_builds,light.lighting_builds),builds)
    def test_visibility_geometry_and_time_invalidation(self):
        fig,ax,ground,building,light=scene();fig.to_scene();before=light.geometry_builds;old=light._factors[id(ground)]
        building.set_visible(False);fig.to_scene();self.assertGreater(light.geometry_builds,before);self.assertNotEqual(old,light._factors[id(ground)])
        before=light.geometry_builds;light.set_position(azl.SunDirection(270,45,O));fig.to_scene();self.assertEqual(light.geometry_builds,before)
    def test_color_changes_invalidate_shadow_materials(self):
        fig,ax,ground,building,light=scene();fig.to_scene();before=light.geometry_builds
        ground.set_color('red');fig.to_scene();self.assertGreater(light.geometry_builds,before)
    def test_frame_observer_and_duplicate_guards(self):
        fig,ax,ground,building,light=scene()
        with self.assertRaises(ValueError):light.set_position(azl.SunDirection(0,45,azl.SolarObserver(1,0)))
        with self.assertRaises(ValueError):ax.solar_light(azl.SunDirection(0,45,O),angular_radius=0)
        with self.assertRaises(ValueError):azl.subplots()[1].solar_light(azl.SunDirection(0,45,O),frame=FRAME)
    def test_refinement_budget_before_allocation(self):
        fig,ax,ground,building,light=scene();light.max_edge_m=.0001
        with self.assertRaises(ValueError):fig.to_scene()
    def test_disk_sampling_unit_length_and_penumbra_changes(self):
        fig,ax,ground,building,light=scene();light.samples=16
        directions=light._directions();self.assertEqual(len(directions),16)
        for d in directions:self.assertAlmostEqual(sum(v*v for v in d),1)
        fig.to_scene();self.assertGreater(light._index.rays,0)
    def test_light_visibility_and_removal(self):
        fig,ax,ground,building,light=scene();light.set_visible(False);fig.to_scene();self.assertEqual(light.geometry_builds,0)
        light.set_visible(True);fig.to_scene();light.remove();self.assertIsNone(ax._solar_lighting);fig.to_scene()
    def test_temporal_binding_keeps_camera_and_geometry_cache(self):
        fig,ax,ground,building,light=scene();fig.to_scene();camera=ax.camera;count=light.geometry_builds
        series=azl.TemporalSeries([0,1],[azl.SunDirection(90,45,O),azl.SunDirection(270,30,O)],unit='frame')
        series.bind(light).apply(1);fig.to_scene();self.assertIs(ax.camera,camera);self.assertEqual(light.geometry_builds,count)
        light.remove()
        with self.assertRaises(ValueError):series.bind(light)
    def test_volume_explicit_frame_and_lifecycle(self):
        fig,ax,ground,building,light=scene()
        field=azl.VolumeField.from_array([[[0,1],[0,1]],[[0,1],[0,1]]],frame=FRAME)
        volume=ax.plot_volume(field);light.bind_volume(volume,shadow_steps=2);self.assertIsNotNone(volume.light)
        light.set_visible(False);self.assertIsNone(volume.light);light.set_visible(True)
        light.set_position(azl.SunDirection(270,30,O));self.assertEqual(volume.light.direction,light.direction)
        light.remove();self.assertIsNone(volume.light)
    def test_masked_texture_shadow_rejected(self):
        fig,ax,ground,building,light=scene();ground.set_texture((1,1,bytes((255,255,255,255))))
        with self.assertRaises(ValueError):fig.to_scene()
    def test_static_exports_and_optional_eclipse_map(self):
        with tempfile.TemporaryDirectory() as folder:
            fig,ax,*_=scene()
            for ext in ('png','svg','pdf'):fig.savefig(Path(folder)/('shadow.'+ext))
        g=azl.EclipseGeometry.from_moon(azl.LunarModel(time_policy='utc-approx').position(T))
        fig,ax=azl.subplots()
        with self.assertRaises(ValueError):ax.eclipse_shadow(g)
        layer=ax.eclipse_shadow(g,allow_approximate=True,step=30,mode='possible');layer.set_visible(False);layer.set_visible(True)
        self.assertEqual(layer.get_geometry(),g);self.assertIn('svg',fig.to_svg())
    def test_body_eclipse_geometry_scales_and_time_update(self):
        model=azl.LunarModel(time_policy='utc-approx');p=model.position(T);g=azl.EclipseGeometry.from_moon(p)
        fig,ax=azl.subplots(subplot_kw={'projection':'3d'});body=ax.earth_moon(p)
        with self.assertRaises(ValueError):body.set_eclipse_geometry(g)
        body.set_eclipse_geometry(g,allow_approximate=True);body.set_scales(distance_scale=.1,moon_radius_scale=2)
        self.assertEqual(body.eclipse_geometry,g);before=body.faces(ax.camera,ax.get_world_bounds(),1,1)
        body.set_position(model.position(T+timedelta(days=1)));self.assertNotEqual(body.eclipse_geometry,g)
        self.assertTrue(before);body.set_eclipse_geometry(None)

if __name__=='__main__':unittest.main()
