"""Optional compilation preserves own scalar arithmetic and exact pixels."""
import importlib.util
import math
from pathlib import Path
import random
import unittest
from unittest.mock import patch
from azimlib.renderers import coverage,pillow
from azimlib.scene import Scene,Path as ScenePath


def scalar():
    spec=importlib.util.spec_from_file_location('detailed_scalar',Path(__file__).resolve().parents[1]/'tools/baselines/detailed-raster-before/coverage.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.CoverageDraw


class NativeCoverageTests(unittest.TestCase):
    def setUp(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Pillow optional')
        self.Image=Image

    def test_convex_segments_match_scalar_for_thin_dense_paths_clips_and_accumulation(self):
        rng=random.Random(408);old=scalar()
        for width in (.03,.1,.35,.7,1.4,2.1,7):
            for join in ('round','miter','bevel'):
                for cap in ('round','butt','square'):
                    points=[(rng.uniform(-3,43),rng.uniform(-3,33)) for _ in range(260)]
                    with self.subTest(width=width,join=join,cap=cap):
                        with self.Image.new('L',(40,30)) as a,self.Image.new('L',(40,30)) as b:
                            current=coverage.CoverageDraw(a)
                            pillow._stroke(current,points,width,cap,join);current.flush()
                            pillow._stroke(old(b),points,width,cap,join)
                            self.assertEqual(a.tobytes(),b.tobytes())

    def test_ellipses_match_accumulated_scalar_masks(self):
        old=scalar();rng=random.Random(918)
        for fill in (0,1,64,127,255):
            boxes=[(rng.uniform(-4,28),rng.uniform(-4,28),rng.uniform(-4,28),rng.uniform(-4,28)) for _ in range(260)]
            boxes+=[(.499999999, .499999999,1.500000001,1.500000001),(5,5,5,5),(0,0,24,24)]
            with self.subTest(fill=fill):
                with self.Image.new('L',(24,24)) as a,self.Image.new('L',(24,24)) as b:
                    current=coverage.CoverageDraw(a);current.enable_native();previous=old(b)
                    for start in range(0,len(boxes),128):
                        for box in boxes[start:start+128]:
                            current.ellipse(box,fill);previous.ellipse(box,fill)
                        current.flush()
                        self.assertEqual(a.tobytes(),b.tobytes())

    def test_intersections_retain_every_vertex_and_float_bit_in_original_order(self):
        import struct
        try:from azimlib.renderers import _coverage_native as native
        except ImportError:self.skipTest('Numba optional')
        import numpy as np
        rng=random.Random(407)
        for count in (4,24,64,256):
            for trial in range(25):
                cx,cy=rng.uniform(-5,5),rng.uniform(-5,5)
                rx,ry=rng.uniform(.0001,5),rng.uniform(.0001,5)
                points=[(cx+rx*x,cy+ry*y) for x,y in coverage.unit_circle(count)]
                for ring in (points,points[::-1],points[3:]+points[:3]):
                    for axis in (0,1):
                        for bound in (-10,0,10,ring[0][axis]):
                            for greater in (False,True):
                                with self.subTest(count=count,trial=trial,axis=axis,bound=bound,greater=greater):
                                    output=np.empty((264,2));size=native._clip(np.asarray(ring),len(ring),axis,bound,greater,output)
                                    a=output[:size].tolist();b=coverage._clip(ring,axis,bound,greater)
                                    self.assertEqual([[struct.pack('!d',v) for v in p] for p in a],
                                                     [[struct.pack('!d',v) for v in p] for p in b])

    def test_area_bits_match_cpython_summation_at_extreme_scales(self):
        import struct
        try:from azimlib.renderers import _coverage_native as native
        except ImportError:self.skipTest('Numba optional')
        import numpy as np
        rng=random.Random(400)
        for count in (3,4,5,9,10,24,64,256):
            for scale in (1e-100,1e-6,1.,1e6,1e100):
                for trial in range(15):
                    points=[(rng.uniform(-5,5)*scale,rng.uniform(-5,5)*scale) for _ in range(count)]
                    with self.subTest(count=count,scale=scale,trial=trial):
                        self.assertEqual(struct.pack('!d',native._area(np.asarray(points),count)),
                                         struct.pack('!d',coverage._area(points)))

    def test_missing_compiler_retains_scalar_and_general_ring_fallback(self):
        old=scalar();points=[(10+9*math.cos(i/15),10+9*math.sin(i/15)) for i in range(300)]
        with patch.object(coverage,'_native_type',return_value=None):
            with self.Image.new('L',(24,24)) as a,self.Image.new('L',(24,24)) as b:
                pillow._stroke(coverage.CoverageDraw(a),points,.7,'round','round',True)
                pillow._stroke(old(b),points,.7,'round','round',True)
                self.assertEqual(a.tobytes(),b.tobytes())
        with self.Image.new('L',(24,24)) as a,self.Image.new('L',(24,24)) as b:
            draw=coverage.CoverageDraw(a);draw.enable_native()
            ring=[(rng, (rng*7)%24) for rng in range(20)]
            draw.polygon([(1,1),(5,1),(5,5),(1,5)]);draw.polygon(ring);draw.flush()
            previous=old(b);previous.polygon([(1,1),(5,1),(5,5),(1,5)]);previous.polygon(ring)
            self.assertEqual(a.tobytes(),b.tobytes())

    def test_complete_alpha_dash_hole_png_matches_scalar_at_two_dpis(self):
        scene=Scene(140,100,None)
        ring=[(70+65*math.cos(i/45),50+44*math.sin(i/45)) for i in range(280)]
        scene.add(ScenePath([ring,[(40,30),(90,30),(90,70),(40,70)]],True,
            dict(fill='#33887766',stroke='#843b9a88',stroke_width=.35,linejoin='round',opacity=.7),clip=(3.3,2.1,130.1,94.2)))
        scene.add(ScenePath([[(i/3,50+25*math.sin(i/8)) for i in range(420)]],False,
            dict(stroke='red',stroke_width=.7,dash=(60,4),linecap='round')))
        for scale in (1,2):
            with self.subTest(scale=scale):
                with pillow.render_image(scene,scale) as a:
                    with patch.object(coverage,'CoverageDraw',scalar()):
                        with pillow.render_image(scene,scale) as b:self.assertEqual(a.tobytes(),b.tobytes())


if __name__=='__main__':unittest.main()
