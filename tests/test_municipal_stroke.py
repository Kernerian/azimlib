"""Coordinate bound lookup preserves masks and complete raster output."""
import importlib.util
import io
import math
from pathlib import Path as FilePath
import random
import struct
import unittest
from unittest.mock import patch
from azimlib.renderers import coverage,render_png
from azimlib.scene import Scene,Path,Circle,Rect

def baseline():
    path=FilePath(__file__).resolve().parents[1]/'tools/baselines/municipal-stroke-before/coverage.py'
    spec=importlib.util.spec_from_file_location('municipal_stroke_baseline',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

class MunicipalStrokeTests(unittest.TestCase):
    def test_area_preserves_float_bits_for_large_and_irregular_rings(self):
        rng=random.Random(451);old=baseline()
        cases=[[],[(0.,0.)],[(0.,0.),(1.,1.)],[(0,0),(1,0),(1,1),(0,1)]]
        for i in range(80):
            count=rng.choice((8,24,64,256));cx,cy=rng.uniform(-20,20),rng.uniform(-20,20)
            rx,ry=rng.uniform(.001,8),rng.uniform(.001,8)
            points=[(cx+rx*c,cy+ry*s) for c,s in coverage.unit_circle(count)]
            cases.extend((points,points[::-1],points[7:]+points[:7]))
            cases.append([(rng.uniform(-1e12,1e12),rng.uniform(-1e12,1e12)) for _ in range(count)])
        for i,points in enumerate(cases):
            with self.subTest(case=i):
                self.assertEqual(struct.pack('!d',coverage._area(points)),struct.pack('!d',old._area(points)))

    def test_concave_and_self_intersecting_polygons_preserve_masks(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Pillow optional')
        old=baseline();rng=random.Random(837)
        for count in (5,8,24,64):
            for i in range(20):
                points=[(rng.uniform(-3,18),rng.uniform(-3,18)) for _ in range(count)]
                with self.subTest(count=count,case=i):
                    with Image.new('L',(16,16)) as a,Image.new('L',(16,16)) as b:
                        coverage.CoverageDraw(a).polygon(points,80);old.CoverageDraw(b).polygon(points,80)
                        self.assertEqual(a.tobytes(),b.tobytes())

    def test_ellipse_fresh_and_accumulated_masks_match_subpixel_edges_and_clipping(self):
        try:from PIL import Image
        except ImportError:self.skipTest('Pillow optional')
        old=baseline();rng=random.Random(913)
        bounds=[(0,0,0,0),(-4,-2,3,5),(.1,.2,1.1,1.2),(0,0,16,16),(2,4,7,5),
                (8,9,2,1),(-50,-50,-20,-20),(40,40,80,80),(-1,-1,0,0),(16,16,19,19)]
        for i in range(160):
            x,y=rng.uniform(-3,18),rng.uniform(-3,18);rx,ry=rng.uniform(.005,7),rng.uniform(.005,7)
            bounds.append((x-rx,y-ry,x+rx,y+ry))
        for fill in (0,1,80,255):
            with Image.new('L',(16,16)) as a,Image.new('L',(16,16)) as b:
                current,previous=coverage.CoverageDraw(a),old.CoverageDraw(b)
                for i,box in enumerate(bounds):
                    with self.subTest(fill=fill,case=i):
                        with Image.new('L',(16,16)) as fresh_a,Image.new('L',(16,16)) as fresh_b:
                            coverage.CoverageDraw(fresh_a).ellipse(box,fill);old.CoverageDraw(fresh_b).ellipse(box,fill)
                            self.assertEqual(fresh_a.tobytes(),fresh_b.tobytes())
                        current.ellipse(box,fill);previous.ellipse(box,fill);self.assertEqual(a.tobytes(),b.tobytes())

    def test_png_preserves_round_joins_caps_dashes_alpha_and_clips(self):
        try:import PIL
        except ImportError:self.skipTest('Pillow optional')
        old=baseline()
        for scale in (1,1.5,2):
            with self.subTest(scale=scale):
                scene=Scene(100,80,None)
                for i,cap in enumerate(('butt','round','square')):
                    scene.add(Path([[(-3,8+i*22),(35.5,3+i*22),(54.2,18+i*22),(103,8+i*22)]],style=dict(
                        stroke='#33557788',stroke_width=.6+i*.3,linejoin='round',linecap=cap,dash=(3.1,1.7),opacity=.8),clip=(2.3,1.7,93.4,76.1)))
                scene.add(Circle(45.2,34.7,9.1,dict(fill='white',stroke='red',stroke_width=.8)))
                scene.add(Rect(9,12,24,30,dict(fill='#ffeebb',stroke='black',stroke_width=.6,opacity=.5)))
                a,b=io.BytesIO(),io.BytesIO();render_png(scene,a,scale)
                with patch.object(coverage,'CoverageDraw',old.CoverageDraw):render_png(scene,b,scale)
                self.assertEqual(a.getvalue(),b.getvalue())

if __name__=='__main__':unittest.main()
