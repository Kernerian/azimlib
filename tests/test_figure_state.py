"""Reference lifecycle plus integration of named maps and stateful plotting."""
import io,json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import unittest
import azimlib as azl
import azimlib.pyplot as plt
from azimlib.cm import ScalarMappable
from azimlib.colors import Normalize
from azimlib.layout_engine import item_bounds
from azimlib.projections import Mercator

REFERENCE=json.loads((Path(__file__).resolve().parents[1]/'docs/figure-state-reference.json').read_text())


class FigureStateTests(unittest.TestCase):
    def setUp(self):azl.close('all');azl.ioff()
    def tearDown(self):azl.close('all');azl.rcdefaults()

    def test_reference_number_labels_reactivation_and_closing(self):
        actions=[lambda:plt.figure(7).add_subplot().set_label('A'),
                 lambda:plt.figure('atlas').add_subplot().set_label('B'),
                 lambda:plt.figure(7),lambda:plt.figure(),lambda:plt.figure('atlas'),
                 lambda:plt.close(7),lambda:plt.close('atlas')]
        for ref,action in zip(REFERENCE['states'],actions):
            with self.subTest(state=ref['name']):
                action();fig=plt.gcf()
                self.assertEqual(plt.get_fignums(),ref['numbers']);self.assertEqual(plt.get_figlabels(),ref['labels'])
                self.assertEqual(fig.number,ref['current']);self.assertEqual(fig.get_label(),ref['label'])
                self.assertEqual([a.get_label() for a in fig.axes],ref['axes'])
                self.assertEqual(fig.gca().get_label() if fig.axes else None,ref['current_axes'])

    def test_reference_axes_mru_selection_preserves_creation_order(self):
        fig,axes=azl.subplots(1,3)
        for ax,label in zip(axes,['A','B','C']):ax.set_label(label)
        actions=[lambda:None,lambda:fig.sca(axes[0]),lambda:fig.sca(axes[1]),
                 lambda:axes[1].remove(),lambda:axes[0].remove()]
        for ref,action in zip(REFERENCE['selection'],actions):
            with self.subTest(state=ref['name']):
                action();self.assertEqual([a.get_label() for a in fig.axes],ref['axes'])
                self.assertEqual(fig.gca().get_label(),ref['active'])

    def test_eight_mosaic_references_keys_labels_specs_and_positions(self):
        for ref in REFERENCE['mosaics']:
            with self.subTest(layout=ref['layout'],options=ref['options']):
                fig,axes=azl.subplot_mosaic(ref['layout'],**ref['options'])
                self.assertEqual(list(axes),[a['key'] for a in ref['axes']])
                for expected,ax in zip(ref['axes'],axes.values()):
                    self.assertEqual(ax.get_label(),expected['label'])
                    self.assertEqual(ax.get_subplotspec().get_geometry(),tuple(expected['geometry']))
                    for a,b in zip(ax.position,expected['bounds']):self.assertAlmostEqual(a,b,places=12)
                self.assertIs(fig.gca(),list(axes.values())[-1]);azl.close(fig)

    def test_reuse_clear_ignore_new_options_and_copy_registry_queries(self):
        fig,ax=azl.subplots(num='atlas',figsize=(4,3),dpi=72)
        ax.plot([-49,-48],[-23,-22]);fig.suptitle('Old')
        with self.assertWarnsRegex(UserWarning,'Ignoring'):
            same=azl.figure('atlas',figsize=(9,9),dpi=200,layout='constrained')
        self.assertIs(fig,same);self.assertEqual(fig.figsize,(4,3));self.assertEqual(fig.dpi,72)
        numbers=azl.get_fignums();numbers.clear();self.assertEqual(azl.get_fignums(),[1])
        self.assertTrue(azl.fignum_exists('atlas'));self.assertTrue(azl.fignum_exists(1))
        self.assertFalse(azl.fignum_exists(99));self.assertIs(azl.figure(fig),fig)
        self.assertIs(azl.figure('atlas',clear=True),fig);self.assertEqual(fig.axes,[])
        self.assertIsNone(ax.get_figure());self.assertIsNone(fig._suptitle)
        self.assertEqual(fig.get_label(),'atlas');self.assertIs(azl.gca().figure,fig)

    def test_sca_routes_pyplot_operations_and_save_to_correct_figure(self):
        atlas,axes=plt.subplots(1,2,num='atlas');other,other_ax=plt.subplots(num='other')
        creation=list(atlas.axes);atlas.canvas.draw()
        self.assertIsNone(plt.sca(axes[0]));self.assertIs(plt.gcf(),atlas);self.assertIs(plt.gca(),axes[0])
        self.assertEqual(atlas.axes,creation);self.assertFalse(atlas.stale)
        plt.plot([-49,-48],[-23,-22],label='Only first');plt.title('Selected map')
        self.assertEqual(len(axes[0].layers),1);self.assertFalse(axes[1].layers);self.assertFalse(other_ax.layers)
        stream=io.StringIO();plt.savefig(stream,format='svg');self.assertIn('Selected map',stream.getvalue())
        plt.sca(other_ax);self.assertIs(plt.gcf(),other);plt.title('Other map')
        self.assertNotIn('Other map',atlas.to_svg())
        axes[0].remove()
        with self.assertRaises(ValueError):plt.sca(axes[0])
        self.assertIs(plt.gcf(),other)
        with self.assertRaises(ValueError):atlas.sca(other_ax)
        with self.assertRaises(ValueError):plt.sca(azl.Figure().add_subplot())

    def test_subplot_reuse_projection_and_spans_do_not_duplicate(self):
        first=plt.subplot(221);second=plt.subplot(2,2,2)
        self.assertIs(plt.subplot(221),first);self.assertIs(plt.gca(),first)
        self.assertEqual(len(plt.gcf().axes),2)
        mer=plt.subplot(221,projection='mercator');self.assertIsNot(mer,first)
        self.assertIs(plt.subplot(221,projection='mercator'),mer)
        self.assertIs(plt.subplot(221),first)
        span=plt.subplot(2,2,(3,4));self.assertIs(plt.subplot(2,2,(3,4)),span)
        gs=plt.gcf().add_gridspec(1,2);named=plt.subplot(gs[0])
        self.assertIs(plt.subplot(gs[0]),named)
        self.assertIsNot(plt.subplot(1,2,2),named)
        count=len(plt.gcf().axes)
        for args,kw in (((220,),{}),((2,2,5),{}),((221,),dict(projection='missing')),((221,),dict(unknown=1))):
            with self.subTest(args=args,kw=kw),self.assertRaises((ValueError,TypeError)):plt.subplot(*args,**kw)
            self.assertEqual(len(plt.gcf().axes),count)

    def test_clear_detaches_components_callbacks_and_preserves_identity_layout(self):
        fig,axes=azl.subplots(1,2,num=12,layout='constrained',figsize=(8,5))
        m=ScalarMappable(Normalize(0,100));shared=fig.colorbar(m,ax=axes,orientation='horizontal')
        cax=fig.add_axes((.9,.2,.03,.6));explicit=fig.colorbar(m,ax=axes[0],cax=cax)
        local=axes[0].colorbar(m)
        line,=axes[0].plot([-49,-48],[-23,-22]);title=fig.suptitle('Old');text=fig.text(.3,.2,'Old text')
        engine=fig.get_layout_engine();plt.clf()
        self.assertIs(fig.get_layout_engine(),engine);self.assertEqual(fig.number,12)
        self.assertEqual(fig.axes,[]);self.assertEqual(fig._colorbars,[]);self.assertEqual(fig._gridspecs,[])
        for obj in (line,title,text,shared,explicit,local,axes[0],cax):self.assertIsNone(obj.get_figure())
        new=fig.gca();fig.canvas.draw();self.assertFalse(fig.stale)
        m.set_clim(0,200);line.set_color('red');self.assertFalse(fig.stale)
        new.plot([-49,-48],[-23,-22]);plt.cla();self.assertIs(plt.gca(),new);self.assertFalse(new.layers)

    def test_close_current_unknown_identity_and_viewer_only_once(self):
        azl.close();self.assertEqual(azl.get_fignums(),[])
        fig=azl.figure(0);other=azl.figure(-3);third=azl.figure('3')
        self.assertEqual(azl.get_fignums(),[-3,0,1]);self.assertFalse(azl.fignum_exists(3))
        viewer=Mock(closed=False);fig._viewer=viewer
        azl.close(99);self.assertIs(azl.gcf(),third)
        azl.close(0);viewer.close.assert_called_once();self.assertTrue(fig._closed)
        azl.close(0);viewer.close.assert_called_once()
        azl.close();self.assertIs(azl.gcf(),other)
        azl.close('all');self.assertEqual(azl.get_figlabels(),[])
        unmanaged=azl.Figure();unmanaged.close();self.assertTrue(unmanaged._closed)
        with self.assertRaises(ValueError):azl.figure(unmanaged)
        with self.assertRaises(TypeError):azl.figure([])
        self.assertEqual(azl.get_fignums(),[])

    def test_labels_and_export_titles_rename_without_changing_number(self):
        fig=azl.figure('atlas');self.assertEqual(fig._window_title(),'Figure 1: atlas')
        fake_window=Mock();fig._viewer=SimpleNamespace(closed=False,window=fake_window,draw_idle=Mock(),close=Mock())
        fig.set_label('Atlas & regiões');fake_window.title.assert_called_with('Figure 1: Atlas & regiões')
        self.assertFalse(azl.fignum_exists('atlas'));self.assertIs(azl.figure('Atlas & regiões'),fig)
        self.assertIn('Atlas &amp; regiões',fig.to_html())
        self.assertIn('Custom title',fig.to_html('Custom title'))
        fig.set_label(None);self.assertEqual(azl.get_figlabels(),['']);self.assertEqual(fig.number,1)

    def test_per_subplot_options_grouping_and_inputs_not_mutated(self):
        options={'projection':'mercator'};details={'projection':'orthographic','projection_kw':{'central_longitude':-50}}
        fig,axes=azl.subplot_mosaic('AA;BC',subplot_kw=options,per_subplot_kw={'BC':details})
        self.assertEqual(axes['A'].projection.name,'mercator')
        self.assertEqual(axes['B'].projection.name,'orthographic');self.assertEqual(axes['C'].projection.central_longitude,-50)
        self.assertEqual(options,{'projection':'mercator'});self.assertEqual(details['projection_kw'],{'central_longitude':-50})
        fig2,axes2=azl.subplot_mosaic([['country','state']],per_subplot_kw={('country','state'):{'projection':Mercator()}})
        self.assertEqual([a.projection.name for a in axes2.values()],['mercator','mercator'])
        multiline='''
            AA
            BC
        '''
        self.assertEqual(list(azl.subplot_mosaic(multiline)[1]),['A','B','C'])

    def test_failed_mosaics_validate_before_axes_grid_or_stale_changes(self):
        fig,ax=azl.subplots();fig.canvas.draw()
        grids=list(fig._gridspecs);old=fig.axes[:];current=fig.gca()
        cases=[('',{}),([],{}),('AA;A.',{}),('AB;A',{}),('AB;BA',{}),
               ([[['A']]],{}),('AB',dict(per_subplot_kw={'C':{}})),
               ('AB',dict(per_subplot_kw={'A':{'projection':'missing'}})),
               ('AB',dict(subplot_kw={'unknown':2})),
               ('AB',dict(per_subplot_kw={'AB':{},'A':{}})),
               ('AB',dict(width_ratios=[1])),
               ('AB',dict(width_ratios=[1,2],gridspec_kw={'width_ratios':[1,2]}))]
        for layout,options in cases:
            with self.subTest(layout=layout,options=options),self.assertRaises((ValueError,TypeError,NotImplementedError)):
                fig.subplot_mosaic(layout,**options)
            self.assertEqual(fig.axes,old);self.assertEqual(fig._gridspecs,grids)
            self.assertIs(fig.gca(),current);self.assertFalse(fig.stale)
        before=azl.get_fignums()
        with self.assertRaises(ValueError):azl.subplot_mosaic('AB;BA')
        self.assertEqual(azl.get_fignums(),before);self.assertIs(azl.gcf(),fig)
        empty=fig.subplot_mosaic('..');self.assertEqual(empty,{})

    def test_mosaic_layout_colorbar_optional_components_and_exports(self):
        for layout in ('tight','constrained'):
            with self.subTest(layout=layout):
                fig,axes=azl.subplot_mosaic('AA;BC',layout=layout,figsize=(9,8),num='Atlas '+layout)
                for label,ax in axes.items():
                    ax.set_extent((-54,-42,-28,-16));ax.set_title(label+' · região')
                    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
                    self.assertIsNone(ax._grid_config);self.assertIsNone(ax._overview)
                axes['A'].scale_bar(length=200);axes['B'].north_arrow();axes['C'].compass()
                fig.colorbar(ScalarMappable(Normalize(0,100)),ax=list(axes.values()),orientation='horizontal',label='Intensidade')
                fig.suptitle('Atlas de mapas nomeados')
                scene=fig.to_scene()
                for _,start,end,_ in scene._layout_groups:
                    box=item_bounds(scene,start,end)
                    if box is not None:
                        x,y,w,h=box;self.assertGreaterEqual(x,-.2);self.assertGreaterEqual(y,-.2)
                        self.assertLessEqual(x+w,scene.width+.2);self.assertLessEqual(y+h,scene.height+.2)
                self.assertIn('Atlas de mapas nomeados',fig.to_svg());self.assertIn('Figure',fig.to_html())
                self.assertEqual(len(fig.axes),3)
                azl.close(fig)

    def test_cax_insets_remove_restore_current_without_reordering(self):
        fig,axes=azl.subplots(1,2);fig.sca(axes[0])
        inset=axes[0].inset_axes((.6,.6,.3,.3));self.assertIs(fig.gca(),axes[0])
        with self.assertRaises(ValueError):plt.sca(inset)
        cax=fig.add_axes((.9,.2,.03,.5));bar=fig.colorbar(ScalarMappable(Normalize(0,1)),ax=axes[0],cax=cax)
        self.assertIs(fig.gca(),cax);bar.remove();self.assertIs(fig.gca(),axes[0])
        fig.delaxes(axes[0]);self.assertIs(fig.gca(),axes[1])
        with self.assertRaises(ValueError):fig.delaxes(axes[0])
        fig.delaxes(axes[1]);self.assertEqual(fig.axes,[]);self.assertIs(fig.gca().figure,fig)


if __name__=='__main__':unittest.main()
