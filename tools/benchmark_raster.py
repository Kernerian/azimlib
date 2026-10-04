"""Reproducible PNG benchmark: python tools/benchmark_raster.py --output result.json."""
import argparse,io,json,platform,random,time
from pathlib import Path
import azimlib as az
from azimlib.renderers import render_png

parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,default=Path('raster-benchmark.json'))
args=parser.parse_args()
random.seed(123)
results=[]
for name in ('state','points'):
    fig,ax=az.subplots(figsize=(6.4,4.8),projection='mercator')
    if name=='state':ax.state('SP');ax.grid(step=1);ax.scale_bar()
    else:ax.scatter([random.uniform(-52,-44) for _ in range(600)],
                    [random.uniform(-25,-20) for _ in range(600)],s=9,edgecolor='none')
    start=time.perf_counter();scene=fig.to_scene();composition=time.perf_counter()-start
    start=time.perf_counter();render_png(scene,io.BytesIO());raster=time.perf_counter()-start
    results.append(dict(name=name,composition=composition,raster=raster,items=len(scene.items)))
    az.close(fig)
report=dict(python=platform.python_version(),platform=platform.platform(),figsize=[6.4,4.8],
            dpi=100,points=600,seed=123,cases=results)
args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
