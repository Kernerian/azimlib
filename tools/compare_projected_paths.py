"""Serial own-pipeline comparison: uncached vertices versus bounded path reuse.

Uses the previous Azimlib geometry compositor, not Matplotlib. Timings measure
composition, not raster/event-loop latency. Memory/PNG run in separate passes.
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
import time
import tracemalloc
from unittest.mock import patch
import azimlib as azl
from azimlib import render_map,projected_paths
from azimlib.projections import Orthographic
from azimlib.renderers import render_png
from benchmark_maps import create
from compare_composition import create_dense


def globe():
    fig,ax=azl.subplots(figsize=(6.4,4.8),projection=Orthographic(central_longitude=-50,central_latitude=-10))
    ax.countries(facecolor='#eeeeee',edgecolor='#777777',linewidth=.3)
    ax.set_extent((-140,40,-70,70));ax.set_title('Globo · hemisfério visível')
    return fig,ax


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeats',type=int,default=6)
    parser.add_argument('--cases',nargs='+',choices=('state','brazil','atlas','dense','globe'),default=['state','brazil','atlas','dense','globe'])
    parser.add_argument('--output',type=Path,default=Path('projected-paths.json'))
    parser.add_argument('--preview-dir',type=Path)
    args=parser.parse_args()
    if args.repeats<1:parser.error('repeats must be positive')
    baseline=Path(__file__).with_name('baselines')/'paths-before'/'render_map.py'
    spec=importlib.util.spec_from_file_location('azimlib._paths_before',baseline)
    previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
    from PIL import __version__ as pillow_version
    report=dict(schema_version=1,azimlib_version=azl.__version__,python=platform.python_version(),
        platform=platform.platform(),pillow_version=pillow_version,repeats=args.repeats,dpi=100,
        source_sha256={name:hashlib.sha256(Path(path).read_bytes()).hexdigest()
            for name,path in [('before',baseline),('current',render_map.__file__),('cache',projected_paths.__file__)]},
        notes=['Serial alternating own previous _geometry pipeline/current; same current viewport/index/style/renderers.',
               'First composition samples have warm data/bounds/viewport/index but no vertex cache.',
               'Warm cache reused across pan/zoom; cull=True in both modes.',
               'Memory instrumentation/PNG are separate from timing; source data and existing bounds excluded.',
               'Retained cache payload/tuple byte counter is not total memory, metadata, native buffers or RSS.',
               'dense uses 2501 synthetic polygons, not municipal boundaries; not GUI latency/general speed guarantees.'],cases=[])
    cache=projected_paths._paths;modes=('before','cached')
    for name in args.cases:
        fig,ax=globe() if name=='globe' else create_dense() if name=='dense' else create(name,1500)
        fig.dpi=100
        def compose(mode):
            if mode=='cached':return fig.to_scene(cull=True)
            with patch.object(render_map,'_geometry',previous._geometry):return fig.to_scene(cull=True)
        # Warm data, projected bounds and envelopes equally, without warming paths.
        compose('before');first={mode:[] for mode in modes}
        for trial in range(args.repeats):
            for mode in modes if trial%2==0 else modes[::-1]:
                cache.clear();gc.collect()
                start=time.perf_counter();compose(mode)
                first[mode].append(time.perf_counter()-start)
        cache.clear();compose('cached')
        samples={mode:[] for mode in modes};zooms={mode:[] for mode in modes};scenes={}
        extent=ax.get_extent()
        for trial in range(args.repeats):
            for mode in modes if trial%2==0 else modes[::-1]:
                start=time.perf_counter();scenes[mode]=compose(mode)
                samples[mode].append(time.perf_counter()-start)
                ax.zoom(1.15)
                try:
                    start=time.perf_counter();compose(mode)
                    zooms[mode].append(time.perf_counter()-start)
                finally:ax.set_extent(extent)
            print(f'{name}: warm/zoom pair {trial+1}/{args.repeats}',flush=True)
        info=cache.info()._asdict();hashes={};images={}
        for mode,scene in scenes.items():
            buffer=io.BytesIO();render_png(scene,buffer);images[mode]=buffer.getvalue()
            hashes[mode]=hashlib.sha256(images[mode]).hexdigest()
        same_scene=scenes['before'].items==scenes['cached'].items and scenes['before'].maps==scenes['cached'].maps
        same_png=len(set(hashes.values()))==1
        cache.clear();gc.collect();tracemalloc.start()
        try:
            value=compose('cached');del value
            retained,peak=tracemalloc.get_traced_memory()
        finally:tracemalloc.stop()
        memory=dict(retained_python=retained,peak_python=peak,cache_info=cache.info()._asdict())
        medians={mode:statistics.median(values) for mode,values in samples.items()}
        report['cases'].append(dict(name=name,first_samples_seconds=first,
            first_median_seconds={mode:statistics.median(values) for mode,values in first.items()},
            samples_seconds=samples,median_seconds=medians,
            zoom_samples_seconds=zooms,zoom_median_seconds={mode:statistics.median(values) for mode,values in zooms.items()},
            cache_info=info,python_cache_composition_allocation_bytes=memory,
            identical_scene=same_scene,identical_png=same_png,png_sha256=hashes))
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
        if args.preview_dir:
            args.preview_dir.mkdir(parents=True,exist_ok=True)
            (args.preview_dir/f'{name}-100.png').write_bytes(images['cached'])
        azl.close(fig);cache.clear()
        print(f'{name}: {medians}; identical Scene/PNG={same_scene}/{same_png}',flush=True)
        if not same_scene or not same_png:raise RuntimeError('Projected reuse changed map')
    print(args.output.resolve(),flush=True)


if __name__=='__main__':main()
