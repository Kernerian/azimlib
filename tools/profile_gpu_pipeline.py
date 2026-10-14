"""Fixed-workload GPU profiling; diagnostic timings never substitute normal runs."""
import argparse,hashlib,importlib.util,json,platform,statistics,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'src'),str(R/'tools')]
import azimlib as azl
from azimlib.renderers.gpu import GpuRenderer
from azimlib.renderers import render_image
from PIL import ImageChops,ImageStat
from validate_gpu import MemoryProbe

def run(output,diagnostic=False):
    output.mkdir(parents=True,exist_ok=False)
    spec=importlib.util.spec_from_file_location('workload',R/'examples/gpu_cartography.py')
    example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)
    fig,ax=example.make_map();original=ax.get_extent();phases=[];parity=[]
    memory=MemoryProbe(diagnostic);parts={}
    def measured(key,fn):
        def call(*a,**kw):
            begin=time.perf_counter_ns()
            try:return fn(*a,**kw)
            finally:parts[key]=parts.get(key,0)+(time.perf_counter_ns()-begin)/1e6
        return call
    began=time.perf_counter_ns()
    with GpuRenderer() as renderer:
        context_ms=(time.perf_counter_ns()-began)/1e6
        if diagnostic:
            class TimedVao:
                def __init__(self,inner):self.inner=inner
                def render(self,*a,**kw):
                    query=renderer.ctx.query(time=True)
                    with query:self.inner.render(*a,**kw)
                    # Synchronous query retrieval perturbs scheduling; this is
                    # a diagnostic run, never a frame-budget measurement.
                    parts['gpu_draw_commands_elapsed_ms']=parts.get('gpu_draw_commands_elapsed_ms',0)+query.elapsed/1e6
                def __getattr__(self,key):return getattr(self.inner,key)
            buffer=renderer._buffer
            def timed_buffer(*a,**kw):return TimedVao(buffer(*a,**kw))
            renderer._buffer=timed_buffer
            renderer.paint_quad=TimedVao(renderer.paint_quad)
            renderer.resolve_quad=TimedVao(renderer.resolve_quad)
            renderer.prepared.get=measured('cpu_mesh_key_prepare_pack_ms',renderer.prepared.get)
            renderer._buffer=measured('cpu_driver_buffer_lookup_upload_submit_ms',renderer._buffer)
            renderer._draw=measured('cpu_driver_draw_submit_including_buffer_ms',renderer._draw)
            resize=renderer._resize
            class FboProxy:
                def __init__(self,inner):self.inner=inner
                def __getattr__(self,key):return getattr(self.inner,key)
                def read(self,*a,**kw):return measured('gpu_completion_wait_and_readback_ms',self.inner.read)(*a,**kw)
            def sized(*a):
                resize(*a)
                if not isinstance(renderer.result,FboProxy):renderer.result=FboProxy(renderer.result)
            renderer._resize=sized
        for phase in ('cold','warm','pan','resume','zoom'):
            samples=[]
            for i in range(1 if phase=='cold' else 24):
                delta=i*.05
                if phase in ('pan','resume'):extent=(original[0]+delta,original[1]+delta,*original[2:])
                elif phase=='zoom':extent=(original[0]+delta,original[1]-delta,original[2]+delta,original[3]-delta)
                else:extent=original
                ax.set_extent(extent);parts.clear();start=time.perf_counter_ns()
                scene=fig.to_scene(cull=True,interactive=True);composed=time.perf_counter_ns()
                image=renderer.render(scene);drawn=time.perf_counter_ns()
                # No GUI is involved: presentation and physical input are deliberately null.
                sample=dict(compose_ms=(composed-start)/1e6,renderer_ms=(drawn-composed)/1e6,total_ms=(drawn-start)/1e6,**parts)
                samples.append(sample)
                if phase=='cold' or phase=='zoom' and i==23:
                    cpu=render_image(scene);diff=ImageChops.difference(image,cpu)
                    metric=ImageStat.Stat(diff);parity.append(dict(phase=phase,mean_channel_error_255=metric.mean))
                    image.save(output/(phase+'-gpu.png'));cpu.save(output/(phase+'-cpu.png'));diff.save(output/(phase+'-difference.png'))
                    cpu.close();diff.close()
                image.close()
            totals=sorted(s['total_ms'] for s in samples)
            phases.append(dict(phase=phase,first_ms=totals[0] if len(totals)==1 else samples[0]['total_ms'],p50_ms=statistics.median(totals),p95_ms=totals[__import__('math').ceil(.95*len(totals))-1],sequential_fps=1000/statistics.mean(totals),samples=samples))
        identity=renderer.info;stats=dict(renderer.stats)
    memory.stop();azl.close('all')
    report=dict(schema=1,diagnostic=diagnostic,system=platform.system(),python=platform.python_version(),hardware=identity,context_ms=context_ms,workload_sha256=hashlib.sha256((R/'examples/gpu_cartography.py').read_bytes()).hexdigest(),phases=phases,parity=parity,memory=memory.result,stats=stats,
        budgets=dict(frame_ms=33,input_to_present_ms=100),budgets_changed=False,
        physical_input_latency_ms=None,presentation_ms=None,
        scopes=['Sequential scene-to-image throughput is not viewer FPS','Diagnostic wrappers, synchronous GPU timer retrieval and RSS sampling add overhead','Driver upload submission is not isolated PCIe/DMA time','GPU timer sums cover draw commands, not uploads, clears or compositor scanout','Readback includes GPU completion wait; not pure transfer bandwidth'],
        source_sha256={p.relative_to(R).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((R/'src/azimlib').rglob('*.py'))})
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(diagnostic=diagnostic,hardware=identity,phases=[{k:v for k,v in p.items() if k!='samples'} for p in phases],parity=parity),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--diagnostic',action='store_true');a=p.parse_args();run(a.output,a.diagnostic)

