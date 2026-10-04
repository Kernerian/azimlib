"""Original municipal geometry + synthetic fields; fresh-process CPU/memory.

No downloads, geographic engine or profiler in the timed measurements. Supply
the development-only GeoJSON prepared by prepare_original_benchmark.py.
"""
import argparse
import cProfile
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import platform
import random
import sys
import time


def build(path, dpi=100, layers=True):
    import azimlib as azl
    from azimlib.io import read_geojson
    start=time.perf_counter();raw=path.read_bytes();data=read_geojson(json.loads(raw))
    read=time.perf_counter()-start
    fig,ax=azl.subplots(figsize=(6.4,4.8),dpi=dpi,projection='mercator')
    ax.municipalities(data,fc='#f4f4f4',ec='#666666',lw=.35,zorder=3)
    ax.set_extent((-53.3,-44.1,-25.4,-19.6))
    if layers:
        x=[-53.3+9.2*i/47 for i in range(48)];y=[-25.4+5.8*i/35 for i in range(36)]
        values=[[math.sin(lon*2)*math.cos(lat*2)+2 for lon in x] for lat in y]
        ax.pcolormesh(x,y,[row[:-1] for row in values[:-1]],cmap='viridis',alpha=.22,zorder=4)
        ax.contour(x,y,values,levels=[1.3,1.6,2,2.4,2.7],linewidths=.55,zorder=5)
        rng=random.Random(408)
        ax.scatter([rng.uniform(-53,-44.4) for _ in range(1200)],
                   [rng.uniform(-25.2,-19.8) for _ in range(1200)],s=3,color='#bc3131',alpha=.65,zorder=6)
    ax.set_title('Original SP geometry · synthetic fields',fontsize=10)
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    return fig,ax,read,hashlib.sha256(raw).hexdigest()


def measure(args):
    if args.runtime:sys.path.insert(0,str(args.runtime.resolve()))
    import azimlib as azl
    from azimlib.renderers.pillow import render_image
    spec=importlib.util.spec_from_file_location('detailed_memory',Path(__file__).with_name('measure_process_memory.py'))
    memory=importlib.util.module_from_spec(spec);spec.loader.exec_module(memory)
    fig,ax,read,input_hash=build(args.geojson,args.dpi,not args.geometry_only)
    if args.view=='pan':ax.set_extent((-52.6,-43.4,-25,-19.2))
    elif args.view=='focus':ax.set_extent((-48,-45.5,-24.5,-22))
    start=time.perf_counter();scene=fig.to_scene(cull=True);compose=time.perf_counter()-start
    before=memory.process_memory();start=time.perf_counter()
    if args.profile:
        profiler=cProfile.Profile();profiler.enable()
    image=render_image(scene)
    if args.profile:profiler.disable();profiler.dump_stats(str(args.profile))
    elapsed=time.perf_counter()-start;after=memory.process_memory()
    digest=hashlib.sha256(image.tobytes()).hexdigest();buffer=io.BytesIO();start=time.perf_counter()
    image.save(buffer,format='PNG');encode=time.perf_counter()-start
    if args.preview:image.save(args.preview)
    image.close()
    warm=None
    if args.warm:
        start=time.perf_counter();image=render_image(scene);warm=time.perf_counter()-start
        assert hashlib.sha256(image.tobytes()).hexdigest()==digest
        image.close()
    root=Path(azl.__file__).parent
    report=dict(schema_version=1,python=platform.python_version(),platform=platform.platform(),
        input_sha256=input_hash,tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        runtime_sha256={str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted(root.rglob('*.py'))},
        dpi=args.dpi,view=args.view,layers=not args.geometry_only,pixels=[scene.width,scene.height],items=len(scene.items),
        read_seconds=read,first_scene_seconds=compose,precise_raster_seconds=elapsed,png_encode_seconds=encode,
        rgba_sha256=digest,png_sha256=hashlib.sha256(buffer.getvalue()).hexdigest(),memory_before=before,memory_after=after,
        profiled=bool(args.profile),warm_uncached_raster_seconds=warm,
        scope='Fresh process, cold precise raster, original XY retained; fields/points synthetic. OS lifetime peak, not allocation-only peak. Profile pass separate from timings; no window/input/monitor latency.')
    assert not any(n.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj') for n in sys.modules)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('dpi','view','items','first_scene_seconds','precise_raster_seconds','rgba_sha256','memory_after')}),flush=True)
    azl.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('geojson',type=Path);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--runtime',type=Path);parser.add_argument('--dpi',type=int,default=100)
    parser.add_argument('--view',choices=('whole','pan','focus'),default='whole')
    parser.add_argument('--geometry-only',action='store_true');parser.add_argument('--profile',type=Path)
    parser.add_argument('--preview',type=Path)
    parser.add_argument('--warm',action='store_true',help='Second uncached raster after imports/JIT compilation; assert exact RGBA')
    measure(parser.parse_args())
