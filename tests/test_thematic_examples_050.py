"""Renderable gallery evidence, not placeholder existence checks."""
import importlib.util,io,sys,unittest
from pathlib import Path
import azimlib as a
class ThematicExamples(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  path=Path(__file__).resolve().parents[1]/'examples/thematic/_scenes.py'
  spec=importlib.util.spec_from_file_location('thematic_examples',path);cls.examples=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.examples)
 def tearDown(self):a.close('all')
 def test_atlas_and_mars_use_same_owned_artist_classes(self):
  for factory in (self.examples.historical,self.examples.mars):
   f,meta=factory();kinds={layer.kind for ax in f.axes for layer in ax.layers}
   self.assertTrue({'thematic_symbols','thematic_region','thematic_path'}<=kinds)
   scene=f.to_scene();self.assertGreater(len(scene.items),50);self.assertTrue(scene._material_notices)
   self.assertTrue(all(layer.axes is ax for ax in f.axes for layer in ax.layers));self.assertIn('fiction',str(meta).lower())
 def test_catalog_raster_only_small_icon_not_page(self):
  from azimlib.scene import RasterIcon,Path
  f,meta=self.examples.catalog();s=f.to_scene();icons=[i for i in s.items if isinstance(i,RasterIcon)]
  self.assertEqual(len(icons),1);self.assertLess(icons[0].width,100);self.assertGreater(sum(isinstance(i,Path) for i in s.items),30)
 def test_pdf_gradient_is_local_alpha_tile_with_hole(self):
  from azimlib.renderers.pdf import _gradient_tiles
  from azimlib.scene import RasterIcon,Path
  from azimlib.picking import primitive_hit
  f,meta=self.examples.regions();scene=f.to_scene();items=_gradient_tiles(scene);tiles=[i for i in items if isinstance(i,RasterIcon)]
  self.assertEqual(len(tiles),1);tile=tiles[0];self.assertLess(tile.width*tile.height,scene.width*scene.height/2)
  self.assertGreater(sum(isinstance(i,Path) for i in items),2)
  self.assertFalse(primitive_hit(tile,(tile.x+tile.width*.52,tile.y+tile.height*.50),0))
  output=io.BytesIO();f.savefig(output,format='pdf');self.assertIn(b'/SMask',output.getvalue())
 def test_groups_toggle_source_without_mutating_other_viewport(self):
  f,meta=self.examples.groups();original=f.to_svg();group=f.axes[0]._groups[0];group.set_visible(False)
  self.assertNotEqual(original,f.to_svg());self.assertTrue(f.axes[1]._groups[0].get_visible());group.set_visible(True);self.assertEqual(original,f.to_svg())
 def test_all_gallery_scenes_have_finite_deterministic_svg(self):
  from azimlib.renderers._common import validate
  for factory in (self.examples.regions,self.examples.paths,self.examples.worlds):
   f,meta=factory();validate(f.to_scene());first=f.to_svg();self.assertEqual(first,f.to_svg());self.assertIn('<path',first)
if __name__=='__main__':unittest.main()
