"""Own hierarchy reference allocation and font-aware nested map integration."""
import io,json,warnings
from pathlib import Path
import unittest
from unittest.mock import patch
import azimlib as azl
from azimlib.gridspec import GridSpec,GridSpecFromSubplotSpec
from azimlib.colors import Normalize
from azimlib.cm import ScalarMappable
from azimlib.layout_engine import item_bounds
from azimlib.renderers import render_png

REFERENCE=json.loads((Path(__file__).resolve().parents[1]/'docs/nested-layout-reference.json').read_text())


class NestedLayoutTests(unittest.TestCase):
    def setUp(self):azl.close('all');azl.ioff()
    def tearDown(self):azl.close('all');azl.rcdefaults()
    def bounds(self,actual,expected):
        for a,b in zip(actual,expected):self.assertAlmostEqual(a,b,places=12)

    def test_ten_nested_manual_positions_params_and_topmost_match_reference(self):
        for case in REFERENCE['cases']:
            with self.subTest(name=case['name'],options=case['options']):
                fig=azl.figure();root=fig.add_gridspec(2,2,width_ratios=[1,2],height_ratios=[2,1])
                nested=root[:,1].subgridspec(2,2,**case['options']);deep=nested[1,0].subgridspec(1,2,wspace=.1)
                spec={'parent':root[:,1],'first':nested[0,0],'span':nested[:,1],'deep first':deep[0,0],'deep last':deep[0,1]}[case['name']]
                self.bounds(spec.get_position(fig).bounds,case['bounds'])
                actual=spec.get_gridspec().get_subplot_params(fig)
                for key,value in case['params'].items():
                    if not key.startswith('_'):self.assertAlmostEqual(actual[key],value,places=12)
                self.assertEqual(spec.get_topmost_subplotspec().get_geometry(),tuple(case['top']))
                self.assertEqual(deep.get_topmost_subplotspec(),root[:,1]);azl.close(fig)

    def test_parent_updates_apply_to_descendants_like_reference(self):
        fig=azl.figure();root=fig.add_gridspec(1,2,width_ratios=[1,2]);child=root[1].subgridspec(2,1)
        axes=[fig.add_subplot(root[0]),fig.add_subplot(child[0]),fig.add_subplot(child[1])]
        actions=[lambda:None,lambda:fig.subplots_adjust(left=.2,right=.95,wspace=.4,hspace=.3),
                 lambda:root.set_width_ratios([3,1]),lambda:root.update()]
        for ref,action in zip(REFERENCE['updates'],actions):
            action()
            with self.subTest(state=ref['name']):
                for ax,expected in zip(axes,ref['positions']):self.bounds(ax.position,expected)
        child.set_height_ratios([1,3]);child.update(hspace=.1)
        self.assertAlmostEqual(axes[2].position[3]/axes[1].position[3],3)
        self.bounds(axes[0].position,root[0].get_position(fig))

    def test_three_nested_mosaics_order_allocation_and_topmost_match_reference(self):
        for ref in REFERENCE['mosaics']:
            with self.subTest(layout=ref['layout']):
                fig,axes=azl.subplot_mosaic(ref['layout'],gridspec_kw={'wspace':.3,'hspace':.4},
                    per_subplot_kw={'C':{'projection':'mercator'}})
                self.assertEqual(list(axes),[a['key'] for a in ref['axes']])
                self.assertEqual(axes['C'].projection.name,'mercator')
                for expected,ax in zip(ref['axes'],axes.values()):
                    self.bounds(ax.position,expected['bounds'])
                    self.assertEqual(ax.get_subplotspec().get_topmost_subplotspec().get_geometry(),tuple(expected['top']))
                azl.close(fig)

    def test_detached_hierarchy_binding_and_cross_figure_rejection(self):
        root=GridSpec(1,2);child=root[1].subgridspec(1,2);deep=child[1].subgridspec(2,1)
        fig=azl.figure();ax=fig.add_subplot(deep[1])
        self.assertEqual(fig._gridspecs,[root,child,deep])
        self.assertTrue(all(g.figure is fig for g in (root,child,deep)))
        other=azl.figure()
        for spec in (root[0],child[0],deep[0]):
            with self.subTest(spec=spec),self.assertRaisesRegex(ValueError,'another figure'):other.add_subplot(spec)
        self.assertFalse(other.axes)
        generated=child.subplots(projection='mercator')
        self.assertEqual(generated.shape,(2,));self.assertEqual(generated[0].projection.name,'mercator')
        self.assertIs(ax.get_figure(),fig)

    def test_numeric_subplot_does_not_reuse_matching_child_grid(self):
        fig=azl.figure();root=fig.add_gridspec(1,1);child=root[0].subgridspec(1,2)
        fig.add_subplot(child[0]);numeric=fig.add_subplot(121)
        self.assertIsNot(numeric.get_gridspec(),child);self.assertNotIsInstance(numeric.get_gridspec(),GridSpecFromSubplotSpec)
        self.assertIs(azl.subplot(121),numeric)
        self.assertIs(azl.subplot(child[0]),fig.axes[0])

    def test_invalid_child_parameters_and_mosaics_leave_hierarchy_unmodified(self):
        fig,ax=azl.subplots();root=ax.get_gridspec();child=root[0].subgridspec(1,2)
        ax2=fig.add_subplot(child[0]);fig.canvas.draw()
        positions=[a.position for a in fig.axes];grids=list(fig._gridspecs)
        for options in (dict(wspace=-1),dict(width_ratios=[0,1]),dict(hspace=float('nan')),dict(left=.2)):
            with self.subTest(options=options),self.assertRaises((ValueError,TypeError)):root[0].subgridspec(1,2,**options)
            self.assertFalse(fig.stale)
        with self.assertRaises(TypeError):child.update(left=.3)
        with self.assertRaises(ValueError):child.update(wspace=-1)
        cases=[[['A',[['A','B']]]],[['A',[['B','B'],['B','.']]]],
               [['A',[['B', [['C','C'],['C','.']]]]]],[[['A']]],
               [['A',[['B'],['C','D']]]]]
        for layout in cases:
            with self.subTest(layout=layout),self.assertRaises((ValueError,TypeError)):fig.subplot_mosaic(layout)
            self.assertEqual(fig._gridspecs,grids);self.assertEqual([a.position for a in fig.axes],positions);self.assertFalse(fig.stale)
        with self.assertRaises(ValueError):fig.subplot_mosaic([['A',[['B','C']]]],per_subplot_kw={'C':{'projection':'missing'}})
        self.assertEqual(fig._gridspecs,grids);self.assertIs(fig.gca(),ax2)
        cyclic=[];cyclic.append([cyclic])
        with self.assertRaisesRegex(ValueError,'nesting'):fig.subplot_mosaic(cyclic)
        self.assertEqual(fig._gridspecs,grids);self.assertFalse(fig.stale)

    def atlas(self,layout,figsize=(11,8)):
        fig,axes=azl.subplot_mosaic([['A',[['B','C'],['D','C']]]],figsize=figsize,layout=layout,
            width_ratios=[1.2,1],subplot_kw={'projection':'mercator'})
        for key,ax in axes.items():
            ax.set_extent((-54,-44,-26,-18));ax.set_title('Mapa '+key+'\nTítulo em duas linhas')
            ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.tick_params(labelrotation=20)
            ax.plot([-52,-48],[-25,-21],linewidth=.6)
        fig.suptitle('Atlas de grupos aninhados')
        return fig,axes

    def inside(self,scene):
        boxes=[]
        for owners,start,end,slot in scene._layout_groups:
            box=item_bounds(scene,start,end)
            if box is None:continue
            x,y,w,h=box;self.assertGreaterEqual(x,-.2);self.assertGreaterEqual(y,-.2)
            self.assertLessEqual(x+w,scene.width+.2);self.assertLessEqual(y+h,scene.height+.2)
            if len(owners)==1:boxes.append(box)
        for i,a in enumerate(boxes):
            for b in boxes[i+1:]:
                self.assertTrue(a[0]+a[2]<=b[0]+.2 or b[0]+b[2]<=a[0]+.2 or a[1]+a[3]<=b[1]+.2 or b[1]+b[3]<=a[1]+.2,(a,b))

    def test_two_engines_nested_spans_titles_and_shared_bar_inside_canvas(self):
        for layout in ('tight','constrained'):
            with self.subTest(layout=layout):
                fig,axes=self.atlas(layout)
                fig.colorbar(ScalarMappable(Normalize(0,100)),ax=list(axes.values()),orientation='horizontal',label='Escala compartilhada')
                axes['B'].scale_bar(length=100,fontsize=8);axes['D'].north_arrow(size=18)
                axes['C'].compass(size=18)
                scene=fig.to_scene();self.inside(scene)
                self.assertAlmostEqual(axes['C'].position[1],axes['D'].position[1])
                self.assertAlmostEqual(axes['C'].position[1]+axes['C'].position[3],axes['B'].position[1]+axes['B'].position[3])
                self.assertFalse(any(ax._grid_config or ax._overview for ax in axes.values()))
                azl.close(fig)

    def test_hidden_removed_axes_text_edits_and_resize_recompute(self):
        fig,axes=self.atlas('constrained');scene=fig.to_scene();positions=[a.position for a in axes.values()]
        axes['B'].set_title('Short');axes['B'].set_visible(False);axes['D'].remove()
        fig.figsize=(12,9);scene=fig.to_scene();self.inside(scene)
        self.assertNotEqual([a.position for a in axes.values()],positions)
        self.assertEqual(axes['D'].position,positions[3])
        axes['B'].set_visible(True);axes['B'].set_in_layout(False);position=axes['B'].position
        fig.to_scene();self.assertEqual(axes['B'].position,position)

    def test_small_figure_mixed_roots_and_unexpected_measurement_restore_all_positions(self):
        fig,axes=self.atlas('constrained',figsize=(1,1));before=[a.position for a in fig.axes];pars=dict(fig.subplotpars)
        with self.assertWarnsRegex(UserWarning,'insufficient nested'):
            self.assertFalse(fig.get_layout_engine().execute(fig))
        self.assertEqual(before,[a.position for a in fig.axes]);self.assertEqual(pars,fig.subplotpars)
        fig.figsize=(11,8)
        with patch.object(fig,'_compose_scene',side_effect=RuntimeError('measure failed')):
            with self.assertRaisesRegex(RuntimeError,'measure failed'):fig.get_layout_engine().execute(fig)
        self.assertEqual(before,[a.position for a in fig.axes]);self.assertEqual(pars,fig.subplotpars)
        fig.add_subplot(1,3,1);before=[a.position for a in fig.axes]
        with self.assertWarnsRegex(UserWarning,'mixed subplot'):fig.to_scene()
        self.assertEqual(before,[a.position for a in fig.axes])

    def test_deeper_grids_own_bars_and_explicit_axes_preserve_positions(self):
        fig=azl.figure(figsize=(11,9),layout='tight');root=fig.add_gridspec(1,2,width_ratios=[1,2])
        child=root[1].subgridspec(2,1);deep=child[1].subgridspec(1,2)
        axes=[fig.add_subplot(root[0]),fig.add_subplot(child[0]),fig.add_subplot(deep[0]),fig.add_subplot(deep[1])]
        for i,ax in enumerate(axes):ax.set_extent((-54,-44,-26,-18));ax.set_title('Map '+str(i));ax.set_xlabel('Lon')
        fig.colorbar(ScalarMappable(Normalize(0,100)),ax=axes[2:],orientation='horizontal',label='Detalhes')
        explicit=fig.add_axes((.02,.02,.1,.1));position=explicit.position
        self.inside(fig.to_scene());self.assertEqual(explicit.position,position)
        self.assertEqual(axes[-1].get_subplotspec().get_topmost_subplotspec(),root[1])

    def test_export_equivalence_culling_and_inputs_preserved(self):
        for dpi in (72,144):
            with self.subTest(dpi=dpi):
                layout=[['A',[['B'],['C']]]];original=json.dumps(layout)
                fig,axes=azl.subplot_mosaic(layout,layout='constrained',figsize=(8,6),dpi=dpi)
                for ax in axes.values():
                    ax.set_extent((-54,-44,-26,-18));ax.plot([-52,-48],[-25,-21],linewidth=.6)
                def png(cull):
                    stream=io.BytesIO();render_png(fig.to_scene(cull=cull),stream);return stream.getvalue()
                self.assertEqual(png(True),png(False));self.assertIn('<svg',fig.to_svg());self.assertIn('Figure',fig.to_html())
                self.assertEqual(json.dumps(layout),original);axes['B'].zoom(1.2);self.assertTrue(fig.to_scene().items)
                azl.close(fig)

    def test_only_active_child_keeps_parent_selection_and_long_title_rolls_back(self):
        fig=azl.figure(figsize=(9,7),layout='constrained')
        root=fig.add_gridspec(2,2);child=root[1,1].subgridspec(1,1)
        ax=fig.add_subplot(child[0]);ax.set_extent((-54,-44,-26,-18));ax.set_title('Only child')
        self.inside(fig.to_scene());self.assertGreater(ax.position[0],.5)
        self.assertLess(ax.position[1]+ax.position[3],.5)
        positions=[a.position for a in fig.axes];pars=dict(fig.subplotpars)
        fig.suptitle('X'*200)
        with self.assertWarnsRegex(UserWarning,'suptitle is wider'):
            self.assertFalse(fig.get_layout_engine().execute(fig))
        self.assertEqual([a.position for a in fig.axes],positions);self.assertEqual(fig.subplotpars,pars)


if __name__=='__main__':unittest.main()
