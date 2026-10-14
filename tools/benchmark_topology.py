"""Reproducible own topology benchmarks and analytic global area oracles.

Synthetic fixtures only; no external data, geometry engines or network. Peak
memory is traced Python allocations, not total native RSS. No release action.
"""
import argparse,hashlib,json,math,platform,sys,time,tracemalloc
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
import azimlib as az
from azimlib import _overlay_planar as plane


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--index-segments',type=int,default=2000)
    parser.add_argument('--polygon-vertices',type=int,default=32)
    args=parser.parse_args()
    if not 10<=args.index_segments<=20000 or not 8<=args.polygon_vertices<=256:parser.error('Supported benchmark sizes: 10..20000 indexed segments, 8..256 polygon vertices')
    tracemalloc.start();start=time.perf_counter()
    shape=plane.Shape(lines=tuple(((Fraction(3*i),Fraction(0)),(Fraction(3*i+1),Fraction(1))) for i in range(args.index_segments)))
    graph=plane.node((shape,))
    index_time=time.perf_counter()-start
    assert len(graph.edges)==args.index_segments and graph.candidate_pairs==0
    def polygon(x):
        coords=tuple((x+math.cos(2*math.pi*i/args.polygon_vertices),math.sin(2*math.pi*i/args.polygon_vertices)) for i in range(args.polygon_vertices))
        return az.Geometry('Polygon',(coords+(coords[0],),))
    a,b=polygon(0),polygon(4);start=time.perf_counter();result=az.union(a,b);overlay_time=time.perf_counter()-start
    expected=args.polygon_vertices*math.sin(2*math.pi/args.polygon_vertices)
    assert abs(result.area()-expected)<1e-12
    global_cases=[]
    east=az.SphericalRegion.hemisphere(0,0)
    for delta in (10,35,80,120,170):
        other=az.SphericalRegion.hemisphere(delta,0);start=time.perf_counter()
        lune=az.intersection(east,other,domain='spherical')
        expected=2*(math.pi-math.radians(delta));actual=lune.area(radius=1)
        assert abs(actual-expected)<1e-10
        global_cases.append(dict(normal_angle_degrees=delta,expected_steradians=expected,actual_steradians=actual,
                                 absolute_error=abs(actual-expected),seconds=time.perf_counter()-start))
    peak=tracemalloc.get_traced_memory()[1];tracemalloc.stop()
    assert peak<128*1024*1024
    report=dict(passed=True,scope='Synthetic local topology; not planetary throughput or native RSS',
                python=platform.python_version(),system=platform.system(),
                index=dict(segments=args.index_segments,candidate_pairs=graph.candidate_pairs,
                           brute_force_pairs=args.index_segments*(args.index_segments-1)//2,seconds=index_time),
                overlay=dict(vertices_per_polygon=args.polygon_vertices,seconds=overlay_time,area=result.area(),expected=args.polygon_vertices*math.sin(2*math.pi/args.polygon_vertices)),
                global_analytic_lunes=global_cases,peak_python_bytes=peak,python_memory_budget_bytes=128*1024*1024,
                runtime_sha256={p.relative_to(ROOT/'src/azimlib').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'src/azimlib').rglob('*.py'))})
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='runtime_sha256'},indent=2))


if __name__=='__main__':main()
