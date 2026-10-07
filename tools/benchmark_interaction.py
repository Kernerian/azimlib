"""Reproducible synthetic urban/dense paint, pan, label, memory and export measurements.

Timings are local evidence, not hardware-independent FPS promises. Memory is
tracemalloc Python allocations plus reported cache payload, not native Qt/Pillow RSS.
"""
import argparse,hashlib,importlib.metadata,json,math,platform,statistics,time,tracemalloc
from pathlib import Path
import azimlib as azl
from azimlib.geometry import Geometry,Feature,FeatureCollection
from azimlib.renderers import render_image
from azimlib.projected_paths import _paths
from azimlib.simplify import _simplified

def measure(fn):
    start=time.perf_counter();value=fn();return value,(time.perf_counter()-start)*1000
def summary(values):
    values=sorted(values);return dict(median_ms=statistics.median(values),p95_ms=values[min(len(values)-1,math.ceil(len(values)*.95)-1)],samples=len(values))
def scenario(name,args,folder):
    fig,ax=azl.subplots(figsize=(6.4,4.8));ax.set_extent((-2,2,-1.5,1.5));ax.set_axis_off();ax.set_title(name)
    if name=='urban':
        features=[]
        for i in range(args.streets):
            y=-1.4+2.8*(i+.5)/args.streets
            points=[(-1.9+3.8*j/64,y+.002*math.sin(j/2+i)) for j in range(65)]
            features.append(Feature(Geometry('LineString',points),{'name':f'Street {i+1}'},i))
        layer=ax.geojson(FeatureCollection(features),edgecolor='#677780',linewidth=.4);layer.set_simplify(.35)
        labels=FeatureCollection(Feature(Geometry('Point',(-1.4+(i%5)*.65,-1+(i//5)*.5)),{'name':f'POI {i+1}'},i) for i in range(20))
        label=ax.labels(labels,'name',avoid_overlap=True,fontsize=7)
    else:
        points=[(1.65*math.sqrt((i+.5)/args.points)*math.cos(i*2.399963229728653),1.25*math.sqrt((i+.5)/args.points)*math.sin(i*2.399963229728653)) for i in range(args.points)]
        layer=ax.scatter([p[0] for p in points],[p[1] for p in points],s=[3],color='#248bb880');label=None
    _paths.clear();_simplified.clear()
    scene,compose=measure(lambda:fig.to_scene(cull=True,interactive=True));image,paint=measure(lambda:render_image(scene));image.close()
    from azimlib.renderers._tile_cache import TileCache
    from azimlib.renderers._interactive import InteractivePathCache
    tiles=TileCache(max_entries=512);paths=InteractivePathCache()
    times=[];compose_times=[];primitives=len(scene.items)
    for i in range(args.samples):
        delta=.01*(i+1);ax.set_extent((-2+delta,2+delta,-1.5,1.5))
        scene,elapsed=measure(lambda:fig.to_scene(cull=True,interactive=True));compose_times.append(elapsed)
        image,elapsed=measure(lambda:render_image(scene,_interactive=True,_tile_cache=tiles,_path_cache=paths));image.close();times.append(elapsed)
    # Allocation tracing is a separate composition pass; it must not inflate timings.
    tracemalloc.start();memory_scene=fig.to_scene(cull=True,interactive=True);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop();del memory_scene
    labels_ms=None
    if label is not None:
        label.set_visible(False);_,without=measure(lambda:fig.to_scene(cull=True));label.set_visible(True);_,with_labels=measure(lambda:fig.to_scene(cull=True));labels_ms=dict(with_labels=with_labels,without_labels=without)
    exports=[]
    for fmt in ('png','svg','pdf'):
        path=folder/(name+'.'+fmt);_,elapsed=measure(lambda:fig.savefig(path));exports.append(dict(format=fmt,milliseconds=elapsed,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    # Presentation must never magnify linewidth when translating the view.
    widths=[i.style.get('stroke_width') for i in scene.items if i.style.get('stroke')=='#677780']
    if name=='urban':assert widths and all(abs(v-.4*fig.dpi/72)<1e-10 for v in widths)
    cache=_simplified.info();assert cache['payload_bytes']<=cache['max_bytes']
    print(name+' measurements finished',flush=True)
    result=dict(scenario=name,features=args.streets if name=='urban' else args.points,first_compose_ms=compose,first_raster_ms=paint,first_paint_ms=compose+paint,
        pan_compose=summary(compose_times),pan_raster=summary(times),pan_total=summary([a+b for a,b in zip(compose_times,times)]),
        tile_cache=dict(hits=tiles.hits,misses=tiles.misses,entries=len(tiles.entries),payload_bytes=tiles.bytes,max_bytes=16*1024*1024),python_peak_bytes=peak,memory_scope='Separate warm composition pass; excludes native allocations and retained caches',primitives=primitives,labels=labels_ms,cache=cache,exports=exports,physical_strokes_verified=name=='urban')
    assert tiles.bytes<=16*1024*1024;tiles.close();fig.close();return result
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--streets',type=int,default=400);p.add_argument('--points',type=int,default=5000);p.add_argument('--samples',type=int,default=4);a=p.parse_args()
    if not 2<=a.samples<=20 or not 1<=a.streets<=20000 or not 1<=a.points<=500000:p.error('samples 2..20, streets 1..20000, points 1..500000')
    a.output.mkdir(parents=True,exist_ok=True)
    packages={}
    for name in ('Pillow','numpy','aggdraw'):
        try:packages[name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:packages[name]=None
    report=dict(passed=True,python=platform.python_version(),platform=platform.system(),packages=packages,scope='Local whole-scene recomposition/raster, synthetic data; not native input latency or total process/native memory',scenarios=[scenario(n,a,a.output) for n in ('urban','dense')])
    (a.output/'result.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
