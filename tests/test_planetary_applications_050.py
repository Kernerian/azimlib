"""Explicit sourced geology, finite exploration and physically honest comparisons."""
import io,json,hashlib,tempfile,unittest,dataclasses
from pathlib import Path
import azimlib as a
S=a.AssetSource('synthetic:own','BSD-3-Clause','Kernerian')
class Applications(unittest.TestCase):
 def tearDown(self):a.close('all')
 def catalog(self,body=a.MARS):
  context=a.PlanetaryContext.for_body(body);names=(a.FeatureName('Synthetic crater','en','Own fictitious scenario'),)
  feature=a.SurfaceFeature('test','crater',a.Geometry('Point',(0,0)),names,S,'synthetic epoch','synthetic',uncertainty_m=100)
  return a.FeatureCatalog(context,(feature,),S)
 def test_nomenclature_and_source_are_not_style_or_mission_truth(self):
  c=self.catalog();data=c.data();self.assertEqual(data.context,c.context);self.assertEqual(data.features[0].properties['status'],'synthetic');self.assertEqual(c.features[0].uncertainty_m,100)
  with self.assertRaises(dataclasses.FrozenInstanceError):c.features[0].epoch='new'
  with self.assertRaises(ValueError):a.FeatureName('name','','authority')
  with self.assertRaises(ValueError):dataclasses.replace(c.features[0],uncertainty_m=-1)
  with self.assertRaises(ValueError):a.FeatureCatalog(c.context,c.features*2,S)
 def test_catalog_real_artists_labels_picking_and_wrong_body(self):
  c=self.catalog();f,ax=a.subplots(body=a.MARS);ax.set_extent((-5,5,-5,5));g=c.draw(ax);self.assertEqual(len(g.get_children()),2);self.assertIn('Synthetic crater',f.to_svg());s=g.get_children()[0];s.set_picker(True);self.assertEqual(s.options['surface_feature'],c.features[0])
  _,moon=a.subplots(body=a.MOON)
  with self.assertRaises(ValueError):c.draw(moon)
 def test_catalog_local_reader_hash_license_context_and_limit(self):
  value={'type':'FeatureCollection','features':[{'type':'Feature','id':'1','geometry':{'type':'Point','coordinates':[1,2]},'properties':dict(name='Site',language='en',authority='Own',kind='instrument',epoch='test',status='synthetic')} ]}
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'own.json';raw=json.dumps(value).encode();path.write_bytes(raw);source=dataclasses.replace(S,sha256=hashlib.sha256(raw).hexdigest())
   c=a.FeatureCatalog.from_file(path,context=a.PlanetaryContext.for_body(a.MOON),source=source);self.assertIs(c.context.body,a.MOON)
   with self.assertRaises(ValueError):a.FeatureCatalog.from_file(path,context=c.context,source=S)
   with self.assertRaises(ValueError):a.FeatureCatalog.from_file(path,context=c.context,source=source,max_bytes=10)
   path.write_bytes(raw+b' ')
   with self.assertRaises(ValueError):a.FeatureCatalog.from_file(path,context=c.context,source=source)
 def test_polygon_fault_and_point_same_group_on_three_worlds(self):
  for body in (a.MARS,a.MOON,a.VENUS):
   c=self.catalog(body);name=(a.FeatureName('Synthetic unit','en','Own'),);area=a.SurfaceFeature('area','geological-unit',a.Geometry('Polygon',(((-3,-3),(3,-3),(3,3),(-3,3),(-3,-3)),)),name,S,'test','synthetic',classification='Author unit')
   fault=a.SurfaceFeature('fault','fault',a.Geometry('LineString',((-2,-1),(2,1))),name,S,'test','synthetic');catalog=a.FeatureCatalog(c.context,(*c.features,area,fault),S);f,ax=a.subplots(body=body);ax.set_extent((-5,5,-5,5));g=catalog.draw(ax,style=lambda f:dict(color='#317f8f',alpha=.5));self.assertTrue({'thematic_symbols','thematic_region','thematic_path','labels'}<={l.kind for l in g.get_children()});self.assertIn('<path',f.to_svg())
 def sequence(self,artist,values,mode='illustrative-plan',unit='degree'):
  return a.ExplorationSequence(a.TemporalSeries(range(len(values)),values,unit='day'),artist.get_context(),S,mode,'position',unit)
 def test_sequence_validates_all_frames_before_mutating(self):
  f,ax=a.subplots(body=a.MARS);s=ax.symbols([(0,0)],'bot');old=s.data
  with self.assertRaises(ValueError):self.sequence(s,[[(1,1)],[(1,92)]]).bind(s)
  self.assertEqual(s.data,old)
  with self.assertRaises(ValueError):self.sequence(s,[[(1,1)]],unit='m').bind(s)
 def test_sequence_missing_frames_exact_selection_and_removal(self):
  f,ax=a.subplots(body=a.MARS);s=ax.symbols([(0,0)],'bot');binding=self.sequence(s,[[(0,0)],None,[(2,3)]]).bind(s);binding.apply(1);self.assertFalse(s.get_visible());binding.at(2);self.assertEqual(s.data,((2,3),));self.assertTrue(s.get_visible())
  with self.assertRaises(KeyError):binding.at(.5)
  with self.assertRaises(IndexError):binding.apply(3)
  s.remove()
  with self.assertRaises(ValueError):binding.apply(0)
 def test_sequence_modes_do_not_enable_prediction(self):
  f,ax=a.subplots(body=a.MARS);s=ax.symbols([(0,0)])
  with self.assertRaises(a.UnsupportedBodyOperation):self.sequence(s,[[(0,0)]],mode='prediction')
  other=a.PlanetaryContext.for_body(a.MOON)
  with self.assertRaises(ValueError):a.ExplorationSequence(a.TemporalSeries([0],[[(0,0)]],unit='day'),other,S,'simulation','position','degree').bind(s)
 def test_animation_reuses_existing_artists_and_restores_requested_frame(self):
  f,ax=a.subplots(body=a.MARS);s=ax.symbols([(0,0)],'bot');binding=self.sequence(s,[[(0,0)],[(1,1)],[(2,2)]]).bind(s);ani=binding.animation(autoplay=False);self.assertEqual(binding.index,0);ani.seek(2,draw=False);self.assertEqual(binding.index,2);self.assertIs(ax.layers[0],s);ani.close()
 def test_world_comparison_physical_scale_and_normalized_are_distinct(self):
  from azimlib.locators import _viewport
  for mode in ('physical','normalized'):
   c=a.compare_worlds((a.EARTH,a.MARS),mode=mode);vps=[_viewport(ax) for ax in c.axes]
   if mode=='physical':self.assertAlmostEqual(vps[0].scale/vps[1].scale,1,places=6)
   else:self.assertNotAlmostEqual(vps[0].scale/vps[1].scale,1,places=2)
   self.assertNotEqual(c.axes[0].get_context(),c.axes[1].get_context());self.assertIn('physical scale' if mode=='normalized' else 'physical reference',c.figure.to_svg())
 def test_comparison_refuses_unknown_modes_and_locator_cross_body(self):
  with self.assertRaises(ValueError):a.compare_worlds((a.MOON,a.MARS),mode='auto')
  c=a.compare_worlds((a.MOON,a.MARS))
  with self.assertRaises(ValueError):c.axes[0].locator(c.axes[1])
if __name__=='__main__':unittest.main()
