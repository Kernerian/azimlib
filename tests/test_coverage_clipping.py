"""Skipping contained half-planes preserves exact coverage, including overlaps."""
import importlib.util
import io
import math
from pathlib import Path as FilePath
import random
import unittest
from unittest.mock import patch
from azimlib.renderers import coverage, render_png
from azimlib.scene import Scene, Path, Rect, Circle
try:
    from PIL import Image
except ImportError:
    Image=None

def baseline():
    path=FilePath(__file__).resolve().parents[1]/'tools/baselines/coverage-clipping-before/coverage.py'
    spec=importlib.util.spec_from_file_location('azimlib.renderers._coverage_clipping_reference',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

@unittest.skipIf(Image is None,'Pillow is optional')
class CoverageClippingTests(unittest.TestCase):
    def test_fractional_concave_degenerate_outside_and_overlapping_masks_match(self):
        old=baseline();rng=random.Random(913)
        cases=[[],[(.1,.2)],[(1,1),(3,1)],[(.2,.3),(5.8,.3),(5.8,.95),(.2,.95)],
               [(1.1,2.2),(6.3,2.2),(6.3,6.9),(3.4,3.7),(1.1,6.9)],
               [(-3,-1),(15.5,.8),(19,14),(-2,15)],[(1,1),(5,5),(1,5),(5,1)]]
        for _ in range(150):
            cx,cy=rng.uniform(-5,20),rng.uniform(-5,20)
            cases.append([(cx+rng.uniform(.1,9)*math.cos(i*math.pi/4),cy+rng.uniform(.1,9)*math.sin(i*math.pi/4)) for i in range(8)])
        for fill in (0,1,80,255):
            current=Image.new('L',(16,16));previous=Image.new('L',(16,16))
            a,b=coverage.CoverageDraw(current),old.CoverageDraw(previous)
            for i,points in enumerate(cases):
                with self.subTest(fill=fill,polygon=i):
                    # Check each mask fresh as well as the accumulating union.
                    fresh_a,fresh_b=Image.new('L',(16,16)),Image.new('L',(16,16))
                    coverage.CoverageDraw(fresh_a).polygon(points,fill)
                    old.CoverageDraw(fresh_b).polygon(points,fill)
                    self.assertEqual(fresh_a.tobytes(),fresh_b.tobytes())
                    a.polygon(points,fill);b.polygon(points,fill)
                    self.assertEqual(current.tobytes(),previous.tobytes())
            for bounds in ((-2.3,-1.8,5.9,8.1),(.15,.25,1.05,1.15),(6,5,13,12)):
                a.ellipse(bounds,fill);b.ellipse(bounds,fill)
                self.assertEqual(current.tobytes(),previous.tobytes())

    def test_contained_half_planes_avoid_calls_and_preserve_vertex_coverage(self):
        old=baseline();points=[(.2,.3),(2.8,.3),(2.8,1.9),(.2,1.9)]
        a,b=Image.new('L',(5,5)),Image.new('L',(5,5))
        with patch.object(coverage,'_clip',wraps=coverage._clip) as current_calls:
            coverage.CoverageDraw(a).polygon(points)
        with patch.object(old,'_clip',wraps=old._clip) as previous_calls:
            old.CoverageDraw(b).polygon(points)
        self.assertEqual(a.tobytes(),b.tobytes())
        self.assertLess(current_calls.call_count,previous_calls.call_count)

    def test_png_strokes_caps_joins_dashes_alpha_and_clips_remain_identical(self):
        old=baseline();scene=Scene(80,65,None)
        for i,(cap,join) in enumerate((('butt','miter'),('round','round'),('square','bevel'))):
            scene.add(Path([[(-4,8+i*17),(25.3,3.9+i*17),(60.6,15.1+i*17),(84,5+i*17)]],
                style=dict(stroke='#2c7897',stroke_width=.7+i*.3,linecap=cap,linejoin=join,dash=[2.3,1.1],opacity=.6),clip=(3.2,2.7,71.3,58.4)))
        scene.add(Rect(11.3,15.7,33.2,25.9,dict(fill='#ffd080',stroke='black',stroke_width=.7,opacity=.4)))
        scene.add(Circle(45.2,34.3,5.1,dict(fill='white',stroke='red',stroke_width=.8)))
        a,b=io.BytesIO(),io.BytesIO();render_png(scene,a)
        with patch.object(coverage,'CoverageDraw',old.CoverageDraw):render_png(scene,b)
        self.assertEqual(a.getvalue(),b.getvalue())
