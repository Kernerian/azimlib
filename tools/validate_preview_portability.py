"""Explicit GPU->CPU fallback and provisional cache contracts on native toolkits.

This is not a hardware performance benchmark. Run without ModernGL installed.
"""
import argparse,json,time,platform,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import azimlib as azl

def run(backend,output):
    fig,ax=azl.subplots(figsize=(4,3));ax.set_extent((-60,-40,-30,-10))
    line,=ax.plot([-58,-42],[-28,-12],linewidth=.8,label='Route');ax.legend();ax.set_title('Preview contracts')
    v=fig.show(backend=backend,renderer='gpu',gpu_fallback='cpu',block=False)
    def pump():
        if backend=='tk':v.window.update()
        else:v.application.processEvents()
    def wait(predicate):
        end=time.monotonic()+20
        while not predicate():
            if time.monotonic()>end:raise TimeoutError('Deferred preview contract timed out')
            pump();time.sleep(.005)
    try:
        wait(lambda:v._view_preview.meta is not None and not v._preview_builder.busy())
        worker=v._pixel_process if backend=='tk' else v._gpu_process
        assert worker.backend_info['fallback'] is True,'This proof requires absence of a hardware context'
        original=ax.get_extent();ax.set_extent((-59,-39,-30,-10))
        before=v._preview_count;v._preview_navigation();pump();assert v._preview_count==before+1
        overlay=v._view_preview.overlay.tobytes();ax.set_extent((-58,-38,-30,-10));v._preview_navigation()
        assert v._view_preview.overlay.tobytes()==overlay
        line.set_color('red');before=v._preview_count;v._preview_navigation();assert v._preview_count==before
        v.draw();wait(lambda:not v._preview_builder.busy() and v._view_preview.meta is not None)
        from azimlib.renderers.pillow import render_image
        scene=fig.to_scene(cull=True,interactive=True);expected=render_image(scene);actual=v._renderer(scene)
        assert expected.tobytes()==actual.tobytes();expected.close();actual.close()
        record={'backend':backend,'system':platform.system(),'machine':platform.machine(),'python':platform.python_version(),'fallback':worker.backend_info,'passed':True,
            'contracts':['deferred cache ready','visible provisional change','fixed decoration','content invalidation','authoritative CPU equality'],
            'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'src/azimlib').rglob('*.py'))},
            'hardware_performance_claim':False}
        output.mkdir(exist_ok=True,parents=True);(output/(backend+'.json')).write_text(json.dumps(record,indent=2)+'\n')
    finally:
        v.close();azl.close('all')
        end=time.monotonic()+5
        while v._preview_builder._thread is not None and v._preview_builder._thread.is_alive() and time.monotonic()<end:time.sleep(.01)
        assert v._preview_builder._thread is None or not v._preview_builder._thread.is_alive()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('tk','qt'),required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();run(args.backend,args.output)
