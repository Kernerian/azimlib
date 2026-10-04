"""Measure own short-ring kernels on complete map scenes, with exact pixels.

Calls alternate serially. Only _area is swapped with our development snapshot;
no external backend, simplified geometry, frame cache or network is used.
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
from azimlib.renderers import coverage,pillow,render_image,render_svg

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def benchmark(output,cases,dpis,repeats,points=1500,geojson=None,preview_dir=None):
    here=Path(__file__).resolve().parent;project=here.parent
    old=load('stroke_kernel_baseline',here/'baselines/stroke-kernels-before/coverage.py')
    maps=load('stroke_kernel_map_factory',here/'benchmark_maps.py')
    scientific=load('stroke_kernel_scientific_factory',project/'examples/scientific.py')
    municipal=load('stroke_kernel_municipal_factory',here/'benchmark_real_geojson.py')
    current=coverage._area;source=None;data=None
    if 'municipal' in cases:
        if geojson is None:raise ValueError('municipal requires an explicitly supplied --geojson path')
        raw=geojson.read_bytes();data=read_geojson(json.loads(raw))
        source=dict(filename=geojson.name,sha256=hashlib.sha256(raw).hexdigest(),features=len(data),
                    vertices=sum(municipal.geometry_vertices(f.geometry) for f in data))
    report=dict(schema_version=1,version=azl.__version__,python=platform.python_version(),platform=platform.platform(),
        tooling_sha256=sha(__file__),factory_sha256={m.__name__:sha(m.__file__) for m in (maps,scientific,municipal)},
        coverage_sha256={'before':sha(old.__file__),'after':sha(coverage.__file__)},renderer_sha256=sha(pillow.__file__),
        source=source,repeats=repeats,points=points,cases=[],notes=[
            'One immutable scene per case/DPI. Before swaps only _area with our own previous snapshot.',
            'Serial alternating calls; raster timings exclude composition, hash, PNG/SVG encoding and I/O.',
            'No concurrent profiling/measurement sampler, geometry simplification or Tk frame cache.',
            'Small local samples; caches warm across calls. Not a statistical or visible-input latency guarantee.',
            'Terrain/vector/point values are synthetic. Bundled boundaries generalized; optional municipal source not redistributed.'])
    for name in cases:
        for dpi in dpis:
            if name=='municipal':fig,ax=municipal.create(data,dpi)
            elif name in ('terrain','globe'):
                fig=getattr(scientific,name+'_example')();fig.set_dpi(dpi)
            else:fig,ax=maps.create(name,points);fig.set_dpi(dpi)
            try:
                scene=fig.to_scene(cull=True);times={'before':[],'after':[]};hashes=[];png_data=None
                for trial in range(repeats):
                    for mode in ('before','after') if trial%2==0 else ('after','before'):
                        with patch.object(coverage,'_area',old._area if mode=='before' else current):
                            start=time.perf_counter();image=render_image(scene);seconds=time.perf_counter()-start
                        try:
                            stream=io.BytesIO();image.save(stream,format='PNG');png_data=stream.getvalue()
                            value=(hashlib.sha256(image.tobytes()).hexdigest(),hashlib.sha256(png_data).hexdigest())
                        finally:image.close()
                        if hashes and value!=hashes[0]:raise RuntimeError(f'RGBA/PNG changed at {name}/{dpi}/{mode}')
                        hashes.append(value);times[mode].append(seconds)
                        print(f'{name}/{dpi}/{trial}/{mode}: {seconds:.3f}s; RGBA/PNG identical',flush=True)
                svg=render_svg(scene).encode('utf-8')
                report['cases'].append(dict(name=name,dpi=dpi,pixels=[scene.width,scene.height],scene_items=len(scene.items),
                    samples_seconds=times,median_seconds={mode:statistics.median(samples) for mode,samples in times.items()},
                    rgba_sha256=hashes[0][0],png_sha256=hashes[0][1],svg_sha256=hashlib.sha256(svg).hexdigest(),identical_rgba=True,identical_png=True))
                if preview_dir:
                    preview_dir.mkdir(parents=True,exist_ok=True)
                    (preview_dir/f'{name}-{dpi}.png').write_bytes(png_data);(preview_dir/f'{name}-{dpi}.svg').write_bytes(svg)
            finally:azl.close(fig)
    forbidden=('matplotlib','cartopy','geopandas','shapely','pyproj')
    assert not any(name.split('.')[0] in forbidden for name in sys.modules)
    report['independent_runtime']=True
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--cases',nargs='+',choices=('state','brazil','atlas','points','terrain','globe','municipal'),default=['state','brazil','atlas','points','terrain','globe'])
    parser.add_argument('--dpi',nargs='+',type=int,default=[100]);parser.add_argument('--repeats',type=int,default=2)
    parser.add_argument('--points',type=int,default=1500);parser.add_argument('--geojson',type=Path);parser.add_argument('--preview-dir',type=Path)
    args=parser.parse_args()
    if min(args.repeats,args.points,*args.dpi)<1:parser.error('DPI/repeats/points must be positive')
    if 'municipal' in args.cases and args.geojson is None:parser.error('municipal requires --geojson')
    benchmark(args.output,args.cases,args.dpi,args.repeats,args.points,args.geojson,args.preview_dir)
