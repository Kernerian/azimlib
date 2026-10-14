"""Original analytic volume, streaming, alpha/depth and editable Artist fixtures."""
import hashlib,io,json,math,os,struct,tempfile,unittest
from dataclasses import replace
from pathlib import Path
import azimlib as azl
from azimlib.volume import VolumeField,VolumeBudget,read_volume,write_volume,_packed
from azimlib.volume_render import VolumeLayer,OpacityTransfer,VolumeLight,trace_ray,inverse_matrix,rasterize_volume,_shade,pick_volume
from azimlib.volume_artist import slice_mesh,isosurface_mesh
from azimlib.colors import Normalize,LogNorm,BoundaryNorm
from azimlib.scene import Raster3D,Scene

IDENTITY=(1.,0,0,0,0,1.,0,0,0,0,1.,0,0,0,0,1.)
def field(n=3,func=lambda x,y,z:x+2*y+3*z,**kwargs):
    return VolumeField.from_array([[[func(x,y,z) for x in range(n)] for y in range(n)] for z in range(n)],**kwargs)
def layer(*,alpha=.5,step=.1,color=(1.,0,0),data=None,light=None):
    data=data or field(2,lambda x,y,z:1,origin=(-1,-1,-.5),spacing=(2,2,1))
    return VolumeLayer(data,IDENTITY,_packed([*color,alpha]*256),(0.,1.),False,step,1.,1.,light)


class VolumeFields(unittest.TestCase):
    def test_linear_sampling_metric_units_and_vector_contract(self):
        f=field(unit='km',value_unit='K');self.assertEqual(f.bounds,(0,2000,0,2000,0,2000));self.assertEqual(f.sample(250,500,750),3.5)
        self.assertIsNone(f.sample(-1,0,0));self.assertEqual(f.sample(2000,2000,2000),12)
        v=field(2,lambda x,y,z:(x,y,z),components=3);self.assertEqual(v.sample(.25,.5,.75),(.25,.5,.75))
        self.assertAlmostEqual(v.component('magnitude').sample(1,1,1),math.sqrt(3),places=6)
        self.assertEqual(v.component(0).sample(.25,.5,.75),.25)
    def test_nodata_interpolation_and_zero_weight_nodes(self):
        f=field(2,lambda x,y,z:None if x==1 and y==1 and z==1 else 2)
        self.assertEqual(f.sample(0,0,0),2);self.assertIsNone(f.sample(.5,.5,.5));self.assertEqual(f.sample(.1,.1,.1,method='nearest'),2)
        self.assertEqual(f.summary['valid_nodes'],7)
        f=field(2,lambda x,y,z:-999 if x else 1,nodata=-999);self.assertIsNone(f.sample(1,0,0))
    def test_dense_shape_and_memory_guards(self):
        for data in ([],[[[1]]],[[[1,2],[3]]]):
            with self.subTest(data=data),self.assertRaises(ValueError):VolumeField.from_array(data)
        with self.assertRaises(ValueError):field(3,budget=VolumeBudget(max_dense_bytes=32))
        with self.assertRaises(ValueError):field(spacing=(1,0,1))
        with self.assertRaises(ValueError):VolumeBudget(max_steps=513)
        with self.assertRaises(ValueError):field(2,lambda x,y,z:1e40)
    def test_brick_roundtrip_selection_hash_and_bounded_cache(self):
        f=field(5,budget=VolumeBudget(max_cache_bytes=64))
        with tempfile.TemporaryDirectory() as folder:
            path=write_volume(Path(folder)/'field.azv',f,brick_size=2);digest=hashlib.sha256(path.read_bytes()).hexdigest();g=read_volume(path,sha256=digest,budget=f.budget)
            self.assertIsNone(g.values);self.assertEqual(g.summary,f.summary);s=g.sampler()
            with self.assertRaises(ValueError):replace(g,shape=(2,2,2))
            for p in ((0,0,0),(4,4,4),(1.5,2.5,3.5),(0,4,1)):
                self.assertEqual(s.sample(p),f.sample(*p));self.assertLessEqual(s.cache_bytes,64)
            selected=g.select((1,3,1,3,1,3));self.assertEqual(selected.shape,(3,3,3));self.assertEqual(selected.origin,(1,1,1));self.assertEqual(selected.sample(2,2,2),12)
            self.assertEqual(g.store.sha256,digest)
            with self.assertRaises(FileExistsError):write_volume(path,f,brick_size=2)
            with self.assertRaises(ValueError):read_volume(path,sha256='0'*64)
    def test_streaming_producer_and_partial_writer_cleanup(self):
        f=field(5)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'stream.azv';write_volume(path,shape=f.shape,bricks=f.iter_bricks(brick_size=2),brick_size=2)
            self.assertEqual(read_volume(path).sample(4,4,4),24)
            missing=Path(folder)/'missing.azv'
            with self.assertRaises(ValueError):write_volume(missing,shape=f.shape,bricks=iter(()),brick_size=2)
            self.assertFalse(missing.exists());self.assertFalse(list(Path(folder).glob('.azv-*')))
            with self.assertRaises(ValueError):write_volume(missing,f,brick_size=2,budget=VolumeBudget(max_file_bytes=64))
            self.assertFalse(missing.exists())
    def test_corrupt_truncated_changed_and_malicious_header_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            path=write_volume(Path(folder)/'field.azv',field(),brick_size=2);g=read_volume(path);original=path.read_bytes()
            path.write_bytes(original[:-1]+bytes((original[-1]^1,)))
            with self.assertRaises(ValueError):read_volume(path)
            # A same-size rapid write can retain its timestamp on Windows.
            # Exercise the documented stat guard deterministically; the read
            # above independently checked payload corruption by SHA-256.
            stamp=path.stat();os.utime(path,ns=(stamp.st_atime_ns,g.store.signature[1]+1_000_000_000))
            with self.assertRaises(ValueError):g.sample(0,0,0)
            path.write_bytes(original[:-1])
            with self.assertRaises(ValueError):read_volume(path)
            path.write_bytes(original+b'x')
            with self.assertRaises(ValueError):read_volume(path)
            meta=dict(shape=[2,2,2],origin=[0,0,0],spacing=[1,1,1],components=10**12,value_unit='1',frame=None,brick_size=2);raw=json.dumps(meta).encode();path.write_bytes(b'AZIMVOL1\n'+struct.pack('<I',len(raw))+raw)
            with self.assertRaises(ValueError):read_volume(path)
    def test_frame_identity_and_roi_errors(self):
        frame=azl.terrain3d.LocalFrame(-46,-23);f=field(frame=frame)
        with tempfile.TemporaryDirectory() as folder:
            g=read_volume(write_volume(Path(folder)/'local.azv',f,brick_size=2));self.assertEqual(g.frame,frame)
        with self.assertRaises(ValueError):f.select((10,20,0,1,0,1))
        with self.assertRaises(ValueError):f.sample(0,0,0,method='guess')


class VolumeReference(unittest.TestCase):
    def test_heterogeneous_midpoint_precision_converges(self):
        f=field(2,lambda x,y,z:z,origin=(-1,-1,0),spacing=(2,2,1))
        base=layer(data=f)
        base=replace(base,table=_packed([v for i in range(256) for v in (1.,0.,0.,.5*i/255)]))
        expected=1-math.exp(-(1+math.log(.5)))
        errors=[]
        for step in (.1,.05,.025):
            actual=trace_ray((replace(base,step=step),),(0,0,-1),(0,0,1))[0][3]
            errors.append(abs(actual-expected))
        self.assertLess(errors[-1],1e-5)
        self.assertTrue(errors[1]<errors[0]/3 and errors[2]<errors[1]/3,errors)
    def test_homogeneous_alpha_length_and_step_invariance(self):
        for step in (.03,.1,.31,2.):
            rgba,_=trace_ray((layer(step=step),),(0,0,-2),(0,0,1))
            self.assertAlmostEqual(rgba[3],.5,places=6);self.assertAlmostEqual(rgba[0],.5,places=6)
        scaled=replace(layer(),density=2)
        self.assertAlmostEqual(trace_ray((scaled,),(0,0,-2),(0,0,1))[0][3],.75,places=6)
        self.assertAlmostEqual(trace_ray((replace(layer(),reference_length=2),),(0,0,-2),(0,0,1))[0][3],1-math.sqrt(.5),places=6)
    def test_overlapping_fields_mix_extinction_order_independently(self):
        red,blue=layer(),layer(color=(0,0,1))
        a=trace_ray((red,blue),(0,0,-2),(0,0,1))[0];b=trace_ray((blue,red),(0,0,-2),(0,0,1))[0]
        self.assertEqual(a,b);self.assertAlmostEqual(a[3],.75,places=6);self.assertAlmostEqual(a[0],.375,places=6)
    def test_nodata_zero_opacity_and_geometry_distance(self):
        missing=layer(data=field(2,lambda x,y,z:None,origin=(-1,-1,-.5),spacing=(2,2,1)))
        self.assertEqual(trace_ray((missing,),(0,0,-2),(0,0,1))[0],(0,0,0,0))
        self.assertEqual(trace_ray((layer(alpha=0),),(0,0,-2),(0,0,1))[0],(0,0,0,0))
        self.assertAlmostEqual(trace_ray((layer(),),(0,0,-2),(0,0,1),maximum=2)[0][3],1-math.sqrt(.5),places=6)
    def test_inverse_camera_roundtrip_and_invalid_transfer(self):
        from azimlib.terrain3d import Camera,matmul
        matrix=Camera().matrix((-1,1,-1,1,-1,1));result=matmul(matrix,inverse_matrix(matrix))
        self.assertTrue(all(abs(v-w)<1e-12 for v,w in zip(result,IDENTITY)))
        with self.assertRaises(ValueError):inverse_matrix((0,)*16)
        with self.assertRaises(ValueError):OpacityTransfer(((0,0),(.5,1),(.5,0),(1,1)))
        with self.assertRaises(ValueError):VolumeLight(shadow_steps=33)
        with self.assertRaises(ValueError):replace(layer(),step=0)
    def test_volume_diffuse_and_self_absorption_are_declared(self):
        data=field(5,lambda x,y,z:1-x*.25,spacing=(.25,)*3);base=layer(data=data,alpha=.2,light=VolumeLight((1,0,0),ambient=0,diffuse=1))
        p=(.5,.5,.5);s=data.sampler();unshadowed=_shade(base,s,p);shadowed=_shade(replace(base,light=VolumeLight((1,0,0),ambient=0,diffuse=1,shadow_steps=8)),s,p)
        self.assertAlmostEqual(unshadowed,1);self.assertLess(shadowed,unshadowed);self.assertAlmostEqual(shadowed,math.sqrt(.8),places=6)
    def test_numpy_matches_reference_and_depth(self):
        triangles=((((-1,-1,0,1),(1,-1,0,1),(1,1,0,1)),(0,0,255,255)),(((-1,-1,0,1),(1,1,0,1),(-1,1,0,1)),(0,0,255,255)))
        item=Raster3D(0,0,8,8,triangles,volumes=(layer(),));a=rasterize_volume(item,8,8,accelerate=False);b=rasterize_volume(item,8,8)
        self.assertEqual(a.rgba,b.rgba);self.assertGreater(a.rgba[2],150);self.assertLess(a.rgba[0],100)
        hit=pick_volume(item,4,4);self.assertIsNotNone(hit);self.assertLess(hit['position'][2],0)
    def test_preallocation_work_guards(self):
        item=Raster3D(0,0,1000,1000,(),volumes=(layer(step=.001),))
        with self.assertRaises(ValueError):rasterize_volume(item,1001,1001)
        with self.assertRaises(ValueError):rasterize_volume(item,1000,1000)
    def test_slice_and_isosurface_plane_are_actual_interpolated_geometry(self):
        f=field(4,lambda x,y,z:x)
        mesh,values=slice_mesh(f,'z',1.25);self.assertTrue(all(p[2]==1.25 for p in mesh.vertices));self.assertEqual(mesh.bounds,(0,3,0,3,1.25,1.25))
        self.assertEqual(values[:4],[0,1,2,3]);iso=isosurface_mesh(f,1.5);self.assertTrue(all(abs(p[0]-1.5)<1e-12 for p in iso.vertices))
        with self.assertRaises(ValueError):isosurface_mesh(f,20)
        with self.assertRaises(ValueError):slice_mesh(f,'z',20)


class VolumeIntegration(unittest.TestCase):
    def tearDown(self):azl.close('all')
    def test_artist_colorbar_atomic_edit_visibility_remove_and_frame(self):
        fig=azl.figure(figsize=(2,2));ax=fig.add_subplot(111,projection='3d');artist=ax.plot_volume(field(),norm=Normalize(0,12));bar=fig.colorbar(artist,ax=ax)
        self.assertIs(bar.mappable,artist);self.assertIs(artist.get_array(),artist.field)
        before=artist.get_data()
        with self.assertRaises(ValueError):artist.set_array(field(2,lambda x,y,z:(x,y,z),components=3))
        with self.assertRaises(ValueError):artist.set_opacity(-1)
        with self.assertRaises(NotImplementedError):artist.set_norm(BoundaryNorm([0,1,2],2))
        self.assertIs(artist.get_data(),before);self.assertIsInstance(artist.norm,Normalize)
        artist.set_visible(False);self.assertTrue(all(not p.volumes for p in fig.to_scene().items if isinstance(p,Raster3D)))
        artist.set_visible(True);artist.set_clim(0,20);self.assertEqual(bar.mappable.get_clim(),(0,20));artist.remove();self.assertIsNone(artist.axes)
    def test_surface_slice_iso_same_camera_and_static_exports(self):
        fig=azl.figure(figsize=(2,2));ax=fig.add_subplot(111,projection='3d');v=ax.plot_volume(field(4),norm=Normalize(0,18));ax.volume_slice(v.field,axis='z',position=1,color='blue');ax.isosurface(v.field,9,color='red')
        scene=fig.to_scene();r=next(p for p in scene.items if isinstance(p,Raster3D));self.assertTrue(r.volumes);self.assertTrue(r.triangles);self.assertEqual(scene.scaled(2).items[1].volumes,r.volumes)
        for kind in ('png','svg','pdf'):
            out=io.StringIO() if kind=='svg' else io.BytesIO();fig.savefig(out,format=kind);self.assertTrue(out.getvalue())
        ax.view_init(azim=20);self.assertNotEqual(next(p for p in fig.to_scene().items if isinstance(p,Raster3D)).volumes[0].inverse,r.volumes[0].inverse)
    def test_temporal_binding_preserves_camera_and_colorbar(self):
        fig=azl.figure(figsize=(2,2));ax=fig.add_subplot(111,projection='3d');a=ax.plot_volume(field());camera=ax.camera
        series=azl.TemporalSeries([0,1],[field(),field(func=lambda x,y,z:2*(x+2*y+3*z))],unit='s');binding=series.bind(a);binding.apply(1)
        self.assertEqual(a.field.sample(1,1,1),12);self.assertEqual(a.get_clim(),(0,24));self.assertIs(ax.camera,camera)
        with self.assertRaises(ValueError):azl.TemporalSeries([0,1],[field(),field(4)],unit='s').bind(a)
    def test_log_norm_and_native_pick_scene(self):
        from types import SimpleNamespace
        from azimlib.picking import contains
        fig=azl.figure(figsize=(2,2));ax=fig.add_subplot(111,projection='3d');a=ax.plot_volume(field(3,lambda x,y,z:1),norm=LogNorm(1,10),opacity=.5);scene=fig.to_scene();item=next(p for p in scene.items if isinstance(p,Raster3D))
        event=SimpleNamespace(x=item.x+item.width/2,y=scene.height-item.y-item.height/2,canvas=SimpleNamespace(scene=scene,figure=fig));fig.stale=False
        hit,props=contains(a,event);self.assertTrue(hit);self.assertEqual(props['value'],1)


@unittest.skipUnless(os.environ.get('AZIMLIB_GPU_TEST')=='1','Actual GPU explicitly opted out')
class VolumeGpu(unittest.TestCase):
    def setUp(self):
        from azimlib.renderers.gpu import GpuRenderer,GpuConfig
        self.renderer=GpuRenderer(GpuConfig(context_backend=os.environ.get('AZIMLIB_GPU_CONTEXT')))
    def tearDown(self):self.renderer.close();azl.close('all')
    def test_large_origin_recentered_without_changing_physical_samples(self):
        shift=(1e8,-2e8,3e8);base=layer(step=.07)
        data=replace(base.field,origin=tuple(v+s for v,s in zip(base.field.origin,shift)))
        inverse=list(IDENTITY)
        for k,s in enumerate(shift):inverse[k*4+3]=s
        moved=replace(base,field=data,inverse=tuple(inverse))
        reference=self.renderer.render(Scene(24,24,None,items=[Raster3D(0,0,24,24,(),volumes=(base,))]))
        actual=self.renderer.render(Scene(24,24,None,items=[Raster3D(0,0,24,24,(),volumes=(moved,))]))
        try:self.assertEqual(actual.tobytes(),reference.tobytes())
        finally:actual.close();reference.close()
    def test_analytic_alpha_depth_and_reused_textures(self):
        item=Raster3D(0,0,32,32,(),volumes=(layer(step=.07),));scene=Scene(32,32,None,items=[item]);gpu=self.renderer.render(scene);cpu=rasterize_volume(item,32,32)
        try:
            self.assertTrue(all(abs(a-b)<=1 for a,b in zip(gpu.getpixel((16,16)),cpu.rgba[(16*32+16)*4:(16*32+16)*4+4])))
            self.assertLessEqual(abs(gpu.getpixel((16,16))[3]-128),1)
        finally:gpu.close()
        uploads=self.renderer.stats['volume_texture_uploads'];self.renderer.render(scene).close();self.assertEqual(self.renderer.stats['volume_texture_uploads'],uploads)
        tris=((((-1,-1,0,1),(1,-1,0,1),(1,1,0,1)),(0,0,255,255)),(((-1,-1,0,1),(1,1,0,1),(-1,1,0,1)),(0,0,255,255)))
        image=self.renderer.render(Scene(32,32,None,items=[replace(item,triangles=tris)]))
        try:self.assertLess(image.getpixel((16,16))[0],100);self.assertGreater(image.getpixel((16,16))[2],150)
        finally:image.close()
    def test_overlap_nodata_and_lighting_match_cpu(self):
        data=field(5,lambda x,y,z:(x+y+z)/12,origin=(-1,-1,-.5),spacing=(.5,.5,.25));a=layer(data=data,light=VolumeLight(shadow_steps=3),step=.2);b=replace(layer(color=(0,0,1)),density=.2)
        item=Raster3D(0,0,24,24,(),volumes=(a,b));cpu=rasterize_volume(item,24,24);gpu=self.renderer.render(Scene(24,24,None,items=[item]))
        try:
            for x,y in ((8,8),(12,12),(16,16)):
                self.assertTrue(all(abs(a-b)<=2 for a,b in zip(gpu.getpixel((x,y)),cpu.rgba[(y*24+x)*4:(y*24+x)*4+4])),(gpu.getpixel((x,y)),cpu.rgba[(y*24+x)*4:(y*24+x)*4+4]))
        finally:gpu.close()
    def test_navigation_worker_and_static_gpu_png(self):
        from azimlib.backends._navigation_process import NavigationProcess
        fig=azl.figure(figsize=(2,2));ax=fig.add_subplot(111,projection='3d');ax.plot_volume(field());worker=NavigationProcess(renderer='gpu',gpu_config=self.renderer.config)
        try:
            image=worker.render(fig.to_scene());self.assertEqual(image.size,(200,200));image.close();self.assertEqual(worker.backend_info['renderer'],'gpu')
            out=io.BytesIO();fig.savefig(out,format='png',renderer='gpu',gpu_config=self.renderer.config);self.assertTrue(out.getvalue().startswith(b'\x89PNG'))
        finally:worker.close()


if __name__=='__main__':unittest.main()
