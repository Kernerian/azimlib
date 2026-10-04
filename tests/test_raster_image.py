"""Direct RGBA buffers preserve own PNG baseline and resource ownership."""
import importlib.util,io,math,unittest
from pathlib import Path as FilePath
from unittest.mock import Mock,patch
from azimlib.renderers import render_image,render_png
from azimlib.scene import Scene,Rect,Path,Circle,Text
try:
    from PIL import Image
except ImportError:Image=None


def baseline():
    path=FilePath(__file__).resolve().parents[1]/'tools/baselines/viewer-raster-before/pillow.py'
    spec=importlib.util.spec_from_file_location('azimlib.renderers._image_before',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@unittest.skipIf(Image is None,'Pillow is optional')
class RasterImageTests(unittest.TestCase):
    def test_image_and_png_match_previous_renderer_bytes(self):
        old=baseline()
        for background in (None,'white','#7799aa66'):
            for scale in (1,1.5,2):
                for rotation in (0,25,90):
                    with self.subTest(background=background,scale=scale,rotation=rotation):
                        scene=Scene(90.3,72.7,background)
                        scene.add(Path([[(-4,3),(86,3),(83,70),(1,68)],[(18,19),(18,39),(40,39),(40,19)]],True,
                                       dict(fill='#ccbbaa88',stroke='black',stroke_width=.55,dash=[2,1],opacity=.6),clip=(2.3,2.7,80,66)))
                        scene.add(Circle(61.2,39.3,8.1,dict(fill='#ff334488',stroke='blue',stroke_width=.7)))
                        scene.add(Text(42,55,'São 20°',dict(fill='black',font_size=10,rotation=rotation,anchor='middle',stroke='white',stroke_width=1)))
                        before=io.BytesIO();old.render_png(scene,before,scale)
                        after=io.BytesIO();render_png(scene,after,scale)
                        self.assertEqual(before.getvalue(),after.getvalue());self.assertFalse(after.closed)
                        image=render_image(scene,scale)
                        try:
                            with Image.open(before) as decoded:
                                self.assertEqual(image.mode,'RGBA');self.assertEqual(image.size,decoded.size)
                                self.assertEqual(image.tobytes(),decoded.convert('RGBA').tobytes())
                        finally:image.close()

    def test_direct_image_does_not_encode_or_decode_png(self):
        scene=Scene(20,16,None);scene.add(Rect(1,2,8,7,dict(fill='red')))
        with patch.object(Image.Image,'save',side_effect=AssertionError('encoding forbidden')):
            with patch.object(Image,'open',side_effect=AssertionError('decoding forbidden')):
                image=render_image(scene)
        self.assertEqual(image.getpixel((4,5)),(255,0,0,255));image.close()

    def test_returned_images_are_owned_and_independent(self):
        scene=Scene(10,8,'white');first=render_image(scene);second=render_image(scene)
        first.putpixel((0,0),(255,0,0,255));first.close()
        self.assertEqual(second.getpixel((0,0)),(255,255,255,255));second.close()

    def test_png_wrapper_closes_image_on_success_and_failure(self):
        for failure in (None,OSError('write failed')):
            with self.subTest(failure=failure):
                image=Mock();image.save.side_effect=failure
                stream=io.BytesIO()
                with patch('azimlib.renderers.pillow.render_image',return_value=image):
                    if failure:
                        with self.assertRaisesRegex(OSError,'write failed'):render_png(Scene(1,1),stream)
                    else:render_png(Scene(1,1),stream)
                image.close.assert_called_once();self.assertFalse(stream.closed)

    def test_invalid_scale_and_scene_remain_rejected(self):
        for scale in (0,-1,math.inf,math.nan):
            with self.subTest(scale=scale):
                with self.assertRaises(ValueError):render_image(Scene(10,8),scale)
        with self.assertRaises(ValueError):render_image(Scene(-10,8))
