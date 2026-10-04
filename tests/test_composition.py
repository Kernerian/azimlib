"""Composition semantics, live edits and layout lifecycle regressions."""
import io,unittest
import azimlib as az
from azimlib.colors import Normalize
from azimlib.cm import ScalarMappable
from azimlib.scene import Text,Circle,Path
from azimlib.navigation import Navigation
from azimlib.renderers import render_png

class CompositionTests(unittest.TestCase):
    def tearDown(self):az.close('all');az.rcdefaults()
    def legend(self,count=5,**kwargs):
        fig,ax=az.subplots();ax.set_extent((-10,10,-10,10))
        handles=[ax.line([(-9+i,-8),(-9+i,8)],label=f'Item {i}') for i in range(count)]
        legend=ax.legend(handles,loc='upper left',**kwargs)
        return fig,ax,legend
    def test_columns_follow_column_major_order_and_live_text_edits(self):
        fig,ax,legend=self.legend(ncols=2,title='Title')
        scene=fig.to_scene();labels={i.text:i for i in scene.items if isinstance(i,Text) and i.text.startswith('Item')}
        self.assertEqual(labels['Item 0'].x,labels['Item 2'].x)
        self.assertEqual(labels['Item 3'].x,labels['Item 4'].x)
        self.assertGreater(labels['Item 3'].x,labels['Item 2'].x)
        self.assertEqual(labels['Item 0'].y,labels['Item 3'].y)
        legend.get_texts()[0].set_text('Edited');legend.get_texts()[1].set_visible(False)
        legend.get_title().set_color('red');legend.get_frame().set_alpha(.3)
        svg=fig.to_svg();self.assertIn('Edited',svg);self.assertNotIn('Item 1</text>',svg)
        legend.set_ncols(1);fig.to_scene();self.assertGreater(legend._last_box[3],50)
    def test_external_anchor_and_expand_mode_preserve_frame_bounds(self):
        fig,ax,legend=self.legend(ncols=3,bbox_to_anchor=(0,-.1,1,0),mode='expand')
        legend.set_loc('upper center');scene=fig.to_scene();box=scene.maps[0]['box'];frame=legend._last_box
        self.assertGreater(frame[1],box[1]+box[3]);self.assertLess(frame[2],box[2])
        legend.set_bbox_to_anchor((.5,.5),transform='figure');legend.set_loc('center');legend.set(mode=None)
        fig.to_scene();x,y,w,h=legend._last_box
        self.assertAlmostEqual(x+w/2,fig.figsize[0]*50);self.assertAlmostEqual(y+h/2,fig.figsize[1]*50)
        before=dict(legend)
        for values in (dict(ncols=0),dict(bbox_to_anchor=(0,0,-1,1)),dict(loc='bad')):
            with self.assertRaises(ValueError):legend.set(**values)
            self.assertEqual(dict(legend),before)
    def test_best_avoids_data_and_composite_handles_keep_both_symbols(self):
        fig,ax=az.subplots();ax.set_extent((-10,10,0,10))
        points=ax.scatter([6,7,8],[8,8.5,9],s=36,label='Points')
        route=ax.line([(-8,1),(-6,2)],color='red')
        legend=ax.legend([(route,points)],['Composite'],loc='best')
        scene=fig.to_scene();self.assertEqual(legend._last_loc,'upper left')
        self.assertTrue(any(isinstance(i,Circle) and i.clip is None for i in scene.items))
        self.assertTrue(any(isinstance(i,Path) and i.clip is None and i.style.get('stroke')=='red' for i in scene.items))
        legend.set_visible(False);self.assertNotIn('Composite',fig.to_svg())
    def test_shared_bar_changes_all_parent_layouts_and_tracks_shared_norm(self):
        fig,axs=az.subplots(2,2,figsize=(8,8));norm=Normalize(0,4);layers=[]
        for i,ax in enumerate(axs.flat):
            layers.append(ax.scatter([-8,8],[-8,8],c=[i,i+1],norm=norm))
            ax.set_extent((-10,10,-10,10))
        original=[m['box'] for m in fig.to_scene().maps];positions=[a.position for a in axs.flat]
        bar=fig.colorbar(layers[0],ax=axs,orientation='horizontal',label='Shared')
        scene=fig.to_scene();self.assertEqual(sum(isinstance(t,Text) and t.text=='Shared' for t in scene.items),1)
        self.assertTrue(all(m['box'][2]<b[2] for m,b in zip(scene.maps,original)))
        self.assertEqual([a.position for a in axs.flat],positions)
        layers[0].set_clim(0,8);self.assertTrue(all(l.norm.vmax==8 for l in layers))
        bar.set_visible(False);self.assertEqual([m['box'] for m in fig.to_scene().maps],original)
        bar.remove();self.assertEqual(fig._colorbars,[])
    def test_explicit_cax_uses_its_rectangle_and_tick_api_without_map_navigation(self):
        fig,ax=az.subplots();layer=ax.scatter([-8,8],[-8,8],c=[0,1]);ax.set_extent((-10,10,-10,10))
        original=fig.to_scene().maps[0]['box'];cax=fig.add_axes((.91,.2,.025,.6))
        bar=fig.colorbar(layer,cax=cax);self.assertIs(bar.ax,cax)
        cax.set_yticks([0,1],labels=['low','high']);cax.tick_params(labelsize=8,colors='red');cax.set_ylabel('Index')
        scene=fig.to_scene();self.assertEqual(len(scene.maps),1);self.assertEqual(scene.maps[0]['box'],original)
        labels=[i for i in scene.items if isinstance(i,Text) and i.text in ('low','high')]
        self.assertTrue(all(i.style['fill']=='red' and i.style['font_size']==8*100/72 for i in labels))
        self.assertIsNone(Navigation(fig).snapshot()[-1])
        bar.remove();self.assertNotIn(cax,fig.axes)
        bar.remove()  # Detachment is idempotent.
    def test_removing_one_of_equal_shared_bars_preserves_the_other(self):
        fig,axs=az.subplots(1,2);m=ScalarMappable(Normalize(0,1))
        first=fig.colorbar(m,ax=axs.flat);second=fig.colorbar(m,ax=axs.flat)
        second.remove()
        self.assertEqual(len(fig._colorbars),1);self.assertIs(fig._colorbars[0],first)
        self.assertIn('svg',fig.to_svg());first.remove()
    def test_invalid_handle_edits_do_not_corrupt_a_legend(self):
        fig,ax,legend=self.legend();before=dict(legend)
        for options,error in ((dict(handles=[object()]),TypeError),(dict(labels=['only one']),ValueError)):
            with self.assertRaises(error):legend.set(**options)
            self.assertEqual(dict(legend),before)
    def test_scatter_legend_uses_live_mapped_color_and_marker_area(self):
        fig,ax=az.subplots();points=ax.scatter([0,1],[0,1],s=[16,100],c=[0,1],norm=Normalize(0,1),label='Points')
        ax.legend(loc='upper left')
        def sample():return next(i for i in fig.to_scene().items if isinstance(i,Circle) and i.clip is None)
        marker=sample();self.assertEqual(marker.style['fill'],points.to_color(0))
        self.assertAlmostEqual(marker.r,(58**.5)*100/72/2)
        points.set_cmap('plasma');self.assertEqual(sample().style['fill'],points.to_color(0))
    def test_multiline_legend_rows_fit_inside_frame(self):
        fig,ax,legend=self.legend(count=2)
        legend.get_texts()[0].set_text('First\nsecond\nthird')
        scene=fig.to_scene();x,y,w,h=legend._last_box
        from azimlib.label_layout import text_box
        for item in scene.items:
            if isinstance(item,Text) and item.text.startswith(('First','Item')):
                tx,ty,tw,th=text_box(item.x,item.y,item.text,item.style)
                self.assertGreaterEqual(ty,y);self.assertLessEqual(ty+th,y+h)
    def test_colorbar_ownership_validation_is_atomic(self):
        fig,ax=az.subplots();other,alien=az.subplots();m=ScalarMappable(Normalize(0,1))
        for kwargs in (dict(ax=[]),dict(ax=[ax,ax]),dict(ax=[alien]),dict(ax=ax,cax=ax),dict(ax=ax,cax=alien)):
            with self.assertRaises(ValueError):fig.colorbar(m,**kwargs)
            self.assertEqual(fig._colorbars,[])
            self.assertIsNone(ax._colorbar)
    def test_shared_layout_has_real_png_and_svg_exports(self):
        fig,axs=az.subplots(1,2)
        for ax in axs.flat:ax.set_extent((-10,10,-10,10))
        bar=fig.colorbar(ScalarMappable(Normalize(0,1)),ax=axs.flat,label='Shared',location='right')
        output=io.BytesIO();render_png(fig.to_scene(),output)
        self.assertTrue(output.getvalue().startswith(b'\x89PNG'));self.assertIn('Shared',fig.to_svg())

if __name__=='__main__':unittest.main()
