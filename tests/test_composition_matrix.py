"""Integration of titles, ticks, bars, global labels, sizes and physical DPI."""
import importlib.util,json,unittest,warnings
from pathlib import Path
import azimlib as azl
from azimlib.layout_engine import item_bounds

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('composition_matrix_tool',ROOT/'tools/compare_composition_matrix.py')
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)


class CompositionMatrixTests(unittest.TestCase):
    def tearDown(self):azl.ioff();azl.close('all');azl.rcdefaults()

    def test_all_54_current_configurations_fit_and_keep_recorded_geometry(self):
        report=json.loads((ROOT/'docs/composition-matrix-reference.json').read_text(encoding='utf-8'))
        self.assertEqual(len(report['cases']),54)
        for case in report['cases']:
            with self.subTest(kind=case['kind'],layout=case['layout'],size=case['size'],dpi=case['dpi']):
                actual=tool.inspect(azl,case['kind'],case['layout'],case['size'],case['dpi'])
                self.assertIsNone(actual['error']);self.assertFalse(actual['warnings'])
                self.assertLessEqual(actual['overflow_logical'],.1)
                for rows in ('positions','logical_bounds'):
                    self.assertEqual(len(actual[rows]),len(case['azimlib'][rows]))
                    for a,b in zip(actual[rows],case['azimlib'][rows]):
                        for x,y in zip(a,b):self.assertAlmostEqual(x,y,places=7)

    def test_54_recorded_cases_preserve_logical_geometry_across_dpi(self):
        cases=json.loads((ROOT/'docs/composition-matrix-reference.json').read_text(encoding='utf-8'))['cases']
        groups={}
        for c in cases:groups.setdefault((c['kind'],c['layout'],tuple(c['size'])),[]).append(c)
        self.assertEqual(len(groups),18)
        for name,group in groups.items():
            with self.subTest(case=name):
                for case in group[1:]:
                    for key in ('positions','logical_bounds'):
                        for a,b in zip(group[0]['azimlib'][key],case['azimlib'][key]):
                            for x,y in zip(a,b):self.assertAlmostEqual(x,y,places=7)

    def test_neighbor_map_decorations_and_global_titles_do_not_overlap(self):
        for kind in ('atlas','nested'):
            for layout in ('tight','constrained'):
                with self.subTest(kind=kind,layout=layout):
                    fig,axes,bar=tool.example.build(kind,layout)
                    scene=fig.to_scene()
                    boxes=[item_bounds(scene,start,end) for owners,start,end,_ in scene._layout_groups if len(owners)==1 and owners[0] in axes]
                    self.assertEqual(len(boxes),len(axes))
                    for i,(x,y,w,h) in enumerate(boxes):
                        for a,b,c,d in boxes[i+1:]:
                            self.assertTrue(min(x+w,a+c)-max(x,a)<.1 or min(y+h,b+d)-max(y,b)<.1)
                    top=scene._layout_suptitle
                    self.assertLessEqual(top[1]+top[3],min(b[1] for b in boxes))
                    azl.close(fig)

    def test_tiny_resize_keeps_solver_state_atomic_and_recovers(self):
        fig,axes,bar=tool.example.build('nested','constrained')
        fig.to_scene();positions=[a.position for a in axes];pars=dict(fig.subplotpars)
        labelpositions=[a.get_position() for a in fig._figure_labels()]
        fig.set_size_inches(2,2)
        with self.assertWarnsRegex(UserWarning,'Previous positions'):
            self.assertFalse(fig.get_layout_engine().execute(fig))
        self.assertEqual(positions,[a.position for a in axes]);self.assertEqual(pars,fig.subplotpars)
        self.assertEqual(labelpositions,[a.get_position() for a in fig._figure_labels()])
        fig.set_size_inches(10,8);scene=fig.to_scene()
        self.assertTrue(scene.maps)

    def test_manual_axes_and_cax_stay_explicit_after_size_and_dpi_edits(self):
        fig=azl.figure(figsize=(8,6),layout='constrained');ax=fig.add_subplot(111)
        manual=fig.add_axes((.7,.7,.2,.2));cax=fig.add_axes((.92,.2,.02,.6))
        ax.set_extent((-54,-42,-28,-16));mapping=azl.cm.ScalarMappable(azl.colors.Normalize(0,100))
        fig.colorbar(mapping,ax=ax,cax=cax)
        for size,dpi in [((8,6),100),((10,8),150),((7,5),200)]:
            with self.subTest(size=size,dpi=dpi):
                fig.set_size_inches(size);fig.set_dpi(dpi);fig.to_scene()
                self.assertEqual(manual.position,(.7,.7,.2,.2));self.assertEqual(cax.position,(.92,.2,.02,.6))

    def test_dimension_edits_do_not_add_optional_components(self):
        fig,ax=azl.subplots();fig.set_size_inches(8,6);fig.set_dpi(200);fig.to_scene()
        self.assertFalse(ax.layers)
        for slot in ('_legend','_scale_bar','_north','_compass','_overview','_colorbar'):
            self.assertIsNone(getattr(ax,slot))
