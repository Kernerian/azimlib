"""Export fidelity and complete authored examples, without human approval claims."""
import importlib.util,io,sys,unittest
from pathlib import Path
import azimlib as a
class Integrated(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'examples/thematic'))
  spec=importlib.util.spec_from_file_location('editorial_example',root/'examples/thematic/editorial_050.py');cls.editorial=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.editorial)
 def tearDown(self):a.close('all')
 def test_real_atlas_has_locator_sections_curves_and_owned_labels(self):
  f,meta=self.editorial.historical();ax=f.axes[0];self.assertTrue(ax.insets);self.assertTrue(ax._legend['_section_lengths']);self.assertTrue(any(l.kind=='labels' for l in ax.layers));self.assertTrue(any(l.kind=='locator' for l in ax.insets[0].layers));self.assertTrue('Lucide' in f.to_svg());self.assertIn('fictional',str(meta))
 def test_mars_atlas_shared_primitives_and_isolated_contexts(self):
  f,meta=self.editorial.mars();ax=f.axes[0];self.assertEqual(ax.get_body(),a.MARS);self.assertTrue({'thematic_symbols','thematic_region','thematic_path','labels'}<={l.kind for l in ax.layers});self.assertEqual(ax.insets[0].get_context(),ax.get_context());self.assertIn('Synthetic',str(meta))
 def test_pdf_raster_layer_is_one_local_tile_not_page_or_surrounding_vectors(self):
  from azimlib.renderers.pdf import _gradient_tiles
  from azimlib.scene import RasterIcon,Path as ScenePath
  f,ax=a.subplots(body=a.MOON,projection='orthographic');ax.set_extent((-180,180,-90,90));r=a.PlanetaryRaster([[(i/5,j/3,.5,1) for i in range(6)] for j in range(4)],(60,0,-180,0,-45,90),ax.get_context(),a.BodySource('own:test','1','Synthetic RGBA'),'BSD-3-Clause',unit='rgba');ax.raster(r);ax.symbols([(0,0)],'flag');scene=f.to_scene();out=_gradient_tiles(scene)
  tiles=[i for i in out if isinstance(i,RasterIcon)];self.assertEqual(len(tiles),1);self.assertGreater(sum(isinstance(i,ScenePath) for i in out),3);self.assertLess(tiles[0].width*tiles[0].height,scene.width*scene.height);stream=io.BytesIO();f.savefig(stream,format='pdf');self.assertIn(b'/SMask',stream.getvalue())
 def test_no_whole_page_bitmap_from_soft_icon_effect(self):
  f,ax=a.subplots();ax.set_extent((-5,5,-5,5));ax.symbols([(0,0)],'bot',size=20,halo=a.IconHalo(),shadow=a.IconShadow(blur=1));ax.line([(-4,-4),(4,4)],color='red');svg=f.to_svg();self.assertEqual(svg.count('<image '),1);self.assertTrue('<path' in svg);self.assertIn('Copyright',svg)
 def test_no_portable_locator_or_editorial_layout_silent_fallback(self):
  f,ax=a.subplots();child=ax.inset();child.locator(ax)
  with self.assertRaises(a.UnsupportedBodyOperation):f.to_html()
 def test_source_geometry_survives_frame_zoom_labels_exports(self):
  f,ax=a.subplots(body=a.MARS);ax.set_extent((-12,12,-8,8));p=a.CartographicPath.geodesic([(-8,-3),(8,3)],context=ax.get_context());artist=ax.cartographic_path(p,label='Geodesic');artist.labels_for('SURFACE',placement='curve',fontsize=8);original=p.points;length=p.surface_length();f.to_svg();ax.zoom(2);f.to_svg();self.assertEqual(p.points,original);self.assertEqual(artist.get_length(),length)
if __name__=='__main__':unittest.main()
