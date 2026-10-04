"""Measured reference allocation and useful spanning-map layout regressions."""
import io
import json
from pathlib import Path
import unittest
import azimlib as azl
from azimlib.gridspec import GridSpec,SubplotSpec
from azimlib.layout_engine import item_bounds
from azimlib.cm import ScalarMappable
from azimlib.colors import Normalize

REFERENCE=Path(__file__).resolve().parents[1]/'docs/gridspec-reference.json'
SELECTIONS={'first':lambda g:g[0],'last':lambda g:g[-1],
            'column':lambda g:g[:,0],'row':lambda g:g[0,:],
            'block':lambda g:g[1:,1:],'negative':lambda g:g[-1,-2:],
            'flat span':lambda g:g[2:5],'all':lambda g:g[:,:]}


class GridSpecTests(unittest.TestCase):
    def tearDown(self):azl.close('all')
    def assert_bounds(self,a,b):
        for av,bv in zip(a,b):self.assertAlmostEqual(av,bv,places=12)
    def test_matplotlib_selections_weights_margins_and_cell_edges(self):
        for case in json.loads(REFERENCE.read_text(encoding='utf-8'))['cases']:
            with self.subTest(options=case['options'],selection=case['selection']):
                fig=azl.figure();gs=fig.add_gridspec(2,3,**case['options'])
                spec=SELECTIONS[case['selection']](gs)
                self.assertEqual(spec.get_geometry(),tuple(case['geometry']))
                self.assertEqual(list(spec.rowspan),case['rows']);self.assertEqual(list(spec.colspan),case['cols'])
                self.assert_bounds(spec.get_position(fig).bounds,case['bounds'])
                for a,b in zip(gs.get_grid_positions(fig),case['edges']):self.assert_bounds(a,b)
                self.assertIs(spec.get_gridspec(),gs);self.assertIs(spec.get_topmost_subplotspec(),spec)
    def test_matplotlib_update_states_and_ratio_application(self):
        ref=json.loads(REFERENCE.read_text(encoding='utf-8'))['updates']
        fig=azl.figure();gs=fig.add_gridspec(2,3,width_ratios=[3,1,2],height_ratios=[1,2])
        axes=[fig.add_subplot(gs[:,0]),fig.add_subplot(gs[0,1:]),fig.add_subplot(gs[1,1:])]
        actions=[lambda:None,
                 lambda:fig.subplots_adjust(left=.2,right=.95,bottom=.08,top=.9,wspace=.4,hspace=.3),
                 lambda:gs.update(left=.25,wspace=.15),
                 lambda:(gs.set_width_ratios([1,2,4]),gs.set_height_ratios([2,1])),
                 lambda:gs.update(),lambda:gs.update(left=None,wspace=None)]
        for expected,action in zip(ref,actions):
            action()
            with self.subTest(state=expected['name']):
                for ax,bounds in zip(axes,expected['positions']):self.assert_bounds(ax.position,bounds)
        self.assertEqual(gs.locally_modified_subplot_params(),[])
    def test_numeric_specs_reuse_grid_and_respect_figure_margins(self):
        fig=azl.figure()
        for case in json.loads(REFERENCE.read_text(encoding='utf-8'))['numeric']:
            args=tuple(tuple(a) if isinstance(a,list) else a for a in case['args'])
            ax=fig.add_subplot(*args)
            self.assertEqual(ax.get_subplotspec().get_geometry(),tuple(case['geometry']))
            self.assert_bounds(ax.position,case['bounds'])
        self.assertEqual(len(fig._gridspecs),1)
        fig.subplots_adjust(left=.3);self.assertAlmostEqual(fig.axes[0].position[0],.3)
        self.assertIsNone(fig.add_axes((.05,.05,.1,.1)).get_subplotspec())
    def test_subplots_shortcuts_squeeze_and_original_inputs_copied(self):
        widths=[2,1];options={'width_ratios':widths,'hspace':.4}
        fig,axes=azl.subplots(2,2,gridspec_kw=options,height_ratios=[1,3],squeeze=False)
        self.assertEqual(axes.shape,(2,2));self.assertEqual(axes[0,0].position[2]/axes[0,1].position[2],2)
        self.assertAlmostEqual(axes[1,0].position[3]/axes[0,0].position[3],3)
        widths[0]=100
        gs=axes[0,0].get_gridspec();self.assertEqual(gs.get_width_ratios(),[2,1])
        copy=gs.get_width_ratios();copy[0]=10;self.assertEqual(gs.get_width_ratios(),[2,1])
        fig2=azl.figure();grid=fig2.add_gridspec(1,2,width_ratios=[3,1])
        result=grid.subplots(subplot_kw={'projection':'mercator'})
        self.assertEqual(result.shape,(2,));self.assertEqual(result[0].projection.name,'mercator')
        self.assertIsInstance(azl.figure().add_gridspec(1,1).subplots(),azl.MapAxes)
    def test_invalid_selections_and_specs(self):
        gs=GridSpec(2,3)
        for selection in (6,-7,(2,0),(0,3),slice(1,1),slice(None,None,-1),slice(None,None,2),(0,1,2)):
            with self.subTest(selection=selection),self.assertRaises((ValueError,IndexError)):gs[selection]
        with self.assertRaises(TypeError):gs[.5]
        with self.assertRaises(ValueError):SubplotSpec(gs,4,2)
        a=gs[:,0];self.assertEqual(a,gs[:,0]);self.assertEqual(hash(a),hash(gs[:,0]))
        self.assertTrue(a.is_first_col());self.assertFalse(a.is_last_col())
        self.assertTrue(a.is_first_row());self.assertTrue(a.is_last_row())
    def test_validation_and_failed_edits_leave_positions_unchanged(self):
        fig,axes=azl.subplots(1,2,width_ratios=[2,1]);gs=axes[0].get_gridspec()
        before=[ax.position for ax in axes];params=gs.get_subplot_params(fig)
        for kwargs in ({'left':.99},{'wspace':-1},{'hspace':float('nan')},{'wrong':1}):
            with self.subTest(kwargs=kwargs),self.assertRaises((ValueError,TypeError)):gs.update(**kwargs)
            self.assertEqual(gs.get_subplot_params(fig),params);self.assertEqual(before,[ax.position for ax in axes])
        for ratios in ([0,1],[-1,2],[1],None):
            if ratios is None:continue
            with self.assertRaises(ValueError):gs.set_width_ratios(ratios)
            self.assertEqual(gs.get_width_ratios(),[2,1])
        count=len(fig.axes)
        for args in ((0,2,1),(2,2,5),(2,2,(4,2)),(2,2,(1,5))):
            with self.assertRaises(ValueError):fig.add_subplot(*args)
            self.assertEqual(len(fig.axes),count)
        with self.assertRaises(ValueError):fig.subplots(width_ratios=[1,2],gridspec_kw={'width_ratios':[2,1]})
        self.assertEqual(len(fig.axes),count)
    def test_grid_ownership_and_detached_binding(self):
        gs=GridSpec(1,2);fig=azl.figure();ax=fig.add_subplot(gs[0])
        self.assertIs(gs.figure,fig);self.assertIs(ax.get_gridspec(),gs)
        other=azl.figure()
        with self.assertRaisesRegex(ValueError,'another figure'):other.add_subplot(gs[1])
        self.assertEqual(other.axes,[])
        with self.assertRaises(ValueError):GridSpec(1,1).subplots()
    def test_full_figure_bounds_and_extremely_small_relative_weights(self):
        fig=azl.figure()
        gs=fig.add_gridspec(2,3,left=0,bottom=0,right=1,top=1,wspace=0,hspace=0,
                            width_ratios=[1e-300,2e-300,3e-300])
        axes=gs.subplots(squeeze=False)
        self.assertEqual(axes[0,2].position[0]+axes[0,2].position[2],1)
        self.assertEqual(axes[1,0].position[1],0)
        self.assertAlmostEqual(axes[0,2].position[2]/axes[0,0].position[2],3)
    def spanning(self,layout):
        fig=azl.figure(figsize=(11,8),layout=layout)
        gs=fig.add_gridspec(2,3,width_ratios=[2,1,1],height_ratios=[1,1.5])
        axes=[fig.add_subplot(gs[:,0]),fig.add_subplot(gs[0,1:]),fig.add_subplot(gs[1,1:])]
        for i,ax in enumerate(axes):
            ax.set_extent((-54,-42,-28,-16));ax.set_title('Mapa regional '+str(i)+'\nSegunda linha')
            ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.tick_params(labelrotation=25)
        fig.suptitle('Atlas com spans')
        return fig,gs,axes
    def assert_inside(self,scene):
        for _,start,end,_ in scene._layout_groups:
            box=item_bounds(scene,start,end)
            if box is None:continue
            x,y,w,h=box
            self.assertGreaterEqual(x,-.2);self.assertGreaterEqual(y,-.2)
            self.assertLessEqual(x+w,scene.width+.2);self.assertLessEqual(y+h,scene.height+.2)
    def test_tight_and_constrained_spans_reserve_titles_ticks_and_shared_colorbar(self):
        for layout in ('tight','constrained'):
            with self.subTest(layout=layout):
                fig,gs,axes=self.spanning(layout)
                fig.colorbar(ScalarMappable(norm=Normalize(0,100)),ax=axes,
                             orientation='horizontal',label='Escala compartilhada')
                scene=fig.to_scene();self.assert_inside(scene)
                # Spanning slot preserves exact union of the row tracks.
                left,top,bottom=axes
                self.assertAlmostEqual(left.position[1],bottom.position[1])
                self.assertAlmostEqual(left.position[1]+left.position[3],top.position[1]+top.position[3])
                self.assertAlmostEqual(top.position[0],bottom.position[0]);self.assertAlmostEqual(top.position[2],bottom.position[2])
                boxes=[item_bounds(scene,start,end) for owners,start,end,_ in scene._layout_groups if len(owners)==1]
                self.assertLess(boxes[0][0]+boxes[0][2],boxes[1][0])
                self.assertLess(boxes[1][1]+boxes[1][3],boxes[2][1])
                self.assertGreater(boxes[0][1],sum(scene._layout_suptitle[1::2]))
    def test_auto_ratios_respond_to_edits_resize_and_dpi(self):
        fig,gs,axes=self.spanning('constrained');fig.to_scene()
        first=[a.position for a in axes];gs.set_width_ratios([1,1,3]);gs.set_height_ratios([2,1])
        self.assert_inside(fig.to_scene());self.assertNotEqual(first,[a.position for a in axes])
        self.assertGreater(axes[1].position[3],axes[2].position[3])
        positions=[a.position for a in axes];fig.dpi=200;self.assert_inside(fig.to_scene())
        for a,b in zip(positions,[a.position for a in axes]):self.assert_bounds(a,b)
        fig.figsize=(12,9);self.assert_inside(fig.to_scene())
        positions=[a.position for a in axes]
        # An unused GridSpec must not change spacing of the active grid.
        fig.add_gridspec(6,9);fig.to_scene()
        for a,b in zip(positions,[a.position for a in axes]):self.assert_bounds(a,b)
    def test_manual_colorbar_slot_hidden_axes_and_exports(self):
        fig=azl.figure(figsize=(9,6));gs=fig.add_gridspec(2,3,width_ratios=[3,2,.2])
        axes=[fig.add_subplot(gs[:,0]),fig.add_subplot(gs[:,1])];cax=fig.add_subplot(gs[:,2])
        for ax in axes:ax.set_extent((-54,-42,-28,-16));ax.line([(-52,-24),(-44,-20)])
        fig.colorbar(ScalarMappable(norm=Normalize(0,100)),ax=axes,cax=cax,label='Valor')
        axes[1].set_visible(False);before=axes[1].position;gs.update(left=.2)
        self.assertNotEqual(before,axes[1].position)
        position=cax.position;stream=io.StringIO();fig.savefig(stream,format='svg')
        self.assertIn('Valor',stream.getvalue());self.assertEqual(cax.position,position)
        self.assertIn('<svg',fig.to_html());self.assertEqual(len(fig.to_scene().maps),1)
    def test_automatic_failure_restores_every_span_and_manual_axes(self):
        fig,gs,axes=self.spanning(None);fig.figsize=(2,2)
        manual=fig.add_axes((.01,.01,.05,.05))
        for ax in axes:ax.set_title('Huge\nHuge\nHuge',fontsize=50)
        before=[a.position for a in fig.axes];pars=dict(fig.subplotpars)
        with self.assertWarnsRegex(UserWarning,'Previous positions'):fig.tight_layout()
        self.assertEqual(before,[a.position for a in fig.axes]);self.assertEqual(pars,fig.subplotpars)
        self.assertIsNone(manual.get_gridspec())


if __name__=='__main__':unittest.main()
