"""Dev-only process/native-buffer memory of complete exports in fresh workers.

Windows working set/private commit via OS API; Unix peak RSS via resource.
No psutil, GIS or plotting dependency. Each case/DPI starts a new interpreter.
"""
import argparse
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import time

def process_memory():
    if sys.platform=='win32':
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(name,ctypes.c_size_t) for name in
                ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
                 'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage')]
        counters=Counters();counters.cb=ctypes.sizeof(counters)
        kernel=ctypes.WinDLL('kernel32',use_last_error=True);api=ctypes.WinDLL('psapi',use_last_error=True)
        kernel.GetCurrentProcess.restype=wintypes.HANDLE
        api.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
        api.GetProcessMemoryInfo.restype=wintypes.BOOL
        if not api.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(counters),counters.cb):raise ctypes.WinError(ctypes.get_last_error())
        return dict(working_set_bytes=counters.WorkingSetSize,peak_working_set_bytes=counters.PeakWorkingSetSize,private_committed_bytes=counters.PrivateUsage,source='Windows GetProcessMemoryInfo')
    import resource
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    current=None
    if sys.platform.startswith('linux'):
        current=int(Path('/proc/self/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
    return dict(working_set_bytes=current,peak_working_set_bytes=peak,private_committed_bytes=None,source='resource peak RSS; /proc current RSS when available')

def worker(name,dpi):
    import io
    import azimlib as azl
    from azimlib.renderers import render_png
    from benchmark_maps import create
    from PIL import __version__ as pillow_version
    samples=dict(imported=process_memory());fig,_=create(name,1500);fig.dpi=dpi
    samples['data_and_artists']=process_memory();scene=fig.to_scene(cull=True)
    samples['scene']=process_memory();buffer=io.BytesIO();start=time.perf_counter();render_png(scene,buffer)
    observed=time.perf_counter()-start;samples['png']=process_memory()
    assert not any(module.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj') for module in sys.modules)
    return dict(name=name,dpi=dpi,pixels=[round(scene.width),round(scene.height)],items=len(scene.items),png_bytes=buffer.tell(),
                observed_png_seconds=observed,pillow=pillow_version,azimlib=azl.__version__,memory=samples)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--child',nargs=2,metavar=('CASE','DPI'))
    parser.add_argument('--cases',nargs='+',choices=('state','brazil','atlas'),default=['state','brazil','atlas'])
    parser.add_argument('--dpi',nargs='+',type=int,default=[100,200])
    parser.add_argument('--output',type=Path,default=Path('process-memory.json'))
    args=parser.parse_args()
    if args.child:
        print(json.dumps(worker(args.child[0],int(args.child[1]))));return
    if any(v<1 for v in args.dpi):parser.error('dpi must be positive')
    report=dict(python=platform.python_version(),platform=platform.platform(),notes=[
        'Each case/DPI runs serially in a fresh interpreter. Process memory includes imported runtime, loaded data, Python allocations and native buffers.',
        'Peak working set is the OS high-water mark of this process, not a stage-specific allocation peak. It is not subtracted from a baseline.',
        'Working set is resident memory and depends on OS policy; Windows PrivateUsage is committed private memory, not a native-only breakdown.',
        'PNG includes rasterization and in-memory encoding with cull=True. No tracemalloc, sampler thread, profiler or GUI. One measurement per case, no general bound/latency guarantee.',
        'Unix current RSS may be unavailable; units are explicitly converted to bytes.'],cases=[])
    for name in args.cases:
        for dpi in args.dpi:
            result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--child',name,str(dpi)],capture_output=True,text=True,timeout=300)
            if result.returncode:raise RuntimeError(result.stderr)
            entry=json.loads(result.stdout);report['cases'].append(entry)
            args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2),encoding='utf-8')
            print(f'{name} {dpi} DPI: process peak {entry["memory"]["png"]["peak_working_set_bytes"]/1024**2:.2f} MiB',flush=True)

if __name__=='__main__':main()
