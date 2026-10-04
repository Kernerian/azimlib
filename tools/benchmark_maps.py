"""Measure complete maps by stage; Matplotlib is never imported.

python tools/benchmark_maps.py --repeats 3 --dpi 100 --output docs/map-benchmark.json
Timing samples exclude file I/O, optional profiling and memory instrumentation.
"""
from __future__ import annotations
import argparse
from collections import Counter
import cProfile
import hashlib
import io
import json
import platform
import pstats
import random
import statistics
import sys
import time
import tracemalloc
from pathlib import Path
import azimlib as azl
from azimlib.renderers import render_png,render_svg
from azimlib.scene import Path as ScenePath
from azimlib.ticker import LongitudeFormatter,LatitudeFormatter

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'examples'))
from gridspec_atlas import create as create_atlas


def create(name,points):
    if name=='atlas':
        fig,_,axes=create_atlas();return fig,axes[0]
    fig,ax=azl.subplots(figsize=(6.4,4.8),projection='mercator',layout='constrained')
    if name=='state':
        ax.states(fit=False,facecolor='#eeeeee',edgecolor='#888888',linewidth=.4)
        ax.state('SP',facecolor='#e1e8ec',edgecolor='#333333',linewidth=.7)
        ax.plot([-50.2,-48.3,-46.63],[-22.5,-22.1,-23.55],'r--',label='Rota demonstrativa')
        ax.legend(loc='upper right');ax.scale_bar(length=100);ax.north_arrow(loc='upper left',size=20)
        ax.set_extent((-54,-43,-26,-19));ax.set_title('São Paulo · mapa completo')
    elif name=='brazil':
        ax.countries(facecolor='#eeeeee',edgecolor='#999999',linewidth=.35)
        ax.map('brazil',facecolor='white',edgecolor='#333333',linewidth=.65)
        ax.states(linewidth=.4);ax.rivers(linewidth=.6,label='Rios')
        ax.legend(loc='lower right');ax.scale_bar();ax.compass(size=20);ax.north_arrow(size=20)
        ax.set_extent((-76,-32,-36,8));ax.set_title('Brasil · limites e hidrografia')
    else:
        rng=random.Random(123)
        ax.states(fit=False,facecolor='#eeeeee',edgecolor='#999999',linewidth=.3)
        ax.scatter([rng.uniform(-52,-44) for _ in range(points)],
                   [rng.uniform(-25,-20) for _ in range(points)],s=9,edgecolor='none',color='#1f77b4',alpha=.6)
        ax.set_extent((-54,-43,-26,-19));ax.set_title(f'{points} pontos · dados sintéticos')
    ax.xaxis.set_major_formatter(LongitudeFormatter());ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    ax.grid(labels=False,color='#b0b0b0',linewidth=.4,linestyle=':')
    return fig,ax


def sample(call,repeats):
    times=[];result=None
    for _ in range(repeats):
        start=time.perf_counter();result=call();times.append(time.perf_counter()-start)
    return dict(samples_seconds=times,median_seconds=statistics.median(times),
                min_seconds=min(times),max_seconds=max(times)),result


def png_bytes(scene):
    buffer=io.BytesIO();render_png(scene,buffer);return buffer.getvalue()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('map-benchmark.json'))
    parser.add_argument('--cases',nargs='+',choices=('state','brazil','atlas','points'),default=['state','brazil','atlas','points'])
    parser.add_argument('--dpi',nargs='+',type=int,default=[100])
    parser.add_argument('--repeats',type=int,default=3)
    parser.add_argument('--points',type=int,default=1500)
    parser.add_argument('--memory',action='store_true',help='Separate Python allocation peak during composition (excludes native Pillow buffers)')
    parser.add_argument('--profile-dir',type=Path,help='Separate additional PNG pass profiled with cProfile')
    parser.add_argument('--preview-dir',type=Path,help='Write the measured PNG/SVG bytes, outside timing samples')
    args=parser.parse_args()
    if args.repeats<1 or args.points<1 or any(d<1 for d in args.dpi):parser.error('repeats, points and dpi must be positive')
    from PIL import __version__ as pillow_version
    report=dict(schema_version=1,azimlib_version=azl.__version__,python=platform.python_version(),
                platform=platform.platform(),pillow_version=pillow_version,
                repeats=args.repeats,seed=123,points=args.points,
                notes=['Measurements are local; no latency or speed guarantee.',
                       'Library/data/font caches remain in-process; setup is not an independent cold-start benchmark.',
                       'PNG includes rasterization and in-memory PNG encoding; SVG includes string serialization.',
                       'zoom_recompose excludes desktop event handling, painting and browser navigation.',
                       'Python memory peak excludes native buffers and is measured separately from timing.'],cases=[])
    for name in args.cases:
        for dpi in args.dpi:
            print(f'{name} {dpi} dpi: setup/composition',flush=True)
            start=time.perf_counter();fig,ax=create(name,args.points);fig.dpi=dpi
            setup=time.perf_counter()-start
            start=time.perf_counter();scene=fig.to_scene();cold=time.perf_counter()-start
            composition,scene=sample(fig.to_scene,args.repeats)
            svg_time,svg=sample(lambda:render_svg(scene),args.repeats)
            print(f'{name} {dpi} dpi: PNG',flush=True)
            raster,png=sample(lambda:png_bytes(scene),args.repeats)
            extent=ax.get_extent()
            def zoom():
                ax.zoom(1.3)
                try:return fig.to_scene()
                finally:ax.set_extent(extent)
            zoom_time,_=sample(zoom,args.repeats)
            memory=None
            if args.memory:
                print(f'{name} {dpi} dpi: separate Python allocation measurement',flush=True)
                tracemalloc.start()
                try:
                    fig.to_scene();_,memory=tracemalloc.get_traced_memory()
                finally:tracemalloc.stop()
            if args.profile_dir:
                args.profile_dir.mkdir(parents=True,exist_ok=True)
                profiler=cProfile.Profile();profiler.runcall(png_bytes,scene)
                profiler.dump_stats(str(args.profile_dir/f'{name}-{dpi}.prof'))
                stream=io.StringIO();pstats.Stats(profiler,stream=stream).strip_dirs().sort_stats('cumulative').print_stats(30)
                (args.profile_dir/f'{name}-{dpi}.txt').write_text(stream.getvalue(),encoding='utf-8')
            result=dict(name=name,dpi=dpi,figsize=list(fig.figsize),pixels=[round(scene.width),round(scene.height)],
                        setup_seconds=setup,cold_composition_seconds=cold,composition=composition,
                        svg=svg_time,png=raster,zoom_recompose=zoom_time,
                        python_composition_peak_bytes=memory,items=len(scene.items),
                        primitive_types=dict(Counter(type(p).__name__ for p in scene.items)),
                        path_vertices=sum(len(part) for p in scene.items if isinstance(p,ScenePath) for part in p.paths),
                        svg_bytes=len(svg.encode('utf-8')),png_bytes=len(png),
                        png_sha256=hashlib.sha256(png).hexdigest())
            report['cases'].append(result)
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
            if args.preview_dir:
                args.preview_dir.mkdir(parents=True,exist_ok=True)
                (args.preview_dir/f'{name}-{dpi}.png').write_bytes(png)
                (args.preview_dir/f'{name}-{dpi}.svg').write_text(svg,encoding='utf-8')
            print(f"{name} {dpi} dpi: compose={composition['median_seconds']:.3f}s PNG={raster['median_seconds']:.3f}s",flush=True)
            azl.close(fig)
    print(args.output.resolve(),flush=True)


if __name__=='__main__':main()
