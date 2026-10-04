"""Compare own stroke coverage before/after on an explicitly supplied GeoJSON.

Serial alternating raster calls; hashes/PNG encoding are outside timings.
No download, geographical dependency, geometry simplification or frame cache.
The development baseline is our own code, excluded from the runtime wheel.
"""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import platform
import statistics
import sys
import time
from unittest.mock import patch

import azimlib as azl
from azimlib.io import read_geojson
from azimlib.renderers import coverage, render_image

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def fingerprint(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def benchmark(path,output,repeats=2,dpi=100):
    here=Path(__file__).resolve().parent
    previous=load('municipal_coverage_reference',here/'baselines/municipal-stroke-before/coverage.py')
    factory=load('municipal_scene_factory',here/'benchmark_real_geojson.py')
    raw=path.read_bytes();data=read_geojson(json.loads(raw))
    fig,ax=factory.create(data,dpi)
    home=ax.get_extent();w,e,s,n=home;cx,cy=(w+e)/2,(s+n)/2;dx,dy=(e-w)/10,(n-s)/10
    views={'whole':home,'focus':(cx-dx,cx+dx,cy-dy,cy+dy),
           'pan':(cx,cx+2*dx,cy-dy,cy+dy),'zoom':(cx-dx/2,cx+dx/2,cy-dy/2,cy+dy/2)}
    report=dict(schema_version=1,version=azl.__version__,python=platform.python_version(),platform=platform.platform(),
        tooling_sha256=fingerprint(__file__),factory_sha256=fingerprint(factory.__file__),
        coverage_sha256={'before':fingerprint(previous.__file__),'after':fingerprint(coverage.__file__)},
        source=dict(filename=path.name,sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),features=len(data),
                    vertices=sum(factory.geometry_vertices(f.geometry) for f in data)),
        dpi=dpi,repeats=repeats,views=[],notes=[
            'Same composed scene per view; own coverage implementation patched only for development comparison.',
            'Serial, alternating order; no concurrent profiling, Tk, frame cache or geometry simplification.',
            'Timings exclude composition, hashing, encoding and I/O. Python/font caches warm across calls.',
            'Small local sample, not a statistical guarantee or visible/physical input latency measurement.',
            'API mesh quality/provenance described separately; source data is not redistributed.'])
    current=coverage.CoverageDraw
    try:
        for name,extent in views.items():
            ax.set_extent(extent);scene=fig.to_scene(cull=True);samples={'before':[],'after':[]};hashes={}
            for trial in range(repeats):
                for mode in ('before','after') if trial%2==0 else ('after','before'):
                    cls=previous.CoverageDraw if mode=='before' else current
                    with patch.object(coverage,'CoverageDraw',cls):
                        start=time.perf_counter();image=render_image(scene);seconds=time.perf_counter()-start
                    try:
                        stream=io.BytesIO();image.save(stream,format='PNG')
                        pixels=(hashlib.sha256(image.tobytes()).hexdigest(),hashlib.sha256(stream.getvalue()).hexdigest())
                    finally:image.close()
                    if hashes and pixels!=next(iter(hashes.values())):raise RuntimeError(f'Pixels/PNG changed: {name}/{mode}')
                    hashes[mode]=pixels;samples[mode].append(seconds)
                    print(f'{name}/{trial}/{mode}: {seconds:.3f}s; identical RGBA/PNG',flush=True)
            report['views'].append(dict(name=name,extent=extent,scene_items=len(scene.items),samples_seconds=samples,
                median_seconds={mode:statistics.median(times) for mode,times in samples.items()},
                rgba_sha256=hashes['after'][0],png_sha256=hashes['after'][1],identical_rgba=True,identical_png=True))
    finally:azl.close(fig)
    forbidden=('matplotlib','cartopy','geopandas','shapely','pyproj')
    if any(name.split('.')[0] in forbidden for name in sys.modules):raise RuntimeError('Forbidden runtime imported')
    report['independent_runtime']=True
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('geojson',type=Path);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--repeats',type=int,default=2);parser.add_argument('--dpi',type=int,default=100)
    args=parser.parse_args()
    if min(args.dpi,args.repeats)<1:parser.error('DPI and repeats must be positive')
    benchmark(args.geojson,args.output,args.repeats,args.dpi)
