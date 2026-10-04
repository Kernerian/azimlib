"""Alternating linear/indexed culling with identical scenes and PNG verification.

Serial development tool. Memory instrumentation runs separately from timing;
synthetic polygons are not municipal boundaries. Matplotlib is never imported.
"""
import argparse
import hashlib
import io
import json
import platform
from pathlib import Path
import statistics
import time
import tracemalloc
from unittest.mock import patch
import azimlib as azl
from azimlib import render_map
from azimlib.geometry import Geometry,Feature,FeatureCollection
from azimlib.renderers import render_png
from benchmark_maps import create
from compare_composition import create_dense


def create_large():
    features=[]
    for y in range(-50,50):
        for x in range(-140,60):
            ring=[(x,y),(x+.8,y),(x+.8,y+.8),(x,y+.8),(x,y)]
            features.append(Feature(Geometry('Polygon',[ring])))
    fig,ax=azl.subplots(figsize=(6.4,4.8),projection='mercator',layout='constrained')
    ax.geojson(FeatureCollection(features),fit=False,facecolor='#dce8ea',edgecolor='#506b75',linewidth=.4)
    ax.set_extent((-54,-43,-26,-19));ax.set_title('20.000 polígonos sintéticos · foco regional')
    return fig,ax


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases',nargs='+',choices=('state','brazil','atlas','dense','large'),default=['state','brazil','atlas','dense','large'])
    parser.add_argument('--repeats',type=int,default=6)
    parser.add_argument('--dpi',type=int,default=100)
    parser.add_argument('--output',type=Path,default=Path('spatial-benchmark.json'))
    parser.add_argument('--preview-dir',type=Path)
    parser.add_argument('--memory',action='store_true')
    args=parser.parse_args()
    if min(args.repeats,args.dpi)<1:parser.error('repeats and dpi must be positive')
    from PIL import __version__ as pillow_version
    report=dict(schema_version=1,azimlib_version=azl.__version__,python=platform.python_version(),
                platform=platform.platform(),pillow_version=pillow_version,repeats=args.repeats,dpi=args.dpi,
                notes=['Warm alternating linear/indexed composition; culling and viewport caching enabled in both.',
                       'Preparation time measured separately before composition on eligible top-level collections.',
                       'Index memory is Python retained/peak allocation on a fresh collection sharing source geometry and cached bounds.',
                       'Memory excludes source geometry, existing bounds, native buffers/RSS and painting; separate from timing.',
                       'dense/large contain 2501/20000 synthetic polygons; not municipal boundaries.',
                       'No claim of general acceleration or GUI latency.'],cases=[])
    modes=('linear','indexed')
    for name in args.cases:
        start=time.perf_counter()
        fig,ax=create_large() if name=='large' else create_dense() if name=='dense' else create(name,1500)
        fig.dpi=args.dpi;setup=time.perf_counter()-start
        prepared=[]
        for layer in ax.layers:
            if layer.kind!='geometry' or len(layer.data)<64:continue
            start=time.perf_counter();index=layer.data._viewport_indexes.get(layer.data,ax.projection)
            elapsed=time.perf_counter()-start;allocation=None
            if args.memory:
                clone=FeatureCollection(layer.data.features)
                tracemalloc.start()
                try:
                    clone._viewport_indexes.get(clone,ax.projection)
                    retained,peak=tracemalloc.get_traced_memory();allocation=dict(retained=retained,peak=peak)
                finally:tracemalloc.stop()
            prepared.append(dict(features=len(layer.data),indexed=index.index.size,always=len(index.always),
                                 seconds=elapsed,python_index_allocation_bytes=allocation))
        def compose(mode):
            if mode=='indexed':return fig.to_scene(cull=True)
            with patch.object(render_map,'_geometry_candidates',return_value=None):return fig.to_scene(cull=True)
        for mode in modes:compose(mode)
        samples={mode:[] for mode in modes};zooms={mode:[] for mode in modes};scenes={};extent=ax.get_extent()
        for trial in range(args.repeats):
            for mode in modes if trial%2==0 else modes[::-1]:
                start=time.perf_counter();scenes[mode]=compose(mode);samples[mode].append(time.perf_counter()-start)
                ax.zoom(1.3)
                try:
                    start=time.perf_counter();compose(mode);zooms[mode].append(time.perf_counter()-start)
                finally:ax.set_extent(extent)
            print(f'{name}: pair {trial+1}/{args.repeats}',flush=True)
        same_scene=scenes['linear'].items==scenes['indexed'].items and scenes['linear'].maps==scenes['indexed'].maps
        hashes={};outputs={}
        for mode,scene in scenes.items():
            stream=io.BytesIO();render_png(scene,stream);outputs[mode]=stream.getvalue()
            hashes[mode]=hashlib.sha256(outputs[mode]).hexdigest()
        same_png=len(set(hashes.values()))==1
        medians={mode:statistics.median(values) for mode,values in samples.items()}
        result=dict(name=name,setup_seconds=setup,index_preparation=prepared,samples_seconds=samples,median_seconds=medians,
                    zoom_samples_seconds=zooms,zoom_median_seconds={mode:statistics.median(values) for mode,values in zooms.items()},
                    composition_reduction_percent=(1-medians['indexed']/medians['linear'])*100,
                    items={mode:len(scene.items) for mode,scene in scenes.items()},
                    identical_scene=same_scene,identical_png=same_png,png_sha256=hashes)
        report['cases'].append(result);args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
        if args.preview_dir:
            args.preview_dir.mkdir(parents=True,exist_ok=True)
            (args.preview_dir/f'{name}-{args.dpi}.png').write_bytes(outputs['indexed'])
        azl.close(fig);print(f'{name}: {medians}, identical scene/PNG={same_scene}/{same_png}',flush=True)
        if not same_scene or not same_png:raise RuntimeError('Spatial index changed the visible scene')
    print(args.output.resolve(),flush=True)


if __name__=='__main__':main()
