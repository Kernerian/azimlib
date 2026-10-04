"""First composition followed by uncached geographic pans and returned views.

Measures scene preparation, not a raster/image cache or native monitor latency.
Binary coordinate hashes preserve every float bit (SVG rounding is not used).
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import struct
import sys
import time


def digest(scene):
    from azimlib.scene import Path as ScenePath
    sha=hashlib.sha256();pair=struct.Struct('<2d');count=struct.Struct('<Q')
    for item in scene.items:
        sha.update(type(item).__name__.encode());sha.update(json.dumps(dict(item.style),sort_keys=True).encode())
        sha.update(json.dumps(item.clip).encode())
        if isinstance(item,ScenePath):
            sha.update(bytes([item.closed]));sha.update(count.pack(len(item.paths)))
            for points in item.paths:
                sha.update(count.pack(len(points)))
                for point in points:sha.update(pair.pack(*point))
        else:
            sha.update(json.dumps({k:v for k,v in vars(item).items() if k not in ('style','clip')},sort_keys=True).encode())
    sha.update(json.dumps(scene.maps,sort_keys=True).encode())
    return sha.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('geojson',type=Path);parser.add_argument('--runtime',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    sys.path.insert(0,str(args.runtime.resolve()))
    import azimlib as azl
    from azimlib.projected_paths import _paths
    from benchmark_detailed_map import build
    from measure_process_memory import process_memory
    fig,ax,read,input_hash=build(args.geojson);_paths.clear()
    home=ax.get_extent();w,e,s,n=home
    views=[('first',home),('new_pan',(w+.4,e+.4,s+.2,n+.2)),('new_pan_2',(w+.8,e+.8,s+.4,n+.4)),
           ('returned_home',home),('returned_pan',(w+.4,e+.4,s+.2,n+.2))]
    records=[]
    for name,extent in views:
        ax.set_extent(extent);start=time.perf_counter();scene=fig.to_scene(cull=True);elapsed=time.perf_counter()-start
        records.append(dict(name=name,extent=extent,scene_seconds=elapsed,items=len(scene.items),
            exact_scene_sha256=digest(scene),cache=_paths.info()._asdict(),memory=process_memory()))
        print(name,elapsed,flush=True)
    root=Path(azl.__file__).parent
    report=dict(schema_version=1,python=platform.python_version(),platform=platform.platform(),input_sha256=input_hash,
        tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),read_seconds=read,
        runtime_sha256={str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in sorted(root.rglob('*.py'))},views=records,
        scope='No raster cache/raster/window/input. First scene + successive novel pans + returned views; packed float bits/styles/clip/map metadata compared. Original XY; fields synthetic; cache bounded separately from process memory.')
    assert records[0]['exact_scene_sha256']==records[3]['exact_scene_sha256']
    assert records[1]['exact_scene_sha256']==records[4]['exact_scene_sha256']
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');azl.close(fig)


if __name__=='__main__':main()
