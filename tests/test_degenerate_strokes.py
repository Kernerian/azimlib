"""Collapsed strokes omit ink, while explicit markers remain independent."""
import io
import json
from pathlib import Path as FilePath
import unittest
import xml.etree.ElementTree as ET
import azimlib as azl
from azimlib.scene import Scene,Path
from azimlib.renderers import render_png,render_svg

class DegenerateStrokeTests(unittest.TestCase):
    def test_native_visibility_reference_for_all_caps_counts_and_markers(self):
        report=json.loads((FilePath(__file__).resolve().parents[1]/'docs/degenerate-strokes-reference.json').read_text())
        self.assertEqual(len(report['cases']),18)
        for row in report['cases']:
            with self.subTest(cap=row['cap'],count=row['count'],marker=row['marker']):
                self.assertEqual(row['matplotlib']['line_visible'],row['azimlib']['line_visible'])
                self.assertEqual(row['azimlib']['line_visible'],row['marker']!='None')

    def test_low_level_png_svg_zero_segments_caps_and_closed_paths(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Pillow optional')
        for cap in ('butt','round','square'):
            for count in (1,2,4):
                for closed in (False,True):
                    with self.subTest(cap=cap,count=count,closed=closed):
                        scene=Scene(20,20,None)
                        scene.add(Path([[(10.,10.)]*count],closed,dict(stroke='red',stroke_width=6,linecap=cap)))
                        stream=io.BytesIO();render_png(scene,stream);stream.seek(0)
                        with Image.open(stream) as image:self.assertIsNone(image.getchannel('A').getbbox())
                        root=ET.fromstring(render_svg(scene))
                        paths=[p for p in root if p.tag.endswith('path')]
                        self.assertEqual(len(paths),1) # Keep one primitive/node for viewer indices.
                        self.assertEqual(paths[0].attrib['d'],'')

    def test_public_plots_keep_marker_and_original_duplicate_data(self):
        for cap in ('butt','round','projecting'):
            for marker in ('None','o'):
                for dpi in (100,200):
                    with self.subTest(cap=cap,marker=marker,dpi=dpi):
                        fig,ax=azl.subplots(figsize=(2,2),dpi=dpi)
                        try:
                            ax.set_extent((-48,-44,-25,-21))
                            line,=ax.plot([-46,-46],[-23,-23],color='red',linewidth=6,solid_capstyle=cap,marker=marker)
                            self.assertEqual(tuple(line.data.features[0].geometry.coordinates),((-46.,-23.),(-46.,-23.)))
                            scene=fig.to_scene()
                            red=[p for p in scene.items if p.style.get('fill')=='red' or p.style.get('stroke')=='red']
                            self.assertEqual(bool(red),marker!='None')
                            self.assertTrue(all(not isinstance(p,Path) for p in red) if marker=='o' else not red)
                        finally:azl.close(fig)

    def test_curved_arrow_collapsed_line_and_mixed_multiline_paths(self):
        fig,ax=azl.subplots(figsize=(2,2))
        try:
            ax.set_extent((-48,-44,-25,-21))
            ax.line([(-46,-23)]*2,color='red',solid_capstyle='projecting',curved=.2,arrow='both')
            self.assertFalse(any(p.style.get('stroke')=='red' for p in fig.to_scene().items))
        finally:azl.close(fig)
        # A zero part must not remove a normal neighboring part or close it.
        scene=Scene(20,20,None)
        scene.add(Path([[(5,5)]*3,[(2,3),(18,15)]],style=dict(stroke='red',linecap='square')))
        self.assertIn('M 2 3 L 18 15',render_svg(scene));self.assertNotIn('M 5 5',render_svg(scene))
        scene=Scene(20,20,None)
        scene.add(Path([[(5,5),(5.0000001,5)]],style=dict(stroke='red',linecap='round',stroke_width=2)))
        self.assertIn('M 5 5 L 5.0000001 5',render_svg(scene))

if __name__=='__main__':unittest.main()
