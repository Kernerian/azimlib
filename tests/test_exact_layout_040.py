"""Accelerated layout must preserve scalar coordinates and collision decisions."""
import random,struct,unittest
from azimlib.projected_paths import screen_points,_pack
from azimlib.viewport import Viewport
from azimlib.projections import Mercator
from azimlib._legend_index import LegendIndex
from azimlib.legend_layout import score
from azimlib.scene import Path,Rect,Circle
from azimlib.renderers._gpu_geometry import fan,packed

class ExactLayout(unittest.TestCase):
    def test_large_fan_packed_bytes_match_scalar_order_and_weights(self):
        rng=random.Random(71);rings=[[(rng.uniform(-300,300),rng.uniform(-300,300)) for _ in range(700)],[(0,0)]*80]
        for signed in (False,True):
            expected=[]
            for ring in rings:
                a=ring[0]
                for b,c in zip(ring[1:-1],ring[2:]):
                    cross=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
                    if cross:expected.extend((x,y,(-1. if cross<0 else 1.) if signed else 1.) for x,y in (a,b,c))
            raw,origin=packed(tuple(expected));actual,anchor=packed(fan(rings,signed=signed))
            self.assertEqual(raw,actual);self.assertEqual(origin,anchor)
        self.assertEqual(packed(fan(iter(rings)))[0],packed(fan(rings))[0])
    def test_affine_float64_bytes_match_scalar_with_rotation(self):
        rng=random.Random(1024);points=[(rng.uniform(-1e8,1e8),rng.uniform(-1e8,1e8)) for _ in range(2000)]
        packed=_pack(points)
        for bearing in (0,17,90,179,270):
            vp=Viewport(Mercator(),(-70,-45,-30,20),(27,39,413,517),bearing=bearing)
            expected=b''.join(struct.pack('<2d',*vp.xy(*p)) for p in points)
            actual=b''.join(struct.pack('<2d',*p) for p in screen_points(packed,vp))
            self.assertEqual(actual,expected)
    def test_custom_viewport_override_is_observed(self):
        class Custom(Viewport):
            def xy(self,x,y):return 1,2
        vp=Custom(Mercator(),(-70,-45,-30,20),(0,0,400,500))
        self.assertEqual(screen_points(_pack([(0,0)]*200),vp),[(1,2)]*200)
    def test_collision_score_matches_scalar_inclusive_and_degenerate(self):
        rng=random.Random(42)
        items=[Path([[(rng.uniform(-1000,1000),rng.uniform(-1000,1000)) for _ in range(40)]],False,{}) for _ in range(10)]
        items.extend([Path([[(0,0),(0,0),(100,0),(100,100),(0,100)]],False,{}),Rect(0,0,5,5,{}),Circle(3,3,5,{})])
        index=LegendIndex(items)
        for box in [(0,0,100,100),(0,0,0,0),(-1,-1,1,1),*(tuple(rng.uniform(-500,500) for _ in range(2))+(80,60) for _ in range(80))]:
            self.assertEqual(index.score(box),score(box,items))

if __name__=='__main__':unittest.main()
