"""Compare own Tk redraw latency/memory in serial fresh before/after workers.

Real withdrawn Tk widgets/event loop, synthetic input, no physical screen paint.
Requires azimlib[gui] and display (Linux can use xvfb-run). No Matplotlib/GIS.
"""
import argparse,gc,hashlib,importlib.util,json,platform,statistics,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from measure_process_memory import process_memory


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def pixel_digest(image):
    digest=hashlib.sha256()
    for top in range(0,image.height,32):
        band=image.crop((0,top,image.width,min(top+32,image.height)))
        try:digest.update(band.tobytes())
        finally:band.close()
    return digest.hexdigest()


def worker(name,dpi,mode,folder,points):
    import tkinter
    import azimlib as azl
    from azimlib.backends import tk
    from azimlib import renderers
    from azimlib.scene import Path as ScenePath
    from benchmark_maps import create
    from PIL import __version__ as pillow_version
    old_tk=load('azimlib.backends._viewer_benchmark_before',folder/'tk.py')
    old_png=load('azimlib.renderers._viewer_png_before',folder/'pillow.py')
    backend=old_tk if mode=='before' else tk
    original=tkinter.Tk
    def hidden(*args,**kwargs):
        root=original(*args,**kwargs);root.withdraw();return root
    imported=process_memory();start=time.perf_counter()
    fig,ax=create(name,points);fig.dpi=dpi
    initial_figsize=list(fig.figsize)
    setup=time.perf_counter()-start;data_memory=process_memory()
    samples=[];viewer=None
    original_png=renderers.render_png
    # Both implementations are loaded in each worker. Only baseline draw
    # selects baseline PNG; after draw uses the direct current RGBA path.
    if mode=='before':renderers.render_png=old_png.render_png
    def measure(stage,operation):
        start=time.perf_counter();operation();elapsed=time.perf_counter()-start
        memory=process_memory()  # hashing/counters are outside the timed call
        scene=viewer.scene
        samples.append(dict(stage=stage,seconds=elapsed,memory=memory,
                            pixels=[viewer._image.width,viewer._image.height],
                            rgba_sha256=pixel_digest(viewer._image),items=len(scene.items),
                            vertices=sum(len(part) for item in scene.items if isinstance(item,ScenePath) for part in item.paths),
                            extents=viewer.navigation.snapshot(),history_index=viewer.navigation.index,
                            stale=fig.stale))
    try:
        start=time.perf_counter()
        with patch.object(tkinter,'Tk',hidden):viewer=backend.FigureWindow(fig)
        fig._viewer=viewer;fig.canvas=viewer;backend._windows.append(viewer)
        open_seconds=time.perf_counter()-start
        measure('open_result',lambda:None)
        samples[-1]['seconds']=open_seconds
        measure('redraw',viewer.draw)
        def center():
            x,y,w,h=viewer._viewport(0).box;return round(x+w/2),round(y+h/2)
        def zoom():
            x,y=center();viewer.wheel(SimpleNamespace(x=x,y=y,delta=120,state=0));viewer.flush_events()
        measure('zoom',zoom)
        def pan():
            viewer.set_mode('pan');x,y=center()
            viewer.press(SimpleNamespace(x=x,y=y,num=1,state=0))
            viewer.motion(SimpleNamespace(x=x+10,y=y+6,state=256))
            viewer.release(SimpleNamespace(x=x+10,y=y+6,num=1,state=256));viewer.flush_events()
        measure('pan_preview_and_release',pan)
        measure('home',lambda:(viewer.home(),viewer.flush_events()))
        def resize():
            width,height=viewer._image.size
            viewer.resize(SimpleNamespace(width=width+80,height=height+60,state='??'))
            ready=tkinter.IntVar(viewer.window,value=0)
            viewer.window.after(200,lambda:ready.set(1))
            viewer.window.wait_variable(ready);viewer.flush_events()
            assert viewer._resize_pending is None
        measure('resize_with_debounce',resize)
        def edit():
            with azl.ion():ax.set_title('Edited viewer benchmark')
            viewer.flush_events()
        measure('edit_title',edit)
        assert all(not sample['stale'] for sample in samples)
        viewer.close();gc.collect();closed=process_memory()
        assert not any(n.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj') for n in sys.modules)
        return dict(name=name,dpi=dpi,mode=mode,setup_seconds=setup,
                    initial_figsize=initial_figsize,tk=tkinter.TkVersion,pillow=pillow_version,
                    memory_imported=imported,memory_data=data_memory,memory_closed=closed,stages=samples)
    finally:
        renderers.render_png=original_png
        if viewer is not None:viewer.close()
        azl.close(fig);azl.ioff()


def compare(entries):
    before,after=entries['before'],entries['after']
    equality=[];medians={}
    for index in range(len(before[0]['stages'])):
        groups={mode:[entry['stages'][index] for entry in entries[mode]] for mode in ('before','after')}
        stage=groups['before'][0]['stage']
        signatures={json.dumps({key:row[key] for key in ('pixels','rgba_sha256','items','vertices','extents','history_index','stale')},sort_keys=True)
                    for rows in groups.values() for row in rows}
        equality.append(dict(stage=stage,identical=len(signatures)==1))
        medians[stage]={mode:dict(seconds=statistics.median(row['seconds'] for row in rows),
            memory={key:statistics.median(row['memory'][key] for row in rows) for key in (
                'working_set_bytes','peak_working_set_bytes','private_committed_bytes')
                if all(row['memory'][key] is not None for row in rows)}) for mode,rows in groups.items()}
    if not all(row['identical'] for row in equality):raise RuntimeError('Viewer pixels/state differ before/after')
    return dict(equality=equality,medians=medians,samples=entries)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-dir',type=Path,default=Path(__file__).with_name('baselines')/'viewer-raster-before')
    parser.add_argument('--child',nargs=3,metavar=('CASE','DPI','MODE'))
    parser.add_argument('--cases',nargs='+',choices=('state','brazil','atlas','points'),default=['state','brazil','atlas'])
    parser.add_argument('--dpi',type=int,nargs='+',default=[100])
    parser.add_argument('--repeats',type=int,default=2)
    parser.add_argument('--points',type=int,default=1500)
    parser.add_argument('--output',type=Path,default=Path('viewer-benchmark.json'))
    args=parser.parse_args();folder=args.baseline_dir.resolve()
    if args.child:
        name,dpi,mode=args.child
        if mode not in ('before','after'):parser.error('invalid child mode')
        print(json.dumps(worker(name,int(dpi),mode,folder,args.points)));return
    if min(*args.dpi,args.repeats,args.points)<1:parser.error('dpi/repeats/points must be positive')
    from azimlib.backends import tk
    from azimlib.renderers import pillow
    fingerprint=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    report=dict(schema_version=1,python=platform.python_version(),platform=platform.platform(),repeats=args.repeats,
        tooling_sha256={name:fingerprint(Path(__file__).with_name(name)) for name in ('benchmark_viewer.py','benchmark_maps.py','measure_process_memory.py')},
        source_sha256=dict(before={name:fingerprint(folder/name) for name in ('tk.py','pillow.py')},
                           after={'tk.py':fingerprint(Path(tk.__file__)),'pillow.py':fingerprint(Path(pillow.__file__))}),
        notes=[
            'Each mode/case/DPI/trial runs in a new interpreter; workers run serially, alternating before/after order. Both own implementations are imported.',
            'Real withdrawn Tk widgets/event loop; synthetic input. No physical input, visible OS presentation, screenshots or perceptual frame latency.',
            'Open includes root/widgets/icons/composition/raster/display/idletasks, but excludes dataset/figure construction. Redraw and actions include composition, raster and PhotoImage/canvas updates.',
            'Resize includes real 180ms debounce and 200ms wait callback. Pan includes one preview motion plus release/recomposition; no continuous-drag throughput benchmark.',
            'Process memory outside operation timing; peak is lifetime OS high-water mark including runtime/Python/data/native/Tk buffers, not stage-only/native-only memory.',
            'Pixel hashing uses small bands after timing/memory sampling; it can affect subsequent OS high-water marks. No profiling/tracemalloc/polling sampler.',
            'Natural Earth bases are generalized bundled data, not detailed municipal/urban data. Atlas thematic values and optional points are synthetic.',
            'Small local samples, no guaranteed speed/memory bound/statistical significance. Source hashes and all raw stage samples are retained.'],cases=[])
    for name in args.cases:
        for dpi in args.dpi:
            entries={'before':[],'after':[]}
            for trial in range(args.repeats):
                for mode in (('before','after') if trial%2==0 else ('after','before')):
                    print(f'{name} {dpi} DPI: {mode}, pair {trial+1}/{args.repeats}',flush=True)
                    result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--child',name,str(dpi),mode,
                        '--baseline-dir',str(folder),'--points',str(args.points)],capture_output=True,text=True,timeout=600)
                    if result.returncode:raise RuntimeError(result.stderr)
                    entries[mode].append(json.loads(result.stdout))
            case=dict(name=name,dpi=dpi,**compare(entries));report['cases'].append(case)
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
            print(f'{name} {dpi}: all seven raster/view states identical',flush=True)


if __name__=='__main__':main()
