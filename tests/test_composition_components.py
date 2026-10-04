"""Cross-component regressions at different physical sizes and export DPI."""
import importlib.util
import io
from pathlib import Path
import unittest
import azimlib as azl
from azimlib.layout_engine import primitive_bounds
from azimlib.scene import Text

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('composition_matrix_example',ROOT/'examples/composition_components.py')
example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)

class CompositionMatrixTests(unittest.TestCase):
    def tearDown(self):azl.close('all');azl.rcdefaults()

    def test_constrained_components_and_labels_stay_inside_figure_at_sizes_dpi_orientations(self):
        for figsize in ((9.6,5.4),(7.6,4.8)):
            for dpi in (72,100,180):
                for orientation in ('horizontal','vertical'):
                    with self.subTest(figsize=figsize,dpi=dpi,orientation=orientation):
                        fig,handles=example.create(figsize=figsize,dpi=dpi,orientation=orientation)
                        scene=fig.to_scene(cull=True)
                        self.assertAlmostEqual(scene.width,figsize[0]*dpi)
                        self.assertAlmostEqual(scene.height,figsize[1]*dpi)
                        self.assertEqual(len(scene.maps),2)
                        for item in scene.items:
                            if not isinstance(item,Text):continue
                            box=primitive_bounds(item)
                            if box is None:continue
                            x,y,w,h=box
                            self.assertGreaterEqual(x,-.01);self.assertGreaterEqual(y,-.01)
                            self.assertLessEqual(x+w,scene.width+.01);self.assertLessEqual(y+h,scene.height+.01)
                        for metadata in scene.maps:
                            self.assertGreater(metadata['box'][2],0);self.assertGreater(metadata['box'][3],0)
                        self.assertNotIn('overview_map',scene.maps[0]);mini=scene.maps[1]['overview_map']
                        self.assertEqual(scene.items[mini['focus_index']].style['stroke'],'black')
                        fig.to_svg();azl.close(fig)

    def test_dpi_scales_every_component_without_changing_logical_geometry(self):
        fig,handles=example.create();logical=fig.to_scene(cull=True)
        fig.set_dpi(180);scaled=fig.to_scene(cull=True)
        self.assertEqual(scaled.items,logical.scaled(1.8).items)
        self.assertEqual(scaled.maps,logical.scaled(1.8).maps)

    def test_component_visibility_roundtrip_and_shared_colorbar_updates(self):
        fig,handles=example.create();before=fig.to_svg()
        for name in ('legend','scale','north','compass','overview','bar'):
            with self.subTest(component=name):
                component=handles[name];component.set_visible(False)
                self.assertNotEqual(before,fig.to_svg());component.set_visible(True)
                self.assertEqual(before,fig.to_svg())
        handles['points'].set_clim(0,200)
        self.assertEqual(handles['field'].get_clim(),(0,200));self.assertEqual(handles['bar'].norm.vmax,200)
        fig.to_scene()

    def test_explicit_text_legend_and_inset_positions_survive_layout_and_dpi(self):
        fig,handles=example.create();left,right=handles['axes']
        heading=fig.suptitle('Título com posição explícita',x=.47,y=.97)
        legend=handles['legend'];legend.set_bbox_to_anchor((.05,.93));legend.set_loc('upper left')
        child=right.inset((.1,.08,.2,.2));child.set_extent((-52,-48,-26,-22));child.set_axis_off()
        before=(heading.get_position(),legend['bbox_to_anchor'],child.position)
        for dpi in (72,100,180):
            with self.subTest(dpi=dpi):
                fig.set_dpi(dpi);fig.to_scene()
                self.assertEqual(before,(heading.get_position(),legend['bbox_to_anchor'],child.position))

    def test_static_exports_contain_no_viewer_and_html_keeps_opt_in_components(self):
        fig,handles=example.create();svg=fig.to_svg()
        self.assertNotIn('<script',svg);self.assertIn('Índice sintético',svg)
        try:
            from PIL import Image
        except ImportError:self.skipTest('Pillow optional raster extra')
        output=io.BytesIO();fig.savefig(output,format='png',dpi=72);output.seek(0)
        with Image.open(output) as image:self.assertEqual(image.size,(691,389))
        html=fig.to_html();self.assertIn('AzimlibComponents',html)

if __name__=='__main__':unittest.main()
