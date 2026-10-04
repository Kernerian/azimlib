"""Measured component frames contain their text after typography edits."""
import unittest,json,importlib.util
from pathlib import Path as FilePath
import azimlib as azl
from azimlib.scene import Scene,Text,Path
from azimlib.viewport import Viewport
from azimlib.legend_layout import render_legend
from azimlib.layout_engine import primitive_bounds


class ComponentFrameTests(unittest.TestCase):
    def tearDown(self):azl.close('all')

    def test_colorbar_dimensions_against_recorded_native_reference(self):
        root=FilePath(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location('colorbar_size_probe',root/'tools/inspect_colorbar_sizes.py')
        probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
        report=json.loads((root/'docs/colorbar-size-reference.json').read_text(encoding='utf-8'))
        self.assertEqual(len(report['cases']),16)
        for case in report['cases']:
            with self.subTest(location=case['location'],layout=case['layout'],shrink=case['shrink']):
                own=probe.inspect(azl,case['location'],case['layout'],case['shrink'])
                for i in (2,3):
                    # Separate constrained solvers reserve slightly different
                    # text space. The selected single-map cases differ <1 px.
                    self.assertAlmostEqual(own[i],case['matplotlib_box'][i],delta=1)

    def test_legend_edited_multiline_title_and_labels_stay_inside_frame(self):
        for fontsize in (7,12,22):
            for ncols in (1,2):
                with self.subTest(fontsize=fontsize,ncols=ncols):
                    fig,ax=azl.subplots()
                    ax.plot([-50,-45],[-25,-20],'o-',label='Água e gp\nSegunda linha')
                    ax.plot([-52,-43],[-27,-19],'D--',label='Rota B')
                    legend=ax.legend(title='Legenda\nTítulo com acentos',fontsize=fontsize,ncols=ncols)
                    legend.get_title().set(fontsize=fontsize+5,fontweight='bold')
                    legend.get_texts()[1].set(fontsize=fontsize+3,fontweight='bold')
                    scene=Scene(1200,1000)
                    render_legend(legend,Viewport(ax.projection,(-54,-42,-28,-16),(100,100,1000,800)),scene)
                    frame=next(p for p in scene.items if isinstance(p,Path) and p.closed)
                    points=frame.paths[0]
                    left=min(x for x,y in points);right=max(x for x,y in points)
                    top=min(y for x,y in points);bottom=max(y for x,y in points)
                    boxes=[primitive_bounds(p) for p in scene.items if isinstance(p,Text)]
                    for x,y,w,h in boxes:
                        self.assertGreaterEqual(x,left);self.assertLessEqual(x+w,right)
                        self.assertGreaterEqual(y,top);self.assertLessEqual(y+h,bottom)
                    for i,(x,y,w,h) in enumerate(boxes):
                        for bx,by,bw,bh in boxes[i+1:]:
                            self.assertFalse(x<bx+bw and x+w>bx and y<by+bh and y+h>by)


if __name__=='__main__':unittest.main()
