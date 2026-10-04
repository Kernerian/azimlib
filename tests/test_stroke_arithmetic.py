"""Exact arithmetic/order, masks and full styles after small-polygon shortcuts."""
import importlib.util
import io
import math
from pathlib import Path as FilePath
import random
import struct
import unittest
from unittest.mock import patch
from azimlib.renderers import coverage,render_png
from azimlib.scene import Scene,Path,Rect,Circle,Text
try:
    from PIL import Image
except ImportError:Image=None

def baseline():
    path=FilePath(__file__).resolve().parents[1]/'tools/baselines/stroke-arithmetic-before/coverage.py'
    spec=importlib.util.spec_from_file_location('azimlib.renderers._stroke_arithmetic_reference',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

class StrokeArithmeticTests(unittest.TestCase):
    def test_area_float_bits_match_translated_reversed_degenerate_and_random_paths(self):
        old=baseline();rng=random.Random(1603)
        cases=[[],[(1,1)],[(1,1),(2,2)],[(0.,0.),(-0.,0.),(0.,-0.)],
               [(1e15,1e15),(1e15+.25,1e15),(1e15,1e15+.5)],
               [(0,0),(2,2),(0,2),(2,0)],[(.2,.3),(.8,.3),(.8,.9),(.2,.9)]]
        for count in (3,4,5,9):
            for _ in range(100):
                scale=rng.choice((1e-100,1e-6,1,1e6,1e100));dx,dy=rng.uniform(-4,4)*scale,rng.uniform(-4,4)*scale
                cases.append([(dx+rng.uniform(-3,3)*scale,dy+rng.uniform(-3,3)*scale) for _ in range(count)])
        for i,points in enumerate(cases):
            for reversed_order in (False,True):
                with self.subTest(case=i,reversed=reversed_order):
                    ordered=list(reversed(points)) if reversed_order else points
                    self.assertEqual(struct.pack('!d',coverage._area(ordered)),struct.pack('!d',old._area(ordered)))

    def test_clip_vertex_bits_and_order_match_both_axes_and_half_planes(self):
        old=baseline();rng=random.Random(861)
        cases=[[],[(0,0)],[(0,0),(0,3),(4,3),(4,0)],[(.1,.2),(1.7,2.3),(.2,2.1)]]
        cases += [[(rng.uniform(-10,10),rng.uniform(-10,10)) for _ in range(rng.randrange(3,12))] for _ in range(100)]
        for i,points in enumerate(cases):
            for axis in (0,1):
                for greater in (False,True):
                    for bound in (-5,0,.3,5):
                        with self.subTest(case=i,axis=axis,greater=greater,bound=bound):
                            original=list(points)
                            expected=old._clip(original,axis,bound,greater);actual=coverage._clip(points,axis,bound,greater)
                            self.assertEqual(len(actual),len(expected))
                            self.assertEqual([struct.pack('!dd',*p) for p in actual],[struct.pack('!dd',*p) for p in expected])
                            self.assertEqual(points,original)

    @unittest.skipIf(Image is None,'Pillow is optional')
    def test_fractional_masks_and_accumulating_overlaps_match(self):
        old=baseline();rng=random.Random(450)
        paths=[[(rng.uniform(-6,23),rng.uniform(-6,23)) for _ in range(rng.randrange(3,10))] for _ in range(140)]
        for fill in (1,80,127,255):
            a,b=Image.new('L',(18,18)),Image.new('L',(18,18));current,previous=coverage.CoverageDraw(a),old.CoverageDraw(b)
            for i,points in enumerate(paths):
                with self.subTest(fill=fill,path=i):
                    fresh_a,fresh_b=Image.new('L',(18,18)),Image.new('L',(18,18))
                    coverage.CoverageDraw(fresh_a).polygon(points,fill);old.CoverageDraw(fresh_b).polygon(points,fill)
                    self.assertEqual(fresh_a.tobytes(),fresh_b.tobytes())
                    fresh_a.close();fresh_b.close()
                    current.polygon(points,fill);previous.polygon(points,fill)
                    self.assertEqual(a.tobytes(),b.tobytes())
            a.close();b.close()

    @unittest.skipIf(Image is None,'Pillow is optional')
    def test_png_caps_joins_custom_dashes_holes_alpha_and_fractional_clips_match(self):
        old=baseline()
        for scale in (1,1.5,2):
            with self.subTest(scale=scale):
                scene=Scene(160,120,None)
                for i,(cap,join) in enumerate((('butt','miter'),('round','round'),('square','bevel'))):
                    scene.add(Path([[(-8,15+i*34),(45.8,7+i*34),(71.3,29+i*34),(168,4+i*34)]],
                        style=dict(stroke='#12345688',stroke_width=.7+i*.4,linecap=cap,linejoin=join,dash=[2.3,1.1,4.5,2.8],opacity=.7),
                        clip=(4.3,3.7,148.4,109.8)))
                scene.add(Path([[(18,22),(142,26),(135,95),(15,91)],[(42,40),(42,78),(111,78),(111,40)]],True,
                    dict(fill='#ffd08880',stroke='#225577',stroke_width=.9,opacity=.5)))
                scene.add(Circle(83.4,66.7,11.3,dict(fill='white',stroke='red',stroke_width=.6)))
                scene.add(Text(78,69,'20°',dict(fill='blue',stroke='white',stroke_width=1,font_size=10,rotation=25)))
                a,b=io.BytesIO(),io.BytesIO();render_png(scene,a,scale)
                with patch.object(coverage,'_area',old._area),patch.object(coverage,'_clip',old._clip):render_png(scene,b,scale)
                self.assertEqual(a.getvalue(),b.getvalue())
