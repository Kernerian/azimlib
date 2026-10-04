"""Viewer event/navigation contracts; no display or Tk import is required."""
from types import SimpleNamespace
from unittest.mock import Mock
from pathlib import Path
import json
import unittest
import azimlib as azl
from azimlib.backends import tk
from azimlib.navigation import Navigation


class TkEventTests(unittest.TestCase):
    def setUp(self):
        self.fig,self.ax=azl.subplots(figsize=(4,3))
        self.ax.set_extent((-60,-40,-30,-10))
        self.viewer=object.__new__(tk.FigureWindow)
        v=self.viewer
        v.figure=self.fig;v.scene=self.fig.to_scene();v.navigation=Navigation(self.fig)
        v._event_callbacks={};v._callback_id=0;v.closed=False;v._drawing=False
        v._pending=v._resize_pending=None
        from azimlib.backends._raster_cache import RasterCache
        v._raster_cache=RasterCache()
        v.draw_idle=Mock();v.window=Mock();v._hide_tip=Mock()
        x,y,w,h=v.scene.maps[0]['box']
        self.event=SimpleNamespace(x=x+w/2,y=y+h/2,num=1,delta=120)

    def tearDown(self):
        if self.viewer in tk._windows:tk._windows.remove(self.viewer)
        azl.close('all')

    def test_scroll_steps_coordinates_and_cursor_anchor(self):
        events=[];v=self.viewer;v.mpl_connect('scroll_event',events.append)
        for delta in (120,-240,60,0):
            with self.subTest(delta=delta):
                self.ax.set_extent((-60,-40,-30,-10))
                self.event.delta=delta
                old_index=v.navigation.index
                v.wheel(self.event)
                event=events[-1];step=delta/120
                self.assertEqual(event.step,step)
                self.assertEqual(event.button,'up' if step>0 else 'down' if step<0 else None)
                self.assertIs(event.canvas,v);self.assertIs(event.inaxes,self.ax)
                self.assertAlmostEqual(event.xdata,-50);self.assertAlmostEqual(event.ydata,-20)
                self.assertEqual(event.y,int(v.scene.height-self.event.y))
                extent=self.ax.get_extent()
                self.assertAlmostEqual(extent[1]-extent[0],20/1.2**step)
                self.assertAlmostEqual((extent[0]+extent[1])/2,-50)
                if not step:self.assertEqual(v.navigation.index,old_index)

    def test_linux_scroll_and_scroll_outside_axes(self):
        events=[];v=self.viewer;v.mpl_connect('scroll_event',events.append)
        for direction in (1,-1):
            with self.subTest(direction=direction):
                event=SimpleNamespace(x=self.event.x,y=self.event.y,num=4 if direction>0 else 5)
                v.wheel(event,direction)
                self.assertEqual(events[-1].step,direction)
                self.assertEqual(events[-1].button,'up' if direction>0 else 'down')
        extent=self.ax.get_extent();index=v.navigation.index
        v.wheel(SimpleNamespace(x=0,y=0,delta=120))
        self.assertIsNone(events[-1].inaxes);self.assertIsNone(events[-1].xdata)
        self.assertEqual(events[-1].step,1)
        self.assertEqual(self.ax.get_extent(),extent);self.assertEqual(v.navigation.index,index)

    def test_disconnect_and_connect_during_dispatch(self):
        v=self.viewer;calls=[]
        def first(event):
            calls.append('first');v.mpl_disconnect(second)
            v.mpl_connect('draw_event',lambda e:calls.append('new'))
        v.mpl_connect('draw_event',first)
        second=v.mpl_connect('draw_event',lambda e:calls.append('removed'))
        v.mpl_connect('draw_event',lambda e:calls.append('last'))
        v._emit('draw_event');self.assertEqual(calls,['first','removed','last'])
        calls.clear();v._emit('draw_event');self.assertEqual(calls,['first','last','new'])

    def test_headless_canvas_dispatch_uses_same_snapshot_rule(self):
        canvas=self.fig.canvas;calls=[]
        def first(event):
            calls.append('first');canvas.mpl_disconnect(second)
        canvas.mpl_connect('draw_event',first)
        second=canvas.mpl_connect('draw_event',lambda e:calls.append('removed'))
        canvas.draw();self.assertEqual(calls,['first','removed'])
        calls.clear();canvas.draw();self.assertEqual(calls,['first'])

    def test_draw_event_exposes_own_scene(self):
        events=[];self.viewer.mpl_connect('draw_event',events.append)
        self.viewer._emit('draw_event')
        self.assertIs(events[0].renderer,self.viewer.scene)
        self.assertEqual(events[0].name,'draw_event')

    def test_selected_contracts_recorded_from_real_matplotlib_tkagg(self):
        reference=json.loads((Path(__file__).resolve().parents[1]/'docs/tk-events-reference.json').read_text())
        events=[];v=self.viewer;v.mpl_connect('scroll_event',events.append)
        for case in reference['windows_scroll']:
            with self.subTest(delta=case['delta']):
                v.wheel(SimpleNamespace(x=205,y=149,delta=case['delta']))
                actual=events[-1]
                self.assertEqual(dict(delta=case['delta'],step=actual.step,button=actual.button,
                                      inaxes=actual.inaxes is self.ax,x=actual.x,y=actual.y),case)
        for case in reference['linux_scroll']:
            with self.subTest(num=case['num']):
                v.wheel(SimpleNamespace(x=205,y=149,num=case['num']),1 if case['num']==4 else -1)
                self.assertEqual(dict(num=case['num'],step=events[-1].step,button=events[-1].button),case)
        calls=[];v._event_callbacks={}
        def first(event):
            calls.append('first');v.mpl_disconnect(second)
            v.mpl_connect('draw_event',lambda e:calls.append('new'))
        v.mpl_connect('draw_event',first)
        second=v.mpl_connect('draw_event',lambda e:calls.append('removed'))
        v.mpl_connect('draw_event',lambda e:calls.append('last'))
        v._emit('draw_event');first_calls=list(calls);calls.clear();v._emit('draw_event')
        self.assertEqual([first_calls,calls],reference['callback_dispatch'])

    def test_resize_coalesces_and_clears_timer(self):
        v=self.viewer;events=[];v.mpl_connect('resize_event',events.append)
        v.window.after.side_effect=['first','second']
        v.resize(SimpleNamespace(width=420,height=310))
        v.resize(SimpleNamespace(width=440,height=320))
        v.window.after_cancel.assert_called_once_with('first')
        self.assertEqual(self.fig.figsize,(4.4,3.2))
        self.assertEqual(v._resize_pending,'second')
        v._resize_redraw()
        self.assertIsNone(v._resize_pending);v.draw_idle.assert_called_once()
        self.assertEqual(len(events),2)
        v.closed=True;v.resize(SimpleNamespace(width=500,height=400))
        self.assertEqual(self.fig.figsize,(4.4,3.2))

    def test_close_cleans_up_even_if_callback_raises(self):
        v=self.viewer;tk._windows.append(v)
        window=v.window
        v._pending='idle';v._resize_pending='resize'
        image=Mock();v._image=image
        v._photo=v._initial_image=v._initial_scene=object()
        def callback(event):
            v.close()  # Reentrancy must not emit another close event.
            raise ValueError('user callback')
        v.mpl_connect('close_event',callback)
        with self.assertRaisesRegex(ValueError,'user callback'):v.close()
        self.assertTrue(v.closed);self.assertTrue(self.fig._closed)
        self.assertNotIn(v,tk._windows)
        self.assertNotIn(self.fig,azl._figures)
        window.destroy.assert_called_once()
        self.assertEqual(window.after_cancel.call_count,2)
        self.assertIsNone(v.window);self.assertIsNone(v.widget);self.assertIsNone(v.message)
        self.assertIsNone(v._image);self.assertIsNone(v._photo)
        image.close.assert_called_once()
        self.assertIsNone(v._pending);self.assertIsNone(v._resize_pending)
        v.close();window.destroy.assert_called_once()


if __name__=='__main__':unittest.main()
