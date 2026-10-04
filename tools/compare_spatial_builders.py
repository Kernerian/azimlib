"""Serial comparison of own spatial builders: preparation, queries and memory.

Geometry bounds are warmed for both builders. Allocation measurements and PNG
painting run outside timing. No external geospatial engine or Matplotlib.
"""
import argparse
import gc
import hashlib
import importlib.util
import io
import json
import platform
from pathlib import Path
import statistics
import sys
import time
import tracemalloc
from unittest.mock import patch
import azimlib as azl
from azimlib import spatial
from azimlib.renderers import render_png
from benchmark_spatial import create_large
from compare_composition import create_dense


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeats',type=int,default=6)
    parser.add_argument('--output',type=Path,default=Path('spatial-builders.json'))
    args=parser.parse_args()
    if args.repeats<1:parser.error('repeats must be positive')
    baseline=Path(__file__).with_name('baselines')/'spatial-before'/'spatial.py'
    spec=importlib.util.spec_from_file_location('azimlib._spatial_before',baseline)
    previous=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=previous;spec.loader.exec_module(previous)
    modes={'before':previous,'packed_str':spatial}
    from PIL import __version__ as pillow_version
    report=dict(schema_version=1,python=platform.python_version(),platform=platform.platform(),
        azimlib_version=azl.__version__,pillow_version=pillow_version,repeats=args.repeats,
        source_sha256={name:hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
                       for name,module in modes.items()},
        notes=['Own median-split BVH versus own packed float64 STR hierarchy.',
               'Fresh index per preparation sample; same source geometries and already cached bounds.',
               'Alternating serial timings; memory, Scene and PNG verification outside preparation/query timing.',
               'Python index allocation excludes source data/bounds, native buffers/RSS and painting.',
               'Synthetic polygons, not municipal boundaries; not GUI latency or general speed guarantees.'],cases=[])
    for name,create in (('dense',create_dense),('large',create_large)):
        fig,ax=create();data=ax.layers[0].data
        for feature in data:feature.geometry.bounds
        prepared={};samples={mode:[] for mode in modes}
        for trial in range(args.repeats):
            for mode in modes if trial%2==0 else reversed(modes):
                cache=modes[mode]._ViewportIndexCache()
                gc.collect()
                start=time.perf_counter();value=cache.get(data,ax.projection)
                samples[mode].append(time.perf_counter()-start);prepared[mode]=value
            print(f'{name}: preparation pair {trial+1}/{args.repeats}',flush=True)
        from azimlib.viewport import Viewport
        vp=Viewport(ax.projection,ax._get_extent(),(0,0,640,480))
        focused=vp._query_bounds(5)
        boxes={'focused':focused,'all':prepared['before'].index.bounds}
        query_samples={mode:{kind:[] for kind in boxes} for mode in modes}
        counts={}
        for kind,box in boxes.items():
            results={mode:value.query(box) for mode,value in prepared.items()}
            if results['before']!=results['packed_str']:raise RuntimeError('Query changed candidate keys')
            counts[kind]=len(results['before'])
            for trial in range(args.repeats):
                for mode in modes if trial%2==0 else reversed(modes):
                    start=time.perf_counter()
                    for _ in range(100):prepared[mode].query(box)
                    query_samples[mode][kind].append((time.perf_counter()-start)/100)
        scenes={};hashes={};memory={}
        cache=data._viewport_indexes
        for mode,module in modes.items():
            with patch.object(cache,'get',return_value=prepared[mode]):
                scenes[mode]=fig.to_scene(cull=True)
            stream=io.BytesIO();render_png(scenes[mode],stream)
            hashes[mode]=hashlib.sha256(stream.getvalue()).hexdigest()
            gc.collect();new_cache=module._ViewportIndexCache();tracemalloc.start()
            try:
                new_cache.get(data,ax.projection)
                retained,peak=tracemalloc.get_traced_memory()
                memory[mode]=dict(retained=retained,peak=peak)
            finally:tracemalloc.stop()
        same_scene=scenes['before'].items==scenes['packed_str'].items and scenes['before'].maps==scenes['packed_str'].maps
        same_png=len(set(hashes.values()))==1
        medians={mode:statistics.median(values) for mode,values in samples.items()}
        report['cases'].append(dict(name=name,features=len(data),samples_seconds=samples,median_seconds=medians,
            query_samples_seconds=query_samples,query_median_seconds={mode:{kind:statistics.median(values)
                for kind,values in series.items()} for mode,series in query_samples.items()},
            query_candidates=counts,python_index_allocation_bytes=memory,
            identical_scene=same_scene,identical_png=same_png,png_sha256=hashes))
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
        print(f'{name}: {medians}; memory={memory}; identical Scene/PNG={same_scene}/{same_png}',flush=True)
        azl.close(fig)
        if not same_scene or not same_png:raise RuntimeError('Builder changed visible map')
    print(args.output.resolve(),flush=True)


if __name__=='__main__':main()
