"""Transient navigation quality, bounded path reuse and GUI coalescing."""
import io
import math
import unittest
from unittest.mock import Mock,patch
from azimlib.backends.tk import FigureWindow
from azimlib.renderers._interactive import InteractivePathCache,simplify_path
from azimlib.scene import Scene,Path,Text


class InteractiveRasterTests(unittest.TestCase):
    def test_simplification_preserves_endpoints_and_bounds_display_error(self):
        points=[(i*.03,math.sin(i*.03)) for i in range(300)]
        original=list(points);result=simplify_path(points)
        self.assertEqual(points,original);self.assertEqual((result[0],result[-1]),(points[0],points[-1]))
        self.assertLess(len(result),len(points)/3)
        for x,y in points:
            distances=[]
            for (ax,ay),(bx,by) in zip(result,result[1:]):
                dx,dy=bx-ax,by-ay;t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy)))
                distances.append(math.hypot(x-ax-t*dx,y-ay-t*dy))
            self.assertLessEqual(min(distances),.15+1e-10)
        ring=points+[(0,0)];closed=simplify_path(ring)
        self.assertEqual(closed[0],closed[-1]);self.assertGreaterEqual(len(closed),4)

    def test_cache_checks_every_vertex_and_returns_current_coordinates(self):
        cache=InteractivePathCache();points=[(i*.03,math.sin(i*.03)) for i in range(300)]
        result=cache.simplify(points);translated=[(x+17,y-23) for x,y in points]
        self.assertEqual(cache.simplify(translated),[(x+17,y-23) for x,y in result])
        self.assertEqual(cache.hits,1)
        translated[70]=(translated[70][0],translated[70][1]+10)
        changed=cache.simplify(translated)
        self.assertEqual(cache.misses,2);self.assertIn(translated[70],changed)
        zoomed=[(2*x,2*y) for x,y in translated];cache.simplify(zoomed)
        self.assertEqual(cache.misses,3)
        for n in range(100):cache.simplify([(x,y*(n+2)) for x,y in points])
        self.assertLessEqual(len(cache.entries),64);self.assertLessEqual(cache.points,50000)

    def test_busy_worker_coalesces_before_composition_and_cache_hashing(self):
        viewer=object.__new__(FigureWindow);viewer._pan_raster=Mock();viewer._pan_raster.busy.return_value=True
        viewer.figure=Mock();viewer._raster_cache=Mock();viewer.window=Mock();viewer._pan_poll=None
        for _ in range(20):viewer._draw_pan_async()
        self.assertTrue(viewer._pan_waiting);viewer.figure.to_scene.assert_not_called()
        viewer._raster_cache.lookup.assert_not_called();viewer._pan_raster.submit.assert_not_called()
        viewer.window.after.assert_called_once()

    def test_preview_keeps_holes_clipping_text_and_static_export_quality(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Pillow optional')
        from azimlib.renderers import render_image,render_png
        scene=Scene(100,80)
        scene.add(Path([[(10,10),(90,10),(90,70),(10,70)],[(30,30),(70,30),(70,50),(30,50)]],True,{'fill':'red'},clip=(0,0,80,80)))
        scene.add(Text(50,20,'N',{'font_size':10,'fill':'black'}))
        exact=render_image(scene);preview=render_image(scene,_interactive=True)
        try:
            self.assertEqual(preview.size,exact.size)
            self.assertEqual(preview.getpixel((50,40)),(255,255,255,255))
            self.assertEqual(preview.getpixel((85,40)),(255,255,255,255))
            with patch('azimlib.renderers._navigation_coverage.AntialiasedStrokeDraw',side_effect=AssertionError('navigation kernel in export')):
                stream=io.BytesIO();render_png(scene,stream)
            stream.seek(0)
            with Image.open(stream) as exported:self.assertEqual(exported.convert('RGBA').tobytes(),exact.tobytes())
        finally:exact.close();preview.close()

    def test_preview_dispatch_does_not_select_exact_renderer(self):
        from azimlib.backends._pan_raster import PanRaster
        from threading import Event
        image=Mock();seen=Event();exact=Mock(side_effect=AssertionError('exact during drag'))
        def preview(scene):seen.set();return image
        worker=PanRaster(exact,preview)
        try:
            worker.submit(1,Scene(1,1),preview=True)
            with worker._condition:self.assertTrue(worker._condition.wait_for(lambda:worker._ready is not None,3))
            self.assertTrue(seen.is_set());self.assertIs(worker.take()[2],image);exact.assert_not_called()
        finally:image.close();worker.close()

    def test_poll_preserves_async_state_when_it_starts_a_waiting_final_frame(self):
        viewer=object.__new__(FigureWindow);viewer.closed=False;viewer._pan_poll=None
        viewer._pan_raster=Mock();viewer._pan_raster.take.return_value=None
        viewer._pan_raster.busy.side_effect=[False,True]
        viewer._pan_waiting=True;viewer._async_pan=True;viewer.drag=None
        viewer._pending=viewer._wheel_pending=None;viewer.window=Mock()
        def submit_final():viewer._pan_poll='already scheduled'
        viewer._draw_pan_async=Mock(side_effect=submit_final)
        viewer._poll_pan()
        self.assertTrue(viewer._async_pan);viewer._draw_pan_async.assert_called_once()
        viewer.window.after.assert_not_called()


if __name__=='__main__':unittest.main()
