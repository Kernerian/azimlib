"""Reproducible synthetic foundation measurements, not planet-scale evidence."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import statistics
import sys
import time
import tracemalloc

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from azimlib._frames import GEODETIC
from azimlib.terrain3d import LocalFrame


def run():
    points = tuple((-180+i*360/1000, -89+(i % 179), (i % 20)*100) for i in range(1000))
    timings = []
    maximum_angle, maximum_height = 0., 0.
    for _ in range(7):
        start = time.perf_counter()
        for point in points:
            result = GEODETIC.from_fixed(GEODETIC.to_fixed(*point))
            maximum_angle = max(maximum_angle, *(abs(a-b) for a, b in zip(point[:2], result[:2])))
            maximum_height = max(maximum_height, abs(point[2]-result[2]))
        timings.append((time.perf_counter()-start)*1000)
    tracemalloc.start()
    held = [GEODETIC.to_fixed(*point) for point in points]
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert len(held) == 1000
    frame = LocalFrame(-46, -23)
    start = time.perf_counter()
    for i in range(10000):
        frame.horizontal(-46+(i % 100)*.0001, -23)
    local_ms = (time.perf_counter()-start)*1000
    # Declared targets have a named workload; timing is not a universal CI gate.
    targets = dict(batch1000_p95_ms=250, held1000_peak_bytes=4*1024*1024,
                   angle_degrees=1e-10, height_metres=1e-7)
    p95 = sorted(timings)[math.ceil(.95*len(timings))-1]
    result = dict(schema_version=1, context='local source tree; synthetic benchmark, not hosted CI or real dataset throughput',
                  python=platform.python_version(), system=platform.system(), machine=platform.machine(),
                  processor=platform.processor(),
                  batch_size=1000, repeats=7, roundtrips=7000,
                  median_ms=statistics.median(timings), p95_ms=p95, samples_ms=timings,
                  held1000_peak_bytes=peak, local_frame_10000_ms=local_ms,
                  max_angle_error_degrees=maximum_angle, max_height_error_metres=maximum_height,
                  targets=targets, targets_met=dict(latency=p95<=targets['batch1000_p95_ms'],
                  memory=peak<=targets['held1000_peak_bytes'], angle=maximum_angle<=targets['angle_degrees'],
                  height=maximum_height<=targets['height_metres']),
                  runtime_sha256={name:hashlib.sha256((ROOT/'src/azimlib'/name).read_bytes()).hexdigest()
                                  for name in ('_frames.py','_timescales.py','_contracts.py','geodesy.py','terrain3d.py')})
    if not result['targets_met']['angle'] or not result['targets_met']['height']:
        raise ArithmeticError('Foundation numeric tolerance failed')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf8')
    print(json.dumps(result, indent=2))
