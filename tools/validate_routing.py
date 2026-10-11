"""Offline own-router trial: reproducible grid plus unchanged licensed OSM.

No download/publication. Disk cap includes this output directory and temporary
indexes. Tracemalloc measures Python allocations, not process/native RSS.
"""
import argparse,hashlib,json,platform,shutil,statistics,sys,tempfile,time,tracemalloc
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import azimlib as az
from azimlib._pbf_decode import OSMRecord as R


def grid(size):
    for y in range(size):
        for x in range(size): yield R('node',y*size+x+1,{},(x*.001,y*.001))
    for y in range(size):
        yield R('way',y+1,{'highway':'residential'},refs=tuple(y*size+x+1 for x in range(size)))
    for x in range(size):
        yield R('way',size+x+1,{'highway':'residential'},refs=tuple(y*size+x+1 for y in range(size)))


def real_route(graph):
    start = next(iter(graph.edges.values())).start
    candidates = sorted(graph.nodes,key=lambda n:az.haversine(graph.nodes[start].coordinate,graph.nodes[n].coordinate),reverse=True)
    for end in candidates[:100]:
        try: return graph.route(start,end)
        except az.RoutingError: continue
    raise AssertionError('No nontrivial real route')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--size',type=int,default=80)
    parser.add_argument('--storage-limit',type=int,default=20_000_000_000)
    parser.add_argument('--reserve-free',type=int,default=15_000_000_000)
    args = parser.parse_args()
    if not 10<=args.size<=100: parser.error('Grid size must be 10..100')
    if not 1024*1024<=args.storage_limit<=20_000_000_000 or args.reserve_free<15_000_000_000:
        parser.error('Require storage <=20 GB and free reserve >=15 GB')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    existing = sum(p.stat().st_size for p in args.output.parent.rglob('*') if p.is_file())
    available = min(128*1024*1024,args.storage_limit-existing)
    if available<1024*1024 or shutil.disk_usage(args.output.parent).free<args.reserve_free+available:
        raise az.RoutingLimitError('Insufficient trial storage/free reserve')
    size = args.size
    source = az.RoutingSource('routing-grid','1','BSD-3-Clause','Kernerian','Own synthetic square road network',
        'urn:azimlib:synthetic:routing-grid-1',hashlib.sha256(f'routing-grid-1:{size}'.encode()).hexdigest())
    tracemalloc.start(); start = time.perf_counter()
    graph = az.RoadGraph.from_records(grid(size),source=source)
    build_seconds = time.perf_counter()-start
    latencies = []; expanded = []
    for i in range(40):
        a = (i*157)%(size*size)+1; b = size*size-(i*79)%(size*size)
        start = time.perf_counter(); route = graph.route(a,b)
        latencies.append(time.perf_counter()-start); expanded.append(route.expanded_states)
        other = graph.route(a,b,algorithm='dijkstra')
        assert abs(route.distance_m-other.distance_m)<1e-6
    # Main/requesting thread keeps servicing heartbeat work during a real query.
    with ThreadPoolExecutor(max_workers=1) as executor:
        task = graph.submit(executor,1,size*size,algorithm='dijkstra')
        beats = []; start = time.perf_counter()
        while not task.done():
            beats.append(time.perf_counter()-start); time.sleep(.005)
        task.result(); elapsed = time.perf_counter()-start
    assert beats,'Query completed before concurrency evidence could be collected'
    with tempfile.TemporaryDirectory(prefix='routing-trial-',dir=args.output.parent) as temp:
        directory = Path(temp)/'grid'
        digest = graph.save(directory,max_bytes=available//2,reserve_free_bytes=args.reserve_free)
        loaded = az.RoadGraph.load(directory)
        assert abs(loaded.route(1,size*size).distance_m-graph.route(1,size*size).distance_m)<1e-6
        graph_bytes = sum(p.stat().st_size for p in directory.iterdir())
        catalog = az.DatasetCatalog(ROOT/'optional-data/urban-sao-paulo-1.0/catalog.json')
        modes = {}
        for mode in ('car','bicycle','foot'):
            real = az.RoadGraph.from_catalog(catalog,'urban-sao-paulo',profile=az.RoutingProfile(mode))
            route = real_route(real)
            oracle = real.route(route.stops[0],route.stops[-1],algorithm='dijkstra')
            assert abs(route.distance_m-oracle.distance_m)<1e-6
            modes[mode] = dict(nodes=len(real.nodes),directed_edges=len(real.edges),
                distance_m=route.distance_m,estimated_duration_s=route.duration_s,route_steps=len(route.steps))
        provenance = real.source.as_dict(); provenance.pop('notices')
    peak = tracemalloc.get_traced_memory()[1]; tracemalloc.stop()
    assert peak<128*1024*1024
    report = dict(passed=True,scope='Regional/synthetic own routing, not planet throughput or native RSS',
        python=platform.python_version(),system=platform.system(),
        synthetic=dict(size=size,nodes=len(graph.nodes),directed_edges=len(graph.edges),
            build_seconds=build_seconds,queries=len(latencies),median_seconds=statistics.median(latencies),
            p95_seconds=sorted(latencies)[int(.95*(len(latencies)-1))],maximum_expanded_states=max(expanded),
            persistence_bytes=graph_bytes,persistence_sha256=digest,astar_dijkstra_agree=True),
        concurrency=dict(main_thread_heartbeats=len(beats),worker_seconds=elapsed,
            largest_heartbeat_gap_seconds=max((b-a for a,b in zip(beats,beats[1:])),default=0),
            worker_mutates_artists=False,scope='Executor responsiveness measurement; not native GUI human acceptance'),
        real=dict(source=provenance,modes=modes),peak_python_bytes=peak,
        python_memory_budget_bytes=128*1024*1024,generated_storage_peak_upper_bound_bytes=existing+graph_bytes,
        storage_limit_bytes=args.storage_limit,reserve_free_bytes=args.reserve_free,
        free_bytes_after=shutil.disk_usage(args.output.parent).free,
        runtime_sha256={p.relative_to(ROOT/'src/azimlib').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'src/azimlib').rglob('*.py'))})
    assert report['generated_storage_peak_upper_bound_bytes']<args.storage_limit
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='runtime_sha256'},indent=2))


if __name__=='__main__': main()
