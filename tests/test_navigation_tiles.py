"""Navigation caches preserve geometry, current clipping and buffer ownership."""
from dataclasses import replace
from threading import Event
import unittest
from unittest.mock import Mock,patch
from azimlib.scene import Scene,Path,Rect,Text
from azimlib.renderers._tile_cache import TileCache
from azimlib.backends._pan_raster import PanRaster
try:
    from PIL import Image
except ImportError:Image=None


@unittest.skipIf(Image is None,'Pillow optional')
class NavigationTilesTests(unittest.TestCase):
    def test_unclipped_translated_tile_reveals_geometry_at_current_clip(self):
        from azimlib.renderers import render_image
        item=Path([[(-15,15),(45,15),(45,50),(-15,50)],[(5,25),(25,25),(25,40),(5,40)]],
                  True,dict(fill='#f4424280',stroke='black',stroke_width=1,opacity=.8),clip=(0,0,55,60))
        cache=TileCache()
        try:
            scene=Scene(80,65);scene.add(item)
            image=render_image(scene,_interactive=True,_tile_cache=cache);image.close()
            moved=replace(item,paths=[[(x+22,y+3) for x,y in p] for p in item.paths],clip=(10,4,60,55))
            scene.items=[moved]
            actual=render_image(scene,_interactive=True,_tile_cache=cache)
            expected=render_image(scene,_interactive=True)
            try:
                self.assertGreater(cache.hits,0)
                self.assertEqual(actual.tobytes(),expected.tobytes())
                self.assertEqual(actual.getpixel((8,20)),(255,255,255,255))
                self.assertNotEqual(actual.getpixel((12,20)),(255,255,255,255))
            finally:actual.close();expected.close()
        finally:cache.close()

    def test_rotated_halo_text_reuses_glyph_at_fresh_position_and_style(self):
        from azimlib.renderers import render_image
        cache=TileCache()
        try:
            for background in (None,'#ffffff'):
                for rotation in (0,27,90):
                    item=Text(20,30,'São 20°',dict(font_size=9,anchor='middle',rotation=rotation,
                              stroke='white',stroke_width=1.2,fill='#115577aa',opacity=.6))
                    scene=Scene(100,70,background);scene.add(item)
                    image=render_image(scene,_interactive=True,_tile_cache=cache);image.close()
                    scene.items=[replace(item,x=37.25,y=45.6,clip=(5,4,90,60))]
                    actual=render_image(scene,_interactive=True,_tile_cache=cache)
                    expected=render_image(scene,_interactive=True)
                    try:self.assertEqual(actual.tobytes(),expected.tobytes())
                    finally:actual.close();expected.close()
            self.assertGreater(cache.hits,0)
        finally:cache.close()

    def test_every_vertex_style_and_supersample_phase_are_checked(self):
        cache=TileCache();image=Image.new('RGBA',(10,10));points=[(i,i%3) for i in range(10)]
        item=Path([points],style=dict(stroke='red'))
        try:
            cache.store(item,2,image,(0,0))
            changed=list(points);changed[2]=(2,90)
            self.assertIsNone(cache.lookup(replace(item,paths=[changed]),2))
            self.assertIsNone(cache.lookup(replace(item,style=dict(stroke='blue')),2))
            self.assertIsNone(cache.lookup(replace(item,paths=[[(x+.2,y) for x,y in points]]),2))
            translated=replace(item,paths=[[(x+4,y-7) for x,y in points]])
            result=cache.lookup(translated,2)
            self.assertEqual(result[1],(8,-14));result[0].close()
            points[2]=(2,90)
            self.assertIsNone(cache.lookup(item,2),'cache owns snapshot of caller geometry')
        finally:image.close();cache.close()

    def test_retention_is_bounded_and_closed_cache_cannot_retain_images(self):
        cache=TileCache();image=Image.new('RGBA',(8,8))
        try:
            for i in range(160):cache.store(Rect(0,0,i+1,1),2,image,(0,0))
            self.assertLessEqual(len(cache.entries),128)
            self.assertLessEqual(cache.bytes,16*1024*1024)
            copy=cache.lookup(Rect(0,0,160,1),2)[0]
            cache.close();self.assertEqual(cache.bytes,0)
            self.assertEqual(copy.getpixel((0,0)),(0,0,0,0));copy.close()
            cache.store(Rect(0,0,160,1),2,image,(0,0));self.assertFalse(cache.entries)
        finally:image.close();cache.close()

    def test_opaque_box_shortcut_is_byte_equal_for_aligned_bands(self):
        from azimlib.renderers import pillow
        for ratio in (2,3):
            source=Image.new('RGBA',(21*ratio,17*ratio))
            source.putdata([(i%256,(i*17)%256,(i*37)%256,255) for i in range(source.width*source.height)])
            expected=source.resize((21,17),Image.Resampling.BOX)
            try:
                with patch.object(pillow,'_BAND_THRESHOLD_BYTES',0),patch.object(pillow,'_BOX_BAND_BYTES',500):
                    actual=pillow._downsample_opaque_box(source,(21,17),Image,ratio=ratio)
                try:self.assertEqual(actual.tobytes(),expected.tobytes())
                finally:actual.close()
            finally:source.close();expected.close()

    def test_controlled_exact_render_is_identical_and_cancel_releases_buffers(self):
        from azimlib.renderers import render_image
        from azimlib.renderers._render_control import RasterControl,RasterCancelled
        scene=Scene(60,40);scene.add(Path([[(1,2),(40,30),(55,7)]],style=dict(stroke='red',stroke_width=2)))
        scene.add(Text(30,20,'N',dict(font_size=10)))
        a=render_image(scene);b=render_image(scene,_cancel=Event())
        try:self.assertEqual(a.tobytes(),b.tobytes())
        finally:a.close();b.close()
        event=Event();event.set();control=RasterControl(event)
        with patch('azimlib.renderers._render_control.RasterControl',return_value=control):
            with self.assertRaises(RasterCancelled):render_image(scene,_cancel=event)
        self.assertFalse(control.buffers)
        control=RasterControl(Event());buffer=control.images(Image).new('L',(10,10))
        control.event.set()
        with self.assertRaises(RasterCancelled):
            draw=control.stroke_draw(buffer)
            for _ in range(32):draw.polygon([(1,1),(4,1),(4,4)])
        control.close()
        with self.assertRaises(ValueError):buffer.getpixel((0,0))

class PriorityTests(unittest.TestCase):
    def test_new_gesture_interrupts_precise_job_and_releases_obsolete_result(self):
        started=Event();stopped=Event();image=Mock();preview=Mock(return_value=Mock())
        def exact(scene,cancel):
            started.set();self.assertTrue(cancel.wait(3));stopped.set();return image
        worker=PanRaster(Mock(side_effect=AssertionError('controlled exact expected')),preview,exact)
        try:
            worker.submit(1,Scene(1,1));self.assertTrue(started.wait(3))
            worker.interrupt_exact();worker.submit(2,Scene(2,2),preview=True)
            with worker._condition:
                self.assertTrue(worker._condition.wait_for(lambda:worker._ready is not None and worker._ready[0]==2,3))
            result=worker.take();self.assertTrue(stopped.is_set())
            image.close.assert_called_once();self.assertIsNone(result[3]);result[2].close()
        finally:worker.close()

    def test_new_gesture_does_not_cancel_active_preview(self):
        started=Event();gate=Event();image=Mock()
        def preview(scene):started.set();gate.wait(3);return image
        worker=PanRaster(Mock(),preview)
        try:
            worker.submit(1,Scene(1,1),preview=True);self.assertTrue(started.wait(3))
            worker.interrupt_exact();self.assertFalse(worker._cancel.is_set());gate.set()
            with worker._condition:self.assertTrue(worker._condition.wait_for(lambda:worker._ready is not None,3))
            self.assertIs(worker.take()[2],image);image.close()
        finally:gate.set();worker.close()

class PortableMetricsTests(unittest.TestCase):
    def test_cached_subset_is_exact_and_cannot_be_mutated_by_export_consumer(self):
        from azimlib import typography as t
        style={};original=t._export_metrics('N012 km',style)
        first=t._export_metrics('N012 km',style);first['chars']['N'][1]=0;first['kern'].clear()
        self.assertEqual(t._export_metrics('N012 km',style),original)
        t._metrics.cache_clear()
        self.assertEqual(t._export_metrics('N012 km',style),original)
        for i in range(80):t._export_metrics(str(i)+'km',style)
        self.assertLessEqual(len(t._portable_subsets),64)


@unittest.skipIf(Image is None,'Pillow optional')
class PixelProcessTests(unittest.TestCase):
    def test_child_pixels_match_owned_renderer_and_closing_stops_child(self):
        try:import aggdraw
        except ImportError:self.skipTest('aggdraw optional')
        from azimlib.backends._navigation_process import NavigationProcess
        from azimlib.renderers import render_image
        worker=NavigationProcess()
        try:
            scene=Scene(75,60);scene.add(Path([[(3,5),(65,45)]],style=dict(stroke='red',stroke_width=.8,linecap='round')))
            scene.add(Text(20,24,'Brasil',dict(font_size=10)))
            actual=worker.render(scene);expected=render_image(scene,_interactive=True)
            try:self.assertEqual(actual.tobytes(),expected.tobytes())
            finally:actual.close();expected.close()
            bad=Scene(20,20);bad.add(Rect(0,0,10,10,dict(stroke_width=-1)))
            with self.assertRaisesRegex(RuntimeError,'stroke_width'):worker.render(bad)
            image=worker.render(scene);image.close()
        finally:worker.close()
        self.assertIsNotNone(worker.process.poll())
        with self.assertRaisesRegex(RuntimeError,'closed'):worker.render(scene)

    def test_private_protocol_handles_short_reads_and_writes(self):
        import io
        from azimlib.backends._navigation_process import _send,_receive
        class ShortPipe(io.BytesIO):
            def write(self,value):return super().write(value[:7])
            def read(self,size):return super().read(min(size,5))
        stream=ShortPipe();value=('image',(10,10),b'rgba'*100)
        _send(stream,value);stream.seek(0);self.assertEqual(_receive(stream),value)

    def test_navigation_stroke_area_does_not_inflate_thin_lines(self):
        try:import aggdraw
        except ImportError:self.skipTest('aggdraw optional')
        import math
        from azimlib.renderers import render_image
        for angle in (0,20,50,90):
            for width in (.5,.8,1.5,2):
                with self.subTest(angle=angle,width=width):
                    scene=Scene(100,100,None);theta=math.radians(angle)
                    scene.add(Path([[(20,20),(20+50*math.cos(theta),20+50*math.sin(theta))]],
                                   style=dict(stroke='black',stroke_width=width,linecap='butt')))
                    exact=render_image(scene);preview=render_image(scene,_interactive=True)
                    try:
                        a=sum(exact.getchannel('A').get_flattened_data())/255
                        b=sum(preview.getchannel('A').get_flattened_data())/255
                        self.assertLess(abs(b/a-1),.04,(a,b))
                    finally:exact.close();preview.close()


if __name__=='__main__':unittest.main()
