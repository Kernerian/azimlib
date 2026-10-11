"""Explicit HTTPS acquisition of a pinned optional OSM extract; no import download."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import urlsplit
from urllib.request import urlopen

# Complete SPDX Markdown ODbL-1.0 text already audited with the optional sample.
# This is a content check, not an inferred license from a URL or filename.
_ODBL_SHA256 = '77d2692c3d64efdd4db18dce2407699baf62930e2b50d6e5ed90b48acf16b7c1'


def acquire(url, destination, *, sha256, version, license_file,
            max_bytes=512 * 1024 * 1024, reserve_free_bytes=15_000_000_000):
    """Create a new local catalog only after a complete verified download.

    OSM tags/source files may contain personal data: acquisition is not a
    publication/privacy approval. Retain the ODbL and attribution when sharing.
    """
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('Use an explicit public HTTPS dataset URL without credentials/query/fragment')
    if not re.fullmatch('[0-9a-f]{64}', sha256) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]*', version):
        raise ValueError('Require a lowercase SHA256 and a safe explicit dataset version')
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0 or not isinstance(reserve_free_bytes, int) or reserve_free_bytes < 0:
        raise ValueError('Invalid acquisition storage budget')
    notice = Path(license_file).read_bytes()
    if len(notice) > 1024 * 1024 or hashlib.sha256(notice.replace(b'\r\n', b'\n')).hexdigest() != _ODBL_SHA256:
        raise ValueError('Supply the complete audited SPDX ODbL-1.0 text; see docs/osm-pbf.md')
    destination = Path(destination)
    if destination.exists():
        raise ValueError('Acquisition requires a new destination; existing data is never replaced')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='azimlib-acquire-', dir=destination.parent) as temporary:
        folder = Path(temporary); digest = hashlib.sha256(); count = 0
        with urlopen(url, timeout=60) as response, (folder / 'data.osm.pbf').open('wb') as output:
            if urlsplit(response.geturl()).scheme != 'https':
                raise ValueError('Refusing a redirect to an insecure URL')
            declared = response.headers.get('Content-Length')
            if declared is not None and (int(declared) < 0 or int(declared) > max_bytes):
                raise ValueError('Download exceeds explicit byte budget')
            while True:
                if shutil.disk_usage(folder).free < reserve_free_bytes + 2 * 1024 * 1024:
                    raise ValueError('Download would consume reserved free disk space')
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                count += len(chunk)
                if count > max_bytes:
                    raise ValueError('Download exceeds explicit byte budget')
                digest.update(chunk); output.write(chunk)
            if declared is not None and count != int(declared):
                raise ValueError('Truncated download')
        if digest.hexdigest() != sha256:
            raise ValueError('Downloaded OSM PBF SHA256 mismatch')
        (folder / 'LICENSE.txt').write_bytes(notice)
        entry = dict(id='osm-extract', version=version, format='osm-pbf', file='data.osm.pbf',
                     crs='EPSG:4326', license='ODbL-1.0', copyright='OpenStreetMap contributors',
                     source=url, attribution='© OpenStreetMap contributors — https://www.openstreetmap.org/copyright',
                     license_file='LICENSE.txt', files={'data.osm.pbf': sha256, 'LICENSE.txt': hashlib.sha256(notice).hexdigest()})
        (folder / 'catalog.json').write_text(json.dumps(dict(schema_version=1, datasets=[entry]), indent=2) + '\n', encoding='utf8')
        (folder / 'README.md').write_text(
            '# Optional OpenStreetMap extract\n\n© OpenStreetMap contributors. Data: ODbL 1.0; see LICENSE.txt.\n'
            'Source and pinned version/SHA256: catalog.json. This database is not Azimlib code.\n'
            'Review tags and the source file for personal data before any redistribution.\n'
            'https://www.openstreetmap.org/copyright\n', encoding='utf8')
        # Same-filesystem directory rename publishes only a completed local catalog.
        folder.rename(destination)
    return dict(passed=True, bytes=count, sha256=sha256, version=version, license='ODbL-1.0')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--license-file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--max-bytes', type=int, default=512 * 1024 * 1024)
    parser.add_argument('--reserve-free-bytes', type=int, default=15_000_000_000)
    args = parser.parse_args(argv)
    print(json.dumps(acquire(args.url, args.output, sha256=args.sha256, version=args.version,
                             license_file=args.license_file, max_bytes=args.max_bytes,
                             reserve_free_bytes=args.reserve_free_bytes), indent=2))


if __name__ == '__main__':
    main()
