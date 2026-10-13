"""Exact collision scoring and unchanged stroke coverage after preparation optimization."""
import math
import random
import sys
import unittest
from pathlib import Path as FilePath
from unittest.mock import patch
sys.path.insert(0,str(FilePath(__file__).resolve().parents[1]/'src'))
from azimlib.scene import Path, Circle, Rect, Text, Scene
from azimlib._legend_index import LegendIndex
from azimlib.legend_layout import score
from azimlib.renderers._gpu_geometry import drawing, circle


class PreparationContracts(unittest.TestCase):
    def test_resolved_text_miss_does_not_repeat_shaping_or_alignment(self):
        from azimlib.renderers._gpu_geometry import PreparationCache
        cache=PreparationCache(100000)
        item=Text(12,15,'resolved',dict(fill='black',font_size=12))
        with patch.object(Text,'__post_init__',side_effect=AssertionError('resolved twice')):
            first,anchor=cache.get(item)
            second,_=cache.get(item)
        self.assertIs(first,second);self.assertEqual(anchor,(12,15))

    def test_index_matches_original_inclusive_degenerate_and_long_segments(self):
        rng=random.Random(90408)
        items=[Path([[(rng.uniform(-400,400),rng.uniform(-400,400)) for _ in range(300)]]),
               Path([[(-1e6,-1e6),(1e6,1e6)],[(0,0),(0,0)],[(64,0),(64,64)]]),
               Circle(64,64,10),Rect(-20,10,5,5),Text(1,1,'Label',dict(font_size=12))]
        index=LegendIndex(items)
        boxes=[(0,0,64,64),(64,64,0,0),(-1e6,-1e6,2e6,2e6)]
        boxes.extend((rng.uniform(-300,300),rng.uniform(-300,300),rng.uniform(0,100),rng.uniform(0,100)) for _ in range(100))
        for box in boxes:
            with self.subTest(box=box):self.assertEqual(index.score(box),score(box,items))
        with patch.dict(sys.modules,{'numpy':None}):fallback=LegendIndex(items)
        for box in boxes:
            with self.subTest(fallback_box=box):self.assertEqual(fallback.score(box),score(box,items))

    def test_cached_circle_retains_original_coordinates(self):
        for rx,ry in ((.4,.4),(2,7),(100,100)):
            count=max(16,min(2048,math.ceil(math.pi*math.sqrt(max(rx,ry)*8))))
            expected=tuple((3+rx*math.cos(i*2*math.pi/count),5+ry*math.sin(i*2*math.pi/count)) for i in range(count))
            self.assertEqual(circle(3,5,rx,ry),expected)

    def test_round_bulk_mesh_matches_scalar_coverage(self):
        try: import numpy as np
        except ImportError:self.skipTest('Optional NumPy absent')
        from azimlib.renderers._gpu_stroke import round_stroke
        from azimlib.renderers._gpu_geometry import StrokeMesh,fan
        from azimlib.renderers.pillow import _stroke
        rings=(((1.,2.),(1.,2.),(4.,8.),(7.,-1.)),((5.,3.),),())
        for closed in (False,True):
            for cap in ('butt','round','square'):
                mesh=StrokeMesh()
                for ring in rings:
                    points=list(ring)
                    if closed and points and points[-1]!=points[0]:points.append(points[0])
                    _stroke(mesh,points,2.,cap,'round',closed)
                scalar=fan(mesh.rings);bulk=round_stroke(rings,2.,cap,closed)
                # Union coverage does not depend on triangle order. Compare all
                # triangle vertices, allowing only binary64 arithmetic roundoff.
                def canonical(a):
                    return sorted(tuple(sorted(tuple(np.round(p[:2],11)) for p in t)) for t in np.asarray(a).reshape(-1,3,3))
                self.assertEqual(canonical(scalar),canonical(bulk))
        self.assertEqual(len(round_stroke(rings,0,'butt',False)),0)

    def test_numpy_is_optional_and_mesh_budget_is_preserved(self):
        from azimlib.renderers._gpu_stroke import round_stroke
        with patch.dict(sys.modules,{'numpy':None}):self.assertIsNone(round_stroke((),1,'butt',False))
        try: import numpy
        except ImportError:return
        with self.assertRaisesRegex(ValueError,'budget'):
            round_stroke(([(float(i),float(i%2)) for i in range(40000)],),2,'round',False)


if __name__=='__main__':unittest.main()
