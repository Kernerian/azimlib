"""Single diagnostic of OS memory around large Pillow resize/composite calls.

Instrumentation is deliberately separate from timing/memory benchmarks. OS
high-water marks are process-wide and callbacks do not observe every allocation
inside a native call. Only trusted own-renderer snapshots may be loaded.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
from unittest.mock import patch
from measure_process_memory import process_memory

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-dir',type=Path)
    parser.add_argument('--case',choices=('state','brazil','atlas'),default='atlas')
    parser.add_argument('--dpi',type=int,default=200)
    parser.add_argument('--output',type=Path,default=Path('raster-memory-diagnostic.json'))
    args=parser.parse_args()
    if args.dpi<1:parser.error('dpi must be positive')
    from PIL import Image,__version__ as pillow_version
    from azimlib.renderers import pillow,coverage
    from benchmark_maps import create
    from compare_raster_versions import module
    renderer=pillow;selected_coverage=coverage
    if args.baseline_dir:
        renderer=module('azimlib.renderers._diagnostic_pillow',args.baseline_dir/'pillow.py')
        selected_coverage=module('azimlib.renderers._diagnostic_coverage',args.baseline_dir/'coverage.py')
    samples=[];resize=Image.Image.resize;composite=Image.Image.alpha_composite
    def record(event,image,target):
        samples.append(dict(event=event,mode=image.mode,source=list(image.size),target=list(target),memory=process_memory()))
    def observed_resize(image,size,*a,**kw):
        large=image.width*image.height>1_000_000
        if large:record('resize_enter',image,size)
        result=resize(image,size,*a,**kw)
        if large:record('resize_exit',image,size)
        return result
    def observed_composite(image,other,*a,**kw):
        large=other.width*other.height>1_000_000
        if large:record('composite_enter',other,image.size)
        result=composite(image,other,*a,**kw)
        if large:record('composite_exit',other,image.size)
        return result
    fig,_=create(args.case,1500);fig.dpi=args.dpi;scene=fig.to_scene(cull=True)
    samples.append(dict(event='scene',memory=process_memory()));buffer=io.BytesIO()
    original=sys.modules['azimlib.renderers.coverage'];sys.modules['azimlib.renderers.coverage']=selected_coverage
    try:
        with patch.object(Image.Image,'resize',observed_resize),patch.object(Image.Image,'alpha_composite',observed_composite):
            renderer.render_png(scene,buffer)
    finally:sys.modules['azimlib.renderers.coverage']=original
    samples.append(dict(event='png',memory=process_memory()))
    assert not any(n.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj') for n in sys.modules)
    report=dict(python=platform.python_version(),platform=platform.platform(),pillow=pillow_version,
        renderer_sha256=hashlib.sha256(Path(renderer.__file__).read_bytes()).hexdigest(),
        case=args.case,dpi=args.dpi,pixels=[scene.width,scene.height],
        png_sha256=hashlib.sha256(buffer.getvalue()).hexdigest(),samples=samples,
        notes=['Single instrumented diagnostic, not used for timing comparison or statistical gain.',
               'Callbacks select native resize/composite calls with more than one million source pixels.',
               'OS high-water mark covers the whole process, not a single stage/native-only allocation. Callbacks do not locate all transient native allocations.'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(f'{args.case} {args.dpi}: {len(samples)} diagnostic events; peak {samples[-1]["memory"]["peak_working_set_bytes"]/1024**2:.2f} MiB')

if __name__=='__main__':main()
