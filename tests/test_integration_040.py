"""Cross-system invariants for the cumulative development tree."""
import importlib.util,io,math,tempfile,unittest
import hashlib
from dataclasses import replace
from itertools import groupby
from pathlib import Path
from datetime import datetime,timedelta,timezone
import azimlib as azl
from pbf_fixture import header,primitive,xml
ROOT=Path(__file__).resolve().parents[1]
def example():
    spec=importlib.util.spec_from_file_location('integrated_example',ROOT/'examples/integration_040.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
class Integrated040(unittest.TestCase):
    def tearDown(self):azl.close('all')
    def test_search_to_routing_to_overlay_and_crs(self):
        demo=example();fig,axes,state=demo.make_city();route=state['route']
        expected=sum(azl.haversine(a,b) for a,b in zip(demo.POINTS,demo.POINTS[1:]))
        self.assertAlmostEqual(route.distance_m,expected,delta=.01)
        self.assertEqual(tuple(key for key,group in groupby(state['clipped'].iter_positions())),((-46.638,-23.55),(-46.635,-23.55),(-46.635,-23.547)))
        self.assertLess(state['crs_max_degrees'],1e-9)
        svg=fig.to_svg();self.assertIn('Offline foot route',svg);self.assertNotIn('<script',svg)
        layer=state['route_layer'];layer.set_visible(False);self.assertFalse(layer.get_visible())
        layer.set_visible(True);self.assertTrue(layer.get_visible())
    def test_independent_xml_pbf_inputs_reach_same_urban_route(self):
        demo=example();records=[dict(kind='node',id=i+1,coordinates=p,tags={}) for i,p in enumerate(demo.POINTS)]
        records.append(dict(kind='way',id=10,refs=(1,2,3),tags={'highway':'residential'}))
        raw=header()+primitive(records)
        with azl.OSMIndex(raw) as index:
            source=replace(demo.data()[0].source,sha256=hashlib.sha256(raw).hexdigest())
            graph=azl.RoadGraph.from_osm_index(index,source=source,profile=azl.RoutingProfile('foot'))
            route=graph.route(1,3)
        a=azl.read_osm(xml(records));b=azl.read_osm_pbf(raw)
        self.assertEqual(a.to_geojson(),b.to_geojson());self.assertAlmostEqual(route.distance_m,demo.data()[1].distance_m,delta=.02)
    def test_local_solar_volume_time_and_camera_contract(self):
        from azimlib.terrain3d import LocalFrame
        frame=LocalFrame(0,45);observer=azl.SolarObserver(0,45);model=azl.SolarModel(time_policy='utc-approx')
        times=[datetime(2025,m,21,12,tzinfo=timezone.utc) for m in (6,12)]
        fig,ax=azl.subplots(figsize=(1,1),subplot_kw={'projection':'3d'})
        surface=ax.plot_surface([-10,10],[-10,10],[[0,0],[0,0]],color='white')
        light=ax.solar_light(model.position(times[0],observer),model=model,frame=frame,max_edge_m=4)
        volume=ax.plot_volume(azl.VolumeField.from_array([[[0,1],[0,1]],[[0,1],[0,1]]],frame=frame),opacity=.1,step=.5)
        light.bind_volume(volume,shadow_steps=2);fig.to_scene();builds=light.geometry_builds;camera=ax.camera;before=light._factors[id(surface)]
        azl.TemporalSeries(times,[model.position(t,observer) for t in times]).bind(light).apply(1)
        fig.to_scene();self.assertIs(ax.camera,camera);self.assertEqual(builds,light.geometry_builds);self.assertNotEqual(before,light._factors[id(surface)])
        # Independent normalizations may differ by a few representable floats.
        # This is a dimensionless roundoff bound, not an eclipse tolerance.
        for a,b in zip(light.direction,volume.light.direction):
            self.assertLessEqual(abs(a-b),4*max(math.ulp(a),math.ulp(b)))
        pdf=io.BytesIO();fig.savefig(pdf,format='pdf');self.assertTrue(pdf.getvalue().startswith(b'%PDF'))
    def test_seam_global_overlay_and_solar_lunar_layers(self):
        fig,ax=azl.subplots(figsize=(2,2),projection='orthographic',projection_kw={'central_longitude':180})
        region=azl.SphericalRegion.from_geometry(example().box(170,-20,190,20))
        ax.region(region,fill_step=10,facecolor='#3a8caa');now=datetime(2025,6,21,12,tzinfo=timezone.utc)
        sun=azl.SolarModel(time_policy='utc-approx').position(now);moon=azl.LunarModel(time_policy='utc-approx').position(now)
        ax.sun(sun);ax.moon(moon);ax.solar_terminator(sun,samples=73)
        self.assertGreater(region.area(radius=1),0);self.assertIn('<svg',fig.to_svg())
        self.assertNotEqual(sun.fixed.frame.kind,'local');self.assertEqual(moon.fixed.frame,sun.fixed.frame)
if __name__=='__main__':unittest.main()
