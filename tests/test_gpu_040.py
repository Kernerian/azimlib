"""GPU contracts run without a device; actual-device tests require explicit opt-in."""
import io
import os
import threading
import unittest
from unittest.mock import patch
from dataclasses import replace
from pathlib import Path as FilePath
import sys
ROOT=FilePath(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from azimlib.scene import Scene,Path,Text,Circle,Rect,Raster3D
from azimlib.renderers.gpu import GpuRenderer,GpuConfig,GpuError,GpuUnavailableError,GpuResourceError,GpuCancelled,render_gpu_image
from azimlib.renderers._gpu_geometry import fan,drawing,PreparationCache


class GpuContracts(unittest.TestCase):
    def test_config_limits(self):
        for kwargs in (dict(max_surface_bytes=0),dict(max_cache_bytes=True),dict(max_vertices=2000001),dict(context_backend='guess')):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):GpuConfig(**kwargs)
    def test_explicit_fallback_and_failure(self):
        with patch('azimlib.renderers.gpu.GpuRenderer',side_effect=GpuUnavailableError('absent')):
            with self.assertRaises(GpuUnavailableError):render_gpu_image(Scene(5,5))
            with self.assertWarns(RuntimeWarning):
                image=render_gpu_image(Scene(5,5),fallback='cpu');self.assertEqual(image.size,(5,5));image.close()
        with self.assertRaises(ValueError):render_gpu_image(Scene(5,5),fallback='auto')
    def test_cancellation_never_falls_back(self):
        with patch('azimlib.renderers.gpu.GpuRenderer',side_effect=GpuCancelled('cancel')):
            with self.assertRaises(GpuCancelled):render_gpu_image(Scene(5,5),fallback='cpu')
    def test_mesh_and_exact_translation_cache(self):
        cache=PreparationCache(100000)
        a=Path((((0,0),(10,0),(10,10)),),True,dict(fill='red',stroke='blue',stroke_width=2))
        b=replace(a,paths=(((5,7),(15,7),(15,17)),))
        packets,anchor=cache.get(a);shifted,offset=cache.get(b)
        self.assertIs(packets,shifted);self.assertEqual(offset,(5,7));self.assertEqual(cache.hits,1)
        changed=replace(b,paths=(((5,7),(15,7),(15,17.001)),))
        cache.get(changed);self.assertEqual(cache.misses,2)
        cache.get(replace(a,style=dict(a.style,stroke_width=3)));self.assertEqual(cache.misses,3)
        self.assertLessEqual(cache.bytes,cache.limit);cache.clear();self.assertEqual(cache.bytes,0)
    def test_caps_dashes_nonzero_text_and_finite_triangle_weights(self):
        line=Path((((0,0),(10,0),(10,10)),),style=dict(stroke='red',stroke_width=2,linecap='round',linejoin='miter',dash=(2,1)))
        packet=drawing(line);self.assertEqual(len(packet),1);self.assertEqual(packet[0].rule,0)
        text=drawing(Text(0,0,'Oé',dict(fill='black',font_size=12)))
        self.assertEqual(text[0].rule,2)
        self.assertEqual({p[2] for p in fan((((0,0),(1,0),(0,1)),((0,0),(0,1),(1,0))),signed=True)},{-1,1})
    def test_public_selection_rejects_unsupported_outputs_before_drawing(self):
        import azimlib as azl
        fig,ax=azl.subplots()
        try:
            with self.assertRaises(ValueError):fig.savefig(io.StringIO(),format='svg',renderer='gpu')
            with self.assertRaises(ValueError):fig.show(backend='browser',renderer='gpu')
            with self.assertRaises(ValueError):fig.savefig(io.BytesIO(),format='png',renderer='magic')
        finally:azl.close(fig)
    def test_capability_query_never_initializes_context(self):
        from azimlib.renderers import get_capabilities
        with patch('azimlib.renderers.gpu.GpuRenderer',side_effect=AssertionError('context')):
            caps=get_capabilities('gpu');self.assertTrue(caps.gpu);self.assertFalse(caps.vector_output);self.assertTrue(caps.volumes)
    def test_preparation_cache_bound(self):
        cache=PreparationCache(1000)
        for i in range(20):cache.get(Rect(0,0,10+i,10,dict(fill='red')))
        self.assertLessEqual(cache.bytes,1000)
    def test_textured_artist_atomic_edits_and_depth_atlas(self):
        import azimlib as azl
        fig=azl.figure();ax=fig.add_subplot(111,projection='3d');texture=(1,1,bytes((255,0,0,255)))
        try:
            artist=ax.plot_surface([0,1],[0,1],[[0,1],[1,2]],texture=texture,color='white')
            ax.plot_surface([0,1],[0,1],[[1,2],[2,3]],color='blue')
            primitive=next(p for p in fig.to_scene().items if isinstance(p,Raster3D))
            self.assertEqual(len(primitive.triangles),4);self.assertEqual(len(primitive.uv),4);self.assertEqual(primitive.texture[:2],(1,2))
            with self.assertRaises(ValueError):artist.set_texture((1,1,bytes((0,0,0,128))))
            self.assertEqual(artist.get_texture(),texture)
            with self.assertRaises(ValueError):artist.set_texture(texture,((0,0),(1,0),(0,1),(float('nan'),1)))
            self.assertEqual(artist.get_texture(),texture)
            artist.set_visible(False);self.assertTrue(all(p.texture is None for p in fig.to_scene().items if isinstance(p,Raster3D)))
            artist.set_visible(True);artist.set_texture(None);self.assertIsNone(artist.get_texture())
        finally:azl.close(fig)
    def test_texture_contract_and_perspective_reference(self):
        from azimlib._texture3d import rasterize_textured,clipped
        texture=(2,2,bytes((255,0,0,255,0,255,0,255,0,0,255,255,255,255,255,255)))
        vertices=((-1,1,0,1),(1,1,0,1),(1,-1,0,1))
        item=Raster3D(0,0,20,20,((vertices,(255,255,255,255)),),texture=texture,uv=(((0,0),(1,0),(1,1)),))
        result=rasterize_textured(item,20,20)
        self.assertEqual(result.rgba[(2*20+5)*4:(2*20+5)*4+4],bytes((255,0,0,255)))
        self.assertEqual(result.rgba[(2*20+15)*4:(2*20+15)*4+4],bytes((0,255,0,255)))
        self.assertEqual(item.scaled(2) if hasattr(item,'scaled') else Scene(20,20,items=[item]).scaled(2).items[0].texture,texture)
        self.assertTrue(clipped(((-2,1,0,1),(1,1,0,1),(1,-1,0,1)),((0,0),(1,0),(1,1))))
        with self.assertRaises(ValueError):replace(item,texture=(2,2,bytes([0,0,0,128])*4))
        with self.assertRaises(ValueError):replace(item,uv=(((0,0),(2,0),(1,1)),))


@unittest.skipUnless(os.environ.get('AZIMLIB_GPU_TEST')=='1','Actual GPU explicitly opted out')
class ActualGpu(unittest.TestCase):
    def setUp(self):self.gpu=GpuRenderer(GpuConfig(context_backend=os.environ.get('AZIMLIB_GPU_CONTEXT')))
    def tearDown(self):self.gpu.close()
    def test_buffer_reuses_exact_bytes_but_separates_programs(self):
        from array import array
        data=array('f',(0,0,1,1,0,1,0,1,1)).tobytes()
        a=self.gpu._buffer(data,self.gpu.mask_program,'3f',('point',))
        b=self.gpu._buffer(bytes(bytearray(data)),self.gpu.mask_program,'3f',('point',))
        self.assertIs(a,b);self.assertEqual(self.gpu.stats['uploads'],1)
        other=self.gpu.ctx.program(vertex_shader='#version 330\nin vec3 point;void main(){gl_Position=vec4(point,1.);}',fragment_shader='#version 330\nout vec4 color;void main(){color=vec4(1.);}')
        try:
            c=self.gpu._buffer(data,other,'3f',('point',))
            self.assertIsNot(a,c);self.assertEqual(self.gpu.stats['uploads'],2)
        finally:other.release()
    def test_evenodd_concavity_holes_and_paint_order(self):
        rings=(((5,5),(75,5),(75,75),(5,75)),((25,25),(55,25),(55,55),(25,55)))
        scene=Scene(80,80,items=[Path(rings,True,dict(fill='red')),Circle(40,40,5,dict(fill='blue'))])
        image=self.gpu.render(scene)
        try:
            self.assertEqual(image.getpixel((10,10)),(255,0,0,255));self.assertEqual(image.getpixel((30,30)),(255,255,255,255));self.assertEqual(image.getpixel((40,40)),(0,0,255,255))
        finally:image.close()
        concave=Scene(80,80,items=[Path((((5,5),(75,5),(75,20),(20,20),(20,75),(5,75)),),True,dict(fill='red'))])
        image=self.gpu.render(concave)
        try:self.assertEqual(image.getpixel((30,30)),(255,255,255,255));self.assertEqual(image.getpixel((10,60)),(255,0,0,255))
        finally:image.close()
    def test_alpha_clip_scale_and_physical_stroke(self):
        scene=Scene(40,40,None,items=[Rect(0,0,40,40,dict(fill='red',opacity=.5),clip=(10,10,20,20)),Path((((0,20),(40,20)),),style=dict(stroke='blue',stroke_width=2))])
        image=self.gpu.render(scene,2)
        try:
            self.assertEqual(image.getpixel((0,0)),(0,0,0,0));self.assertEqual(image.getpixel((30,30))[:3],(255,0,0))
            self.assertLessEqual(abs(image.getpixel((30,30))[3]-128),1)  # RGBA16F/UNORM conversion budget.
            self.assertEqual(image.getpixel((30,40)),(0,0,255,255));self.assertNotEqual(image.getpixel((30,44)),(0,0,255,255))
        finally:image.close()
    def test_depth_homogeneous_clip_and_masked_faces(self):
        far=((-1,-1,.8,1),(1,-1,.8,1),(0,1,.8,1));near=tuple((x,y,-.8,w) for x,y,z,w in far)
        scene=Scene(80,80,items=[Raster3D(0,0,80,80,((near,(255,0,0,255)),(far,(0,0,255,255))))])
        image=self.gpu.render(scene)
        try:self.assertEqual(image.getpixel((40,40)),(255,0,0,255))
        finally:image.close()
        outside=tuple((x,y,2,w) for x,y,z,w in far)
        image=self.gpu.render(Scene(80,80,items=[replace(scene.items[0],triangles=((outside,(255,0,0,255)),))]))
        try:self.assertEqual(image.getpixel((40,40)),(255,255,255,255))
        finally:image.close()
        with self.assertRaises(ValueError):self.gpu.render(Scene(80,80,items=[replace(scene.items[0],triangles=((far,(255,0,0,128)),))]))
    def test_reuse_edit_resize_thread_generation_cancel_lifecycle(self):
        scene=Scene(50,50,items=[Circle(20,20,8,dict(fill='red'))])
        self.gpu.render(scene,generation=2).close();uploads=self.gpu.stats['uploads']
        self.gpu.render(scene,generation=3).close();self.assertEqual(uploads,self.gpu.stats['uploads'])
        self.gpu.render(Scene(60,60,items=[replace(scene.items[0],x=30)])).close();self.assertEqual(uploads,self.gpu.stats['uploads'])
        with self.assertRaises(GpuCancelled):self.gpu.render(scene,generation=1)
        event=threading.Event();event.set()
        with self.assertRaises(GpuCancelled):self.gpu.render(scene,cancel=event)
        failures=[]
        def other():
            try:self.gpu.render(scene)
            except GpuError:failures.append(True)
        t=threading.Thread(target=other);t.start();t.join();self.assertEqual(failures,[True])
        self.gpu.close();self.gpu.close()
        with self.assertRaises(GpuError):self.gpu.render(scene)
    def test_resource_budget_and_explicit_lost_context(self):
        self.gpu.config=replace(self.gpu.config,max_surface_bytes=10)
        with self.assertRaises(GpuResourceError):self.gpu.render(Scene(10,10))
        self.gpu.lost=True
        with self.assertRaises(GpuError):self.gpu.render(Scene(10,10))
    def test_worker_shared_scene_concurrent_pipe_and_exports(self):
        from azimlib.backends._navigation_process import NavigationProcess
        scene=Scene(80,80,items=[Text(10,40,'Azimlib',dict(font_size=12)),Circle(30,60,5,dict(fill='green'))])
        worker=NavigationProcess(renderer='gpu',gpu_config=self.gpu.config)
        try:
            image=worker.render(scene);expected=self.gpu.render(scene)
            self.assertEqual(image.tobytes(),expected.tobytes());image.close();expected.close()
            self.assertEqual(worker.backend_info['renderer'],'gpu')
            results=[]
            def render():
                image=worker.render(scene);results.append(image.size);image.close()
            threads=[threading.Thread(target=render) for _ in range(3)]
            for t in threads:t.start()
            for t in threads:t.join()
            self.assertEqual(results,[(80,80)]*3)
        finally:worker.close()
    def test_textured_perspective_cpu_gpu_and_exports(self):
        from azimlib._texture3d import rasterize_textured
        from azimlib.renderers import render_svg,render_pdf
        # Homogeneous W varies: UV is perspective-correct, not screen-linear.
        vertices=((-1,1,0,1),(2,2,0,2),(2,-2,0,2))
        texture=(2,2,bytes((255,0,0,255,0,255,0,255,0,0,255,255,255,255,255,255)))
        item=Raster3D(0,0,80,80,((vertices,(255,255,255,255)),),texture=texture,uv=(((0,0),(1,0),(1,1)),))
        scene=Scene(80,80,items=[item]);image=self.gpu.render(scene);reference=rasterize_textured(item,80,80)
        try:
            for x,y in ((10,5),(60,5),(70,60)):
                expected=tuple(reference.rgba[(y*80+x)*4:(y*80+x)*4+4]);self.assertEqual(image.getpixel((x,y)),expected)
        finally:image.close()
        self.gpu.render(scene).close();self.assertEqual(self.gpu.stats['texture_uploads'],1)
        self.assertIn('data:image/png;base64',render_svg(scene));self.assertTrue(render_pdf(scene).startswith(b'%PDF'))
    def test_worker_sends_only_pixels_not_artist_or_mappingproxy_state(self):
        import azimlib as azl
        from azimlib.backends._navigation_process import NavigationProcess
        fig,ax=azl.subplots(figsize=(2,2));ax.map('brazil');worker=NavigationProcess(renderer='gpu',gpu_config=self.gpu.config)
        try:
            scene=fig.to_scene();self.assertTrue(scene._pick_records)
            image=worker.render(scene);self.assertEqual(image.size,(200,200));image.close()
        finally:worker.close();azl.close(fig)


if __name__=='__main__':unittest.main()
