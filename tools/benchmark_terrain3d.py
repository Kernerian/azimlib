"""Bounded own triangle raster performance; excludes GPU/FPS/human latency claims."""
import argparse,hashlib,json,math,platform,statistics,time,sys,tracemalloc
from pathlib import Path
import azimlib as azl
from azimlib.terrain3d import Camera,rasterize
from azimlib.terrain_axes import surface_mesh,SurfaceArtist

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    runtime=Path(azl.__file__).resolve().parent;assert runtime.is_relative_to(Path(sys.prefix).resolve())
    cases=[]
    for n,accelerate in ((16,False),(32,True),(64,True)):
        values=[[50*math.sin(i/7)*math.cos(j/9) for i in range(n)] for j in range(n)]
        mesh=surface_mesh([i*10 for i in range(n)],[j*10 for j in range(n)],values,'m','m');artist=SurfaceArtist(mesh)
        faces=artist.faces(Camera(),mesh.bounds,4/3,1);rasterize(faces,320,240,accelerate=accelerate)
        times=[]
        for _ in range(3):
            t=time.perf_counter();result=rasterize(faces,320,240,accelerate=accelerate);times.append(time.perf_counter()-t)
        tracemalloc.start();rasterize(faces,320,240,accelerate=accelerate);_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        cases.append(dict(grid=n,triangles=len(mesh.triangles),accelerate=accelerate,seconds=times,median_seconds=statistics.median(times),python_tracemalloc_peak=peak,rgba_sha256=hashlib.sha256(result.rgba).hexdigest()))
    report=dict(version=azl.__version__,platform=platform.system(),dimensions=[320,240],scope='Raster only, 3 samples after warmup; tracemalloc is not RSS/native memory; no FPS claim',cases=cases,limits=dict(vertices=50000,triangles=20000,pixels=8000000,bbox_tests=64000000),runtime_sha256={p.relative_to(runtime).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(runtime.rglob('*.py'))},tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
if __name__=='__main__':main()
