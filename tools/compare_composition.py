"""Compare own viewport before/cache/culling on reproducible map compositions.

Serial development tool: swaps trusted Azimlib classes; do not run with threads.
All modes share current immutable geometry bounds and the same raster renderer.
"""
from contextlib import ExitStack
import argparse
import hashlib
import importlib.util
import io
import json
import platform
from pathlib import Path
import statistics
import time
from unittest.mock import patch
import azimlib as azl
from azimlib import render_map,overview
from azimlib.geometry import Geometry,Feature,FeatureCollection
from azimlib.renderers import render_png
from azimlib.viewport import Viewport,_cached_bounds
from benchmark_maps import create


def create_dense():
    """Synthetic regular polygons; not municipal or authoritative boundaries."""
    fig,ax=azl.subplots(figsize=(6.4,4.8),projection='mercator',layout='constrained')
    features=[]
    for y in range(-50,31,2):
        for x in range(-120,1,2):
            ring=[(x,y),(x+1.6,y),(x+1.6,y+1.6),(x,y+1.6),(x,y)]
            features.append(Feature(Geometry('Polygon',[ring])))
    ax.geojson(FeatureCollection(features),fit=False,facecolor='#dce8ea',edgecolor='#506b75',linewidth=.4)
    ax.set_extent((-54,-43,-26,-19));ax.set_title('Base sintética · foco regional')
    return fig,ax


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases',nargs='+',choices=('state','brazil','atlas','dense'),default=['state','brazil','atlas','dense'])
    parser.add_argument('--dpi',type=int,default=100)
    parser.add_argument('--repeats',type=int,default=4)
    parser.add_argument('--output',type=Path,default=Path('composition-comparison.json'))
    parser.add_argument('--preview-dir',type=Path)
    args=parser.parse_args()
    if min(args.dpi,args.repeats)<1:parser.error('dpi and repeats must be positive')
    baseline=Path(__file__).with_name('baselines')/'viewport-before'/'viewport.py'
    spec=importlib.util.spec_from_file_location('azimlib._viewport_baseline',baseline)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    from PIL import __version__ as pillow_version
    report=dict(schema_version=1,azimlib_version=azl.__version__,python=platform.python_version(),
                platform=platform.platform(),pillow_version=pillow_version,dpi=args.dpi,repeats=args.repeats,
                baseline_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(),
                notes=['Serial alternating warm-composition trials; no GUI/event-loop latency measurement.',
                       'All three modes use current immutable geometry bounds; before replaces only Viewport.',
                       'PNG comparisons use one output per mode, after timing, without file I/O in timings.',
                       'dense contains 2501 synthetic polygons, not municipal boundaries.',
                       'Results are local observations, not a general speed guarantee.'],cases=[])
    modes=('before','cached_full','cached_culled')
    for name in args.cases:
        fig,ax=create_dense() if name=='dense' else create(name,1500);fig.dpi=args.dpi
        scenes={};timings={mode:[] for mode in modes};zoom={mode:[] for mode in modes}
        def compose(mode):
            cls=module.Viewport if mode=='before' else Viewport
            with ExitStack() as stack:
                for target in (render_map,overview):stack.enter_context(patch.object(target,'Viewport',cls))
                return fig.to_scene(cull=mode=='cached_culled')
        _cached_bounds.cache_clear()
        for mode in modes:compose(mode)
        extent=ax.get_extent()
        for trial in range(args.repeats):
            for mode in modes if trial%2==0 else modes[::-1]:
                start=time.perf_counter();scenes[mode]=compose(mode)
                timings[mode].append(time.perf_counter()-start)
                ax.zoom(1.3)
                try:
                    start=time.perf_counter();compose(mode);zoom[mode].append(time.perf_counter()-start)
                finally:ax.set_extent(extent)
            print(f'{name}: composition pair {trial+1}/{args.repeats}',flush=True)
        hashes={};outputs={}
        for mode,scene in scenes.items():
            buffer=io.BytesIO();render_png(scene,buffer);outputs[mode]=buffer.getvalue()
            hashes[mode]=hashlib.sha256(outputs[mode]).hexdigest()
        same=len(set(hashes.values()))==1
        medians={mode:statistics.median(values) for mode,values in timings.items()}
        result=dict(name=name,samples_seconds=timings,median_seconds=medians,
                    zoom_samples_seconds=zoom,zoom_median_seconds={mode:statistics.median(values) for mode,values in zoom.items()},
                    items={mode:len(scene.items) for mode,scene in scenes.items()},
                    identical_png=same,png_sha256=hashes,
                    reduction_percent_vs_before={mode:(1-medians[mode]/medians['before'])*100 for mode in modes[1:]})
        report['cases'].append(result)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
        if args.preview_dir:
            args.preview_dir.mkdir(parents=True,exist_ok=True)
            (args.preview_dir/f'{name}-{args.dpi}.png').write_bytes(outputs['cached_culled'])
        azl.close(fig)
        print(f'{name}: {medians}; identical PNG={same}',flush=True)
        if not same:raise RuntimeError('Composition optimization changed PNG output')
    print(args.output.resolve(),flush=True)


if __name__=='__main__':main()
