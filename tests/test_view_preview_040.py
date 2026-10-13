"""Provisional navigation never replaces authoritative rendering or edited content."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import azimlib as azl
from azimlib.backends._view_preview import ViewPreview,PreviewBuilder
from azimlib.renderers.pillow import render_image


class PreviewContracts(unittest.TestCase):
    def setUp(self):
        self.fig,self.ax=azl.subplots(figsize=(4,3))
        self.ax.set_extent((-60,-40,-30,-10))
        self.line,=self.ax.plot([-58,-42],[-28,-12],linewidth=2)
        self.ax.set_title('Fixed decoration')
        self.preview=ViewPreview()
    def tearDown(self):self.preview.clear();azl.close('all')
    def capture(self):
        return self.preview.capture(self.fig,self.fig.to_scene(cull=True,interactive=True),render_image)
    def test_view_reuses_one_base_and_round_trip_does_not_accumulate_resampling(self):
        self.assertTrue(self.capture());original=self.preview.ink.tobytes()
        self.ax.set_extent((-59,-39,-30,-10));a=self.preview.render(self.fig)
        self.ax.set_extent((-58,-38,-30,-10));b=self.preview.render(self.fig)
        self.ax.set_extent((-59,-39,-30,-10));c=self.preview.render(self.fig)
        self.assertIsNotNone(a);self.assertEqual(a.tobytes(),c.tobytes())
        self.assertEqual(original,self.preview.ink.tobytes());a.close();b.close();c.close()
    def test_content_edits_invalidate_even_after_draw_complete(self):
        for change in (lambda:self.line.set_color('red'),lambda:self.ax.set_title('Changed'),
                       lambda:self.ax.grid(True),lambda:self.ax.set_bearing(15),
                       lambda:self.fig.set_dpi(120)):
            self.assertTrue(self.capture());change();self.fig._draw_complete()
            self.assertIsNone(self.preview.render(self.fig))
    def test_decorations_stay_fixed_and_export_is_authoritative(self):
        self.assertTrue(self.capture());overlay=self.preview.overlay.tobytes()
        self.ax.set_extent((-55,-45,-25,-15));image=self.preview.render(self.fig)
        self.assertIsNotNone(image);self.assertEqual(overlay,self.preview.overlay.tobytes())
        scene=self.fig.to_scene();expected=render_image(scene)
        # The map outside cached coverage is deliberately provisional.
        self.assertNotEqual(expected.tobytes(),image.tobytes())
        image.close();expected.close()
    def test_budget_and_multiple_maps_fail_closed(self):
        self.preview.MAX_BYTES=1;self.assertFalse(self.capture())
        self.preview.MAX_BYTES=32*1024**2
        self.fig.add_axes((.1,.1,.2,.2));self.assertFalse(self.capture())

    def test_locator_parameter_edits_invalidate_without_replacing_the_locator(self):
        self.assertTrue(self.capture())
        locator=self.ax.xaxis.get_major_locator()
        locator.set_params(nbins=3)
        self.assertIs(locator,self.ax.xaxis.get_major_locator())
        self.assertIsNone(self.preview.render(self.fig))

    def test_fixed_layer_is_reused_only_when_primitives_match(self):
        self.assertTrue(self.capture())
        other=ViewPreview();calls=[]
        try:
            self.assertTrue(other.prepare(self.fig,self.fig.to_scene(),reuse=self.preview))
            self.assertTrue(other.build(lambda scene:(calls.append(scene),render_image(scene))[1]))
            self.assertEqual(len(calls),1)
            self.assertEqual(other.overlay.tobytes(),self.preview.overlay.tobytes())
            self.ax.set_title('Different');calls.clear()
            self.assertTrue(other.prepare(self.fig,self.fig.to_scene(),reuse=self.preview))
            self.assertTrue(other.build(lambda scene:(calls.append(scene),render_image(scene))[1]))
            self.assertEqual(len(calls),2)
        finally:other.clear()

    def test_async_capture_does_not_block_and_discards_mutated_model(self):
        from threading import Event
        import time
        entered=Event();release=Event()
        def renderer(scene):entered.set();release.wait(5);return render_image(scene)
        builder=PreviewBuilder(renderer)
        try:
            self.assertTrue(builder.submit(self.fig,self.fig.to_scene()))
            self.assertTrue(entered.wait(2))
            self.line.set_color('purple');release.set()
            end=time.monotonic()+5
            while builder.busy() and time.monotonic()<end:
                candidate=builder.take(self.fig)
                self.assertIsNone(candidate);time.sleep(.005)
            self.assertFalse(builder.busy())
        finally:release.set();builder.close()

    def test_async_latest_generation_wins_and_renderer_failure_is_optional(self):
        from threading import Event
        import time
        entered=Event();release=Event()
        def renderer(scene):entered.set();release.wait(5);return render_image(scene)
        builder=PreviewBuilder(renderer)
        try:
            builder.submit(self.fig,self.fig.to_scene());self.assertTrue(entered.wait(2))
            self.ax.set_title('Newest');builder.submit(self.fig,self.fig.to_scene());release.set()
            candidate=None;end=time.monotonic()+5
            while candidate is None and time.monotonic()<end:
                candidate=builder.take(self.fig);time.sleep(.005)
            self.assertIsNotNone(candidate);self.assertIsNotNone(candidate.render(self.fig))
            candidate.clear()
        finally:release.set();builder.close()
        def broken(scene):raise RuntimeError('Optional cache unavailable')
        builder=PreviewBuilder(broken)
        try:
            self.assertTrue(builder.submit(self.fig,self.fig.to_scene()))
            end=time.monotonic()+3
            while builder.busy() and time.monotonic()<end:time.sleep(.005)
            self.assertIsNone(builder.take(self.fig));self.assertFalse(builder.busy())
        finally:builder.close()

    def test_worker_snapshot_preserves_resolved_text_without_initializing_it_again(self):
        from unittest.mock import patch
        from azimlib.scene import Text,Scene
        from azimlib.backends._pan_raster import frozen_scene
        item=Text(17,23,'Resolved',{'fill':'black','fontsize':13})
        scene=Scene(100,80,'white');scene.add(item)
        with patch.object(Text,'__post_init__',side_effect=AssertionError('Repeated shaping')):
            frozen=frozen_scene(scene)
        self.assertEqual((frozen.items[0].x,frozen.items[0].y),(17,23))
        self.assertIsNot(frozen.items[0],item)
        self.assertIsNot(frozen.items[0].style,item.style)
        item.style['fill']='red';self.assertEqual(frozen.items[0].style['fill'],'black')


if __name__=='__main__':unittest.main()
