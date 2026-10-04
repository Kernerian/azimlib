"""Short-ring kernels retain arithmetic order and actual rendered coverage."""
import importlib.util
import io
import math
from pathlib import Path as FilePath
import random
import struct
import unittest
from unittest.mock import patch
from azimlib.renderers import coverage,render_png
from azimlib.scene import Scene,Path,Circle,Text

def baseline():
    path=FilePath(__file__).resolve().parents[1]/'tools/baselines/stroke-kernels-before/coverage.py'
    spec=importlib.util.spec_from_file_location('short_ring_reference',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

class StrokeKernelTests(unittest.TestCase):
    def test_area_bits_at_all_kernel_sizes_with_extreme_scales_and_ring_orders(self):
        old=baseline();rng=random.Random(6173)
        for count in range(3,12):
            for scale in (1e-100,1e-6,1.,1e6,1e100):
                for trial in range(40):
                    points=[(rng.uniform(-5,5)*scale,rng.uniform(-5,5)*scale) for _ in range(count)]
                    for ordered in (points,points[::-1],points[2:]+points[:2]):
                        with self.subTest(count=count,scale=scale,trial=trial,first=ordered[0]):
                            self.assertEqual(struct.pack('!d',coverage._area(ordered)),struct.pack('!d',old._area(ordered)))

    def test_collinear_repeated_signed_zero_and_large_offset_vertices(self):
        old=baseline()
        for count in range(3,12):
            cases=[[(0.,-0.)]*count,[(float(i),float(i)) for i in range(count)],
                   [(1e15+i*.25,1e15+(i%3)*.25) for i in range(count)],
                   [(math.cos(i),math.sin(i)) for i in range(count-1)]+[(1.,0.)]]
            for i,points in enumerate(cases):
                with self.subTest(count=count,case=i):
                    self.assertEqual(struct.pack('!d',coverage._area(points)),struct.pack('!d',old._area(points)))

    def test_random_polygon_and_ellipse_masks_preserve_accumulation_and_clipping(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Pillow optional')
        old=baseline();rng=random.Random(809)
        for fill in (1,64,127,255):
            with Image.new('L',(20,20)) as a,Image.new('L',(20,20)) as b:
                current,previous=coverage.CoverageDraw(a),old.CoverageDraw(b)
                for trial in range(100):
                    count=rng.choice((3,4,5,6,7,8,9,10,24))
                    points=[(rng.uniform(-3,23),rng.uniform(-3,23)) for _ in range(count)]
                    box=tuple(rng.uniform(-3,23) for _ in range(4))
                    with self.subTest(fill=fill,trial=trial,count=count):
                        current.polygon(points,fill);previous.polygon(points,fill)
                        current.ellipse(box,fill);previous.ellipse(box,fill)
                        self.assertEqual(a.tobytes(),b.tobytes())

    def test_png_styles_markers_halos_holes_and_clips_at_three_export_scales(self):
        try:import PIL
        except ImportError:self.skipTest('Pillow optional')
        old=baseline()
        scene=Scene(170,130,None)
        for row,cap in enumerate(('butt','round','square')):
            for column,join in enumerate(('miter','round','bevel')):
                y=10+row*35;x=column*53
                scene.add(Path([[(x-8,y),(x+15.3,y+28.2),(x+45.8,y+2)]],style=dict(
                    stroke='#843b9a88',stroke_width=.4+column*.3,linecap=cap,linejoin=join,
                    dash=(2.1,1.3,4.5,2.3) if column==2 else (),opacity=.8),clip=(2.3,1.4,164.2,123.1)))
        scene.add(Path([[(12,13),(145,15),(130,109),(13,115)],[(45,35),(47,86),(97,86),(98,35)]],True,
                       dict(fill='#55aabb66',stroke='black',stroke_width=.7,opacity=.5)))
        scene.add(Circle(115.4,88.3,6.5,dict(fill='white',stroke='red',stroke_width=.6)))
        scene.add(Text(75.3,77.1,'23°S',dict(fill='#333333',stroke='white',stroke_width=1,font_size=10,rotation=25)))
        for scale in (1,1.5,2):
            with self.subTest(scale=scale):
                a,b=io.BytesIO(),io.BytesIO();render_png(scene,a,scale)
                with patch.object(coverage,'_area',old._area):render_png(scene,b,scale)
                self.assertEqual(a.getvalue(),b.getvalue())

if __name__=='__main__':unittest.main()
