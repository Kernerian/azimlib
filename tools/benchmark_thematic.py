"""Fixed-workload CPU Phase C measurements; no GPU latency guarantee."""
import argparse,hashlib,json,math,os,platform,statistics,subprocess,time,tracemalloc
from pathlib import Path
import azimlib as a

def main(output):
 output.parent.mkdir(parents=True,exist_ok=True)
 try:sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
 except (OSError,subprocess.CalledProcessError):sha=os.environ.get('GITHUB_SHA','unavailable')
 f,ax=a.subplots(body=a.MARS,figsize=(6,4),dpi=100);ax.set_extent((-20,20,-15,15))
 g=ax.group(name='Fixed workload');points=[(-18+(i%40)*.9,-12+(i//40)*2) for i in range(400)]
 g.add(ax.symbols(points,'gold',size=4,color='#a87b3c'))
 polygon=[(8*math.cos(i*math.tau/128),6*math.sin(i*math.tau/128)) for i in range(128)]
 g.add(ax.region(a.RegionDefinition.polygon(polygon,context=ax.get_context()),facecolor='#5695a3',alpha=.3))
 p=a.CartographicPath.spline([(-15,-8),(-5,7),(5,-5),(15,8)],context=ax.get_context(),samples_per_segment=200)
 g.add(ax.cartographic_path(p,linewidth=1.2,path_symbol='arrow',spacing=30))
 cold_start=time.perf_counter();f.to_scene();first_scene_ms=(time.perf_counter()-cold_start)*1000
 base=(-20,20,-15,15)
 operations={'warm_scene':lambda i:f.to_scene(),'pan':lambda i:(ax.set_extent((-20+i%2,20+i%2,-15,15)),f.to_scene()),'zoom':lambda i:(ax.set_extent((-20+i%2*2,20-i%2*2,-15+i%2,15-i%2)),f.to_scene()),'toggle':lambda i:(g.set_visible(bool(i%2)),f.to_scene())}
 rows=[]
 for name,fn in operations.items():
  ax.set_extent(base);g.set_visible(True)
  for i in range(3):fn(i)
  values=[]
  for i in range(12):
   start=time.perf_counter();fn(i);values.append((time.perf_counter()-start)*1000)
  rows.append(dict(operation=name,raw_ms=values,median_ms=statistics.median(values),p95_ms=sorted(values)[math.ceil(.95*len(values))-1],variance_ms2=statistics.pvariance(values)))
 ax.set_extent(base);g.set_visible(True)
 for fmt in ('png','svg','pdf'):
  import io
  values=[];sizes=[]
  for i in range(3):
   stream=io.StringIO() if fmt=='svg' else io.BytesIO();start=time.perf_counter();f.savefig(stream,format=fmt);values.append((time.perf_counter()-start)*1000);sizes.append(len(stream.getvalue().encode('utf8') if fmt=='svg' else stream.getvalue()))
  rows.append(dict(operation='export_'+fmt,raw_ms=values,median_ms=statistics.median(values),p95_ms=max(values),variance_ms2=statistics.pvariance(values),bytes=sizes))
 tracemalloc.start();f.to_scene();current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
 # Separate stress workload: nested ownership and two independent viewports.
 f2,axes=a.subplots(1,2,body=a.MARS,figsize=(6,4),dpi=100)
 for axis in axes:axis.set_extent((-20,20,-15,15))
 root=axes[0].group(name='Depth 0');leaf=root
 for depth in range(8):leaf=axes[0].group(parent=leaf,name='Depth '+str(depth+1))
 positions=[(-18+(i%40)*.9,-12+(i//40)*.9) for i in range(1000)]
 leaf.add(axes[0].symbols(positions,'village',size=3))
 clone=root.instantiate(axes[1]);stress=[]
 for i in range(3):f2.to_scene()
 for i in range(12):
  start=time.perf_counter();leaf.set_visible(bool(i%2));f2.to_scene();stress.append((time.perf_counter()-start)*1000)
 rows.append(dict(operation='stress_1000_symbols_depth8_two_viewports_toggle',raw_ms=stress,median_ms=statistics.median(stress),p95_ms=max(stress),variance_ms2=statistics.pvariance(stress)))
 a.close(f2)
 import importlib.metadata
 report=dict(sha=sha,version=a.__version__,platform=platform.system(),machine=platform.machine(),processor=platform.processor(),python=platform.python_version(),pillow=importlib.metadata.version('Pillow'),dimensions=[600,400],dpi=100,workload=dict(symbols=400,region_vertices=128,route_samples=len(p.points)),warmup=3,repetitions=12,exports_repetitions=3,first_prepared_scene_ms=first_scene_ms,memory=dict(traced_single_frame_peak_bytes=peak,traced_current_bytes=current),measurements=rows,scope='Sequential local/CI CPU process. Scene preparation and full export are separate; toolkit presentation, cold process and GPU are not measured. No 33/100 ms claim.')
 output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report));a.close(f)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
