"""Frozen-drag navigation contracts; no Matplotlib dependency."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import azimlib as azl
from azimlib.backends.tk import FigureWindow
from azimlib.navigation import Navigation,drag_extent,viewport_from_metadata
from azimlib.scene import Text

ROOT=Path(__file__).resolve().parents[1]


class PanInteractionTests(unittest.TestCase):
    def tearDown(self):azl.close('all')

    def test_selected_reference_drags_and_frozen_start(self):
        reference=json.loads((ROOT/'docs/pan-interaction-reference.json').read_text(encoding='utf-8'))
        fig,ax=azl.subplots();ax.set_extent(reference['initial_extent'])
        viewport=viewport_from_metadata(ax.projection,fig.to_scene().maps[0])
        self.assertEqual(len(reference['cases']),60)
        for case in reference['cases']:
            with self.subTest(button=case['button'],key=case['key'],start=case['start'],end=case['end']):
                # Previous motion must never become the anchor of this drag.
                ax.set_extent((-65,-35,-25,5))
                extent=drag_extent(ax,viewport,case['start'],case['end'],button=case['button'],
                                   constraint=case['key'],initial_extent=reference['initial_extent'])
                for own,expected in zip(extent,case['extent']):self.assertAlmostEqual(own,expected,places=10)

    def viewer(self,fig):
        viewer=object.__new__(FigureWindow)
        viewer.figure=fig;viewer.scene=fig.to_scene();viewer.navigation=Navigation(fig)
        viewer.mode='pan';viewer.constraint=None;viewer.drag=None;viewer.closed=False
        viewer._overview_box=None;viewer.widget=Mock();viewer.widget.cget.return_value='fleur'
        viewer.message=Mock();viewer._emit=Mock();viewer.draw_idle=Mock();viewer._display=Mock()
        return viewer

    def test_motion_changes_live_limits_and_release_pushes_once(self):
        fig,axes=azl.subplots(1,2,sharex=True,figsize=(6,3))
        left,right=axes
        for ax in axes:ax.set_extent((-76,-32,-36,8))
        viewer=self.viewer(fig);viewport=viewer._viewport(0)
        x,y,w,h=viewport.box;start=(x+w*.5,y+h*.5);initial=left.get_extent()
        viewer.press(SimpleNamespace(x=start[0],y=start[1],num=1,state=0))
        for dx,dy in ((12,4),(25,-8)):
            event=SimpleNamespace(x=start[0]+dx,y=start[1]+dy,state=256)
            viewer.motion(event)
            expected=drag_extent(left,viewport,start,(event.x,event.y),initial_extent=initial)
            self.assertEqual(left.get_extent(),expected)
            self.assertEqual(right.get_xlim(),left.get_xlim())
            self.assertEqual(right.get_ylim(),initial[2:])
            self.assertEqual(viewer.navigation.index,0)
        viewer._display.assert_not_called()  # No translated bitmap preview.
        self.assertEqual(viewer.draw_idle.call_count,2)
        panned=left.get_extent()
        viewer.release(SimpleNamespace(x=event.x,y=event.y,num=1,state=0))
        self.assertEqual(left.get_extent(),panned)
        self.assertEqual(len(viewer.navigation.history),2)
        self.assertIsNone(viewer.drag)

    def test_ticks_move_and_axes_frame_stays_fixed_during_pan(self):
        fig,ax=azl.subplots();ax.set_extent((-76,-32,-36,8))
        ax.set_xticks([-70,-60,-50,-40],labels=['west','middle','east','far'])
        viewer=self.viewer(fig);before=viewer.scene;viewport=viewer._viewport(0)
        x,y,w,h=viewport.box;start=(x+w*.5,y+h*.5)
        viewer.press(SimpleNamespace(x=start[0],y=start[1],num=1,state=0))
        viewer.motion(SimpleNamespace(x=start[0]+20,y=start[1]+10,state=256))
        after=fig.to_scene()
        a=next(item for item in before.items if isinstance(item,Text) and item.text=='middle')
        b=next(item for item in after.items if isinstance(item,Text) and item.text=='middle')
        self.assertAlmostEqual(b.x-a.x,20,places=7)
        for old,new in zip(before.maps[0]['box'],after.maps[0]['box']):self.assertAlmostEqual(old,new,places=7)
        viewer._display.assert_not_called()

    def test_stationary_pan_preserves_extent_and_history(self):
        fig,ax=azl.subplots();ax.set_extent((-76,-32,-36,8));viewer=self.viewer(fig)
        viewport=viewer._viewport(0);x,y,w,h=viewport.box
        event=SimpleNamespace(x=x+w*.5,y=y+h*.5,num=1,state=0)
        initial=ax.get_extent();viewer.press(event);viewer.release(event)
        self.assertEqual(ax.get_extent(),initial);self.assertEqual(len(viewer.navigation.history),1)

    def test_missing_release_finishes_at_last_held_position(self):
        for button,mask in ((1,256),(3,1024)):
            for recovery in ('enter','motion'):
                with self.subTest(button=button,recovery=recovery):
                    fig,ax=azl.subplots();ax.set_extent((-76,-32,-36,8))
                    viewer=self.viewer(fig);vp=viewer._viewport(0)
                    x,y,w,h=vp.box;start=(x+w*.5,y+h*.5)
                    viewer.press(SimpleNamespace(x=start[0],y=start[1],num=button,state=0))
                    viewer.motion(SimpleNamespace(x=start[0]+20,y=start[1]-10,state=mask))
                    held=ax.get_extent();viewer.leave(SimpleNamespace(x=-10,y=20,state=mask))
                    getattr(viewer,recovery)(SimpleNamespace(x=start[0]-80,y=start[1]+90,state=0))
                    self.assertEqual(ax.get_extent(),held)
                    self.assertIsNone(viewer.drag)
                    self.assertEqual(len(viewer.navigation.history),2)
                    viewer.motion(SimpleNamespace(x=start[0]+90,y=start[1]+60,state=0))
                    viewer.release(SimpleNamespace(x=start[0]+90,y=start[1]+60,num=button,state=0))
                    self.assertEqual(ax.get_extent(),held)
                    self.assertEqual(len(viewer.navigation.history),2)
                    # A new grab uses the current view, not stale display metadata.
                    viewer.press(SimpleNamespace(x=start[0],y=start[1],num=button,state=0))
                    viewer.motion(SimpleNamespace(x=start[0]+8,y=start[1]+5,state=mask))
                    expected=drag_extent(ax,viewer.drag['viewport'],start,(start[0]+8,start[1]+5),
                                         button=button,initial_extent=held)
                    self.assertEqual(ax.get_extent(),expected)

    def test_held_drag_continues_outside_axes_and_across_canvas_reentry(self):
        fig,ax=azl.subplots();ax.set_extent((-76,-32,-36,8));viewer=self.viewer(fig)
        vp=viewer._viewport(0);x,y,w,h=vp.box;start=(x+w*.5,y+h*.5);initial=ax.get_extent()
        viewer.press(SimpleNamespace(x=start[0],y=start[1],num=1,state=0))
        viewer.leave(SimpleNamespace(x=x-5,y=start[1],state=256))
        viewer.motion(SimpleNamespace(x=x-5,y=start[1],state=256))
        self.assertIsNotNone(viewer.drag)
        self.assertEqual(ax.get_extent(),drag_extent(ax,vp,start,(x-5,start[1]),initial_extent=initial))
        viewer.enter(SimpleNamespace(x=start[0]+10,y=start[1],state=256))
        viewer.motion(SimpleNamespace(x=start[0]+10,y=start[1],state=256))
        self.assertEqual(ax.get_extent(),drag_extent(ax,vp,start,(start[0]+10,start[1]),initial_extent=initial))
        self.assertEqual(len(viewer.navigation.history),1)

    def test_new_gesture_retires_old_preview_and_zoom_lost_release_cancels_box(self):
        fig,ax=azl.subplots();viewer=self.viewer(fig);vp=viewer._viewport(0)
        x,y,w,h=vp.box;start=(x+w*.5,y+h*.5);viewer._pan_raster=Mock()
        viewer._pan_prefetched=True;viewer.press(SimpleNamespace(x=start[0],y=start[1],num=1,state=0))
        viewer._pan_raster.clear.assert_called_once();self.assertFalse(viewer._pan_prefetched)
        viewer.mode='zoom';initial=ax.get_extent()
        viewer.motion(SimpleNamespace(x=start[0]+20,y=start[1]+20,state=256))
        viewer.enter(SimpleNamespace(x=start[0]+50,y=start[1]+50,state=0))
        self.assertIsNone(viewer.drag);self.assertEqual(ax.get_extent(),initial)
        self.assertEqual(len(viewer.navigation.history),1)
        viewer.widget.delete.assert_called_with('rubberband')

    def test_cursor_viewport_uses_current_unpainted_model_and_matches_full_scene(self):
        for projection in ('equirectangular','mercator','albers'):
            for extent in ((-79,-35,-34,9),(-55,-43,-27,-13)):
                with self.subTest(projection=projection,extent=extent):
                    fig,ax=azl.subplots(projection=projection);ax.set_extent((-76,-32,-36,8))
                    viewer=self.viewer(fig);ax.set_extent(extent)
                    current=viewer._viewport(0)
                    expected=viewport_from_metadata(ax.projection,fig.to_scene().maps[0])
                    for name in ('scale','ox','oy'):
                        self.assertAlmostEqual(getattr(current,name),getattr(expected,name),places=7)
                    for actual,wanted in zip(current.box,expected.box):self.assertAlmostEqual(actual,wanted,places=7)
                    x,y,w,h=current.box
                    for point in ((x+w*.25,y+h*.75),(x+w*.5,y+h*.5)):
                        for actual,wanted in zip(current.inverse(*point),expected.inverse(*point)):
                            self.assertAlmostEqual(actual,wanted,places=10)

    def test_mercator_right_drag_preserves_projected_cursor_anchor(self):
        fig,ax=azl.subplots(projection='mercator');ax.set_extent((-76,-32,-36,8))
        viewport=viewport_from_metadata(ax.projection,fig.to_scene().maps[0])
        x,y,w,h=viewport.box;start=(x+w*.35,y+h*.45);anchor=viewport.inverse(*start)
        original=ax.get_extent()
        ax.set_extent(drag_extent(ax,viewport,start,(start[0]+30,start[1]-15),button=3,initial_extent=original))
        projected=viewport_from_metadata(ax.projection,fig.to_scene().maps[0]).project(*anchor)
        for actual,expected in zip(projected,start):self.assertAlmostEqual(actual,expected,places=6)

    def test_tooltip_is_immediate_right_aligned_and_removed_on_leave(self):
        viewer=object.__new__(FigureWindow);viewer.closed=False;viewer._tooltip=None
        viewer.tk=Mock();viewer.window=Mock();button=Mock()
        button.winfo_rootx.return_value=120;button.winfo_rooty.return_value=300;button.winfo_width.return_value=28
        viewer._show_tip(button,'Reset original view')
        viewer.tk.Toplevel.assert_called_once_with(button)
        viewer._tooltip.wm_geometry.assert_called_once_with('+148+300')
        viewer.tk.Label.return_value.pack.assert_called_once_with(ipadx=1)
        viewer.window.after.assert_not_called()
        tip=viewer._tooltip;viewer._hide_tip();tip.destroy.assert_called_once_with()
        self.assertIsNone(viewer._tooltip)


if __name__=='__main__':unittest.main()
