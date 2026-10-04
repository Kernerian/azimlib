"""Physical Figure dimensions, title anchors and startup lifecycle integration."""
import io,json,math,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import azimlib as azl
from azimlib.backends import tk
from azimlib.scene import Text
from azimlib.typography import POINT


class SizingTitleTests(unittest.TestCase):
    def setUp(self):
        azl.ioff();self.fig,self.ax=azl.subplots()
        self.ax.set_extent((-54,-42,-28,-16))
    def tearDown(self):azl.ioff();azl.close('all');azl.rcdefaults()

    def test_size_dpi_and_artist_properties_preserve_view_and_invalidate(self):
        extent=self.ax.get_extent();seen=[];self.fig.add_callback(lambda a:seen.append((a.get_size_inches(),a.get_dpi())))
        self.fig.canvas.draw();self.fig.set_size_inches(8,5,forward=False)
        self.assertTrue(self.fig.stale);self.assertEqual(seen,[((8.,5.),100.)])
        self.fig.set_dpi(150);self.assertEqual(self.fig.canvas.get_width_height(),(1200,750))
        self.fig.set_figwidth(6);self.fig.set_figheight(4)
        self.assertEqual(self.fig.get_size_inches(),(6,4));self.assertEqual(self.ax.get_extent(),extent)
        self.assertEqual(azl.getp(self.fig,'dpi'),150)
        azl.setp(self.fig,size_inches=(5,4),dpi=200)
        self.assertEqual(self.fig.canvas.get_width_height(),(1000,800))

    def test_invalid_dimensions_and_dpi_are_atomic_without_viewer_calls(self):
        viewer=Mock(closed=False);self.fig._viewer=viewer;self.fig.canvas.draw()
        for method,args in [('set_size_inches',v) for v in [(-1,4),(0,4),(math.inf,4),([4],),([4,3,2],),(None,)]]+[
            ('set_dpi',(v,)) for v in (0,-1,math.nan,math.inf,None,'invalid')]:
            with self.subTest(method=method,args=args):
                with self.assertRaises(ValueError):getattr(self.fig,method)(*args)
                self.assertEqual(self.fig.get_size_inches(),(6.4,4.8));self.assertEqual(self.fig.get_dpi(),100)
                self.assertFalse(self.fig.stale);viewer.resize_figure.assert_not_called()
        self.fig._viewer=None

    def test_forward_flag_and_closed_viewer(self):
        viewer=Mock(closed=False);self.fig._viewer=viewer
        self.fig.set_size_inches((4,3),forward=False);viewer.resize_figure.assert_not_called()
        self.fig.set_size_inches(5,4);viewer.resize_figure.assert_called_once_with(500,400)
        self.fig.set_dpi(150);viewer.resize_figure.assert_called_with(750,600)
        viewer.closed=True;viewer.resize_figure.reset_mock();self.fig.set_figwidth(6)
        viewer.resize_figure.assert_not_called();self.fig._viewer=None

    def test_dpi_changes_scene_scale_without_changing_layout_or_font_points(self):
        self.fig.set_layout_engine('constrained');title=self.ax.set_title('Physical title',pad=12)
        self.fig.to_scene();position=self.ax.position
        for dpi in (72,100,150,200):
            with self.subTest(dpi=dpi):
                self.fig.set_dpi(dpi);scene=self.fig.to_scene()
                for a,b in zip(position,self.ax.position):self.assertAlmostEqual(a,b)
                item=next(i for i in scene.items if isinstance(i,Text) and i.text=='Physical title')
                self.assertAlmostEqual(item.style['font_size'],title.get_fontsize()*dpi/72)
                self.assertAlmostEqual(scene.width,6.4*dpi)

    def test_three_titles_reuse_hide_remove_and_clear_independently(self):
        titles={loc:self.ax.set_title(loc,loc=loc) for loc in ('left','center','right')}
        self.assertEqual(len({id(a) for a in titles.values()}),3)
        for loc,artist in titles.items():self.assertIs(artist,self.ax.set_title('New '+loc,loc=loc))
        titles['left'].set_visible(False);titles['right'].remove()
        svg=self.fig.to_svg();self.assertNotIn('New left',svg);self.assertNotIn('New right',svg);self.assertIn('New center',svg)
        self.ax.clear();self.fig.canvas.draw()
        for artist in titles.values():
            self.assertIsNone(artist.get_figure());artist.set_text('Detached')
        self.assertFalse(self.fig.stale)

    def test_title_location_anchor_is_independent_of_text_alignment_and_html_metadata(self):
        for loc,ha in [('left','right'),('center','left'),('right','center')]:
            with self.subTest(loc=loc,ha=ha):
                self.ax.set_title(loc,loc=loc,ha=ha,pad=12)
                scene=self.fig.to_scene();x,y,w,h=scene.maps[0]['box']
                item=next(i for i in scene.items if isinstance(i,Text) and i.text==loc)
                self.assertAlmostEqual(item.x,x+{'left':0,'center':.5,'right':1}[loc]*w)
                self.assertAlmostEqual(item.y,y-12*POINT)
                anchor=next(a for a in scene.maps[0]['anchor_ranges'] if any(scene.items[i] is item for i in a['indices']))
                self.assertEqual(anchor['align'],loc)

    def test_title_defaults_validation_and_fontdict_precedence(self):
        with azl.rc_context({'axes.titlelocation':'right','axes.titlepad':10}):
            title=self.ax.set_title('Right',{'fontsize':9,'color':'red'},fontsize=11)
        self.assertIs(title,self.ax._right_title);self.assertEqual(title.get_fontsize(),11)
        self.fig.canvas.draw()
        for kwargs in ({'loc':'bottom'},{'pad':math.nan},{'loc':'left','fontsize':-1}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):self.ax.set_title('Invalid',**kwargs)
                self.assertIsNone(self.ax._left_title);self.assertFalse(self.fig.stale)

    def test_png_resolution_override_does_not_mutate_figure_size_dpi_or_create_viewer(self):
        from azimlib import renderers
        self.fig.set_size_inches(4,3);self.fig.set_dpi(150)
        with patch.object(renderers,'render_png') as render:
            stream=io.BytesIO();self.fig.savefig(stream,format='png',dpi=300)
        scene=render.call_args.args[0];self.assertEqual((scene.width,scene.height),(600,450))
        self.assertEqual(render.call_args.kwargs['scale'],2)
        self.assertEqual(self.fig.get_size_inches(),(4,3));self.assertEqual(self.fig.get_dpi(),150)
        self.assertFalse(hasattr(self.fig,'_viewer'))

    def test_first_tk_draw_is_registered_and_has_callbacks_before_emission(self):
        events=[];old=self.fig.canvas;cid=old.mpl_connect('draw_event',events.append)
        viewer=Mock(closed=False,_event_callbacks={},_callback_id=0)
        def draw():
            self.assertIs(self.fig.canvas,viewer);self.assertIs(self.fig._viewer,viewer)
            self.assertIn(viewer,tk._windows)
            for name,callback in tuple(viewer._event_callbacks.values()):
                if name=='draw_event':callback(SimpleNamespace(canvas=viewer))
        viewer.draw.side_effect=draw
        with patch.object(tk,'FigureWindow',return_value=viewer) as factory:
            self.assertIs(tk.show(self.fig,block=False),viewer)
        factory.assert_called_once_with(self.fig,initial_draw=False)
        self.assertEqual(len(events),1);self.assertEqual(viewer._callback_id,cid)
        tk._windows.remove(viewer);self.fig._viewer=None;self.fig.canvas=old

    def test_failed_startup_restores_canvas_registry_and_can_retry(self):
        old=self.fig.canvas;viewer=Mock(closed=False,_event_callbacks={},_callback_id=0)
        viewer.draw.side_effect=ValueError('draw failed')
        def close():
            viewer.closed=True;tk._windows.remove(viewer);self.fig._closed=True
            if self.fig in azl._figures:azl._figures.remove(self.fig)
        viewer.close.side_effect=close
        with patch.object(tk,'FigureWindow',return_value=viewer):
            with self.assertRaisesRegex(ValueError,'draw failed'):tk.show(self.fig,block=False)
        self.assertIs(self.fig.canvas,old);self.assertIsNone(self.fig._viewer)
        self.assertIn(self.fig,azl._figures);self.assertFalse(self.fig._closed)

    def test_recorded_dimension_title_contracts(self):
        import importlib.util
        root=Path(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location('sizing_reference_tool',root/'tools/inspect_sizing_titles.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        reference=json.loads((root/'docs/sizing-titles-reference.json').read_text(encoding='utf-8'))
        self.assertEqual(module.contracts(azl),reference['matplotlib'])
