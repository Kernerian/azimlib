"""Local synthetic volume evidence; no downloads, publishing or desktop captures."""
import argparse
from array import array
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import shutil
import statistics
import sys
import time
import tracemalloc

ROOT=Path(__file__).resolve().parents[1]


def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as source:
        for data in iter(lambda:source.read(65536),b''):digest.update(data)
    return digest.hexdigest()


def streaming_trial(output):
    """Process every node of a file much larger than the permitted dense payload."""
    import azimlib as azl
    # Trial-wide storage policy is separate from the library's per-file limit.
    existing=sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
    planned=10*1024**2
    if existing+planned>20_000_000_000 or shutil.disk_usage(output).free-planned<15_000_000_000:
        raise RuntimeError('Trial storage budget or system free-space reserve would be exceeded')
    n=128;b=16;budget=azl.VolumeBudget(max_dense_bytes=256*1024,max_cache_bytes=64*1024)
    def bricks():
        for bz in range(n//b):
            for by in range(n//b):
                for bx in range(n//b):
                    values=array('f',(float(x+2*y+3*z) for z in range(bz*b,(bz+1)*b)
                        for y in range(by*b,(by+1)*b) for x in range(bx*b,(bx+1)*b)))
                    if sys.byteorder!='little':values.byteswap()
                    yield (bx,by,bz),values.tobytes()
    tracemalloc.start();start=time.perf_counter()
    try:
        path=azl.write_volume(output/'linear-128.azv',shape=(n,n,n),bricks=bricks(),brick_size=b,
            value_unit='analytic units',budget=budget)
        written=time.perf_counter()-start;digest=sha256(path);start=time.perf_counter()
        field=azl.read_volume(path,budget=budget,sha256=digest);verified=time.perf_counter()-start
        assert field.summary==dict(valid_nodes=n**3,minimum=(0.,),maximum=(762.,))
        sampler=field.sampler();value=sampler.sample((22.5,25.5,28.5))
        assert value==159. and sampler.cache_bytes<=budget.max_cache_bytes
        roi=field.select((20,35,20,35,20,35))
        assert roi.shape==(16,16,16) and roi.sample(22.5,25.5,28.5)==value
        peak=tracemalloc.get_traced_memory()[1]
    finally:tracemalloc.stop()
    return dict(shape=[n,n,n],bricks_verified=(n//b)**3,nodes_verified=n**3,summary=field.summary,
        file_bytes=path.stat().st_size,sha256=digest,dense_payload_limit_bytes=budget.max_dense_bytes,
        sampler_cache_limit_bytes=budget.max_cache_bytes,sampler_cache_bytes=sampler.cache_bytes,
        roi_shape=roi.shape,roi_payload_bytes=len(roi.values),analytic_sample=value,
        write_seconds=written,full_verification_seconds=verified,python_traced_peak_bytes=peak,
        memory_scope='tracemalloc peak during streaming write/read/selection; not process RSS or driver VRAM',
        storage_policy=dict(maximum_generated_bytes=20_000_000_000,reserved_free_bytes=15_000_000_000))


def validate(output,*,gpu=False,native=False,context=None):
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
    import azimlib as azl
    from azimlib.renderers import render_image
    from PIL import ImageChops,ImageStat
    from publication_privacy import findings
    output=Path(output)
    if output.exists():raise FileExistsError('Volume evidence requires a new output directory')
    output.mkdir(parents=True)
    module=importlib.util.spec_from_file_location('volume_example',ROOT/'examples/volume_cloud.py')
    example=importlib.util.module_from_spec(module);module.loader.exec_module(example)
    fig,ax,volume=example.make_cloud();sections,sax=example.make_sections()
    files=[];comparisons=[];timings=[];captures=[];renderer=None;hardware=None
    try:
        if gpu:
            from azimlib.renderers.gpu import GpuRenderer,GpuConfig
            renderer=GpuRenderer(GpuConfig(context_backend=context));hardware=renderer.info
        for name,figure in (('cloud',fig),('sections',sections)):
            scene=figure.to_scene(simplify=False);samples=[]
            for i in range(3):
                start=time.perf_counter();image=render_image(scene);samples.append(time.perf_counter()-start)
                if i==0:image.save(output/f'{name}-cpu.png');files.append(f'{name}-cpu.png')
                image.close()
            timings.append(dict(scene=name,backend='cpu',cold_seconds=samples[0],warm_median_seconds=statistics.median(samples[1:])))
            for extension in ('svg','pdf'):
                filename=f'{name}-cpu.{extension}';figure.savefig(output/filename);files.append(filename)
            if renderer is not None:
                samples=[]
                for i in range(3):
                    start=time.perf_counter();image=renderer.render(scene);samples.append(time.perf_counter()-start)
                    if i==0:image.save(output/f'{name}-gpu.png');files.append(f'{name}-gpu.png')
                    image.close()
                timings.append(dict(scene=name,backend='gpu',cold_seconds=samples[0],warm_median_seconds=statistics.median(samples[1:])))
                from PIL import Image
                with Image.open(output/f'{name}-cpu.png') as cpu,Image.open(output/f'{name}-gpu.png') as device:
                    diff=ImageChops.difference(cpu,device);metric=ImageStat.Stat(diff)
                    filename=f'{name}-difference.png';diff.save(output/filename);files.append(filename);diff.close()
                    comparisons.append(dict(scene=name,mean_absolute_channel_error_255=metric.mean,extrema=metric.extrema,
                        note='Full figure includes geometry edge coverage and raster depth differences; analytic interior tolerance is tested separately'))
        series=azl.TemporalSeries([0,1],[example.cloud(),example.cloud(2)],unit='s')
        binding=series.bind(volume);camera=ax.camera;binding.apply(1)
        assert ax.camera is camera
        fig.savefig(output/'cloud-time-1.png');files.append('cloud-time-1.png');binding.apply(0)
        from azimlib.animation import FuncAnimation
        animation=FuncAnimation(fig,lambda index:binding.apply(index),frames=2,autoplay=False)
        try:animation.save(output/'cloud-time.gif',fps=2)
        finally:animation.close()
        files.append('cloud-time.gif');binding.apply(0)
        if native:
            from validate_text_engine import capture_tk
            for backend in ('tk','qt'):
                options=dict(renderer='gpu',gpu_config=renderer.config) if gpu else {}
                viewer=fig.show(backend=backend,block=False,**options)
                try:
                    for _ in range(8):viewer.flush_events();time.sleep(.03)
                    viewer.draw();viewer.flush_events()
                    name=f'{backend}-volume-native.png';path=output/name
                    if backend=='tk':mode=capture_tk(viewer,path)
                    else:
                        if not viewer.window.grab().save(str(path)):raise RuntimeError('Native Qt window capture failed')
                        mode='own-native-qt-window-grab'
                    if gpu:
                        worker=viewer._pixel_process if backend=='tk' else viewer._gpu_process
                        assert worker.backend_info['renderer']=='gpu' and not worker.backend_info['fallback']
                    files.append(name);captures.append(dict(backend=backend,mode=mode,renderer='gpu' if gpu else 'cpu'))
                finally:viewer.close()
        stream=streaming_trial(output);files.append('linear-128.azv')
        report=dict(schema_version=1,scope='Local original synthetic fields, not release CI or human acceptance',
            system=platform.system(),python=platform.python_version(),hardware=hardware,streaming=stream,
            timings=timings,comparisons=comparisons,native=captures,temporal_frames=2,
            source_sha256={p.relative_to(ROOT).as_posix():sha256(p) for p in sorted((ROOT/'src/azimlib').rglob('*.py'))},
            files={name:sha256(output/name) for name in files},validation_tool_sha256=sha256(__file__))
        data=json.dumps(report,indent=2)+'\n'
        if findings(data.encode()):raise RuntimeError('Volume metadata privacy scan failed')
        (output/'manifest.json').write_text(data,encoding='utf8',newline='\n')
        links=''.join(f'<li><a href="{name}">{name}</a></li>' for name in files)
        (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Azimlib volume review</title>'
            '<h1>Original cloud, slices and isosurface</h1><p>Compare CPU/GPU, terrain occlusion, density, '
            'gradient light, text, colorbar and PNG versus embedded-raster SVG/PDF. Native captures are not human approval.</p>'
            '<img src="cloud-cpu.png" width="600"><img src="sections-cpu.png" width="600"><ul>'+links+'</ul>',encoding='utf8',newline='\n')
        for path in output.iterdir():
            if path.suffix!='.azv' and findings(path.read_bytes()):raise RuntimeError('Volume evidence privacy scan failed')
        return report
    finally:
        if renderer is not None:renderer.close()
        azl.close('all')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--gpu',action='store_true');parser.add_argument('--native',action='store_true');parser.add_argument('--context')
    args=parser.parse_args();result=validate(args.output,gpu=args.gpu,native=args.native,context=args.context)
    print(json.dumps({k:result[k] for k in ('system','hardware','streaming','timings','comparisons','native')},indent=2))
