"""Measured layout, live edits, manual control and independent exports."""
import io
import unittest
from unittest.mock import patch
import azimlib as azl
from azimlib import ticker
from azimlib.cm import ScalarMappable
from azimlib.colors import Normalize
from azimlib.layout_engine import TightLayoutEngine,ConstrainedLayoutEngine,PlaceHolderLayoutEngine,item_bounds,primitive_bounds
from azimlib.scene import Text


class LayoutTests(unittest.TestCase):
    def tearDown(self):azl.close('all')
    def decorate(self,ax):
        ax.set_extent((-54,-42,-28,-16))
        ax.set_title('Título regional\nSegunda linha',fontsize=14)
        ax.set_xlabel('Longitude geográfica');ax.set_ylabel('Latitude geográfica')
        ax.xaxis.set_major_formatter(ticker.LongitudeFormatter())
        ax.yaxis.set_major_formatter(ticker.LatitudeFormatter())
        ax.tick_params(labelsize=12,labelrotation=25)
    def assert_inside(self,scene,rect=None):
        left,top,right,bottom=rect or (0,0,scene.width,scene.height)
        for _,start,end,_ in scene._layout_groups:
            box=item_bounds(scene,start,end)
            if box is None:continue
            x,y,w,h=box
            self.assertGreaterEqual(x,left-.2);self.assertGreaterEqual(y,top-.2)
            self.assertLessEqual(x+w,right+.2);self.assertLessEqual(y+h,bottom+.2)
    def test_import_alias_and_default_manual_layout(self):
        fig,ax=azl.subplots();self.assertIsNone(fig.get_layout_engine())
        position=ax.position;ax.set_title('Título');fig.to_scene()
        self.assertEqual(position,ax.position)
        self.assertFalse(any(l.kind=='grid' for l in ax.layers))
        self.assertIsNone(ax._overview)
        manual,_=azl.subplots(layout='none');self.assertIsNone(manual.get_layout_engine())
        engine=TightLayoutEngine()
        managed,_=azl.subplots(layout=engine);self.assertIs(managed.get_layout_engine(),engine)
        engine.set(rect=None);self.assertEqual(engine.get()['rect'],(0,0,1,1))
    def test_grid_decorations_fit_without_neighbor_overlap(self):
        fig,axs=azl.subplots(2,2,figsize=(9,8),layout='constrained')
        for ax in axs.flat:self.decorate(ax)
        fig.suptitle('Atlas geográfico')
        scene=fig.to_scene();self.assert_inside(scene)
        boxes=[item_bounds(scene,start,end) for _,start,end,_ in scene._layout_groups]
        self.assertLess(boxes[0][0]+boxes[0][2],boxes[1][0])
        self.assertLess(boxes[0][1]+boxes[0][3],boxes[2][1])
        self.assertLess(scene._layout_suptitle[1]+scene._layout_suptitle[3],boxes[0][1])
    def test_tight_is_once_but_engine_reacts_to_text_and_resize(self):
        fig,ax=azl.subplots(figsize=(5,5));self.decorate(ax);fig.tight_layout()
        first=ax.position;ax.set_title('Title\nLine\nAnother line',fontsize=20);fig.to_scene()
        self.assertEqual(first,ax.position);self.assertIsInstance(fig.get_layout_engine(),PlaceHolderLayoutEngine)
        fig.set_layout_engine('tight');self.assert_inside(fig.to_scene())
        self.assertNotEqual(first,ax.position)
        fig.figsize=(6,7);self.assert_inside(fig.to_scene())
    def test_external_legend_reserves_space_and_visibility_releases_it(self):
        fig,ax=azl.subplots(figsize=(7,5),layout='tight');ax.set_extent((-54,-42,-26,-18))
        line,=ax.plot([-52,-44],[-24,-20],label='Rota de pesquisa')
        legend=ax.legend([line],['Rota de pesquisa'],loc='center left',bbox_to_anchor=(1.03,.5))
        self.assert_inside(fig.to_scene());reserved=ax.position
        legend.set_visible(False);fig.to_scene();hidden=ax.position
        self.assertGreater(hidden[2],reserved[2])
        legend.set_visible(True);legend.set_in_layout(False);scene=fig.to_scene()
        self.assertEqual(hidden,ax.position)
        self.assertTrue(any(isinstance(p,Text) and p.text=='Rota de pesquisa' for p in scene.items))
    def test_in_layout_text_exclusion_does_not_hide_text(self):
        fig,ax=azl.subplots(figsize=(5,5),layout='tight');ax.set_extent((-54,-42,-28,-16))
        title=ax.set_title('One\nTwo\nThree',fontsize=20);fig.to_scene();reserved=ax.position
        title.set_in_layout(False);scene=fig.to_scene()
        self.assertGreater(ax.position[3],reserved[3])
        self.assertTrue(any(isinstance(p,Text) and p.text=='Three' for p in scene.items))
        title.set(in_layout=True);fig.to_scene();self.assertEqual(reserved,ax.position)
    def test_horizontal_vertical_and_shared_colorbars_fit(self):
        for orientation in ('vertical','horizontal'):
            with self.subTest(orientation=orientation):
                fig,axs=azl.subplots(1,2,figsize=(9,5),layout='constrained')
                for ax in axs.flat:self.decorate(ax)
                bar=fig.colorbar(ScalarMappable(norm=Normalize(0,100)),ax=axs,
                                 orientation=orientation,label='Indicador sintético',format='%.0f%%')
                self.assert_inside(fig.to_scene())
                positions=[ax.position for ax in axs.flat]
                bar.remove();self.assert_inside(fig.to_scene())
                self.assertNotEqual(positions,[ax.position for ax in axs.flat])
                fig,ax=azl.subplots(figsize=(5,5),layout='tight');self.decorate(ax)
                fig.colorbar(ScalarMappable(norm=Normalize(0,100)),ax=ax,orientation=orientation,label='Valor')
                self.assert_inside(fig.to_scene())
    def test_cax_and_add_axes_stay_at_explicit_positions(self):
        fig=azl.figure(figsize=(7,5),layout='tight')
        cax=fig.add_axes((.92,.25,.02,.5));position=cax.position
        ax=fig.add_subplot(111);self.decorate(ax)
        fig.colorbar(ScalarMappable(norm=Normalize(0,1)),ax=ax,cax=cax)
        fig.to_scene();self.assertEqual(position,cax.position)
        fig.set_layout_engine('none');fig.subplots_adjust(left=.2)
        self.assertEqual(position,cax.position);self.assertEqual(ax.position[0],.2)
    def test_constrained_manual_adjust_warning_then_disable(self):
        fig,ax=azl.subplots(layout='constrained');fig.to_scene();position=ax.position
        with self.assertWarnsRegex(UserWarning,'incompatible'):fig.subplots_adjust(left=.3)
        self.assertEqual(position,ax.position)
        fig.set_layout_engine('none')
        self.assertIsInstance(fig.get_layout_engine(),PlaceHolderLayoutEngine)
        with self.assertWarnsRegex(UserWarning,'incompatible'):fig.subplots_adjust(left=.3)
        fig.set_layout_engine(None);fig.subplots_adjust(left=.3);fig.to_scene()
        self.assertEqual(ax.position[0],.3)
    def test_dpi_preserves_physical_layout_and_exports(self):
        positions=[]
        for dpi in (100,200):
            fig,ax=azl.subplots(figsize=(5,5),dpi=dpi,layout='tight');self.decorate(ax)
            self.assert_inside(fig.to_scene());positions.append(ax.position)
            stream=io.StringIO();fig.savefig(stream,format='svg')
            self.assertIn('<svg',stream.getvalue());self.assertIn('Longitude',stream.getvalue())
            self.assertIn('azimlib',fig.to_html().lower())
        for a,b in zip(*positions):self.assertAlmostEqual(a,b)
    def test_labelpad_and_large_ticks_have_real_clearance(self):
        fig,ax=azl.subplots(figsize=(6,6),layout='tight');ax.set_extent((-54,-42,-28,-16))
        ax.tick_params(labelsize=22)
        ax.set_xlabel('Longitude',labelpad=12);ax.set_ylabel('Latitude',labelpad=12)
        scene=fig.to_scene();self.assert_inside(scene)
        x,y,w,h=scene.maps[0]['box']
        xlabel=next(p for p in scene.items if isinstance(p,Text) and p.text=='Longitude')
        ylabel=next(p for p in scene.items if isinstance(p,Text) and p.text=='Latitude')
        ticks=[primitive_bounds(scene.items[i]) for i in scene.maps[0]['tick_indices'] if isinstance(scene.items[i],Text)]
        self.assertGreaterEqual(primitive_bounds(xlabel)[1]-max(b[1]+b[3] for b in ticks if b[1]>=y+h),12*100/72-.2)
        self.assertLessEqual(primitive_bounds(ylabel)[0]+primitive_bounds(ylabel)[2],min(b[0] for b in ticks if b[0]+b[2]<=x)-12*100/72+.2)
    def test_measurement_does_not_reproject_geographic_layers(self):
        fig,ax=azl.subplots(layout='tight');ax.line([(-52,-25),(-44,-20)])
        from azimlib import render_map
        original=render_map._geometry
        with patch.object(render_map,'_geometry',wraps=original) as project:
            fig.to_scene();self.assertEqual(project.call_count,1)
    def test_failure_is_atomic_and_options_validated_before_changes(self):
        fig,ax=azl.subplots(figsize=(2,2));ax.set_extent((-54,-42,-28,-16))
        ax.set_title('Too large\nToo large\nToo large',fontsize=40)
        position=ax.position;pars=dict(fig.subplotpars)
        with self.assertWarnsRegex(UserWarning,'Previous positions'):fig.tight_layout()
        self.assertEqual(position,ax.position);self.assertEqual(pars,fig.subplotpars)
        engine=TightLayoutEngine();parameters=engine.get()
        for kwargs in ({'pad':-1},{'rect':(0,0,2,1)},{'w_pad':float('nan')}):
            with self.assertRaises(ValueError):engine.set(**kwargs)
            self.assertEqual(parameters,engine.get())
        with self.assertRaises(ValueError):ConstrainedLayoutEngine(rect=(.2,.2,1,1))
    def test_rect_and_excluded_axes(self):
        fig,axs=azl.subplots(1,2,figsize=(9,5));self.decorate(axs[0]);self.decorate(axs[1])
        axs[1].set_in_layout(False);position=axs[1].position
        fig.tight_layout(rect=(.1,.1,.9,.9));self.assertEqual(position,axs[1].position)
        scene=fig.to_scene();_,start,end,_=scene._layout_groups[0]
        box=item_bounds(scene,start,end)
        self.assertGreaterEqual(box[0],90);self.assertLessEqual(box[0]+box[2],810)
    def test_zoom_preserves_extent_and_recalculates_decorations(self):
        fig,ax=azl.subplots(layout='tight');self.decorate(ax);fig.to_scene()
        ax.zoom(2);extent=ax.get_xlim()+ax.get_ylim()
        self.assert_inside(fig.to_scene());self.assertEqual(extent,ax.get_xlim()+ax.get_ylim())
        self.assertIsNone(ax._overview)
    def test_hidden_axes_still_follow_manual_grid_adjustment(self):
        fig,axs=azl.subplots(1,2)
        axs[1].set_visible(False);axs[1].set_in_layout(False)
        before=axs[1].position;fig.subplots_adjust(left=.2,wspace=.4)
        self.assertNotEqual(before,axs[1].position)
    def test_mixed_grids_are_reported_without_partial_changes(self):
        fig=azl.figure();a=fig.add_subplot(111);b=fig.add_subplot(221)
        before=(a.position,b.position)
        with self.assertWarnsRegex(UserWarning,'mixed subplot'):fig.tight_layout()
        self.assertEqual(before,(a.position,b.position))
