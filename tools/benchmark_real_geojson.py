"""Benchmark an explicitly supplied local GeoJSON; no download or GIS backend.

Compare linear/indexed culling, scene/PNG equivalence at every view, and real
withdrawn Tk pan/zoom/history. Timings include no memory profiler. API geometry
may be simplified: source quality/provenance are the caller's responsibility.
"""
import argparse
import hashlib
import io
import importlib.util
import json
from pathlib import Path
import platform
import statistics
import sys
import time
from types import SimpleNamespace
from unittest.mock import patch

import azimlib as azl
from azimlib import render_map
from azimlib.io import read_geojson
from azimlib.renderers import render_png
_spec=importlib.util.spec_from_file_location('real_geojson_process_memory',Path(__file__).with_name('measure_process_memory.py'))
_memory=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_memory)
process_memory=_memory.process_memory


def positions(value):
    if not value:return 0
    if isinstance(value[0],(int,float)):return 1
    return sum(positions(child) for child in value)


def geometry_vertices(geometry):
    if geometry is None:return 0
    if geometry.type=='GeometryCollection':return sum(geometry_vertices(g) for g in geometry.geometries)
    return positions(geometry.coordinates)


def create(collection,dpi):
    fig,ax=azl.subplots(figsize=(5.2,4.2),dpi=dpi,projection='mercator',layout='constrained')
    ax.municipalities(collection,fc='#f4f4f4',ec='#666666',lw=.35)
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.set_title('Municípios · base fornecida')
    return fig,ax


def digest(scene):
    stream=io.BytesIO();start=time.perf_counter();render_png(scene,stream)
    elapsed=time.perf_counter()-start
    return hashlib.sha256(stream.getvalue()).hexdigest(),elapsed,stream.getvalue()


def benchmark(path,output,*,dpi=100,repeats=3,tk=False,preview_dir=None,tk_only=False):
    start=time.perf_counter();raw=path.read_bytes();collection=read_geojson(json.loads(raw))
    read_seconds=time.perf_counter()-start
    if collection.bounds is None:raise ValueError('Benchmark input needs nonempty geographic geometry')
    fig,ax=create(collection,dpi);home=ax.get_extent()
    w,e,s,n=home;cx,cy=(w+e)/2,(s+n)/2;dx,dy=(e-w)/10,(n-s)/10
    views={'whole':home,'focus':(cx-dx,cx+dx,cy-dy,cy+dy),
           'pan':(cx,cx+2*dx,cy-dy,cy+dy),'zoom':(cx-dx/2,cx+dx/2,cy-dy/2,cy+dy/2)}
    try:
        start=time.perf_counter();index=collection._viewport_indexes.get(collection,ax.projection)
        index_seconds=time.perf_counter()-start
        from azimlib.backends import tk as tk_backend,_raster_cache
        from azimlib.renderers import pillow
        fingerprint=lambda module:hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
        report=dict(schema_version=1,azimlib_version=azl.__version__,python=platform.python_version(),platform=platform.platform(),
            tooling_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            runtime_sha256={module.__name__:fingerprint(module) for module in (tk_backend,_raster_cache,pillow)},
            source=dict(filename=path.name,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),features=len(collection),
                        vertices=sum(geometry_vertices(f.geometry) for f in collection),bounds=collection.bounds),
            dpi=dpi,repeats=repeats,tk_only=tk_only,read_validate_seconds=read_seconds,index_seconds=index_seconds,
            indexed_features=index.index.size,always_features=len(index.always),views=[],tk=None,
            notes=['Local source explicitly supplied; no implicit network access.',
                   'Warm alternating linear/indexed culling; caches enabled in both. PNG raster/encoding reported separately once per mode/view.',
                   'Process memory outside timing; peak is process lifetime high-water mark, not stage-only allocation.',
                   'Tk, if requested: real withdrawn widgets, synthetic input, no visible presentation or physical-input latency.',
                   'Small local sample; no general speed guarantee. Detailed relative to bundled examples does not imply full-resolution original data.'])
        for name,extent in (() if tk_only else views.items()):
            ax.set_extent(extent);samples={'linear':[],'indexed':[]};scenes={}
            def compose(mode):
                if mode=='indexed':return fig.to_scene(cull=True)
                with patch.object(render_map,'_geometry_candidates',return_value=None):return fig.to_scene(cull=True)
            for mode in samples:compose(mode)
            for trial in range(repeats):
                for mode in ('linear','indexed') if trial%2==0 else ('indexed','linear'):
                    start=time.perf_counter();scenes[mode]=compose(mode);samples[mode].append(time.perf_counter()-start)
            same_scene=scenes['linear'].items==scenes['indexed'].items and scenes['linear'].maps==scenes['indexed'].maps
            renders={mode:digest(scene) for mode,scene in scenes.items()}
            same_png=renders['linear'][0]==renders['indexed'][0]
            report['views'].append(dict(name=name,extent=extent,samples_seconds=samples,
                median_seconds={mode:statistics.median(values) for mode,values in samples.items()},
                scene_items=len(scenes['indexed'].items),identical_scene=same_scene,identical_png=same_png,
                png_sha256={mode:value[0] for mode,value in renders.items()},
                png_seconds={mode:value[1] for mode,value in renders.items()},memory=process_memory()))
            if preview_dir:
                preview_dir.mkdir(parents=True,exist_ok=True);(preview_dir/f'municipalities-{name}.png').write_bytes(renders['indexed'][2])
            if not same_scene or not same_png:raise RuntimeError(f'Culling changed pixels/scene at {name}')
            print(f'{name}: identical scene/PNG, {report["views"][-1]["median_seconds"]}',flush=True)
        if tk:
            import tkinter
            from azimlib.backends import tk as backend
            original=tkinter.Tk
            def hidden(*args,**kwargs):
                root=original(*args,**kwargs);root.withdraw();return root
            ax.set_extent(home);viewer=None;stages=[]
            try:
                with patch.object(tkinter,'Tk',hidden):viewer=backend.FigureWindow(fig)
                fig._viewer=viewer;fig.canvas=viewer
                def measure(name,operation):
                    start=time.perf_counter();operation();viewer.flush_events();elapsed=time.perf_counter()-start
                    stages.append(dict(stage=name,seconds=elapsed,extent=ax.get_extent(),history_index=viewer.navigation.index,
                                       pixels=list(viewer._image.size),memory=process_memory(),
                                       rgba_sha256=hashlib.sha256(viewer._image.tobytes()).hexdigest(),
                                       cache=dict(hits=viewer._raster_cache.hits,misses=viewer._raster_cache.misses,
                                                  retained_rgba_bytes=viewer._raster_cache.bytes)))
                    if fig.stale:raise RuntimeError('Viewer did not redraw')
                def center():
                    x,y,w,h=viewer._viewport(0).box;return round(x+w/2),round(y+h/2)
                def zoom():
                    x,y=center();viewer.wheel(SimpleNamespace(x=x,y=y,delta=120,state=0))
                def pan():
                    viewer.set_mode('pan');x,y=center()
                    viewer.press(SimpleNamespace(x=x,y=y,num=1,state=0))
                    viewer.motion(SimpleNamespace(x=x+10,y=y+6,state=256))
                    viewer.release(SimpleNamespace(x=x+10,y=y+6,num=1,state=256))
                measure('redraw',viewer.draw);measure('zoom',zoom);measure('pan_preview_release',pan)
                measure('back',viewer.back);measure('forward',viewer.forward);measure('home',viewer.home)
                if ax.get_extent()!=home:raise RuntimeError('Home did not restore original extent')
                report['tk']=dict(stages=stages,home_restored=True,tk_version=tkinter.TkVersion)
            finally:
                if viewer is not None:viewer.close()
        forbidden=('matplotlib','cartopy','geopandas','shapely','pyproj')
        if any(name.split('.')[0] in forbidden for name in sys.modules):raise RuntimeError('Forbidden runtime imported')
        report['independent_runtime']=True
        output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        return report
    finally:azl.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('geojson',type=Path);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--dpi',type=int,default=100);parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--tk',action='store_true');parser.add_argument('--preview-dir',type=Path)
    parser.add_argument('--tk-only',action='store_true',help='Measure only the Tk stages; skip composition/PNG view matrix')
    args=parser.parse_args()
    if min(args.dpi,args.repeats)<1:parser.error('DPI/repeats must be positive')
    benchmark(args.geojson,args.output,dpi=args.dpi,repeats=args.repeats,tk=args.tk or args.tk_only,preview_dir=args.preview_dir,tk_only=args.tk_only)

if __name__=='__main__':main()
