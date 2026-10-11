"""Own solar contracts and analytic invariants; no redistributed ephemeris tables."""
from datetime import datetime,date,timedelta,timezone
import math,tempfile,unittest
from pathlib import Path
import azimlib as azl
from azimlib.solar import AU_METRES
from azimlib.scene import Text,Circle
from azimlib.temporal import TemporalSeries

UTC=timezone.utc
T=datetime(2025,6,21,12,tzinfo=UTC)
APPROX=azl.SolarModel(time_policy='utc-approx')
O=azl.SolarObserver(-46.63,-23.55)
def offsets(**kwargs):
    return azl.SolarTimeOffsets(datetime(2025,1,1,tzinfo=UTC),datetime(2026,1,1,tzinfo=UTC),
        source='Explicit synthetic clock fixture, not an EOP measurement',tai_minus_utc=37,ut1_minus_utc=kwargs.get('dut1',0),uncertainty_seconds=.1)
def vector(lon,lat):
    l,p=math.radians(lon),math.radians(lat)
    return (math.cos(p)*math.cos(l),math.cos(p)*math.sin(l),math.sin(p))
def dot(a,b):return sum(x*y for x,y in zip(a,b))

class SolarNumeric(unittest.TestCase):
    def test_strict_requires_both_offsets_and_interval(self):
        for correction in (None,azl.SolarTimeOffsets(T,T+timedelta(days=1),source='fixture',tai_minus_utc=37)):
            with self.assertRaises(ValueError):azl.SolarModel().position(T,offsets=correction)
        with self.assertRaises(ValueError):azl.SolarModel().position(T+timedelta(days=370),offsets=offsets())
        self.assertEqual(azl.SolarModel().position(T,offsets=lambda instant:offsets()).time_policy,'strict')
    def test_explicit_approx_does_not_ignore_offsets(self):
        with self.assertRaises(ValueError):APPROX.position(T,offsets=offsets())
        self.assertGreater(APPROX.position(T).angular_budget_degrees,.05)
    def test_naive_dates_model_limits_and_invalid_options(self):
        for t in (T.replace(tzinfo=None),datetime(1971,12,31,tzinfo=UTC),datetime(2101,1,1,tzinfo=UTC)):
            with self.assertRaises(ValueError):APPROX.position(t)
        for kw in ({'time_policy':'guess'},{'aberration':1},{'parallax':'yes'},{'refraction':True}):
            with self.assertRaises((ValueError,TypeError)):azl.SolarModel(**kw)
        with self.assertRaises(ValueError):APPROX.position(T,azl.SolarObserver(0,0,100001))
    def test_earth_rotation_tracks_ut1_not_tt(self):
        a=azl.SolarModel().position(T,offsets=offsets());b=azl.SolarModel().position(T,offsets=offsets(dut1=.5))
        self.assertEqual(a.right_ascension,b.right_ascension)
        self.assertAlmostEqual(b.sidereal_angle-a.sidereal_angle,.5*360.98564736629/86400,places=7)
    def test_manual_cardinal_directions_and_world_frame(self):
        for az,v in ((0,(0,1,0)),(90,(1,0,0)),(180,(0,-1,0)),(270,(-1,0,0))):
            d=azl.SunDirection(az,0,O)
            for a,b in zip(d.lighting_direction,v):self.assertAlmostEqual(a,b)
            self.assertAlmostEqual(dot(d.fixed_direction,d.fixed_direction),1)
        self.assertEqual(azl.SunDirection(-90,20).azimuth,270)
        with self.assertRaises(ValueError):azl.SunDirection(0,91)
        with self.assertRaises(ValueError):azl.SunDirection(0,0).subsolar
    def test_geocentric_distance_and_declination_extremes(self):
        for year in (1972,2000,2025,2100):
            for month in (1,3,6,9,12):
                with self.subTest(year=year,month=month):
                    s=APPROX.position(datetime(year,month,21,tzinfo=UTC))
                    self.assertTrue(.98<s.distance_m/AU_METRES<1.02);self.assertLessEqual(abs(s.declination),23.5)
                    self.assertAlmostEqual(math.sqrt(dot(s.fixed.xyz,s.fixed.xyz)),s.distance_m,places=4)
    def test_subsolar_and_parallax_use_translation(self):
        s=APPROX.position(T);obs=azl.SolarObserver(*s.subsolar)
        p=APPROX.position(T,obs)
        self.assertGreater(p.geometric_elevation,89.99)
        for obs in (O,azl.SolarObserver(0,90),azl.SolarObserver(180,-90)):
            p=APPROX.position(T,obs);q=azl.SolarModel(time_policy='utc-approx',parallax=False).position(T,obs)
            self.assertLessEqual(abs(p.geometric_elevation-q.geometric_elevation),.0026)
            self.assertAlmostEqual(math.degrees(math.asin(p.lighting_direction[2])),p.geometric_elevation)
    def test_refraction_is_optional_and_never_changes_light(self):
        p=APPROX.position(T,O);q=azl.SolarModel(time_policy='utc-approx',refraction=azl.SolarRefraction()).position(T,O)
        self.assertEqual(p.fixed,q.fixed);self.assertEqual(p.lighting_direction,q.lighting_direction)
        self.assertGreater(q.elevation,p.elevation)
        f=azl.SolarRefraction();self.assertAlmostEqual(f.correction(0),1735/3600)
        self.assertEqual(f.correction(-2),0);self.assertEqual(f.correction(90),0)
        self.assertEqual(azl.SolarRefraction(0).correction(0),0)
        with self.assertRaises(ValueError):azl.SolarRefraction(1200)
    def test_aberration_switch_is_small_and_explicit(self):
        a=APPROX.position(T);b=azl.SolarModel(time_policy='utc-approx',aberration=False).position(T)
        self.assertAlmostEqual(b.ecliptic_longitude-a.ecliptic_longitude,20.49/3600/(a.distance_m/AU_METRES))
        self.assertFalse(b.aberration)
    def test_terminator_is_closed_and_perpendicular_to_light(self):
        s=APPROX.position(T);g=s.terminator(samples=73)
        self.assertEqual(g.coordinates[0],g.coordinates[-1])
        for p in g.coordinates:self.assertAlmostEqual(dot(vector(*p),s.fixed_direction),0,places=12)
        for n in (True,16,4098):
            with self.assertRaises(ValueError):s.terminator(samples=n)
    def test_seasons_and_bounded_daily_paths(self):
        seasons=APPROX.seasons(2025)
        for (name,t),target in zip(seasons.items(),(0,90,180,270)):
            difference=(APPROX.position(t).ecliptic_longitude-target+180)%360-180
            self.assertLess(abs(difference),.000003)
        path=APPROX.path([T+timedelta(hours=i) for i in range(25)],O)
        self.assertEqual(len(path.mesh().vertices),50);self.assertEqual(len(path.mesh().triangles),48)
        with self.assertRaises(ValueError):APPROX.path([T,T],O)
        with self.assertRaises(ValueError):APPROX.path(iter([T,T+timedelta(hours=1)]),O)
        with self.assertRaises(ValueError):azl.SolarPath([path.positions[0]]*2,O)
        with self.assertRaises(ValueError):path.mesh(width=1000)
    def test_normal_events_and_root_residual(self):
        e=APPROX.events(T.date(),O)
        self.assertEqual(e.status,'crossings');self.assertTrue(e.sunrise<e.transit<e.sunset)
        for t in (e.sunrise,e.sunset):self.assertLess(abs(APPROX.position(t,O).geometric_elevation+5/6),.001)
        self.assertLess(abs(APPROX.position(e.transit,O).hour_angle),.001)
        self.assertTrue(all(v>0 for v in e.estimated_model_timing_seconds))
    def test_polar_day_and_night_no_fabricated_rises(self):
        for lat,status in ((90,'always_above'),(-90,'always_below')):
            e=APPROX.events(T.date(),azl.SolarObserver(0,lat))
            self.assertEqual(e.status,status);self.assertIsNone(e.sunrise);self.assertIsNone(e.sunset)
    def test_horizon_and_refraction_event_conventions(self):
        a=APPROX.events(T.date(),O);b=APPROX.events(T.date(),azl.SolarObserver(O.longitude,O.latitude,horizon=2))
        self.assertGreater(b.sunrise,a.sunrise);self.assertLess(b.sunset,a.sunset)
        c=azl.SolarModel(time_policy='utc-approx',refraction=azl.SolarRefraction()).events(T.date(),O)
        self.assertEqual(a,c)
        with self.assertRaises(TypeError):APPROX.events(T,O)
    def test_civil_day_uses_explicit_zone(self):
        e=APPROX.events(T.date(),O,zone=timezone(timedelta(hours=-3)))
        self.assertEqual(e.start.hour,3);self.assertEqual(e.end-e.start,timedelta(days=1))
        with self.assertRaises(ValueError):APPROX.events(T.date(),O,zone=None)
    def test_grazing_is_reported_without_precision_claim(self):
        obs=azl.SolarObserver(0,90,horizon=APPROX.position(T,azl.SolarObserver(0,90)).geometric_elevation+5/6)
        self.assertEqual(APPROX.events(T.date(),obs).status,'grazing_or_uncertain')

class SolarArtists(unittest.TestCase):
    def setUp(self):self.s=APPROX.position(T,O);self.next=APPROX.position(T+timedelta(hours=3),O)
    def test_optional_attached_editable_visible_artist(self):
        fig,ax=azl.subplots();self.assertFalse(any(getattr(l,'_solar_artist',False) for l in ax.layers))
        extent=ax.get_extent();sun=ax.sun(self.s,annotation='Sun',annotation_style={'fontsize':10});sun.set_picker(True)
        self.assertEqual(ax.get_extent(),extent);self.assertIs(sun.axes,ax)
        sun.set_position(self.next);self.assertEqual(sun.get_position(),self.next)
        sun.set_visible(False);self.assertFalse(sun.get_visible());sun.set_visible(True)
        self.assertIn('Sun',fig.to_svg());sun.set_annotation(None);sun.remove();self.assertIsNone(sun.axes)
    def test_failed_observer_update_is_atomic(self):
        _,ax=azl.subplots();sun=ax.sun(self.s);before=sun.data
        with self.assertRaises(ValueError):sun.set_position(APPROX.position(T,azl.SolarObserver(0,0)))
        self.assertIs(sun.data,before);self.assertEqual(sun.state,self.s)
    def test_point_picking_retains_feature_identity_and_hides(self):
        from types import SimpleNamespace
        fig,ax=azl.subplots();sun=ax.sun(self.s);sun.set_picker(3)
        from azimlib.navigation import viewport_from_metadata
        scene=fig.canvas.draw();vp=viewport_from_metadata(ax.projection,scene.maps[0]);x,y=vp.project(*self.s.subsolar)
        event=SimpleNamespace(canvas=fig.canvas,x=x,y=scene.height-y,inaxes=ax)
        hit,properties=sun.contains(event);self.assertTrue(hit);self.assertEqual(properties['features'][0].id,'sun')
        sun.set_visible(False);self.assertFalse(sun.contains(event)[0])
    def test_night_mask_and_terminator_share_geometry(self):
        _,ax=azl.subplots();shade=ax.nightshade(self.s,step=15);old=shade.get_array()
        self.assertTrue(any(v is None for v in old));self.assertTrue(any(v==1 for v in old))
        shade.set_position(self.next);self.assertNotEqual(old,shade.get_array())
        term=ax.solar_terminator(self.s);self.assertEqual(term.data[0].geometry,self.s.terminator())
        with self.assertRaises(ValueError):term.set_position(azl.SunDirection(0,40,O))
        with self.assertRaises(ValueError):ax.nightshade(self.s,step=.1)
        with self.assertRaises(TypeError):shade.set_position(None)
    def test_temporal_binding_preserves_artist_extent_and_frames(self):
        fig,ax=azl.subplots();sun=ax.sun(self.s);extent=ax.get_extent();series=TemporalSeries([T,T+timedelta(hours=3)],[self.s,self.next])
        binding=series.bind(sun);self.assertIs(binding.apply(1),sun);self.assertEqual(ax.get_extent(),extent)
        self.assertEqual(sun.state,self.next)
        with self.assertRaises(ValueError):series.bind(sun,scale='frame')
        with self.assertRaises(ValueError):TemporalSeries([T],[self.next]).bind(sun)
        sun.remove()
        with self.assertRaises(RuntimeError):binding.apply(0)
    def test_time_setters_require_explicit_clock_configuration(self):
        _,ax=azl.subplots();sun=ax.sun(self.s,model=APPROX);sun.set_time(T+timedelta(hours=3));self.assertEqual(sun.state,self.next)
        sun.set_manual(90,30);self.assertIsInstance(sun.state,azl.SunDirection)
        _,ax=azl.subplots();strict=ax.sun(self.s)
        with self.assertRaises(ValueError):strict.set_time(T)
    def test_sky_mesh_and_camera_preserved_on_update(self):
        fig,ax=azl.subplots(subplot_kw={'projection':'3d'},figsize=(3,3));sun=ax.sun(self.s,model=APPROX)
        camera=ax.camera;self.assertEqual(len(sun.mesh.triangles),24)
        series=TemporalSeries([T,T+timedelta(hours=3)],[self.s,self.next]);series.bind(sun).apply(1)
        self.assertEqual(ax.camera,camera);self.assertEqual(sun.state,self.next)
        self.assertIn('svg',fig.to_svg());sun.set_visible(False)
        with self.assertRaises(ValueError):ax.sun(APPROX.position(T,azl.SolarObserver(20,20)))
        with self.assertRaises(ValueError):ax.nightshade(self.s)
    def test_daily_sky_path_is_an_editable_surface(self):
        fig,ax=azl.subplots(subplot_kw={'projection':'3d'});path=APPROX.path([T,T+timedelta(hours=1)],O)
        artist=ax.sun_path(path);self.assertEqual(len(artist.mesh.triangles),2);artist.set_color('red');artist.set_visible(False)
        with self.assertRaises(ValueError):azl.subplots()[1].sun_path(path)
    def test_exact_horizon_cells_have_no_visible_area(self):
        from azimlib.projections import Orthographic
        _,ax=azl.subplots();shade=ax.nightshade(self.s)
        self.assertFalse(shade._visible_cell(Orthographic(),90,120,-30,30))
        self.assertFalse(shade._visible_cell(Orthographic(),-120,-90,0,30))
        self.assertTrue(shade._visible_cell(Orthographic(),60,90,-30,30))
        self.assertTrue(shade._visible_cell(Orthographic(central_latitude=90),0,30,60,90))
    def test_default_solar_label_flips_inward_near_right_edge(self):
        fig,ax=azl.subplots(figsize=(4,3));ax.set_extent((-20,20,-20,20))
        state=azl.SunDirection(0,90,azl.SolarObserver(19,0))
        ax.sun(state,annotation='Solar annotation');scene=fig.to_scene()
        text=next(item for item in scene.items if isinstance(item,Text) and item.text=='Solar annotation')
        self.assertEqual(text.style['anchor'],'end');self.assertEqual(text.style['stroke'],'white')
    def test_projection_and_static_exports(self):
        with tempfile.TemporaryDirectory() as folder:
            for projection in ('equirectangular','mercator','orthographic'):
                fig,ax=azl.subplots(projection=projection,figsize=(3,2));ax.sun(self.s,annotation='Solar');ax.solar_terminator(self.s,samples=73);ax.nightshade(self.s,step=30)
                for ext in ('svg','pdf','png'):
                    p=Path(folder)/(projection+'.'+ext);fig.savefig(p);self.assertGreater(p.stat().st_size,100)
    def test_reference_parser_and_angular_metric_use_original_fixture(self):
        import sys
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
        from validate_solar import rows,separation,direction,crossings
        import json
        data=rows(json.dumps({'result':'$$SOE\n 2025-Jun-21 12:00, , , 90, 20, 1, 0,\n$$EOE'}))
        self.assertEqual(data[0][0],T);self.assertEqual(data[0][1],(90,20,1,0))
        self.assertAlmostEqual(separation(direction(359,0),direction(1,0)),2)
        result=crossings([(T,(0,-1)),(T+timedelta(minutes=5),(0,1))],1,0)
        self.assertEqual(result,[(T+timedelta(minutes=2,seconds=30),True)])
