"""Compare process peak memory in alternating fresh before/after workers.

Trusted own-renderer snapshots only; no plotting/GIS imports. Both workers load
both renderer implementations, then select one before rendering the same map.
OS high-water marks include runtime/data/Python/native buffers, not just PNG.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
from measure_process_memory import process_memory

def worker(name,dpi,mode,folder):
    import azimlib as azl
    from azimlib.renderers import pillow,coverage
    from benchmark_maps import create
    from compare_raster_versions import module
    from PIL import __version__ as pillow_version
    old_pillow=module('azimlib.renderers._memory_baseline_pillow',folder/'pillow.py')
    old_coverage=module('azimlib.renderers._memory_baseline_coverage',folder/'coverage.py')
    samples=dict(imported=process_memory())
    fig,_=create(name,1500);fig.dpi=dpi
    samples['data_and_artists']=process_memory();scene=fig.to_scene(cull=True)
    samples['scene']=process_memory();buffer=io.BytesIO()
    original=sys.modules['azimlib.renderers.coverage']
    sys.modules['azimlib.renderers.coverage']=old_coverage if mode=='before' else coverage
    try:
        start=time.perf_counter()
        (old_pillow if mode=='before' else pillow).render_png(scene,buffer)
        observed=time.perf_counter()-start;samples['png']=process_memory()
    finally:sys.modules['azimlib.renderers.coverage']=original
    assert not any(n.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj') for n in sys.modules)
    return dict(name=name,dpi=dpi,mode=mode,pixels=[round(scene.width),round(scene.height)],items=len(scene.items),
                png_bytes=buffer.tell(),png_sha256=hashlib.sha256(buffer.getvalue()).hexdigest(),
                observed_png_seconds=observed,pillow=pillow_version,azimlib=azl.__version__,memory=samples)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-dir',type=Path,default=Path(__file__).with_name('baselines')/'raster-buffers-before')
    parser.add_argument('--child',nargs=3,metavar=('CASE','DPI','MODE'))
    parser.add_argument('--cases',nargs='+',choices=('state','brazil','atlas'),default=['state','brazil','atlas'])
    parser.add_argument('--dpi',nargs='+',type=int,default=[100,200])
    parser.add_argument('--repeats',type=int,default=2)
    parser.add_argument('--output',type=Path,default=Path('raster-memory-comparison.json'))
    args=parser.parse_args();folder=args.baseline_dir.resolve()
    if args.child:
        if args.child[2] not in ('before','after'):parser.error('invalid mode')
        print(json.dumps(worker(args.child[0],int(args.child[1]),args.child[2],folder)));return
    if min(*args.dpi,args.repeats)<1:parser.error('dpi and repeats must be positive')
    from azimlib.renderers import pillow
    def fingerprint(path):return {n:hashlib.sha256((path/n).read_bytes()).hexdigest() for n in ('pillow.py','coverage.py')}
    report=dict(python=platform.python_version(),platform=platform.platform(),repeats=args.repeats,
        renderer_source_sha256=dict(before=fingerprint(folder),after=fingerprint(Path(pillow.__file__).parent)),notes=[
        'Every mode/case/DPI/trial starts a fresh interpreter; serial trials reverse before/after order. Both implementations are imported in every worker.',
        'Identical map construction and cull=True. PNG hashing follows memory sampling; encoding is included. No profiler/tracemalloc/GUI.',
        'OS peak working set includes runtime, data, Python and native buffers for the whole process lifetime; no baseline subtraction/native-only breakdown.',
        'Resident memory depends on OS policy. Private committed memory is a different counter. Few samples do not establish a general memory bound or speed guarantee.'],cases=[])
    for name in args.cases:
        for dpi in args.dpi:
            samples={'before':[],'after':[]}
            for trial in range(args.repeats):
                for mode in (('before','after') if trial%2==0 else ('after','before')):
                    result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--child',name,str(dpi),mode,
                        '--baseline-dir',str(folder)],capture_output=True,text=True,timeout=300)
                    if result.returncode:raise RuntimeError(result.stderr)
                    samples[mode].append(json.loads(result.stdout))
                print(f'{name} {dpi}: pair {trial+1}/{args.repeats}',flush=True)
            hashes={entry['png_sha256'] for mode in samples.values() for entry in mode}
            metadata={(tuple(entry['pixels']),entry['items'],entry['png_bytes']) for mode in samples.values() for entry in mode}
            same=len(hashes)==len(metadata)==1
            medians={mode:{key:statistics.median(entry['memory']['png'][key] for entry in entries)
                for key in ('peak_working_set_bytes','working_set_bytes','private_committed_bytes')
                if all(entry['memory']['png'][key] is not None for entry in entries)} for mode,entries in samples.items()}
            before=medians['before']['peak_working_set_bytes'];after=medians['after']['peak_working_set_bytes']
            report['cases'].append(dict(name=name,dpi=dpi,identical_png=same,samples=samples,png_memory_medians=medians,
                peak_reduction_percent=(1-after/before)*100))
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
            print(f'{name} {dpi}: peak {before/1024**2:.2f} -> {after/1024**2:.2f} MiB; same PNG={same}',flush=True)
            if not same:raise RuntimeError('Scenes/PNG differ between workers')

if __name__=='__main__':main()
