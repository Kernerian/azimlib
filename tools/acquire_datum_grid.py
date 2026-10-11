"""Explicit acquisition of pinned, licensed optional LINZ grids. Never implicit."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from urllib.parse import urlsplit
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def models():
    return deepcopy(json.loads((ROOT/'src/azimlib/data/optional-grids.json').read_text('utf8'))['datasets'])


def _https(url):
    parts = urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError('Require public HTTPS without credentials/query/fragment')


def acquire(identifier, destination, *, max_bytes=128*1024*1024,
            max_storage_bytes=20_000_000_000, reserve_free_bytes=15_000_000_000):
    """New directory only, complete data/notice hashes and atomic catalog delivery.

    Download sizes are fixed by the reviewed preset. All generated payloads,
    notices and metadata count against the storage budget. On any failure the
    incomplete temporary directory is removed and no catalog is delivered.
    """
    for value in (max_bytes,max_storage_bytes,reserve_free_bytes):
        if isinstance(value,bool) or not isinstance(value,int) or value < 0:
            raise ValueError('Require nonnegative integer storage budgets')
    if max_bytes <= 0 or max_storage_bytes <= 0: raise ValueError('Byte budgets must be positive')
    entries = [m for m in models() if m['id'] == identifier]
    if len(entries) != 1: raise KeyError('Unknown pinned official grid model')
    entry = entries[0]; destination = Path(destination)
    if destination.exists(): raise ValueError('Require new destination; never overwrite a grid catalog')
    license_bytes = (ROOT/'licenses/CC-BY-4.0.txt').read_bytes()
    if hashlib.sha256(license_bytes).hexdigest() != entry['files']['CC-BY-4.0.txt']:
        raise ValueError('Complete bundled CC BY 4.0 license hash mismatch')
    required = entry['download_bytes']+len(license_bytes)+64*1024
    if entry['download_bytes'] > max_bytes or required > max_storage_bytes:
        raise ValueError('Pinned grid exceeds explicit byte/storage budget')
    _https(entry['source'])
    destination.parent.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(destination.parent).free < reserve_free_bytes+required:
        raise ValueError('Grid acquisition would consume reserved free disk space')
    with tempfile.TemporaryDirectory(prefix='azimlib-grid-',dir=destination.parent) as tmp:
        folder = Path(tmp); used = 0
        def download(url, name, limit, expected_size=None):
            nonlocal used
            _https(url); digest = hashlib.sha256(); count = 0
            with urlopen(url,timeout=60) as response, (folder/name).open('wb') as stream:
                _https(response.geturl())
                declared = response.headers.get('Content-Length')
                if declared is not None and not 0 <= int(declared) <= limit:
                    raise ValueError('Download declared size exceeds limit')
                while True:
                    chunk = response.read(min(1024*1024,limit-count+1))
                    if not chunk: break
                    count += len(chunk); used += len(chunk)
                    if count > limit or used > max_storage_bytes or shutil.disk_usage(folder).free-len(chunk) < reserve_free_bytes:
                        raise ValueError('Download would exceed explicit resource budget')
                    digest.update(chunk); stream.write(chunk)
            if declared is not None and count != int(declared) or expected_size is not None and count != expected_size:
                raise ValueError('Grid download truncated or size mismatch')
            if digest.hexdigest() != entry['files'][name]: raise ValueError('Grid/notice SHA256 mismatch')
        download(entry['source'],entry['file'],max_bytes,entry['download_bytes'])
        notice = 'LICENCE.proj-datumgrid-nz'
        download(entry['source'].rsplit('/',1)[0]+'/'+notice,notice,4096)
        (folder/'CC-BY-4.0.txt').write_bytes(license_bytes)
        (folder/'catalog.json').write_text(json.dumps(dict(schema_version=1,datasets=[entry]),indent=2)+'\n',encoding='utf8')
        (folder/'README.md').write_text('# Optional datum grid\n\n'+entry['attribution']+'\n\nData retain CC BY 4.0, independently of the Azimlib BSD license.\n',encoding='utf8')
        if sum(p.stat().st_size for p in folder.iterdir()) > max_storage_bytes:
            raise ValueError('Final catalog exceeds storage budget')
        import sys
        sys.path.insert(0,str(ROOT/'src'))
        from azimlib import DatasetCatalog
        DatasetCatalog(folder/'catalog.json').grid_operation(identifier,version=entry['version'])
        # Rename within the same volume; no partial catalog is exposed.
        folder.rename(destination)
    return dict(passed=True,id=identifier,version=entry['version'],sha256=entry['files'][entry['file']],
                bytes=entry['download_bytes'],license=entry['license'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model',required=True,choices=[m['id'] for m in models()])
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--max-bytes',type=int,default=128*1024*1024)
    parser.add_argument('--max-storage-bytes',type=int,default=20_000_000_000)
    parser.add_argument('--reserve-free-bytes',type=int,default=15_000_000_000)
    args = parser.parse_args(argv)
    print(json.dumps(acquire(args.model,args.output,max_bytes=args.max_bytes,
                             max_storage_bytes=args.max_storage_bytes,reserve_free_bytes=args.reserve_free_bytes),indent=2))


if __name__ == '__main__': main()
