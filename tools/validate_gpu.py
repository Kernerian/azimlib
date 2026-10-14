"""Local original GPU/CPU parity and timing packet; never publish or capture the desktop."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import platform
import statistics
import sys
import time

ROOT=Path(__file__).resolve().parents[1]


class MemoryProbe:
    """Optional sampled aggregate RSS, including own workers; not a VRAM quota."""
    def __init__(self,enabled):
        self.result=dict(requested=enabled,available=False,sampling_interval_seconds=.01)
        self.thread=None
        if not enabled:return
        try:
            import psutil
        except ImportError:return
        import threading
        self.done=threading.Event();self.process=psutil.Process()
        self.result.update(available=True,psutil_version=psutil.__version__,sampled_peak_aggregate_rss_bytes=0,samples=0,
            scope='Sampled process plus children RSS sum; shared pages may be counted more than once; not driver VRAM or a guaranteed instantaneous peak')
        def run():
            while not self.done.is_set():
                processes=[self.process]+self.process.children(recursive=True);total=0
                for process in processes:
                    try:total+=process.memory_info().rss
                    except psutil.NoSuchProcess:pass
                    except psutil.AccessDenied:self.result['inaccessible_process_observed']=True
                self.result['sampled_peak_aggregate_rss_bytes']=max(total,self.result['sampled_peak_aggregate_rss_bytes'])
                self.result['samples']+=1;self.done.wait(.01)
        self.thread=threading.Thread(target=run,daemon=True);self.thread.start()
    def stop(self):
        if self.thread is not None:self.done.set();self.thread.join();self.thread=None


def validate(output,context=None,*,native=False,measure_memory=False):
    sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
    import azimlib as azl
    from azimlib.renderers.gpu import GpuRenderer,GpuConfig
    from azimlib.renderers import render_image
    from PIL import ImageChops,ImageStat
    from publication_privacy import findings
    output=Path(output)
    if output.exists():raise FileExistsError('GPU evidence requires a new output directory')
    output.mkdir(parents=True)
    memory=MemoryProbe(measure_memory)
    module=importlib.util.spec_from_file_location('gpu_example',ROOT/'examples/gpu_cartography.py')
    example=importlib.util.module_from_spec(module);module.loader.exec_module(example)
    config=GpuConfig(context_backend=context);files=[];scenes=[];bench=[];captures=[]
    fig,ax=example.make_map();terrain,tax,surface=example.make_terrain()
    try:
        with GpuRenderer(config) as renderer:
            for name,figure in (('map',fig),('terrain',terrain)):
                scene=figure.to_scene(simplify=False)
                start=time.perf_counter();gpu=renderer.render(scene);cold=time.perf_counter()-start
                cpu=render_image(scene)
                try:
                    for role,image in (('gpu',gpu),('cpu',cpu)):
                        filename=f'{name}-{role}.png';image.save(output/filename);files.append(filename)
                    diff=ImageChops.difference(gpu,cpu);metric=ImageStat.Stat(diff)
                    filename=f'{name}-difference.png';diff.save(output/filename);files.append(filename);diff.close()
                    scenes.append(dict(name=name,cold_renderer_seconds=cold,mean_absolute_channel_error_255=metric.mean,extrema=metric.extrema))
                finally:gpu.close();cpu.close()
                figure.savefig(output/f'{name}-cpu.svg');figure.savefig(output/f'{name}-cpu.pdf');files.extend((f'{name}-cpu.svg',f'{name}-cpu.pdf'))
            original=ax.get_extent()
            for phase in ('warm','pan','resume','zoom','temporal-edit'):
                samples=[];compose=[]
                for i in range(12):
                    if phase in ('pan','resume'):
                        delta=i*.05;ax.set_extent((original[0]+delta,original[1]+delta,original[2],original[3]))
                    elif phase=='zoom':
                        delta=i*.05;ax.set_extent((original[0]+delta,original[1]-delta,original[2]+delta,original[3]-delta))
                    elif phase=='temporal-edit':ax._title.set_text(f'GPU frame {i}')
                    start=time.perf_counter();scene=fig.to_scene(cull=True,interactive=True);compose.append(time.perf_counter()-start)
                    start=time.perf_counter();image=renderer.render(scene);samples.append(time.perf_counter()-start);image.close()
                values=sorted(samples)
                bench.append(dict(phase=phase,samples=len(samples),first_renderer_ms=samples[0]*1000,p50_renderer_ms=statistics.median(samples)*1000,
                                  p95_renderer_ms=values[math_ceil(.95*len(values))-1]*1000,p95_compose_ms=sorted(compose)[math_ceil(.95*len(compose))-1]*1000,
                                  mean_sequential_fps=1/statistics.mean(a+b for a,b in zip(samples,compose))))
            hardware=renderer.info;stats=dict(renderer.stats)
        ax.set_extent(original);ax._title.set_text('Azimlib · GPU cartography')
        fig.savefig(output/'map-gpu-export.png',renderer='gpu',gpu_config=config);files.append('map-gpu-export.png')
        if native:
            from validate_text_engine import capture_tk
            for backend in ('tk','qt'):
                viewer=fig.show(backend=backend,renderer='gpu',gpu_config=config,block=False)
                try:
                    for _ in range(8):viewer.flush_events();time.sleep(.03)
                    viewer.draw();viewer.flush_events()
                    filename=f'{backend}-gpu-native.png';target=output/filename
                    if backend=='tk':mode=capture_tk(viewer,target);worker=viewer._pixel_process
                    else:
                        if not viewer.window.grab().save(str(target)):raise RuntimeError('Native Qt capture failed')
                        mode='own-native-qt-window-grab';worker=viewer._gpu_process
                    assert worker.backend_info['renderer']=='gpu' and not worker.backend_info['fallback']
                    files.append(filename);captures.append(dict(backend=backend,mode=mode,renderer=worker.backend_info['renderer']))
                finally:viewer.close()
        identity=str(hardware.get('GL_RENDERER','')).lower()
        memory.stop()
        report=dict(schema_version=1,scope='Local device scene/render measurements; not physical mouse-input latency or multiplatform human acceptance',system=platform.system(),python=platform.python_version(),hardware=hardware,
            hardware_accelerated=not any(s in identity for s in ('llvmpipe','softpipe','software','swiftshader')),comparisons=scenes,benchmark=bench,renderer_stats=stats,native=captures,
            memory=memory.result,
            validation_tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            source_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'src/azimlib').rglob('*.py'))},
            files={name:hashlib.sha256((output/name).read_bytes()).hexdigest() for name in files})
        (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
        links=''.join(f'<li><a href="{f}">{f}</a></li>' for f in files)
        (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Azimlib GPU review</title><h1>GPU / CPU</h1><p>Own renderers. Compare holes, text, strokes, opacity, texture, depth and PNG versus CPU SVG/PDF. Native captures do not prove physical input latency.</p><img src="map-gpu.png" width="700"><img src="terrain-gpu.png" width="600"><ul>'+links+'</ul>',encoding='utf8',newline='\n')
        for path in output.iterdir():
            if findings(path.read_bytes()):raise RuntimeError('GPU evidence privacy scan failed')
        return report
    finally:memory.stop();azl.close('all')


def math_ceil(value):
    import math
    return math.ceil(value)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--context');parser.add_argument('--native',action='store_true');parser.add_argument('--measure-memory',action='store_true',help='Optional sampled RSS; profiling can perturb timing. Run separately from timing-only measurements.');args=parser.parse_args()
    result=validate(args.output,args.context,native=args.native,measure_memory=args.measure_memory)
    print(json.dumps({k:result[k] for k in ('system','hardware','hardware_accelerated','comparisons','benchmark','renderer_stats','native')},indent=2))
