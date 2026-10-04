"""Exact BOX/alpha bands preserve arbitrary RGBA, seams and owned images."""
import importlib.util
import io
from pathlib import Path as FilePath
import random
import unittest
from unittest.mock import patch
from azimlib.renderers import pillow
from azimlib.scene import Scene, Rect, Path, Text, Circle
try:
    from PIL import Image
except ImportError:
    Image=None

def baseline():
    path=FilePath(__file__).resolve().parents[1]/'tools/baselines/raster-box-before/pillow.py'
    spec=importlib.util.spec_from_file_location('azimlib.renderers._box_reference',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

@unittest.skipIf(Image is None,'Pillow is optional')
class RasterBandTests(unittest.TestCase):
    def setUp(self):
        # Exercise the large-buffer path using small, fast fixtures.
        threshold=patch.object(pillow,'_BAND_THRESHOLD_BYTES',1)
        threshold.start();self.addCleanup(threshold.stop)

    def test_small_images_keep_original_resize_and_composite_paths(self):
        source=Image.new('RGBA',(30,39),'#12345678');destination=Image.new('RGBA',(36,47),'#55667788')
        reference=source.resize((10,13),Image.Resampling.BOX)
        expected=destination.copy();expected.alpha_composite(source,(3,4))
        with patch.object(pillow,'_BAND_THRESHOLD_BYTES',16*1024*1024),\
             patch.object(source,'crop',side_effect=AssertionError('unnecessary source crop')):
            actual=pillow._downsample_box(source,(10,13),Image)
            pillow._composite_rgba(destination,source,(3,4))
        self.assertEqual(actual.tobytes(),reference.tobytes());self.assertEqual(destination.tobytes(),expected.tobytes())
        self.assertEqual(source.getpixel((0,0)),(18,52,86,120))
        actual.close();reference.close();expected.close();source.close();destination.close()

    def test_box_bands_match_full_filter_for_random_rgba_and_partial_last_bands(self):
        rng=random.Random(9701)
        for width,height in ((1,1),(1,13),(7,2),(11,17),(79,31),(101,97)):
            data=rng.randbytes(width*height*9*4)
            source=Image.frombytes('RGBA',(width*3,height*3),data)
            reference=source.resize((width,height),Image.Resampling.BOX)
            for rows in (1,2,3,7,32):
                with self.subTest(width=width,height=height,rows=rows):
                    with patch.object(pillow,'_BOX_BAND_BYTES',width*3*3*4*rows):
                        actual=pillow._downsample_box(source,(width,height),Image)
                    self.assertEqual(actual.mode,'RGBA');self.assertEqual(actual.size,(width,height))
                    self.assertEqual(actual.tobytes(),reference.tobytes())
                    self.assertEqual(source.tobytes(),data)
                    actual.close()
            reference.close();source.close()

    def test_opaque_transparent_and_alternating_rows_keep_seams_and_hidden_rgb(self):
        for alpha in (0,1,127,254,255):
            source=Image.new('RGBA',(45,69))
            pixels=source.load()
            for y in range(source.height):
                for x in range(source.width):pixels[x,y]=((x*43)%256,(y*79)%256,255 if y%2 else 0,alpha)
            reference=source.resize((15,23),Image.Resampling.BOX)
            with self.subTest(alpha=alpha),patch.object(pillow,'_BOX_BAND_BYTES',45*3*4*2):
                actual=pillow._downsample_box(source,(15,23),Image)
                self.assertEqual(actual.tobytes(),reference.tobytes())
                actual.close()
            reference.close();source.close()

    def test_alpha_bands_match_full_composition_at_offsets_and_small_budgets(self):
        rng=random.Random(911)
        for width,height in ((1,1),(3,17),(19,31),(79,47)):
            a=rng.randbytes((width+9)*(height+11)*4);b=rng.randbytes(width*height*4)
            destination=Image.frombytes('RGBA',(width+9,height+11),a)
            source=Image.frombytes('RGBA',(width,height),b)
            for origin in ((0,0),(3,5),(9,11)):
                reference=destination.copy();reference.alpha_composite(source,origin)
                for rows in (1,2,7,32):
                    with self.subTest(width=width,height=height,origin=origin,rows=rows):
                        actual=destination.copy()
                        with patch.object(pillow,'_COMPOSITE_BAND_BYTES',width*4*rows):
                            pillow._composite_rgba(actual,source,origin)
                        self.assertEqual(actual.tobytes(),reference.tobytes())
                        self.assertEqual(destination.tobytes(),a);self.assertEqual(source.tobytes(),b)
                        actual.close()
                reference.close()
            destination.close();source.close()

    def test_rendered_png_matches_previous_renderer_with_forced_multiple_bands(self):
        old=baseline()
        for background in (None,'white','#33445544'):
            for scale in (.6,1,1.5,2):
                with self.subTest(background=background,scale=scale):
                    scene=Scene(97.3,73.7,background)
                    scene.add(Rect(-2,1.7,98.9,68.3,dict(fill='#ffcc0080',stroke='black',stroke_width=.7,opacity=.6)))
                    scene.add(Path([[(-3,10),(90,2.3),(95,65.8),(2,68)],[(23,21),(23,41),(51,41),(51,21)]],True,
                        dict(fill='#2468ab',stroke='red',stroke_width=.6,fill_opacity=.3,opacity=.7,dash=[3,1]),clip=(5.1,4.8,84.2,62.7)))
                    scene.add(Circle(48,36,19.4,dict(fill='#12233470',stroke='white',stroke_width=.8)))
                    scene.add(Text(48,39,'São 20°',dict(font_size=12,rotation=27,anchor='middle',fill='#123456cc',
                        background='#dddddd88',stroke='white',stroke_width=1,opacity=.8),clip=(12.1,9.6,73.3,54.7)))
                    a,b=io.BytesIO(),io.BytesIO();old.render_png(scene,a,scale)
                    with patch.object(pillow,'_BOX_BAND_BYTES',2048),patch.object(pillow,'_COMPOSITE_BAND_BYTES',2048):
                        pillow.render_png(scene,b,scale)
                    self.assertEqual(a.getvalue(),b.getvalue());self.assertFalse(b.closed)

    def test_working_bands_are_bounded_and_wide_single_row_falls_back_safely(self):
        source=Image.new('RGBA',(300,99),'#01234567');destination=Image.new('RGBA',source.size)
        original_crop=Image.Image.crop;original_composite=Image.Image.alpha_composite
        crops=[];composites=[]
        def crop(image,box):
            result=original_crop(image,box);crops.append((result.width,result.height));return result
        def composite(image,other,*args,**kwargs):
            composites.append(other.size);return original_composite(image,other,*args,**kwargs)
        with patch.object(pillow,'_BOX_BAND_BYTES',1),patch.object(pillow,'_COMPOSITE_BAND_BYTES',1),\
             patch.object(Image.Image,'crop',crop),patch.object(Image.Image,'alpha_composite',composite):
            reduced=pillow._downsample_box(source,(100,33),Image)
            pillow._composite_rgba(destination,source,(0,0))
        self.assertTrue(crops);self.assertTrue(composites)
        self.assertTrue(all(height<=3 for _,height in crops))
        self.assertTrue(all(height==1 for _,height in composites))
        reference=source.resize((100,33),Image.Resampling.BOX)
        self.assertEqual(reduced.tobytes(),reference.tobytes());self.assertEqual(destination.tobytes(),source.tobytes())
        reference.close();reduced.close();destination.close();source.close()

    def test_failed_band_operations_release_temporaries_but_preserve_borrowed_inputs(self):
        source=Image.new('RGBA',(30,39),'red');destination=Image.new('RGBA',source.size)
        original_new=Image.new;original_crop=Image.Image.crop;owned=[]
        def new(*args,**kwargs):
            result=original_new(*args,**kwargs);owned.append(result);return result
        def crop(*args,**kwargs):
            result=original_crop(*args,**kwargs);owned.append(result);return result
        with patch.object(pillow,'_BOX_BAND_BYTES',1),patch.object(Image,'new',new),\
             patch.object(Image.Image,'crop',crop),patch.object(Image.Image,'resize',side_effect=OSError('resize failed')):
            with self.assertRaisesRegex(OSError,'resize failed'):pillow._downsample_box(source,(10,13),Image)
        for image in owned:
            with self.assertRaises(ValueError):image.getpixel((0,0))
        owned.clear()
        with patch.object(pillow,'_COMPOSITE_BAND_BYTES',1),patch.object(Image.Image,'crop',crop),\
             patch.object(Image.Image,'alpha_composite',side_effect=OSError('compose failed')):
            with self.assertRaisesRegex(OSError,'compose failed'):pillow._composite_rgba(destination,source,(0,0))
        for image in owned:
            with self.assertRaises(ValueError):image.getpixel((0,0))
        self.assertEqual(source.getpixel((0,0)),(255,0,0,255))
        self.assertEqual(destination.getpixel((0,0)),(0,0,0,0))
        source.close();destination.close()

    def test_box_requires_internal_integer_ratio_and_rgba(self):
        for mode,size in (('RGBA',(31,39)),('RGB',(30,39))):
            with self.subTest(mode=mode,size=size):
                source=Image.new(mode,size)
                with self.assertRaisesRegex(ValueError,'3x RGBA'):pillow._downsample_box(source,(10,13),Image)
                source.close()
