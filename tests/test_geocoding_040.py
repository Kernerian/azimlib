"""Own local search, uncertainty, spherical distances and licensed import gates."""
from dataclasses import replace,FrozenInstanceError
import hashlib,io,json,math
from pathlib import Path
import sqlite3,tempfile,unittest
import random
import tracemalloc
from types import SimpleNamespace

import azimlib as az
from azimlib._geocode_text import normalize_name,tokens,edit_distance
from azimlib import _geocode_geometry as geo

ROOT = Path(__file__).resolve().parents[1]
SOURCE = az.GeocodingSource('synthetic','1','BSD-3-Clause','Kernerian','Own synthetic fixture',
                           'urn:azimlib:synthetic:geocoding-1',hashlib.sha256(b'azimlib-geocoding-fixture-1').hexdigest(),('Own synthetic test data.',))


def record(identifier,name,point=(0.,0.),kind='poi',address=None,geometry=None,aliases=()):
    return az.GeocodingRecord(identifier,kind,(name,*aliases),geometry or az.Geometry('Point',point),
                             SOURCE.id,address or az.Address())


def rectangle(x0,y0,x1,y1): return ((x0,y0),(x1,y0),(x1,y1),(x0,y1),(x0,y0))


class GeocodingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.counter = 0

    def build(self,records,**kwargs):
        self.counter += 1
        index = az.LocalGeocoder.build(self.root/str(self.counter),records,sources=(SOURCE,),**kwargs)
        self.addCleanup(index.close); return index

    def test_display_unicode_aliases_and_token_contract(self):
        index = self.build([record('a','São José',aliases=('Sao Jose','サンジョゼ','東京都庁','CAFÉ')),
                            record('b','Straße'),record('c','Αθήνα'),record('d','Москва')])
        for query,identifier in (('sa\u0303o jose','a'),('ＳＡＯ　ＪＯＳＥ','a'),('サンジョゼ','a'),('東京都庁','a'),('cafe','a'),('STRASSE','b'),('ΑΘΉΝΑ','c'),('Москва','d')):
            with self.subTest(query=query): self.assertEqual(index.search(query)[0].record.id,identifier)
        self.assertEqual(index.search('東京',prefix=True)[0].match,'prefix')
        self.assertEqual(index.search('São José')[0].name,'São José')
        self.assertEqual(normalize_name('Café',accents=True),'café')
        self.assertEqual(tokens('Rue 12-B'),('rue','12','b'))
        self.assertEqual(edit_distance('park','pakr'),2)
        with self.assertRaises(FrozenInstanceError): SOURCE.id='other'

    def test_ambiguity_limit_and_exact_ranking(self):
        index = self.build([record('a','Central Park'),record('b','Central Park',(1,1)),record('c','Central Park West',(2,2))])
        results = index.search('Central Park',limit=1)
        self.assertTrue(results.ambiguous); self.assertTrue(results.truncated); self.assertEqual(results.total,3)
        self.assertEqual(results[0].record.id,'a'); self.assertEqual(results[0].score,120)
        self.assertLess(index.search('Central Park')[2].score,120)
        self.assertFalse(index.search('missing').ambiguous)
        self.assertIn('Coverage',index.search('missing').diagnostics[0])

    def test_fuzzy_is_explicit_and_all_tokens_required(self):
        index = self.build([record('a','Central Park'),record('b','Central Station')])
        self.assertEqual(len(index.search('Centarl Park')),0)
        found = index.search('Centarl Park',fuzzy=True)
        self.assertEqual(found.total,1); self.assertEqual(found[0].match,'approximate')
        self.assertLess(found[0].score,100)
        self.assertEqual(index.search('Central Missing').total,0)
        with self.assertRaises(az.GeocodingLimitError): index.search('a'*129,fuzzy=True)

    def test_literal_house_numbers_and_declared_filters(self):
        records = [record('a','Casa sintética',kind='address',address=az.Address('12-B','Rua Teste',city='São Paulo',country='BR')),
                   record('b','Casa sintética',(1,1),kind='address',address=az.Address('12','Rua Teste',city='Outra',country='BR')),
                   record('c','Casa sintética',(2,2),kind='address',address=az.Address('12-14','Rua Teste',city='São Paulo',country='BR'))]
        index = self.build(records)
        result = index.search(filters={'street':'rua teste','house_number':'12-b','city':'sao paulo'})
        self.assertEqual(result.total,1); self.assertEqual(result[0].record.id,'a')
        self.assertEqual(index.search(filters={'house_number':'13'},interpolate=True).total,0)
        self.assertEqual(index.search('Casa',kinds=('poi',)).total,0)
        with self.assertRaises(ValueError): index.search('Casa',filters={'invented':'x'})

    def test_near_bbox_and_spherical_distances(self):
        index = self.build([record('a','Station',(0,0)),record('b','Station',(.01,0)),record('c','Station',(1,0))])
        found = index.search('Station',near=(.011,0),radius_m=2000)
        self.assertEqual([r.record.id for r in found],['b','a'])
        self.assertAlmostEqual(found[0].distance_m,az.haversine((.011,0),(.01,0)),places=6)
        self.assertEqual(index.search('Station',bbox=(-.001,-.001,.001,.001)).total,1)
        self.assertEqual(index.reverse(0,0,radius_m=0).total,1)
        for kwargs in ({'radius_m':-1},{'radius_m':float('nan')},{'radius_m':True}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError): index.reverse(0,0,**kwargs)

    def test_reverse_street_point_boundary_and_hole(self):
        shape = az.Geometry('Polygon',(rectangle(-2,-2,2,2),rectangle(-.25,-.25,.25,.25)))
        index = self.build([record('a','Boundary',kind='locality',geometry=shape),
                            record('b','Street',kind='street',geometry=az.Geometry('LineString',((-1,0),(1,0)))),
                            record('c','Address',(.1,.1),kind='address',address=az.Address('1','Street'))])
        representative = index.search('Boundary')[0]
        self.assertEqual(representative.precision,'boundary_representative')
        self.assertFalse(-.25<representative.coordinate[0]<.25 and -.25<representative.coordinate[1]<.25)
        found = index.reverse(.5,.5,radius_m=1,kinds=('locality',))
        self.assertTrue(found[0].contains); self.assertEqual(found[0].distance_m,0)
        self.assertEqual(found[0].to_feature(boundary=True).geometry,shape)
        self.assertEqual(index.reverse(0,0,radius_m=10,kinds=('locality',)).total,0)
        street = index.reverse(.2,.01,radius_m=2000,kinds=('street',))[0]
        self.assertEqual(street.precision,'nearest_centerline'); self.assertAlmostEqual(street.coordinate[0],.2,places=6)
        self.assertAlmostEqual(street.distance_m,az.haversine((.2,.01),(.2,0)),places=5)
        self.assertIsNone(street.record.accuracy_m)

    def test_dateline_pole_and_arc_extrema_candidates(self):
        line = az.Geometry('LineString',((-70,70),(70,70)))
        p = geo.at_fraction(line.coordinates,.5)
        index = self.build([record('a','Dateline',(-179.999,0)),record('b','Pole',(120,90)),
                            record('c','Arched road',kind='street',geometry=line),
                            record('d','Wrapped street',kind='street',geometry=az.Geometry('LineString',((179,0),(-179,0))))])
        self.assertEqual(index.reverse(179.999,0,radius_m=300,kinds=('poi',))[0].record.id,'a')
        self.assertEqual(index.reverse(-20,89.999,radius_m=200,kinds=('poi',))[0].record.id,'b')
        self.assertEqual(index.reverse(*p,radius_m=1,kinds=('street',))[0].record.id,'c')
        self.assertEqual(index.reverse(180,0,radius_m=10,kinds=('street',))[0].record.id,'d')

    def endpoints(self):
        first = record('start','Rua Sintética 10',(0,0),'address',az.Address('10','Rua Sintética',city='Cidade Sintética'))
        last = record('end','Rua Sintética 20',(.01,0),'address',az.Address('20','Rua Sintética',city='Cidade Sintética'))
        r = record('range','Rua Sintética',kind='interpolation',address=az.Address(street='Rua Sintética',city='Cidade Sintética'),
                   geometry=az.Geometry('LineString',((0,0),(.005,.002),(.01,0))))
        return first,last,az.AddressRange(r,'start','end',2)

    def test_explicit_interpolation_even_and_no_extrapolation(self):
        first,last,r = self.endpoints(); index = self.build([first,last],ranges=(r,))
        filters = {'street':'Rua Sintética','city':'Cidade Sintética','house_number':'14'}
        self.assertEqual(index.search(filters=filters).total,0)
        result = index.search(filters=filters,interpolate=True)[0]
        self.assertEqual(result.precision,'interpolated'); self.assertEqual(result.match,'interpolated')
        self.assertEqual(result.range_ids,('start','end')); self.assertIsNone(result.record.accuracy_m)
        self.assertEqual(result.record.address.house_number,'14')
        expected = geo.at_fraction(r.record.geometry.coordinates,.4)
        self.assertLess(az.haversine(result.coordinate,expected),1e-8)
        for number in ('9','13','22','14-B','14-16'):
            with self.subTest(number=number):
                self.assertEqual(index.search(filters=dict(filters,house_number=number),interpolate=True).total,0)
        self.assertTrue(index.search(filters=dict(filters,house_number='10'),interpolate=True).ambiguous)
        self.assertTrue(all(v.record.kind!='interpolation' for v in index.reverse(.004,.001,radius_m=10000)))

    def test_interpolation_missing_mismatched_and_descending(self):
        first,last,r = self.endpoints()
        for records,address_range in (([first],r),([first,replace(last,address=replace(last.address,street='Other'))],r),
                                      ([first,last],replace(r,step=3)),([first,last],replace(r,record=replace(r.record,geometry=az.Geometry('LineString',((0,0),(.02,0))))))):
            with self.subTest(records=len(records)),self.assertRaises(ValueError): self.build(records,ranges=(address_range,))
        descending = replace(r,record=replace(r.record,geometry=az.Geometry('LineString',tuple(reversed(r.record.geometry.coordinates)))),start_id='end',end_id='start')
        index = self.build([first,last],ranges=(descending,))
        self.assertEqual(index.search(filters={'street':'Rua Sintética','house_number':'16'},interpolate=True).total,1)

    def test_import_allowlist_privacy_address_opt_in_and_aliases(self):
        features = az.FeatureCollection((az.Feature(az.Geometry('Point',(0,0)),
            {'name':'Local público','name:en':'Public place','alt_name':'Alias;Outro','amenity':'library',
             'addr:housenumber':'12','addr:street':'Rua Teste','phone':'PRIVATE_CONTACT_SENTINEL',
             'email':'PRIVATE_CONTACT_SENTINEL','user':'PRIVATE_EDITOR_SENTINEL','note':'PRIVATE_NOTE_SENTINEL'},'node/1'),
             az.Feature(az.Geometry('LineString',((0,0),(1,0))),{'name':'Rua Teste','highway':'residential'},'way/2')))
        records = tuple(az.records_from_features(features,SOURCE))
        self.assertEqual(records[0].kind,'poi'); self.assertEqual(records[0].address.house_number,'')
        self.assertEqual(records[1].address.street,'Rua Teste')
        index = self.build(az.records_from_features(features,SOURCE,include_addresses=True))
        self.assertEqual(index.search('Public place')[0].record.kind,'address')
        raw = b''.join(p.read_bytes() for p in index.directory.iterdir())
        self.assertNotIn(b'PRIVATE_',raw)
        before = hashlib.sha256(raw).hexdigest(); index.search('Local'); index.reverse(0,0)
        self.assertEqual(hashlib.sha256(b''.join(p.read_bytes() for p in index.directory.iterdir())).hexdigest(),before)

    def test_budgets_cleanup_duplicates_and_no_overwrite(self):
        for kwargs,records in (({'max_records':1},[record('a','One'),record('b','Two')]),
                               ({'max_bytes':65536},[record(str(i),'Station '+str(i),(i/100,0)) for i in range(1000)]),
                               ({'min_free_bytes':10**30},[record('a','One')])):
            with self.subTest(kwargs=kwargs),self.assertRaises(az.GeocodingLimitError): self.build(records,**kwargs)
        self.assertFalse(any(p.name.startswith('.geocode-build-') for p in self.root.iterdir()))
        with self.assertRaises(ValueError): self.build([record('same','One'),record('same','Two')])
        index = self.build([record('a','One')])
        with self.assertRaises(FileExistsError): az.LocalGeocoder.build(index.directory,(),sources=(SOURCE,))
        with self.assertRaises(sqlite3.OperationalError): index._db.execute('DELETE FROM records')
        index.close()
        with self.assertRaises(RuntimeError): index.search('One')

    def test_candidate_overflow_never_claims_uniqueness(self):
        index = self.build([record(str(i),'Common Station',(i/100,0)) for i in range(5)],max_candidates=2)
        for operation in (lambda:index.search('Common'),lambda:index.reverse(0,0,radius_m=100000),lambda:index.search('Comon',fuzzy=True)):
            with self.subTest(operation=operation),self.assertRaises(az.GeocodingLimitError): operation()

    def test_integrity_database_manifest_and_notices(self):
        index = self.build([record('a','Station')]); directory = index.directory; index.close()
        manifest_path = directory/'manifest.json'; original = manifest_path.read_text(encoding='utf8')
        data = json.loads(original); data['sources'][0]['license']='incorrect'; manifest_path.write_text(json.dumps(data),encoding='utf8')
        with self.assertRaises(ValueError): az.LocalGeocoder(directory)
        data = json.loads(original); data['records']=999; manifest_path.write_text(json.dumps(data),encoding='utf8')
        with self.assertRaises(ValueError): az.LocalGeocoder(directory)
        manifest_path.write_text(original,encoding='utf8')
        with (directory/'index.sqlite').open('ab') as stream: stream.write(b'changed')
        with self.assertRaises(ValueError): az.LocalGeocoder(directory)

    def test_invalid_geometry_source_and_query_contracts(self):
        for origin in ('file:///private/data','https://name:credential@example.org/data','https://example.org/data?token=value'):
            with self.subTest(origin=origin),self.assertRaises(ValueError): replace(SOURCE,origin=origin)
        for geometry in (az.Geometry('Point',(181,0)),az.Geometry('Point',(0,0,2)),
                         az.Geometry('LineString',((0,0),(180,0))),az.Geometry('Polygon',(rectangle(-170,-1,170,1),)),
                         az.Geometry('MultiPoint',((0,0),(1,1)))):
            with self.subTest(kind=geometry.type),self.assertRaises(ValueError): self.build([record('a','Invalid',geometry=geometry)])
        index = self.build([record('a','One')])
        for kwargs in ({},{'query':'x','bbox':(1,0,-1,1)},{'query':'x','limit':True},{'query':'x','kinds':('unknown',)}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError): index.search(**kwargs)

    def test_real_licensed_catalog_query_reverse_and_notice(self):
        path = ROOT/'optional-data/urban-sao-paulo-1.0/catalog.json'
        if not path.exists(): self.skipTest('Optional licensed urban catalog absent')
        catalog = az.DatasetCatalog(path)
        index = az.LocalGeocoder.from_catalog(catalog,'urban-sao-paulo',self.root/'real',include_addresses=False)
        self.addCleanup(index.close)
        source = index.sources['urban-sao-paulo']
        self.assertEqual(source.license,'ODbL-1.0'); self.assertTrue(source.notices)
        records = [index._record(r[0]) for r in index._db.execute('SELECT rid FROM records')]
        self.assertGreater(len(records),10)
        street = next(r for r in records if r.kind=='street')
        results = index.search(street.name,kinds=('street',))
        self.assertIn(street.id,{r.record.id for r in results})
        p = geo.representative(street.geometry)[0]
        self.assertTrue(index.reverse(*p,radius_m=1,kinds=('street',)).total)
        self.assertIn('OpenStreetMap',results[0].to_feature().properties['attribution'])

    def test_layer_labels_picking_and_exports(self):
        index = self.build([record('a','Public station',(-46.63,-23.55))])
        results = index.search('Public station')
        fig,ax = az.subplots(figsize=(3,3)); self.addCleanup(lambda:az.close(fig))
        layer = ax.geojson(results.to_features(),color='red',label='Search result')
        layer.set_picker(True); ax.labels(layer,halo='white'); ax.legend()
        self.assertEqual(layer.data.features[0].id,'synthetic:a')
        self.assertEqual(layer.data.features[0].properties['precision'],'source_point')
        scene = fig.to_scene(cull=True,interactive=True)
        from azimlib.scene import Circle
        marker = next(item for owner,_,start,end in scene._pick_records if owner is layer
                      for item in scene.items[start:end] if isinstance(item,Circle))
        event = SimpleNamespace(x=marker.x,y=scene.height-marker.y,canvas=SimpleNamespace(scene=scene,figure=fig))
        hit,properties = layer.contains(event)
        self.assertTrue(hit); self.assertEqual(properties['features'][0].id,'synthetic:a')
        for extension in ('svg','png'):
            with self.subTest(format=extension):
                path = self.root/f'search.{extension}'; fig.savefig(path,dpi=100)
                self.assertGreater(path.stat().st_size,500)
        feature = results[0].to_feature()
        self.assertEqual(feature.geometry.coordinates,(-46.63,-23.55))

    def test_explicit_external_provider_no_implicit_fallback(self):
        index = self.build([record('a','Station')]); calls = []
        def provider(query): calls.append(query); return index.search(query)
        external = az.ExternalGeocoder(provider)
        self.assertEqual(index.search('missing').total,0); self.assertEqual(calls,[])
        self.assertEqual(external.search('Station').total,1); self.assertEqual(calls,['Station'])
        with self.assertRaises(NotImplementedError): external.reverse(0,0)
        with self.assertRaises(TypeError): az.ExternalGeocoder(lambda q:[]) .search('Station')

    def test_spatial_index_matches_brute_force_global_point_oracle(self):
        randomizer = random.Random(90405)
        records = [record(str(i),'Public station',(randomizer.uniform(-180,180),randomizer.uniform(-90,90))) for i in range(150)]
        records += [record('seam','Dateline',(-180,0)),record('pole','Pole',(0,90))]
        index = self.build(records)
        queries = [(randomizer.uniform(-180,180),randomizer.uniform(-90,90),randomizer.uniform(0,3000000)) for _ in range(40)]
        queries += [(180,0,0),(-180,0,0),(120,90,0),(0,0,21000000)]
        for lon,lat,radius in queries:
            with self.subTest(lon=lon,lat=lat,radius=radius):
                expected = {r.id for r in records if az.haversine((lon,lat),r.geometry.coordinates)<=radius+1e-6}
                actual = index.reverse(lon,lat,radius_m=radius,limit=1000)
                self.assertEqual({r.record.id for r in actual},expected)

    def test_pbf_stream_import_preserves_source_and_hash(self):
        from pbf_fixture import header,primitive,scene
        raw = header()+primitive(scene())
        source = replace(SOURCE,sha256=hashlib.sha256(raw).hexdigest())
        with az.OSMIndex(raw,directory=self.root,max_disk_bytes=1024*1024,reserve_free_bytes=0) as osm:
            index = az.LocalGeocoder.from_osm_index(osm,source,self.root/'pbf')
            self.addCleanup(index.close)
            self.assertEqual(index.sources[source.id].sha256,osm.sha256)
            self.assertGreater(index.metadata['records'],0)
            with self.assertRaises(ValueError): az.LocalGeocoder.from_osm_index(osm,SOURCE,self.root/'wrong-pbf')

    def test_short_fuzzy_and_result_model_consistency(self):
        index = self.build([record('a','A'),record('b','AB')])
        self.assertEqual(index.search('X',fuzzy=True).total,1)
        with self.assertRaises(ValueError): az.GeocodingResults((),2,False,True)
        with self.assertRaises(ValueError): replace(index.search('A')[0],source=replace(SOURCE,id='other'))

    def test_generic_reader_chunking_short_reads_limits_and_memory(self):
        from azimlib._readers import binary,xml_root
        class Short(io.BytesIO):
            def read(self,size=-1):
                self.assertion(size)
                return super().read(min(size,7))
            assertion = staticmethod(lambda size:None)
        reader = Short(b'abc'*100)
        reader.assertion = lambda size:self.assertLessEqual(size,65536)
        self.assertEqual(binary(reader,300),b'abc'*100)
        with self.assertRaises(ValueError): binary(Short(b'a'*301),300)
        self.assertEqual(xml_root(io.StringIO('<osm version="0.6"><tag k="café"/></osm>')).tag,'osm')
        with self.assertRaises(TypeError): binary(io.StringIO('text'))
        file = self.root/'small.bin';file.write_bytes(b'x'*1000)
        tracemalloc.start()
        try:
            self.assertEqual(binary(file),b'x'*1000)
            peak=tracemalloc.get_traced_memory()[1]
        finally: tracemalloc.stop()
        self.assertLess(peak,1024*1024)

    def test_address_opt_in_is_boolean_and_null_is_not_an_address(self):
        feature = az.Feature(az.Geometry('Point',(0,0)),{'name':'Public library','amenity':'library','addr:housenumber':None},'library')
        for opt_in in ('false','true',1,None):
            with self.subTest(opt_in=opt_in),self.assertRaises(ValueError):
                tuple(az.records_from_features((feature,),SOURCE,include_addresses=opt_in))
        record = tuple(az.records_from_features((feature,),SOURCE,include_addresses=True))[0]
        self.assertEqual(record.kind,'poi'); self.assertEqual(record.address.house_number,'')
        feature = az.Feature(feature.geometry,dict(feature.properties,**{'addr:housenumber':True}),feature.id)
        with self.assertRaises(ValueError): tuple(az.records_from_features((feature,),SOURCE,include_addresses=True))


if __name__=='__main__': unittest.main()
