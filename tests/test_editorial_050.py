"""Numerical/geometric and lifecycle contracts for editorial maps."""
import io,math,unittest
import azimlib as a
from azimlib.scene import Path as ScenePath
from azimlib.legend_layout import entries
class Editorial(unittest.TestCase):
 def tearDown(self):a.close('all')
 def source(self,body=a.MARS):
  f,ax=a.subplots(body=body);ax.set_extent((-20,20,-10,10));return f,ax
 def test_inset_context_default_independent_body_and_ownership(self):
  f,ax=self.source();one=ax.inset((.7,.1,.25,.25));two=ax.inset((.1,.1,.25,.25),body=a.MOON)
  self.assertEqual(one.get_context(),ax.get_context());self.assertIs(two.get_body(),a.MOON);self.assertIs(one._parent_axes,ax)
  with self.assertRaises(ValueError):two.locator(ax)
 def test_footprint_matches_inverse_corners_and_updates(self):
  f,ax=self.source();g=a.viewport_footprint(ax);lons=[p[0] for p in g.coordinates];lats=[p[1] for p in g.coordinates]
  self.assertAlmostEqual(min(lons),-20,places=6);self.assertAlmostEqual(max(lats),10,places=6)
  child=ax.inset();child.set_extent((-180,180,-90,90));l=child.locator(ax,shade=True);first=l.footprint();ax.pan(5,0);self.assertNotEqual(first,l.footprint());self.assertIn('<path',f.to_svg())
 def test_static_locator_is_frozen_and_same_source_data_unchanged(self):
  f,ax=self.source();child=ax.inset();child.set_extent((-180,180,-90,90));l=child.locator(ax,sync=False);g=l.footprint();ax.pan(3,0);self.assertEqual(g,l.footprint())
 def test_orthographic_visible_limb_inverse_and_antimeridian(self):
  f,ax=a.subplots(body=a.MOON,projection='orthographic');ax.set_extent((-180,180,-90,90));g=a.viewport_footprint(ax)
  self.assertGreater(len(g.coordinates),200);self.assertTrue(all(math.isfinite(v) for p in g.coordinates for v in p));self.assertGreater(max(abs(p[1]) for p in g.coordinates),89)
  f2,b=self.source();b.set_extent((160,180,-10,10));child=b.inset();child.set_extent((-180,180,-90,90));child.locator(b,mask_outside=True);f2.to_scene()
 def test_link_forward_bidirectional_cycles_and_cleanup(self):
  f,ax=self.source();b=ax.inset();c=ax.inset((.05,.05,.2,.2));link=ax.link_view(b,bidirectional=True);ax.pan(2,0);self.assertEqual(ax.get_extent(),b.get_extent());b.zoom(2);self.assertEqual(ax.get_extent(),b.get_extent())
  second=b.link_view(c)
  with self.assertRaises(ValueError):c.link_view(ax)
  b.remove();self.assertFalse(link.active);self.assertFalse(second.active)
 def test_legend_sections_icons_gradients_and_flow_scale(self):
  f,ax=self.source();s=ax.symbols([(0,0)],'rover',category='Rover',halo=a.IconHalo());r=a.RegionDefinition.polygon([(-5,-5),(5,-5),(5,5),(-5,5)],context=ax.get_context());g=ax.region(r,gradient=a.LinearGradient((-5,0),(5,0),('red','blue'),'decorative'),label='Effect')
  scale=a.FlowScale(0,100,'t/year');keys=scale.keys((20,80));legend=ax.legend(sections=[a.LegendSection('Sites',(s,)),a.LegendSection('Areas',(g,)),a.LegendSection('Flow',keys)],ncols=2)
  labels=[text for text,symbols in entries(legend)];self.assertIn('Sites',labels);self.assertIn('80 t/year',labels)
  svg=f.to_svg();self.assertTrue('lucide:bot' in svg);self.assertIn('Sites',svg);self.assertIn('font-weight="bold"',svg)
  with self.assertRaises(ValueError):scale.width(101)
  path=a.CartographicPath.polyline([(-1,0),(1,0)],context=ax.get_context());p=ax.flow_path(path,20,scale=scale);self.assertEqual(p.options['flow_unit'],'t/year');self.assertAlmostEqual(p.style['linewidth'],1.2,places=12)
 def test_theme_precedence_reversal_does_not_add_data(self):
  f,ax=self.source();s=ax.symbols([(0,0)],'gold');before=len(ax.layers);ax.set_theme('historical');self.assertEqual(s.style['color'],'#7b5740');g=ax.group(style={'color':'blue'});g.add(s);self.assertEqual(s.style['color'],'blue');s.set(color='red');self.assertEqual(s.style['color'],'red');g.discard(s);ax.set_theme(None);self.assertEqual(s.style['color'],'red');self.assertEqual(len(ax.layers),before)
  for name in ('atlas','political','physical','scientific','geological','planetary-exploration'):self.assertIsInstance(a.get_theme(name),a.CartographicTheme)
 def test_associated_region_path_labels_context_and_lifecycle(self):
  f,ax=self.source();r=ax.region(a.RegionDefinition.polygon([(-8,-6),(8,-6),(8,6),(-8,6)],context=ax.get_context()));label=r.labels_for('Synthetic region',fontsize=8);self.assertEqual(label.get_context(),ax.get_context());self.assertIn('Synthetic region',f.to_svg());r.set_visible(False);self.assertFalse(label.get_visible());r.remove();self.assertFalse(label.get_visible())
  _,moon=self.source(a.MOON)
  with self.assertRaises(ValueError):moon.labels(a.PlanetaryData(a.FeatureCollection(()),ax.get_context()))
 def test_collision_obstacles_exclusion_scale_and_budget(self):
  from azimlib.label_layout import obstacle_boxes,plan_labels
  f,ax=self.source();s=ax.symbols([(0,0)],'bot',size=40);label=ax.labels(a.PlanetaryData(a.FeatureCollection((a.Feature(a.Geometry('Point',(0,0)),{'name':'Here'}),)),ax.get_context()),offsets=((0,0),),fontsize=8)
  f.to_scene();from azimlib.locators import _viewport
  vp=_viewport(ax);self.assertNotIn((id(label),0),plan_labels(ax,vp));label.options['collision_exclude']=(s,);self.assertIn((id(label),0),plan_labels(ax,vp));label.options['max_span']=1;self.assertNotIn((id(label),0),plan_labels(ax,vp))
  with self.assertRaises(ValueError):ax.labels(a.PlanetaryData(a.FeatureCollection((a.Feature(a.Geometry('Point',(0,0)),{'name':'A'}),)*2),ax.get_context()),max_candidates=1)
 def test_curved_plain_labels_and_complex_text_refusal(self):
  f,ax=self.source();p=ax.cartographic_path(a.CartographicPath.bezier([(-15,-4),(-9,7),(9,7),(15,-4)],context=ax.get_context()),label='Editorial route');p.labels_for('SURFACE ROUTE',placement='curve',fontsize=8);self.assertIn('paint-order',f.to_svg())
  from azimlib.curved_text import curve_candidates
  with self.assertRaises(ValueError):list(curve_candidates(p.definition.geometry,__import__('azimlib.locators',fromlist=['_viewport'])._viewport(ax),'العربية',{'font_size':10}))
 def test_page_auto_manual_dimensions_and_notes(self):
  f=a.figure(figsize=(11,8));page=f.cartographic_page(body=a.MARS,title='Atlas',subtitle='Declared data');page.axes.set_extent((-10,10,-10,10));page.note('Synthetic scenario, no mission inference.');s=page.axes.symbols([(0,0)],'bot',category='Site');page.legend(sections=[a.LegendSection('Sites',(s,))]);first=page.axes.position;self.assertTrue(f.to_scene().items);f.set_size_inches(8,11);f.to_scene();self.assertNotEqual(first,page.axes.position);self.assertIs(page.axes.get_body(),a.MARS)
  stream=io.BytesIO();f.savefig(stream,format='pdf');self.assertTrue(stream.getvalue().startswith(b'%PDF'))
 def test_locator_source_removed_removes_live_target_artist(self):
  f,ax=self.source();b=f.add_axes((.1,.1,.3,.3),body=a.MARS);l=b.locator(ax);ax.remove();self.assertIsNone(l.axes)
 def test_associated_labels_clone_to_new_source_and_remain_independent(self):
  f,ax=self.source();other=ax.inset();g=ax.group();s=g.add(ax.symbols([(0,0)],'bot'));label=g.add(s.labels_for('Site'));clone=g.instantiate(other);cs,cl=clone.get_children();self.assertIs(cl.options['associated_source'](),cs);s.set_visible(False);self.assertFalse(label.get_visible());self.assertTrue(cl.get_visible())
 def test_polar_annulus_has_two_geographic_boundaries(self):
  f,ax=a.subplots(body=a.MARS,projection='stereographic',projection_kw={'central_latitude':90});ax.set_extent((-180,180,55,89));g=a.viewport_footprint(ax);self.assertEqual(g.type,'MultiLineString');self.assertEqual(len(g.coordinates),2);self.assertEqual({p[1] for r in g.coordinates for p in r},{55,89})
if __name__=='__main__':unittest.main()
