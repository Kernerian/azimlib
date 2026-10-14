"""Own analytic invariants and integration contracts, no reference tables."""
from datetime import datetime,timedelta,timezone
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import math,tempfile,unittest
import azimlib as azl
from azimlib.lunar import _dot,_length,MOON_RADIUS_M
from azimlib.lunar_artists import _sphere
from azimlib.terrain3d import cross
T=datetime(2025,6,21,12,tzinfo=timezone.utc)
MODEL=azl.LunarModel(time_policy='utc-approx')
O=azl.SolarObserver(-46.63,-23.55)

class LunarNumeric(unittest.TestCase):
    def test_time_contract(self):
        with self.assertRaises(ValueError):azl.LunarModel().position(T)
        for t in (T.replace(tzinfo=None),T.replace(year=1971),T.replace(year=2101)):
            with self.assertRaises(ValueError):MODEL.position(t)
        correction=azl.SolarTimeOffsets(T,T+timedelta(days=1),source='Synthetic clock fixture',tai_minus_utc=37,ut1_minus_utc=0,uncertainty_seconds=.1)
        p=azl.LunarModel().position(T,offsets=correction)
        self.assertEqual(p.time_policy,'strict')
        with self.assertRaises(ValueError):MODEL.position(T,offsets=correction)
        calls=[]
        azl.LunarModel().position(T,offsets=lambda t:(calls.append(t) or correction))
        self.assertEqual(len(calls),1)
    def test_invalid_options(self):
        for kw in ({'time_policy':'guess'},{'parallax':1},{'refraction':True}):
            with self.assertRaises((TypeError,ValueError)):azl.LunarModel(**kw)
    def test_ranges_and_fixed_frame_extremes(self):
        for y in (1972,2000,2025,2100):
            for month in range(1,13):
                p=MODEL.position(T.replace(year=y,month=month))
                self.assertTrue(350e6<p.distance_m<410e6)
                self.assertAlmostEqual(_length(p.fixed.xyz),p.distance_m,places=6)
                self.assertLess(abs(p.ecliptic_latitude),6)
                self.assertEqual(p.fixed.frame.kind,'fixed')
    def test_sublunar_and_topocentric_distance(self):
        p=MODEL.position(T);q=MODEL.position(T,azl.SolarObserver(*p.sublunar))
        self.assertGreater(q.geometric_elevation,89.9)
        self.assertTrue(6e6<p.distance_m-q.topocentric_distance_m<6.5e6)
        self.assertAlmostEqual(_length(tuple(m-o for m,o in zip(q.fixed.xyz,q.observer_origin))),q.topocentric_distance_m)
    def test_parallax_disabled_and_poles(self):
        for obs in (O,azl.SolarObserver(0,90),azl.SolarObserver(180,-90)):
            a=MODEL.position(T,obs);b=azl.LunarModel(time_policy='utc-approx',parallax=False).position(T,obs)
            self.assertTrue(0<abs(a.geometric_elevation-b.geometric_elevation)<1.2)
            self.assertAlmostEqual(b.distance_m,b.topocentric_distance_m,places=5)
            self.assertAlmostEqual(b.right_ascension,b.topocentric_right_ascension)
    def test_refraction_does_not_change_physical_phase(self):
        a=MODEL.position(T,O);b=azl.LunarModel(time_policy='utc-approx',refraction=azl.SolarRefraction()).position(T,O)
        self.assertEqual(a.illuminated_fraction,b.illuminated_fraction)
        self.assertEqual(a.fixed,b.fixed);self.assertGreaterEqual(b.elevation,a.elevation)
    def test_phase_and_orientation_analytic_geometry(self):
        p=MODEL.position(T)
        # Independent artificial vectors: Sun on +X, Moon at opposite/quadrature.
        sun=replace(p.sun,fixed=replace(p.sun.fixed,xyz=(1e15,0.,0.)))
        for xyz,expected in (((-384e6,0.,0.),1),((384e6,0.,0.),0),((0.,384e6,0.),.5)):
            q=replace(p,sun=sun,fixed=replace(p.fixed,xyz=xyz))
            self.assertAlmostEqual(q.illuminated_fraction,expected,places=6)
        self.assertIsNone(replace(p,sun=sun,fixed=replace(p.fixed,xyz=(-384e6,0.,0.))).bright_limb_position_angle)
        q=replace(p,sun=sun,fixed=replace(p.fixed,xyz=(0.,384e6,0.)))
        self.assertAlmostEqual(q.bright_limb_position_angle,270)
    def test_manual_finite_coordinates(self):
        for az,el in ((0,20),(90,0),(180,-30),(270,80)):
            p=azl.MoonDirection(az,el,384e6,O);a,e=O.azimuth_elevation(p.fixed)
            self.assertAlmostEqual(a,az);self.assertAlmostEqual(e,el)
            self.assertAlmostEqual(_length(tuple(m-o for m,o in zip(p.fixed.xyz,O.fixed_position.xyz))),384e6,places=5)
        for args in ((0,91,1,O),(0,0,0,O),(0,0,1,None)):
            with self.assertRaises(ValueError):azl.MoonDirection(*args)
    def test_path_contract_and_mesh(self):
        path=MODEL.path([T,T+timedelta(hours=1),T+timedelta(hours=2)])
        self.assertEqual(len(path.groundtrack.coordinates),3);self.assertEqual(len(path.mesh().triangles),4)
        self.assertIn('Earth-fixed',path.__doc__)
        for dates in ([T],[T,T],[T+timedelta(days=1),T]):
            with self.assertRaises(ValueError):MODEL.path(dates)
        with self.assertRaises(ValueError):path.mesh(distance_scale=0)

class LunarArtists(unittest.TestCase):
    def setUp(self):self.p=MODEL.position(T,O);self.next=MODEL.position(T+timedelta(hours=6),O)
    def test_map_edit_label_and_picking(self):
        from azimlib.navigation import viewport_from_metadata
        fig,ax=azl.subplots();moon=ax.moon(self.p,annotation='Moon',color='red');moon.set_picker(3)
        scene=fig.canvas.draw();vp=viewport_from_metadata(ax.projection,scene.maps[0]);x,y=vp.project(*self.p.sublunar)
        hit,props=moon.contains(SimpleNamespace(canvas=fig.canvas,x=x,y=scene.height-y,inaxes=ax))
        self.assertTrue(hit);self.assertEqual(props['features'][0].id,'moon')
        moon.set_annotation('Updated');moon.set_visible(False);self.assertFalse(moon.contains(SimpleNamespace(canvas=fig.canvas,x=x,y=scene.height-y,inaxes=ax))[0])
    def test_atomic_observer_and_clock_update(self):
        _,ax=azl.subplots();moon=ax.moon(self.p,model=MODEL);old=moon.data
        with self.assertRaises(ValueError):moon.set_position(MODEL.position(T))
        self.assertIs(moon.data,old);moon.set_time(T+timedelta(hours=6));self.assertEqual(moon.state,self.next)
        moon.set_manual(90,30,384e6);self.assertIsInstance(moon.state,azl.MoonDirection)
    def test_temporal_prevalidation_and_identity(self):
        _,ax=azl.subplots();moon=ax.moon(self.p);series=azl.TemporalSeries([T,T+timedelta(hours=6)],[self.p,self.next]);extent=ax.get_extent()
        self.assertIs(series.bind(moon).apply(1),moon);self.assertEqual(ax.get_extent(),extent)
        with self.assertRaises(ValueError):azl.TemporalSeries([T],[self.next]).bind(moon)
        with self.assertRaises(ValueError):series.bind(moon,scale='frame')
        binding=series.bind(moon);moon.remove()
        with self.assertRaises(RuntimeError):binding.apply(0)
    def test_physical_and_display_scales_are_separate(self):
        _,ax=azl.subplots(subplot_kw={'projection':'3d'});body=ax.earth_moon(self.p);centers=body.physical_centers;phase=body.state.illuminated_fraction
        self.assertEqual(body.display_centers,centers);body.set_scales(distance_scale=.1,moon_radius_scale=4)
        self.assertEqual(body.physical_centers,centers);self.assertEqual(body.state.illuminated_fraction,phase)
        self.assertAlmostEqual(_length(body.display_centers['moon']),self.p.distance_m*.1)
        old=body.mesh
        with self.assertRaises(ValueError):body.set_scales(distance_scale=.0001)
        self.assertIs(body.mesh,old)
    def test_body_normals_and_winding(self):
        vs,faces,normals=_sphere((0,0,0),(2,2,1),12,6)
        for f in faces:
            a,b,c=(vs[i] for i in f);normal=cross(tuple(y-x for x,y in zip(a,b)),tuple(y-x for x,y in zip(a,c)))
            self.assertGreater(_dot(normal,tuple(sum(vs[i][k] for i in f) for k in range(3))),0)
    def test_global_frame_and_exaggeration_guards(self):
        _,ax=azl.subplots(subplot_kw={'projection':'3d'});ax.vertical_exaggeration=2
        with self.assertRaises(ValueError):ax.earth_moon(self.p)
        _,ax=azl.subplots();
        with self.assertRaises(ValueError):ax.earth_moon(self.p)
        _,ax=azl.subplots(subplot_kw={'projection':'3d'});ax.local_frame='other';ax.layers.append(SimpleNamespace())
        with self.assertRaises(ValueError):ax.earth_moon(self.p)
    def test_lighting_is_unchanged_by_display_scales(self):
        _,ax=azl.subplots(subplot_kw={'projection':'3d'});body=ax.earth_moon(self.p)
        colors=[v[1] for v in body.faces(ax.camera,ax.get_world_bounds(),1,1)]
        body.set_scales(distance_scale=.1,moon_radius_scale=3)
        self.assertEqual(colors,[v[1] for v in body.faces(ax.camera,ax.get_world_bounds(),1,1)])
        self.assertGreater(len(set(colors)),10)
    def test_3d_time_camera_and_path(self):
        _,ax=azl.subplots(subplot_kw={'projection':'3d'});body=ax.earth_moon(self.p);camera=ax.camera
        azl.TemporalSeries([T,T+timedelta(hours=6)],[self.p,self.next]).bind(body).apply(1)
        self.assertEqual(ax.camera,camera);self.assertEqual(body.state,self.next)
        path=MODEL.path([T,T+timedelta(hours=6)]);ax.moon_path(path)
    def test_static_exports_projection_and_3d(self):
        with tempfile.TemporaryDirectory() as directory:
            for projection in ('equirectangular','mercator','orthographic','3d'):
                fig,ax=azl.subplots(subplot_kw={'projection':projection},figsize=(2,2))
                if projection=='3d':ax.earth_moon(self.p,distance_scale=.1,moon_radius_scale=3);ax.set_axis_off()
                else:ax.moon(self.p,annotation='Moon');ax.moon_path(MODEL.path([T,T+timedelta(hours=6)]))
                for ext in ('png','svg','pdf'):
                    p=Path(directory)/(projection+'.'+ext);fig.savefig(p);self.assertGreater(p.stat().st_size,100)

if __name__=='__main__':unittest.main()
