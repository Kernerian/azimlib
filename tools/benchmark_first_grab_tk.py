"""First frame of a cold drag and a new drag during precise raster work.

Withdrawn real Tk widgets and actual renderers; timed synthetic input only.
No monitor-presentation or physical-input claim.
"""
import argparse,hashlib,importlib.util,json,time
from pathlib import Path
from types import SimpleNamespace
from threading import Event
import azimlib as azl

spec=importlib.util.spec_from_file_location('comparison',Path(__file__).with_name('show_viewer_comparison.py'))
case=importlib.util.module_from_spec(spec);spec.loader.exec_module(case)


def run():
    fig=case.build(azl);viewer=fig.show(block=False);viewer.window.withdraw()
    viewer.set_mode('pan');observed=[];started=Event();original=viewer._present
    def present(scene,image,**kwargs):
        original(scene,image,**kwargs);observed.append((time.perf_counter(),kwargs.get('complete',True)))
    viewer._present=present
    exact=getattr(viewer._pan_raster,'controlled_renderer',None)
    kind='controlled_renderer' if exact is not None else 'renderer'
    exact=exact or viewer._pan_raster.renderer
    def render(scene,*args):started.set();return exact(scene,*args)
    setattr(viewer._pan_raster,kind,render)
    def wait(predicate):
        end=time.perf_counter()+10
        while not predicate():
            if time.perf_counter()>end:raise RuntimeError('first-grab timeout')
            viewer.window.update();time.sleep(.001)
    def drag():
        viewport=viewer._viewport(0);x,y,w,h=viewport.box
        start=(round(x+w*.5),round(y+h*.5))
        viewer.press(SimpleNamespace(x=start[0],y=start[1],num=1,state=0))
        observed.clear();began=time.perf_counter()
        event=SimpleNamespace(x=start[0]+17,y=start[1]+8,state=256)
        viewer.motion(event);wait(lambda:bool(observed))
        latency=(observed[0][0]-began)*1000
        viewer.release(SimpleNamespace(x=event.x,y=event.y,num=1,state=0))
        return latency
    try:
        cold=drag();wait(started.is_set)
        # A new real gesture arrives while the worker's exact renderer runs.
        active_at_regrab=viewer._pan_raster._active and not getattr(viewer._pan_raster,'_active_preview',False)
        second=drag();viewer.flush_events()
        from azimlib.renderers import render_image
        expected=render_image(viewer.scene)
        try:assert viewer._image.tobytes()==expected.tobytes()
        finally:expected.close()
        import azimlib.backends.tk as backend
        import azimlib.renderers.pillow as raster
        return dict(cold_first_frame_ms=cold,regrab_first_frame_ms=second,
                    exact_worker_active_at_regrab=active_at_regrab,exact_final_frame=True,
                    figure_pixels=viewer.get_width_height(),
                    sha256={name:hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                            for name,module in (('backend',backend),('renderer',raster))},
                    scope=__doc__)
    finally:viewer.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=run();args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
