"""Pinned icon provenance, faithful geometry, effects and isolation."""
import io,math,json,hashlib,unittest
from pathlib import Path
from unittest.mock import patch
import azimlib as a
from azimlib.scene import RasterIcon,Path as ScenePath
from azimlib.thematic_assets import _arc_points,parse_svg,AssetSource,get_symbol
class Lucide(unittest.TestCase):
 def tearDown(self):a.close('all')
 def test_pinned_raw_files_and_catalog_integrity(self):
  root=Path(__file__).resolve().parents[1];m=json.loads((root/'src/azimlib/assets/lucide/manifest.json').read_text('utf8'))
  self.assertEqual(len(m['icons']),30);self.assertEqual(m['version'],'1.61.0')
  self.assertEqual(hashlib.sha256((root/m['license_file']).read_bytes()).hexdigest(),m['license_sha256'])
  for row in m['icons']:
   self.assertEqual(hashlib.sha256((root/'src/azimlib/assets/lucide'/row['file']).read_bytes()).hexdigest(),row['sha256']);self.assertIn(m['commit'],row['source']);self.assertFalse(row['modified'])
 def test_original_and_aliases_remain_identifiable(self):
  self.assertEqual(len(a.symbol_catalog('original')),18);self.assertEqual(len(a.lucide_catalog()),30)
  self.assertEqual(get_symbol('rover').name,'lucide:bot');self.assertEqual(get_symbol('original:rover').name,'rover');self.assertEqual(get_symbol('ivory').source.origin,'azimlib:programmatic-catalog')
  with self.assertRaises(ValueError):get_symbol('lucide:rover')
 def test_no_network_during_parsing_or_render(self):
  with patch('urllib.request.urlopen',side_effect=AssertionError('No implicit network')):
   f,ax=a.subplots(body=a.MOON);ax.symbols([(0,0)],'lucide:rocket');self.assertIn('lucide:rocket',f.to_svg())
 def test_arc_endpoint_and_circular_radius_analytic(self):
  points=_arc_points((1,0),(0,1),1,1,0,0,1)
  self.assertEqual(points[-1],(0,1))
  for x,y in points:self.assertAlmostEqual(x*x+y*y,1,places=12)
  self.assertEqual(_arc_points((0,0),(1,1),0,1,0,0,0),((1,1),))
 def test_compact_arc_flags_and_smooth_curves(self):
  source=AssetSource('own:test','BSD-3-Clause','Kernerian')
  icon=parse_svg(b'<svg viewBox="0 0 24 24" fill="none" stroke="red"><path d="M2 4a2 2 0 002 2C6 8 7 8 8 7s2-2 3 0Q12 9 14 8t3 0"/></svg>',name='test',source=source)
  self.assertGreater(len(icon.parts[0].paths[0]),30)
  with self.assertRaises(ValueError):parse_svg(b'<svg viewBox="0 0 10 10"><path d="M1 1A2 2 0 3 0 2 3"/></svg>',name='bad',source=source)
 def scene(self,**kw):
  f,ax=a.subplots(body=a.MARS);ax.set_extent((-2,2,-2,2));artist=ax.symbols([(0,0)],'lucide:bot',size=24,**kw);return f,artist,f.to_scene()
 def test_default_vectors_stroke_rounding_and_no_effects(self):
  f,s,scene=self.scene();self.assertFalse(any(isinstance(i,RasterIcon) for i in scene.items));self.assertFalse(any(i.style.get('_icon_effect') for i in scene.items));self.assertIn('stroke-linecap="round"',f.to_svg())
 def test_stroke_width_and_halo_are_independent(self):
  f,s,scene=self.scene(stroke_width=1.5,halo=a.IconHalo(width=1.2,alpha=.7));data=[i for o,_,lo,hi in scene._pick_records if o is s for i in scene.items[lo:hi]]
  effects=[i for i in scene.items if i.style.get('_icon_effect')];self.assertTrue(effects);self.assertTrue(all(i not in data for i in effects));self.assertGreater(effects[0].style['stroke_width'],data[0].style['stroke_width'])
 def test_hard_shadow_is_vector_and_soft_is_local_raster(self):
  for blur in (0,1.2):
   f,s,scene=self.scene(shadow=a.IconShadow(blur=blur),halo=a.IconHalo(color='#17232f'))
   icons=[i for i in scene.items if isinstance(i,RasterIcon)];self.assertEqual(len(icons),int(blur>0));self.assertTrue(any(isinstance(i,ScenePath) for i in scene.items));self.assertIn('Lucide',f.to_svg())
   if blur:self.assertLess(icons[0].width*icons[0].height,scene.width*scene.height/4)
   output=io.BytesIO();f.savefig(output,format='pdf');self.assertTrue(output.getvalue().startswith(b'%PDF'))
 def test_effect_validation_and_anchor_invariance(self):
  for factory in (lambda:a.IconHalo(width=-1),lambda:a.IconShadow(blur=9),lambda:a.IconShadow(offset=(100,0)),lambda:a.IconHalo(alpha=2)):
   with self.assertRaises(ValueError):factory()
  f,s,scene=self.scene();base=[i for o,_,lo,hi in scene._pick_records if o is s for i in scene.items[lo:hi]];s.set_halo(a.IconHalo());s.set_shadow(a.IconShadow(blur=1));updated=f.to_scene();front=[i for o,_,lo,hi in updated._pick_records if o is s for i in updated.items[lo:hi]];self.assertEqual(base,front)
 def test_group_clone_keeps_effect_definitions_not_artist(self):
  f,axes=a.subplots(1,2,body=a.MARS);g=axes[0].group();s=g.add(axes[0].symbols([(0,0)],'gold',halo=a.IconHalo(),shadow=a.IconShadow()));clone=g.instantiate(axes[1]);self.assertIsNot(clone.get_children()[0],s);self.assertEqual(clone.get_children()[0].style['icon_halo'],s.style['icon_halo'])
 def test_soft_effect_partially_clipped_icon(self):
  f,ax=a.subplots(body=a.MARS);ax.set_extent((-2,2,-2,2))
  ax.symbols([(2,2)],'bot',size=32,halo=a.IconHalo(),shadow=a.IconShadow(blur=1))
  self.assertTrue(f.to_scene().items)
 def test_style_copy_is_detached_snapshot(self):
  import copy
  f,s,scene=self.scene();snapshot=copy.deepcopy(s.style)
  self.assertIsInstance(snapshot,dict);s.set_halo(a.IconHalo())
  self.assertNotIn('icon_halo',snapshot)
if __name__=='__main__':unittest.main()
