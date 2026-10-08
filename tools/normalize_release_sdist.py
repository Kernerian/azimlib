"""Canonicalize sdist transport headers without changing any payload bytes."""
import argparse
import gzip
import hashlib
import io
import json
import tarfile
from pathlib import Path


def normalize(path, epoch):
    with tarfile.open(path, 'r:gz') as archive:
        entries = {}
        for member in archive.getmembers():
            if not (member.isfile() or member.isdir()):
                raise ValueError('Only regular files/directories are supported')
            if member.name in entries:
                raise ValueError('Duplicate archive member')
            parts = Path(member.name).parts
            if member.name.startswith(('/', '\\')) or '..' in parts:
                raise ValueError('Unsafe archive path')
            entries[member.name] = (member.isdir(), archive.extractfile(member).read() if member.isfile() else b'')
    output = io.BytesIO()
    with gzip.GzipFile(filename='', fileobj=output, mode='wb', mtime=epoch) as compressed:
        with tarfile.open(fileobj=compressed, mode='w', format=tarfile.PAX_FORMAT) as archive:
            for name, (directory, data) in sorted(entries.items()):
                info = tarfile.TarInfo(name)
                info.type = tarfile.DIRTYPE if directory else tarfile.REGTYPE
                info.mode = 0o755 if directory else 0o644
                info.mtime = epoch
                info.size = 0 if directory else len(data)
                archive.addfile(info, None if directory else io.BytesIO(data))
    canonical = output.getvalue()
    with tarfile.open(fileobj=io.BytesIO(canonical), mode='r:gz') as archive:
        actual = {member.name: (member.isdir(), archive.extractfile(member).read() if member.isfile() else b'') for member in archive}
    if actual != entries:
        raise RuntimeError('Normalization changed a file payload')
    path.write_bytes(canonical)
    return {'file': path.name, 'sha256': hashlib.sha256(canonical).hexdigest(), 'members': len(entries),
            'source_date_epoch': epoch, 'payloads_preserved': True,
            'policy': 'Sorted members, fixed timestamps/ownership/modes, empty gzip filename; payload bytes unchanged'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sdist', type=Path, required=True)
    parser.add_argument('--epoch', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = normalize(args.sdist, args.epoch)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8', newline='\n')
    print(json.dumps(report))
