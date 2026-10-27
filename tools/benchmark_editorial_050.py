"""Fixed editorial workloads; preparation vs raster/exports, no latency guarantee."""
import argparse,io,json,math,platform,statistics,subprocess,time,tracemalloc
from pathlib import Path
import azimlib as a

def main(output):
 f=a.figure(figsize=(10,7),dpi=100);page=f.cartographic_page(body=a.MARS,title='Fixed editorial benchmark',subtitle='CPU; explicit workload and all samples');ax=page.axes;ax.set_extent((-20,20,-15,15));g=ax.group(name='Symbols')
 positions=[(-18+(i%12)*3.1,-12+(i//12)*2.4) for i in range(120)]
 symbol=g.add(ax.symbols(positions,'bot',size=8,halo=a.IconHalo(width=.45),shadow=a.IconShadow(blur=.4,alpha=.15)))
 names=tuple('P'+str(i) for i in range(120));labels=g.add(symbol.labels_for(names,fontsize=5))
 r=ax.region(a.RegionDefinition.polygon([(-15,-10),(15,-10),(15,10),(-15,10)],context=ax.get_context()),facecolor='#d6b678',alpha=.25)
 path=ax.cartographic_path(a.CartographicPath.spline([(-15,-8),(-5,10),(5,-6),(15,8)],context=ax.get_context(),samples_per_segment=200),color='#9b6351',linewidth=1.2)
 page.legend(sections=[a.LegendSection('Sites',(symbol,),('120 author sites',)),a.LegendSection('Area',(r,),('Author area',))],fontsize=8);inset=page.locator(shade=True)
 actions={'warm_preparation':lambda i:f.to_scene(),'pan_locator':lambda i:(ax.set_extent((-20+i%2,20+i%2,-15,15)),f.to_scene()),'zoom_locator':lambda i:(ax.set_extent((-20+i%2*2,20-i%2*2,-15+i%2,15-i%2)),f.to_scene()),'group_toggle':lambda i:(g.set_visible(bool(i%2)),f.to_scene())};rows=[]
 for name,fn in actions.items():
  ax.set_extent((-20,20,-15,15));g.set_visible(True)
  for i in range(2):fn(i)
  raw=[]
  for i in range(8):
   start=time.perf_counter();fn(i);raw.append((time.perf_counter()-start)*1000)
  rows.append(dict(operation=name,raw_ms=raw,median_ms=statistics.median(raw),p95_ms=max(raw),variance_ms2=statistics.pvariance(raw)))
 ax.set_extent((-20,20,-15,15));g.set_visible(True)
 for fmt in ('png','svg','pdf'):
  raw=[];sizes=[]
  for i in range(2):
   stream=io.StringIO() if fmt=='svg' else io.BytesIO();start=time.perf_counter();f.savefig(stream,format=fmt);raw.append((time.perf_counter()-start)*1000);sizes.append(len(stream.getvalue()))
  rows.append(dict(operation='full_export_'+fmt,raw_ms=raw,median_ms=statistics.median(raw),p95_ms=max(raw),variance_ms2=statistics.pvariance(raw),bytes=sizes))
 tracemalloc.start();f.to_scene();current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
 try:
  import psutil
  process=psutil.Process();rss=process.memory_info().rss;cpu=platform.processor()
 except ImportError:rss=None;cpu=platform.processor()
 output.parent.mkdir(parents=True,exist_ok=True);report=dict(sha=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),version=a.__version__,platform=platform.system(),machine=platform.machine(),processor=cpu,python=platform.python_version(),backend='CPU',dpi=100,pixels=[1000,700],workload=dict(symbols=120,labels=120,halo=True,soft_shadow=True,region_vertices=5,route_samples=len(path.definition.points),locator=1,legend_sections=2),warmup=2,preparation_repetitions=8,export_repetitions=2,tracemalloc_peak_bytes=peak,rss_observed_bytes=rss,measurements=rows,scope='Diagnostic sequential process; no guarantee of33ms/100ms, cold start or toolkit presentation; no cherry-picked repetition.')
 output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps(report));a.close(f)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
