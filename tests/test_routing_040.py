"""Original routing fixtures/oracles; no reference GIS/router implementation."""
import hashlib
import io
import json
from pathlib import Path
import random
import tempfile
import threading
import unittest
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor, CancelledError

import azimlib as az
from azimlib._pbf_decode import OSMRecord as R, OSMMember as M
from pbf_fixture import header, primitive, xml


def source(raw=b'synthetic'):
    return az.RoutingSource('routing-test','1','BSD-3-Clause','Kernerian','Own synthetic network',
                            'urn:azimlib:synthetic:routing-tests',hashlib.sha256(raw).hexdigest(),('Synthetic data: BSD-3-Clause',))


def node(i,x,y=0,**tags): return R('node',i,tags,(x,y))
def way(i,refs,**tags): return R('way',i,dict(highway='residential',**tags),refs=refs)
def restriction(i,from_way,to_way,via,kind='no_right_turn',**tags):
    members = [M('way',from_way,'from')]
    members += [M('node',via,'via')] if isinstance(via,int) else [M('way',w,'via') for w in via]
    members += [M('way',to_way,'to')]
    return R('relation',i,dict(type='restriction',restriction=kind,**tags),members=members)


def square():
    return [node(1,0),node(2,.01),node(3,.01,.01),node(4,0,.01),node(5,.02,0),
            way(10,(1,2)),way(20,(2,3)),way(30,(3,4)),way(40,(4,1)),way(50,(2,5))]


def graph(records=None,**options): return az.RoadGraph.from_records(square() if records is None else records,source=source(),**options)
def ids(route): return tuple(step.edge.way_id for step in route.steps)


class RoutingTests(unittest.TestCase):
    def test_units_models_geometry_and_immutable_graph(self):
        g = graph(); r = g.route(1,3)
        self.assertAlmostEqual(r.distance_m,az.haversine((0,0),(.01,0))+az.haversine((.01,0),(.01,.01)),delta=.02)
        self.assertAlmostEqual(r.duration_s,r.distance_m/30*3.6)
        self.assertEqual(r.geometry.type,'LineString')
        self.assertEqual(r.instructions[0].maneuver,'depart')
        self.assertEqual(r.instructions[-1].maneuver,'arrive')
        with self.assertRaises(TypeError): g.nodes[10] = g.nodes[1]
        with self.assertRaises(AttributeError): g.profile = az.RoutingProfile('foot')
        with self.assertRaises(TypeError): g.profile.speeds_kmh['road'] = 2
        with self.assertRaises(TypeError): az.RoadGraph()

    def test_distance_and_time_choose_different_optima(self):
        records = [node(1,0),node(2,.01),node(3,.005,.003),
                   way(10,(1,2),maxspeed='5'),way(20,(1,3,2),maxspeed='100')]
        g = graph(records,profile=az.RoutingProfile(speeds_kmh={'residential':100}))
        self.assertEqual(ids(g.route(1,2)),(10,))
        self.assertEqual(ids(g.route(1,2,objective='time')),(20,20))
        for objective in ('distance','time'):
            a = g.route(1,2,objective=objective); b = g.route(1,2,objective=objective,algorithm='dijkstra')
            self.assertAlmostEqual(a.distance_m,b.distance_m); self.assertAlmostEqual(a.duration_s,b.duration_s)

    def test_geometric_crossings_and_levels_do_not_create_links(self):
        records = [node(1,-.01),node(2,.01),node(3,0,-.01),node(4,0,.01),
                   way(10,(1,2),bridge='yes',layer='1'),way(20,(3,4),tunnel='yes',layer='-1')]
        g = graph(records)
        with self.assertRaises(az.RoutingError): g.route(1,4)
        with self.assertRaisesRegex(az.RoutingError,'Ambiguous'): g.snap((0,0))
        self.assertEqual(g.edges['10:0:1'].tags['bridge'],'yes')
        # Shared IDs are explicit ramps/junctions, even when way levels differ.
        records = [node(1,0),node(2,.01),node(3,.01,.01),way(10,(1,2),layer='1'),way(20,(2,3),layer='0')]
        self.assertEqual(ids(graph(records).route(1,3)),(10,20))

    def test_coincident_distinct_node_ids_stay_disconnected(self):
        g = graph([node(1,0),node(2,.01),node(3,.01),node(4,.02),way(10,(1,2)),way(20,(3,4))])
        with self.assertRaises(az.RoutingError): g.route(1,4)
        with self.assertRaisesRegex(az.RoutingError,'Ambiguous'): g.snap((.01,0))

    def test_oneway_reverse_roundabout_and_mode_override(self):
        for tags,valid in (({'oneway':'yes'},(1,2)),({'oneway':'-1'},(2,1)),({'junction':'roundabout'},(1,2))):
            records = [node(1,0),node(2,.01),way(10,(1,2),**tags)]
            for mode in ('car','bicycle','foot'):
                with self.subTest(tags=tags,mode=mode):
                    g = graph(records,profile=az.RoutingProfile(mode))
                    g.route(*valid)
                    if mode=='foot': g.route(*valid[::-1])
                    else:
                        with self.assertRaises(az.RoutingError): g.route(*valid[::-1])
        g = graph([node(1,0),node(2,.01),way(10,(1,2),oneway='yes',**{'oneway:bicycle':'no'})],profile=az.RoutingProfile('bicycle'))
        g.route(2,1)

    def test_access_hierarchy_barriers_and_privacy(self):
        records = square()+[node(6,.03),way(60,(5,6),access='no',motorcar='yes',note='Private conversation',**{'contact:phone':'not imported'})]
        self.assertIn(60,ids(graph(records).route(1,6)))
        with self.assertRaises(az.RoutingError): graph(records,profile=az.RoutingProfile('foot')).route(1,6)
        for barrier,mode,open_ in (('bollard','car',False),('bollard','foot',True),('wall','foot',False)):
            with self.subTest(barrier=barrier,mode=mode):
                records = [node(1,0),node(2,.01,barrier=barrier),node(3,.02),way(10,(1,2,3))]
                if open_: graph(records,profile=az.RoutingProfile(mode)).route(1,3)
                else:
                    with self.assertRaises(az.RoutingError): graph(records,profile=az.RoutingProfile(mode))
        g = graph(square()+[node(6,.03),way(60,(5,6),access='destination')])
        with self.assertRaises(az.RoutingError): g.route(1,6)
        self.assertNotIn('note',next(e for e in graph(square()).edges.values()).tags)

    def test_speed_units_direction_and_custom_profiles(self):
        g = graph([node(1,0),node(2,.01),way(10,(1,2),maxspeed='20 mph',**{'maxspeed:backward':'10'})],
                  profile=az.RoutingProfile(speeds_kmh={'residential':100}))
        self.assertAlmostEqual(g.edges['10:0:1'].speed_kmh,32.18688)
        self.assertEqual(g.edges['10:0:-1'].speed_kmh,10)
        self.assertGreater(g.route(2,1).duration_s,g.route(1,2).duration_s)
        for value in (-1,0,float('nan'),float('inf'),True):
            with self.subTest(value=value),self.assertRaises(ValueError): az.RoutingProfile(speeds_kmh={'road':value})

    def test_unknown_and_conditional_rules_fail_closed(self):
        for tags in ({'oneway':'reversible'},{'access':'unknown'},{'maxspeed':'signals'},
                     {'access:conditional':'no @ (Mo-Fr)'},{'oneway:bicycle:conditional':'yes @ (wet)'},
                     {'oneway:motor_vehicle:conditional':'yes @ (wet)'},{'motor_vehicle:forward':'no'},
                     {'access:forward:conditional':'no @ (wet)'},{'area':'yes'}):
            mode = 'bicycle' if 'oneway:bicycle:conditional' in tags else 'car'
            with self.subTest(tags=tags),self.assertRaises(az.UnsupportedRoutingRule):
                graph([node(1,0),node(2,.01),way(10,(1,2),**tags)],profile=az.RoutingProfile(mode))
        with self.assertRaises(az.UnsupportedRoutingRule):
            graph(square()+[restriction(90,10,20,2,**{'restriction:conditional':'no_right_turn @ (Mo-Fr)'})])
        relation = R('relation',90,{'type':'restriction','restriction:foot:conditional':'no_right_turn @ (wet)'},
                     members=restriction(90,10,20,2).members)
        with self.assertRaises(az.UnsupportedRoutingRule):
            graph(square()+[relation],profile=az.RoutingProfile('foot'))
        # A pedestrian-only conditional is irrelevant for a car profile.
        graph(square()+[relation])

    def test_via_node_no_only_except_and_mode_restrictions(self):
        g = graph(square()+[restriction(90,10,20,2)])
        self.assertEqual(ids(g.route(1,3)),(40,30))
        g = graph(square()+[restriction(90,10,50,2,'only_straight_on')])
        r = g.route(1,3,via=(2,))
        # A global optimum may approach the stop from another street; it must
        # never leave way 10 for anything but way 50 at this junction.
        self.assertNotEqual(ids(r)[:2],(10,20))
        self.assertEqual(ids(g.route(1,5,via=(2,))),(10,50))
        records = square()+[restriction(90,10,20,2,except_='unused',**{'except':'bicycle'})]
        self.assertEqual(ids(graph(records,profile=az.RoutingProfile('bicycle')).route(1,3,via=(2,))),(10,20))
        # Generic vehicle restrictions do not apply to foot.
        self.assertEqual(ids(graph(square()+[restriction(90,10,20,2)],profile=az.RoutingProfile('foot')).route(1,3,via=(2,))),(10,20))
        relation = R('relation',90,{'type':'restriction','restriction:bicycle':'no_right_turn'},members=restriction(90,10,20,2).members)
        self.assertEqual(ids(graph(square()+[relation]).route(1,3,via=(2,))),(10,20))

    def test_u_turn_is_not_straight_on_on_same_way(self):
        records = [node(1,0),node(2,.01),node(3,.02),way(10,(1,2,3)),restriction(90,10,10,2,'no_u_turn')]
        g = graph(records)
        self.assertEqual(ids(g.route(1,3)),(10,10))
        result = g.route(1,1,via=(2,))
        self.assertEqual([s.edge.id for s in result.steps],['10:0:1','10:1:1','10:1:-1','10:0:-1'])

    def test_via_way_restriction_remembers_history_across_stops(self):
        records = [node(1,0),node(2,.01),node(3,.02),node(4,.03),node(5,.02,.01),
                   way(10,(1,2),oneway='yes'),way(20,(2,3),oneway='yes'),way(30,(3,4),oneway='yes'),
                   way(40,(3,5,4),oneway='yes'),restriction(90,10,30,(20,),'no_straight_on')]
        g = graph(records)
        self.assertEqual(ids(g.route(1,4)),(10,20,40,40))
        self.assertEqual(ids(g.route(1,4,via=(2,3))),(10,20,40,40))
        records[-1] = restriction(90,10,30,(20,),'only_straight_on')
        g = graph(records)
        self.assertEqual(ids(g.route(1,4)),(10,20,30))
        with self.assertRaises(az.RoutingError): g.route(1,5)

    def test_ordered_via_way_chain_and_multisegment_via(self):
        records = [node(i,(i-1)*.01) for i in range(1,7)]
        records += [way(10,(1,2),oneway='yes'),way(20,(2,3,4),oneway='yes'),way(30,(4,5),oneway='yes'),
                    way(40,(5,6),oneway='yes'),restriction(90,10,40,(20,30),'no_straight_on')]
        g = graph(records)
        with self.assertRaises(az.RoutingError): g.route(1,6)
        g.route(2,6)
        with self.assertRaises(az.RoutingLimitError): graph(records,max_rule_states=1)

    def test_snap_partial_edges_direction_and_same_segment(self):
        records = [node(1,0),node(2,.01),node(3,.02),way(10,(1,2,3),oneway='yes')]
        g = graph(records)
        r = g.route((.002,.00001),(.008,-.00001),snap_radius_m=5)
        self.assertAlmostEqual(r.distance_m,az.haversine((.002,0),(.008,0)),delta=1e-6)
        self.assertEqual(len(r.steps),1); self.assertGreater(r.stops[0].distance_m,1)
        self.assertAlmostEqual(r.steps[0].start_fraction,.2)
        with self.assertRaises(az.RoutingError): g.route((.008,0),(.002,0))
        r = g.route((.002,0),(.018,0),via=((.005,0),(.015,0)))
        self.assertAlmostEqual(r.distance_m,az.haversine((.002,0),(.018,0)),delta=1e-6)
        with self.assertRaises(az.RoutingError): g.snap((1,1),radius_m=1)
        with self.assertRaises(az.RoutingError): graph(records).route(g.snap(1),2)

    def test_virtual_splits_do_not_evade_turn_restrictions(self):
        g = graph(square()+[restriction(90,10,20,2)])
        r = g.route((.005,0),3,via=((.008,0),))
        self.assertNotEqual(ids(r)[:3],(10,10,20))
        self.assertEqual(ids(r)[-1],30)

    def test_snapping_dateline_polar_and_brute_force(self):
        records = [node(1,179.9,80),node(2,-179.9,80),way(10,(1,2))]
        g = graph(records)
        snap = g.snap((180,80),radius_m=100)
        self.assertLess(snap.distance_m,2); self.assertAlmostEqual(snap.fraction,.5,places=7)
        r = g.route(1,snap); self.assertAlmostEqual(r.distance_m,g.edges['10:0:1'].distance_m/2,places=6)
        random_ = random.Random(42)
        records = []
        for i in range(20):
            x,y = random_.uniform(-.1,.1),random_.uniform(-.1,.1)
            records += [node(i*2+1,x,y),node(i*2+2,x+.001,y+.001),way(i+1,(i*2+1,i*2+2))]
        g = graph(records)
        from azimlib._geocode_geometry import nearest
        for _ in range(30):
            p = (random_.uniform(-.1,.1),random_.uniform(-.1,.1))
            expected = min(nearest(az.Geometry('LineString',e.geometry),p)[1] for e in g.edges.values())
            self.assertAlmostEqual(g.snap(p,radius_m=50000).distance_m,expected,places=6)

    def test_small_random_network_all_pairs_against_floyd_oracle(self):
        random_ = random.Random(67)
        for trial in range(8):
            records = [node(i+1,random_.uniform(0,.1),random_.uniform(0,.1)) for i in range(8)]
            records += [way(i+1,(i+1,i+2),oneway='yes') for i in range(7)]
            for i in range(15):
                a,b = random_.sample(range(1,9),2); records.append(way(100+i,(a,b),oneway='yes',maxspeed=str(random_.randint(5,30))))
            g = graph(records)
            for objective in ('distance','time'):
                distances = {(i,j):0. if i==j else float('inf') for i in range(1,9) for j in range(1,9)}
                for e in g.edges.values():
                    distances[e.start,e.end] = min(distances[e.start,e.end],e.distance_m if objective=='distance' else e.duration_s)
                for k in range(1,9):
                    for i in range(1,9):
                        for j in range(1,9): distances[i,j] = min(distances[i,j],distances[i,k]+distances[k,j])
                for (a,b),value in distances.items():
                    with self.subTest(trial=trial,objective=objective,a=a,b=b):
                        if value==float('inf'):
                            with self.assertRaises(az.RoutingError): g.route(a,b,objective=objective)
                        else:
                            result = g.route(a,b,objective=objective)
                            self.assertAlmostEqual(result.distance_m if objective=='distance' else result.duration_s,value,places=6)

    def test_corruption_budgets_and_cancellation(self):
        for records in ([node(1,0),node(1,.01)], [node(1,0),way(1,(1,2))],
                        [node(1,0),node(2,0),way(1,(1,2))], [node(1,0),node(2,180),way(1,(1,2))]):
            with self.subTest(records=records),self.assertRaises(az.RoutingError): graph(records)
        for limits in ({'max_records':2},{'max_edges':1},{'max_bytes':10}):
            with self.subTest(limits=limits),self.assertRaises(az.RoutingLimitError): graph(**limits)
        g = graph()
        with self.assertRaises(az.RoutingLimitError): g.route(1,3,max_states=1)
        with self.assertRaises(az.RoutingLimitError): g.snap((0,0),max_candidates=1)
        event = threading.Event(); event.set()
        with self.assertRaises(CancelledError): g.route(1,3,cancel=event)
        for options in ({'objective':'fuel'},{'algorithm':'other'},{'via':iter([2])},{'max_states':True}):
            with self.subTest(options=options),self.assertRaises(ValueError): g.route(1,3,**options)

    def test_persistence_hash_notices_privacy_and_rebuild(self):
        records = square()+[node(6,.03,**{'note':'private fixture','contact:email':'fixture@example.invalid'}),
                            way(60,(5,6),oneway='yes',**{'note':'not retained','contact:phone:conditional':'not retained'})]
        g = graph(records)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'graph'; digest = g.save(path,max_bytes=1024*1024)
            raw = (path/'graph.json').read_bytes()
            self.assertEqual(digest,hashlib.sha256(raw).hexdigest())
            self.assertNotIn(b'private fixture',raw); self.assertNotIn(b'contact:',raw)
            self.assertIn(b'Synthetic data: BSD-3-Clause',raw)
            loaded = az.RoadGraph.load(path)
            self.assertAlmostEqual(loaded.route(1,6).distance_m,g.route(1,6).distance_m)
            self.assertEqual(loaded.source,g.source)
            with self.assertRaises(FileExistsError): g.save(path)
            with self.assertRaises(az.RoutingLimitError): g.save(Path(temp)/'small',max_bytes=10)
            self.assertFalse((Path(temp)/'small').exists())
            (path/'graph.json').write_bytes(raw+b' ')
            with self.assertRaises(az.RoutingError): az.RoadGraph.load(path)

    def test_xml_pbf_topology_and_restrictions_equivalent(self):
        records = square()+[restriction(90,10,20,2)]
        rows = [dict(kind=r.kind,id=r.id,tags=dict(r.tags),coordinates=r.coordinates,refs=r.refs,
                     members=[(m.kind,m.id,m.role) for m in r.members]) for r in records]
        raw = xml(rows)
        a = az.RoadGraph.from_osm(raw,source=source(raw))
        pbf = header()+primitive(rows)
        with az.OSMIndex(io.BytesIO(pbf)) as index:
            b = az.RoadGraph.from_osm_index(index,source=source(pbf))
            self.assertEqual(tuple(a.edges),tuple(b.edges))
            self.assertAlmostEqual(a.route(1,3).distance_m,b.route(1,3).distance_m)
            with self.assertRaises(az.RoutingError): az.RoadGraph.from_osm_index(index,source=source())
        with self.assertRaises(az.RoutingError): az.RoadGraph.from_osm(raw,source=source())
        with self.assertRaises(ValueError): az.RoadGraph.from_osm(b'<!DOCTYPE osm><osm version="0.6"/>',source=source(b'<!DOCTYPE osm><osm version="0.6"/>'))

    def test_real_licensed_catalog_and_all_pairs_subset(self):
        path = Path(__file__).resolve().parents[1]/'optional-data/urban-sao-paulo-1.0/catalog.json'
        if not path.exists(): self.skipTest('Optional licensed dataset is absent')
        catalog = az.DatasetCatalog(path)
        for mode in ('car','bicycle','foot'):
            with self.subTest(mode=mode):
                g = az.RoadGraph.from_catalog(catalog,'urban-sao-paulo',profile=az.RoutingProfile(mode))
                self.assertEqual(g.source.license,'ODbL-1.0'); self.assertTrue(g.source.notices)
                edge = next(iter(g.edges.values()))
                self.assertAlmostEqual(g.route(edge.start,edge.end).distance_m,edge.distance_m,places=5)

    def test_async_owner_thread_map_picking_and_playback(self):
        g = graph()
        fig,ax = az.subplots(figsize=(6,4))
        with ThreadPoolExecutor(max_workers=1) as executor:
            task = g.submit(executor,1,3)
            result = task.result(timeout=10)
            layer = task.draw(ax,color='red',linewidth=2,label='Network route')
            layer.set_picker(True)
            self.assertEqual(layer.data[0].properties['osm_way_id'],result.steps[0].edge.way_id)
            self.assertTrue(layer.get_visible()); layer.set_visible(False); self.assertFalse(layer.get_visible()); layer.set_visible(True)
            future = executor.submit(task.draw,ax)
            with self.assertRaises(RuntimeError): future.result(timeout=10)
        scene = fig.to_scene(cull=True,interactive=True)
        from azimlib.scene import Path as ScenePath
        primitive_ = next(item for owner,_,start,end in scene._pick_records if owner is layer
                          for item in scene.items[start:end] if isinstance(item,ScenePath) and item.paths)
        a,b = primitive_.paths[0][:2]
        event = SimpleNamespace(x=(a[0]+b[0])/2,y=scene.height-(a[1]+b[1])/2,
                                canvas=SimpleNamespace(scene=scene,figure=fig))
        hit,properties = layer.contains(event)
        self.assertTrue(hit)
        self.assertTrue(any('osm_way_id' in feature.properties for feature in properties['features']))
        ax.legend(); ax.scale_bar(); ax.grid(False)
        animation = result.playback(ax,frames=5,autoplay=False,s=24)
        animation.seek(4)
        self.assertEqual(tuple(animation.route_marker.get_offsets()[0]),result.stops[-1].coordinate)
        self.assertEqual(result.sample(0),result.stops[0].coordinate)
        self.assertEqual(result.sample(result.duration_s+1),result.stops[-1].coordinate)
        self.assertGreater(len(fig.to_svg()),1000)
        animation.close(); az.close(fig)

    def test_multi_from_no_entry_and_inaccessible_only_turn(self):
        relation = R('relation',90,{'type':'restriction','restriction':'no_entry'},members=(
            M('way',10,'from'),M('way',30,'from'),M('node',2,'via'),M('way',50,'to')))
        # Make both from-ways enter node 2.
        records = [node(1,0),node(2,.01),node(3,.01,.01),node(4,.02),
                   way(10,(1,2)),way(30,(3,2)),way(50,(2,4)),relation]
        g = graph(records)
        with self.assertRaises(az.RoutingError): g.route(1,4)
        g.route(2,4)
        records = square()+[restriction(90,10,50,2,'only_straight_on')]
        records[9] = way(50,(2,5),access='no')
        with self.assertRaises(az.UnsupportedRoutingRule): graph(records)

    def test_stationary_route_and_geocoding_coordinates(self):
        g = graph()
        point = SimpleNamespace(coordinate=(.005,0))
        route = g.route(point,point)
        self.assertEqual(route.geometry.type,'Point')
        self.assertEqual(route.distance_m,0)
        self.assertEqual(route.duration_s,0)
        self.assertEqual(route.sample(100),route.stops[0].coordinate)
        self.assertEqual(route.to_features()[0].geometry.type,'Point')
        with self.assertRaises(ValueError): route.sample(-1)

    def test_persistence_retains_excluded_reference_topology(self):
        records = square()+[node(6,.03),way(60,(5,6),access='private'),restriction(90,50,60,5)]
        g = graph(records)
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)/'graph'
            g.save(target)
            loaded = az.RoadGraph.load(target)
            self.assertEqual(tuple(g.edges),tuple(loaded.edges))
            with self.assertRaises(az.RoutingError): loaded.route(1,6)
            manifest = target/'manifest.json'
            manifest.write_text('{"schema":1,"schema":1}',encoding='utf8')
            with self.assertRaises(az.RoutingError): az.RoadGraph.load(target)


if __name__=='__main__': unittest.main()
