"""Chunked preparation preserves buffer bytes, vertex count, bounds and order."""
import unittest,random
from azimlib.renderers._gpu_stroke import round_stroke
from azimlib.renderers._gpu_geometry import packed,PackedMesh

class MeshPackets(unittest.TestCase):
    def test_packet_matches_original_staging_bytes_for_caps_and_zoom_scales(self):
        try:import numpy as np
        except ImportError:self.skipTest('NumPy acceleration optional')
        rng=random.Random(64);source=[[(rng.uniform(-200,200),rng.uniform(-200,200)) for _ in range(90)],[(0,0),(0,0),(0,20),(30,20)]]
        for scale in (.03,.9,1,3,70):
            rings=[[(x*scale+3.17,y*scale-9.31) for x,y in part] for part in source]
            for cap in ('butt','round','square'):
                for closed in (False,True):
                    before=round_stroke(rings,1.7,cap,closed);after=round_stroke(rings,1.7,cap,closed,pack=True)
                    self.assertIsInstance(after,PackedMesh);self.assertEqual(packed(before),packed(after));self.assertEqual(len(before),len(after))
                    bounds=tuple(map(float,(before[:,0].min(),before[:,1].min(),before[:,0].max(),before[:,1].max())))
                    self.assertEqual(bounds,after.bounds)
    def test_empty_zero_width_and_absent_numpy_do_not_invent_vertices(self):
        from unittest.mock import patch
        import sys
        for width in (0,1):
            value=round_stroke([],width,'round',False,pack=True)
            if value is not None:self.assertEqual(len(value),0)
        with patch.dict(sys.modules,{'numpy':None}):self.assertIsNone(round_stroke([],1,'butt',False,pack=True))

if __name__=='__main__':unittest.main()
