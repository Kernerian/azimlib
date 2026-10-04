"""Alternating own-renderer comparison on exactly the same complete-map scenes.

Provide trusted snapshots of Azimlib's pillow.py and coverage.py in baseline-dir.
This development tool swaps their coverage module serially; never use it in a
multi-threaded application. It does not import any external plotting backend.
"""
import argparse
import hashlib
import importlib.util
import io
import json
import platform
from pathlib import Path
import statistics
import sys
import time
import azimlib
from azimlib.renderers import pillow as current_renderer,coverage as current_coverage
from benchmark_maps import create


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-dir',type=Path,default=Path(__file__).with_name('baselines')/'raster-before')
    parser.add_argument('--output',type=Path,default=Path('renderer-comparison.json'))
    parser.add_argument('--cases',nargs='+',choices=('state','brazil','atlas','points'),default=['state','brazil','atlas','points'])
    parser.add_argument('--dpi',type=int,default=100)
    parser.add_argument('--repeats',type=int,default=4)
    parser.add_argument('--points',type=int,default=1500)
    args=parser.parse_args()
    if min(args.dpi,args.repeats,args.points)<1:parser.error('dpi, repeats and points must be positive')
    old_renderer=module('azimlib.renderers._baseline_pillow',args.baseline_dir/'pillow.py')
    old_coverage=module('azimlib.renderers._baseline_coverage',args.baseline_dir/'coverage.py')
    from PIL import __version__ as pillow_version
    def fingerprint(folder):return {name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in ('pillow.py','coverage.py')}
    report=dict(python=platform.python_version(),platform=platform.platform(),pillow_version=pillow_version,
                dpi=args.dpi,repeats=args.repeats,points=args.points,
                renderer_source_sha256={'before':fingerprint(args.baseline_dir),
                                       'after':fingerprint(Path(current_renderer.__file__).parent)},
                policy='Each pair reverses before/after order; one immutable scene per case; PNG encoding included; no profiling or memory instrumentation.',cases=[])
    coverage_name='azimlib.renderers.coverage'
    original=sys.modules[coverage_name]
    try:
        for name in args.cases:
            fig,_=create(name,args.points);fig.dpi=args.dpi;scene=fig.to_scene()
            timings={'before':[],'after':[]};hashes={'before':set(),'after':set()}
            for trial in range(args.repeats):
                order=('before','after') if trial%2==0 else ('after','before')
                for which in order:
                    renderer,coverage=(old_renderer,old_coverage) if which=='before' else (current_renderer,current_coverage)
                    sys.modules[coverage_name]=coverage
                    buffer=io.BytesIO();start=time.perf_counter();renderer.render_png(scene,buffer)
                    timings[which].append(time.perf_counter()-start)
                    hashes[which].add(hashlib.sha256(buffer.getvalue()).hexdigest())
                print(f'{name}: pair {trial+1}/{args.repeats}',flush=True)
            same=len(hashes['before'])==len(hashes['after'])==1 and hashes['before']==hashes['after']
            before=statistics.median(timings['before']);after=statistics.median(timings['after'])
            result=dict(name=name,items=len(scene.items),samples_seconds=timings,
                        before_median_seconds=before,after_median_seconds=after,
                        reduction_percent=(1-after/before)*100,identical_png=same,
                        png_sha256={k:sorted(v) for k,v in hashes.items()})
            report['cases'].append(result)
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
            print(f'{name}: {before:.3f}s -> {after:.3f}s; same PNG={same}',flush=True)
            azimlib.close(fig)
            if not same:raise RuntimeError('Raster optimization changed PNG output')
    finally:sys.modules[coverage_name]=original
    print(args.output.resolve(),flush=True)


if __name__=='__main__':main()
