"""Indexed topology must expand to exactly the preceding float32 triangles."""
import math,random,unittest,sys,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from azimlib.renderers._gpu_indexed import indexed_stroke
from azimlib.renderers._gpu_stroke import round_stroke
from azimlib.renderers._gpu_geometry import packed,PreparationCache
from azimlib.scene import Path as Primitive

class Indexed(unittest.TestCase):
    def test_indices_preserve_triangle_bytes_bounds_origin_and_order(self):
        import numpy as np
        rng=random.Random(7908)
        for scale in (.01,1,100):
            rings=[[(scale*rng.uniform(-300,300),scale*rng.uniform(-300,300)) for _ in range(90)],[(0,0),(0,0),(4,0),(4,4)],[(3,3)],[]]
            for cap in ('butt','round','square'):
                for closed in (False,True):
                    old=round_stroke(rings,1.7,cap,closed,pack=True);new=indexed_stroke(rings,1.7,cap,closed)
                    positions=np.frombuffer(new.raw,dtype='f4').reshape(-1,3);indices=np.frombuffer(new.indices,dtype='<u4')
                    self.assertEqual(positions[indices].tobytes(),old.raw)
                    self.assertEqual(new.origin,old.origin);self.assertEqual(new.bounds,old.bounds);self.assertEqual(len(new),len(old))
                    self.assertLess(len(new.raw)+len(new.indices),len(old.raw))

    def test_mutation_and_topology_are_part_of_signature(self):
        cache=PreparationCache(1000000)
        a,_=cache.get(Primitive([[(0,0),(10,5),(20,0)]],style=dict(stroke='red',stroke_width=1)))
        b,_=cache.get(Primitive([[(0,0),(11,5),(20,0)]],style=dict(stroke='red',stroke_width=1)))
        self.assertNotEqual(a.signature,b.signature)
        self.assertIsNotNone(a[0].indices)
        self.assertLessEqual(cache.bytes,cache.limit)

    def test_empty_zero_and_optional_numpy(self):
        from unittest.mock import patch
        for width in (0,1):self.assertEqual(len(indexed_stroke([],width,'butt',False)),0)
        with patch.dict(sys.modules,{'numpy':None}):self.assertIsNone(indexed_stroke([],1,'butt',False))

    def test_near_ulp_and_extreme_offsets_preserve_degenerate_predicate(self):
        import numpy as np
        for offset in (0.,1e7,1e12):
            for width in (.0001,.1,4,400):
                rings=[[(offset,offset),(offset+20,offset+5),(offset+40,offset-5)]]
                old=round_stroke(rings,width,'round',False,pack=True);new=indexed_stroke(rings,width,'round',False)
                v=np.frombuffer(new.raw,dtype='f4').reshape(-1,3);idx=np.frombuffer(new.indices,dtype='<u4')
                self.assertEqual(v[idx].tobytes(),old.raw)
                self.assertEqual(new.bounds,old.bounds);self.assertEqual(new.origin,old.origin)

    @unittest.skipUnless(os.environ.get('AZIMLIB_GPU_TEST')=='1','Explicit GPU contract trial required')
    def test_topology_and_vao_persist_while_positions_update(self):
        from azimlib.renderers.gpu import GpuRenderer,GpuConfig
        from azimlib.scene import Scene
        with GpuRenderer(GpuConfig(context_backend=os.environ.get('AZIMLIB_GPU_CONTEXT'))) as renderer:
            def scene(middle):return Scene(30,20,items=[Primitive([[(2,2),middle,(25,2)]],style=dict(stroke='red',stroke_width=1.7))])
            renderer.render(scene((12,12))).close();uploads=renderer.stats['index_uploads']
            vao=next(entry[0] for key,entry in renderer._cache.items() if key[0]=='indexed-slot')
            renderer.render(scene((13,13))).close()
            self.assertEqual(renderer.stats['index_uploads'],uploads)
            self.assertGreater(renderer.stats['buffer_updates'],0)
            self.assertIs(vao,next(entry[0] for key,entry in renderer._cache.items() if key[0]=='indexed-slot'))
            self.assertLessEqual(renderer._cache_bytes,renderer.config.max_cache_bytes)

if __name__=='__main__':unittest.main()
