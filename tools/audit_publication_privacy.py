"""Scan tracked files, all local refs/reflogs and optional release archives."""
import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys
import tarfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publication_privacy import findings

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def audit(history=False, archives=()):
    problems = []
    tracked = git('ls-files', '-z').decode().split('\0')[:-1]
    def check(name, data):
        if name.endswith('.geojson.gz'):
            data = gzip.decompress(data)
        for kind in findings(data):
            problems.append({'file': name, 'kind': kind})
    for name in tracked:
        check(name, (ROOT / name).read_bytes())
    blobs = 0
    commits = 0
    unreferenced = []
    if history:
        objects = git('rev-list', '--objects', '--all', '--reflog').decode().splitlines()
        for row in objects:
            oid, _, name = row.partition(' ')
            kind = git('cat-file', '-t', oid).strip()
            if kind == b'blob':
                blobs += 1
                check(name or oid, git('cat-file', 'blob', oid))
            elif kind == b'commit':
                commits += 1
                check('commit:' + oid, git('cat-file', 'commit', oid))
        fsck = subprocess.run(['git', 'fsck', '--full', '--unreachable', '--no-reflogs'], cwd=ROOT,
                              capture_output=True, text=True)
        if fsck.returncode or fsck.stderr.strip():
            problems.append({'file': '.git', 'kind': 'integrity-or-unreadable-object'})
        for line in fsck.stdout.splitlines():
            match = re.fullmatch(r'(?:unreachable|dangling) (blob|commit|tree|tag) ([0-9a-f]{40,64})', line)
            if match is None:
                problems.append({'file': '.git', 'kind': 'unexpected-fsck-output'})
                continue
            kind, oid = match.groups()
            # Normal staging can leave valid blobs unreferenced. Inspect them,
            # never prune them or confuse their presence with Git corruption.
            body = git('cat-file', kind, oid)
            if kind in ('blob', 'commit', 'tag'):
                if body.startswith(b'\x1f\x8b'): body = gzip.decompress(body)
                check('unreferenced:' + oid, body)
            unreferenced.append({'oid': oid, 'type': kind, 'bytes': len(body)})
    checked_archives = []
    for path in archives:
        if path.name.endswith(('.whl', '.zip')):
            with zipfile.ZipFile(path) as archive:
                assert archive.testzip() is None
                for name in archive.namelist():
                    if not name.endswith('/'):
                        check(path.name + ':' + name, archive.read(name))
        else:
            with tarfile.open(path) as archive:
                for member in archive.getmembers():
                    if member.isfile():
                        check(path.name + ':' + member.name, archive.extractfile(member).read())
        checked_archives.append({'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    return {'tracked_files': len(tracked), 'historical_blobs': blobs,
            'historical_commits': commits, 'unreferenced_objects_checked': unreferenced, 'local_refs': git('for-each-ref', '--format=%(refname)').decode().splitlines(),
            'archives': checked_archives, 'findings': problems, 'passed': not problems,
            'scope': 'Pattern-based technical scan of named local files/refs/archives; not exhaustive secret detection or remote GitHub erasure.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', action='store_true')
    parser.add_argument('--archive', action='append', type=Path, default=[])
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = audit(args.history, args.archive)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['passed'] else 1)
