"""Offline bounded OSM PBF trial; regional results are not planet-scale evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import re
import sys
import time
import tracemalloc
from datetime import datetime, timezone
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'tools'))
from azimlib import OSMIndex
from measure_process_memory import process_memory


def memory_cgroup(max_bytes):
    """Fail closed: a planet trial requires a dedicated Linux cgroup v2 cap."""
    if sys.platform != 'linux' or not isinstance(max_bytes, int) or max_bytes <= 0:
        raise ValueError('Planet trial requires Linux cgroup v2 and a positive memory ceiling')
    entries = Path('/proc/self/cgroup').read_text().splitlines()
    names = [line[3:] for line in entries if line.startswith('0::')]
    if len(names) != 1 or names[0] == '/' or '..' in Path(names[0]).parts:
        raise ValueError('Require a dedicated non-root cgroup v2 (not a remapped namespace)')
    directory = Path('/sys/fs/cgroup') / names[0].lstrip('/')
    def snapshot():
        maximum = (directory / 'memory.max').read_text().strip()
        swap = (directory / 'memory.swap.max').read_text().strip()
        if maximum != str(max_bytes) or swap != '0':
            raise ValueError('Actual memory.max / memory.swap.max differs from declared budget')
        events = dict(line.split() for line in (directory / 'memory.events').read_text().splitlines())
        if any(int(events.get(k, '0')) for k in ('oom', 'oom_kill', 'oom_group_kill')):
            raise ValueError('Cgroup has OOM events; require a fresh dedicated trial cgroup')
        return dict(maximum_bytes=max_bytes, swap_maximum_bytes=0,
                    peak_bytes=int((directory / 'memory.peak').read_text()),
                    oom_events={k: int(events.get(k, '0')) for k in ('oom', 'oom_kill', 'oom_group_kill')})
    return snapshot


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--index-directory', type=Path)
    parser.add_argument('--scope', choices=('regional', 'synthetic', 'planet'), default='regional')
    parser.add_argument('--max-storage-bytes', type=int, default=20_000_000_000)
    parser.add_argument('--reserve-free-bytes', type=int, default=15_000_000_000)
    parser.add_argument('--missing', choices=('error', 'skip'), default='error')
    parser.add_argument('--bbox', type=float, nargs=4, metavar=('WEST', 'SOUTH', 'EAST', 'NORTH'))
    parser.add_argument('--dataset-version')
    parser.add_argument('--source-url')
    parser.add_argument('--full-reference-audit', action='store_true')
    parser.add_argument('--max-memory-bytes', type=int)
    args = parser.parse_args(argv)
    memory_snapshot = None
    if args.scope == 'planet':
        if (not args.dataset_version or not args.source_url or
                not args.full_reference_audit or args.missing != 'error' or args.bbox is not None):
            parser.error('Planet trial requires source/version, full reference audit, strict missing refs and no bbox')
        url = urlsplit(args.source_url)
        try:
            dated = datetime.strptime(args.dataset_version, '%Y-%m-%d').strftime('%y%m%d')
        except ValueError:
            parser.error('Planet dataset version must be the actual snapshot date YYYY-MM-DD')
        if (url.scheme != 'https' or url.hostname != 'planet.openstreetmap.org' or
                url.username or url.password or url.query or url.fragment or
                not re.fullmatch(r'/pbf/planet-' + dated + r'\.osm\.pbf', url.path)):
            parser.error('Planet trial requires a pinned official HTTPS PBF source URL')
        memory_snapshot = memory_cgroup(args.max_memory_bytes)
        memory_snapshot()  # Check enforcement before any ingest allocation.
    size = args.input.stat().st_size
    # Count the supplied input conservatively, even if it already exists. Reserve
    # 16 MiB for reports/SQLite filesystem bookkeeping, outside max_page_count.
    budget = args.max_storage_bytes - size - 16 * 1024 * 1024
    if budget < 1024 * 1024:
        parser.error('Input plus index/report reservation exceeds total storage budget')
    memory_before = process_memory()
    tracemalloc.start(); started = time.perf_counter()
    try:
        with OSMIndex(args.input, directory=args.index_directory, max_disk_bytes=budget,
                      reserve_free_bytes=args.reserve_free_bytes, missing=args.missing,
                      expected_sha256=args.sha256) as index:
            build_seconds = time.perf_counter() - started
            features = vertices = 0; geometry_counts = {}
            for feature in index.features(bbox=args.bbox):
                features += 1; vertices += sum(1 for _ in feature.geometry.iter_positions())
                kind = feature.geometry.type; geometry_counts[kind] = geometry_counts.get(kind, 0) + 1
            references = index.audit_references() if args.full_reference_audit else None
            if references is not None and not references['passed']:
                raise ValueError('Full reference audit found missing references')
            stats = dict(index.statistics); header = index.header
            if stats['input_bytes_read'] != size:
                raise ValueError('Complete input byte count does not match file size')
            disk = index._path.stat().st_size
            assert disk <= budget
            report = dict(passed=True, declared_scope=args.scope, input_bytes=size,
                          input_sha256=index.sha256, header=header, statistics=stats,
                          completed_utc=datetime.now(timezone.utc).isoformat(),
                          dataset_version=args.dataset_version, source_url=args.source_url,
                          complete_input_verified=True, references=references,
                          cgroup_memory=memory_snapshot() if memory_snapshot else None,
                          selected_features=features, selected_vertices=vertices,
                          geometry_counts=geometry_counts, build_seconds=build_seconds,
                          total_seconds=time.perf_counter() - started,
                          python_peak_bytes=tracemalloc.get_traced_memory()[1],
                          python_peak_scope='tracemalloc; excludes native SQLite caches and OS page cache',
                          process_memory_before=memory_before, process_memory_after=process_memory(),
                          index_peak_bytes=disk, max_storage_bytes=args.max_storage_bytes,
                          reserve_free_bytes=args.reserve_free_bytes,
                          planet_scale_confirmed=False,
                          python=platform.python_version(), system=platform.system(),
                          source_sha256={p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                         for p in (ROOT / 'src/azimlib').glob('*pbf*.py')})
    except Exception as exc:
        # Avoid paths/tags in public reports. The exception type and failed status
        # are sufficient for a gate; local diagnostics can be captured separately.
        report = dict(passed=False, declared_scope=args.scope, error_type=type(exc).__name__,
                      planet_scale_confirmed=False, total_seconds=time.perf_counter()-started)
    finally:
        tracemalloc.stop()
    # The scope label alone cannot establish a planet-scale test. Human review
    # of the pinned source, counts, resources and complete run remains required.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
