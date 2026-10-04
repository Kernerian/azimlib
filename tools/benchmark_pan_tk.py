"""Measure real Tk renderers under timed synthetic drags; not physical input."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import time
from types import SimpleNamespace
import importlib.util

import azimlib as azl
spec=importlib.util.spec_from_file_location('viewer_comparison',Path(__file__).with_name('show_viewer_comparison.py'))
comparison=importlib.util.module_from_spec(spec);spec.loader.exec_module(comparison)
build=comparison.build


def run(library,duration):
    own=library=='azimlib'
    if own:api=azl
    else:
        import matplotlib
        matplotlib.use('TkAgg')
        import matplotlib.pyplot as api
        from matplotlib.backend_bases import MouseEvent
    fig=build(api);ax=fig.axes[0];fig.show(block=False) if own else api.show(block=False)
    canvas=fig.canvas;window=canvas.window if own else canvas.manager.window
    window.withdraw();window.update();canvas.draw()
    frames=[];handlers=[];heartbeats=[];preparations=[];rasters=[]
    if own:
        canvas.set_mode('pan');vp=canvas._viewport(0)
        bx,by,bw,bh=vp.box;start=(round(bx+bw/2),round(by+bh/2))
        present=canvas._present
        def measured_present(*a,**kw):
            present(*a,**kw);frames.append(time.perf_counter())
        canvas._present=measured_present
        prepare=canvas._draw_pan_async
        def measured_prepare():
            before=time.perf_counter();prepare();preparations.append(time.perf_counter()-before)
        canvas._draw_pan_async=measured_prepare
        for kind in ('renderer','preview_renderer','controlled_renderer'):
            if not callable(getattr(canvas._pan_raster,kind,None)):continue
            renderer=getattr(canvas._pan_raster,kind)
            def measured_render(scene,*args,renderer=renderer,kind=kind):
                before=time.perf_counter();image=renderer(scene,*args)
                rasters.append((kind,time.perf_counter()-before));return image
            setattr(canvas._pan_raster,kind,measured_render)
        canvas.press(SimpleNamespace(x=start[0],y=start[1],num=1,state=0))
    else:
        toolbar=canvas.manager.toolbar;toolbar.pan()
        bx,by,bw,bh=ax.bbox.bounds;start=(round(bx+bw/2),round(by+bh/2))
        canvas.mpl_connect('draw_event',lambda event:frames.append(time.perf_counter()))
        toolbar.press_pan(MouseEvent('button_press_event',canvas,*start,button=1))
    initial=ax.get_xlim()+ax.get_ylim();began=time.perf_counter();released=None;last=start
    failure=[]
    def heartbeat():
        heartbeats.append(time.perf_counter())
        if released is None:window.after(10,heartbeat)
    def step():
        nonlocal released,last
        elapsed=time.perf_counter()-began;fraction=min(1,elapsed/duration)
        last=(round(start[0]+120*fraction),round(start[1]+25*fraction*(1 if own else -1)))
        before=time.perf_counter()
        if own:canvas.motion(SimpleNamespace(x=last[0],y=last[1],state=256))
        else:toolbar.drag_pan(MouseEvent('motion_notify_event',canvas,*last,buttons={1}))
        handlers.append(time.perf_counter()-before)
        if fraction<1:window.after(16,step)
        else:
            released=time.perf_counter()
            if own:canvas.release(SimpleNamespace(x=last[0],y=last[1],num=1,state=0))
            else:toolbar.release_pan(MouseEvent('button_release_event',canvas,*last,button=1))
            window.after(10,settled)
    def settled():
        busy=(canvas._pan_raster.busy() or canvas._pending is not None or canvas._async_pan) if own else canvas._idle_draw_id is not None
        if busy and time.perf_counter()-released<15:window.after(10,settled)
        else:
            if busy:failure.append('final frame timeout')
            window.quit()
    watchdog=window.after(round((duration+20)*1000),window.quit)
    window.after(0,heartbeat);window.after(0,step);window.mainloop();ended=time.perf_counter();window.after_cancel(watchdog)
    held=[t for t in frames if t<=released];gaps=[(b-a)*1000 for a,b in zip(heartbeats,heartbeats[1:])]
    report=dict(library=library,figure_pixels=canvas.get_width_height(),duration_seconds=released-began,
                motion_events=len(handlers),held_frames=len(held),held_frames_per_second=len(held)/(released-began),
                first_held_frame_ms=(held[0]-began)*1000 if held else None,
                motion_handler_max_ms=max(handlers)*1000,heartbeat_max_gap_ms=max(gaps),
                heartbeat_median_gap_ms=statistics.median(gaps),settle_after_release_ms=(ended-released)*1000,
                initial_extent=initial,final_extent=ax.get_xlim()+ax.get_ylim(),errors=failure,
                scope='Withdrawn actual Tk widgets, timed synthetic handlers, real raster/PhotoImage delivery. Not physical-input or visible-monitor latency.')
    if own:
        report['prepare_max_ms']=max(preparations)*1000
        report['raster_median_ms']={kind:statistics.median(v for k,v in rasters if k==kind)*1000 for kind in ('renderer','preview_renderer','controlled_renderer') if any(k==kind for k,v in rasters)}
        import azimlib.backends.tk as backend
        import azimlib.renderers.pillow as renderer
        report['sha256']={name:hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() for name,module in (('backend',backend),('renderer',renderer))}
        names=('azimlib.backends._navigation_process','azimlib.backends._pan_raster',
               'azimlib.renderers._tile_cache','azimlib.renderers._navigation_coverage',
               'azimlib.renderers._interactive','azimlib.typography')
        report['navigation_sha256']={name:hashlib.sha256(Path(importlib.import_module(name).__file__).read_bytes()).hexdigest() for name in names}
        from importlib.metadata import version
        report['generic_dependencies']={name:version(name) for name in ('Pillow','aggdraw','numpy')}
        report['pixel_process']=canvas._pixel_process is not None
        canvas.close()
    else:api.close(fig)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library',choices=('azimlib','matplotlib'),required=True)
    parser.add_argument('--duration',type=float,default=2)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=run(args.library,args.duration)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
