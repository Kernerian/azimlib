"""Buffer reuse preserves PNG bytes, alpha composition and stream ownership."""
import importlib.util
import io
from pathlib import Path as FilePath
import unittest
from unittest.mock import patch
from azimlib.renderers import pillow
from azimlib.scene import Scene, Path, Rect, Circle, Text
try:
    from PIL import Image
except ImportError:
    Image=None

def baseline():
    path=FilePath(__file__).resolve().parents[1]/'tools/baselines/raster-buffers-before/pillow.py'
    spec=importlib.util.spec_from_file_location('azimlib.renderers._buffer_reference',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

@unittest.skipIf(Image is None,'Pillow is optional')
class RasterBufferTests(unittest.TestCase):
    def compare(self,scene,scale=1):
        a,b=io.BytesIO(),io.BytesIO()
        pillow.render_png(scene,a,scale);baseline().render_png(scene,b,scale)
        self.assertFalse(a.closed);self.assertFalse(b.closed)
        self.assertEqual(a.getvalue(),b.getvalue())

    def test_fill_stroke_alpha_holes_dashes_and_clips_match(self):
        for background in (None,'#ffffff','#77889944'):
            for scale in (1,1.5,2):
                for fill,fill_opacity in (('none',1),('#eaaa22',1),('#eaaa2280',.6),('#eaaa2200',1),('red',0)):
                    for opacity in (0,.004,.3,1):
                        with self.subTest(background=background,scale=scale,fill=fill,fill_opacity=fill_opacity,opacity=opacity):
                            scene=Scene(55,48,background)
                            scene.add(Rect(1.2,2.1,35.7,28.3,dict(fill='#77bbff80',opacity=.6)))
                            scene.add(Path([[(-2,5.3),(49.1,4.2),(50.9,44.6),(3.2,39.1)],
                                            [(11.1,12.5),(11.1,26.8),(30.5,26.8),(30.5,12.5)]],True,
                                dict(fill=fill,fill_opacity=fill_opacity,stroke='#223344aa',stroke_opacity=.7,
                                     stroke_width=.8,linecap='square',linejoin='miter',dash=[2.3,1.1],opacity=opacity),
                                clip=(2.7,3.2,48.5,38.3)))
                            scene.add(Circle(35.8,29.4,4.9,dict(fill=fill,fill_opacity=fill_opacity,stroke='red',stroke_width=.5)))
                            self.compare(scene,scale)

    def test_interleaved_text_rotation_background_halo_and_cropping_match(self):
        for background in (None,'#eeeeee','#66778844'):
            for rotation in (0,27,90):
                for scale in (1,1.5,2):
                    with self.subTest(background=background,rotation=rotation,scale=scale):
                        scene=Scene(100,78,background)
                        for i in range(3):
                            scene.add(Text(15+i*29,18+i*18,'São 20°',dict(fill='#115577aa',background='#ddccbb88',
                                font_size=9,anchor='middle',rotation=rotation,stroke='white',stroke_width=1.3,
                                fill_opacity=.7,stroke_opacity=.8,opacity=.6),clip=(9.2,3.7,72.4,65.8)))
                            scene.add(Rect(3.3,2.5,93.2,71.7,dict(fill='#44556622',stroke='#22334488',stroke_width=.7,opacity=.4)))
                        self.compare(scene,scale)
                        # Rendering must not mutate the caller's reusable Scene.
                        self.compare(scene,scale)

    def test_first_shape_paint_uses_fewer_rgba_buffers_with_identical_output(self):
        scene=Scene(32,28,None)
        scene.add(Rect(2.3,3.8,24.6,19.5,dict(fill='#1289ab80',stroke='black',stroke_width=.5)))
        scene.add(Path([[(4,7),(18,13),(26,21)]],style=dict(stroke='red',stroke_width=.7)))
        def measure(renderer):
            sizes=[];original=Image.new;buffer=io.BytesIO()
            def new(mode,size,*args,**kwargs):
                if mode=='RGBA':sizes.append(size)
                return original(mode,size,*args,**kwargs)
            with patch.object(Image,'new',side_effect=new):renderer.render_png(scene,buffer)
            return sizes,buffer.getvalue()
        old,png_old=measure(baseline());new,png_new=measure(pillow)
        self.assertEqual(png_old,png_new)
        self.assertLess(sum(w*h for w,h in new),sum(w*h for w,h in old))

    def test_output_stream_remains_owned_by_caller_on_save_failure(self):
        class FailingStream(io.BytesIO):
            def write(self,data):raise OSError('simulated output failure')
        stream=FailingStream();scene=Scene(10,10)
        scene.add(Rect(1,1,5,5,dict(fill='red')))
        with self.assertRaisesRegex(OSError,'simulated'):pillow.render_png(scene,stream)
        self.assertFalse(stream.closed)

    def test_owned_tiles_and_masks_are_released_before_encoding(self):
        # Hold object references deliberately: buffers should be released by
        # ownership, without relying on a later item or garbage collection.
        images=[];original=Image.new;test=self
        def new(mode,size,*args,**kwargs):
            result=original(mode,size,*args,**kwargs)
            # Pillow's internal premultiplied RGBa rotation intermediate is
            # owned by Pillow, not the renderer. Track our RGBA/L buffers.
            if mode in ('RGBA','L') and size!=(1,1):images.append(result)
            return result
        class CheckingStream(io.BytesIO):
            def write(self,data):
                for image in images:
                    with test.assertRaises(ValueError):image.getpixel((0,0))
                return super().write(data)
        scene=Scene(80,65,None)
        scene.add(Rect(1.3,2.1,74.2,60.5,dict(fill='#ffaa2280',stroke='black',stroke_width=.6,opacity=.7)))
        scene.add(Text(35,27,'20°',dict(fill='blue',background='white',stroke='white',stroke_width=1,
            font_size=10,rotation=25,opacity=.6),clip=(15,15,40,35)))
        with patch.object(Image,'new',side_effect=new):pillow.render_png(scene,CheckingStream())
        self.assertGreater(len(images),5)
