"""Audit original toolbar artwork in source and optional distribution archives."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def audit(reference=None, wheel=None, sdist=None, source_zip=None):
    runtime=ROOT/'src/azimlib'
    manifest=json.loads((runtime/'assets/icons/manifest.json').read_text(encoding='utf-8'))
    assert manifest['source']=='Original Azimlib geometry' and manifest['license']=='BSD-3-Clause'
    assert len(manifest['files_sha256'])==21
    digest=lambda data:hashlib.sha256(data).hexdigest()
    assert manifest['geometry_sha256']==digest((runtime/'_toolbar_icons.py').read_bytes())
    assert manifest['generator_sha256']==digest((ROOT/'tools/build_toolbar_icons.py').read_bytes())
    expected={'azimlib/assets/icons/'+name:value for name,value in manifest['files_sha256'].items()}
    for name,value in expected.items():assert digest((ROOT/'src'/name).read_bytes())==value,name
    assert 'LicenseRef-MatplotlibIcons' not in (ROOT/'pyproject.toml').read_text(encoding='utf-8')
    removed=('NOTICE_ICONS','LICENSE_MATPLOTLIB_ICONS')
    assert all(not (ROOT/name).exists() for name in removed)
    foreign=set()
    if reference:
        foreign={digest(path.read_bytes()) for path in reference.iterdir() if path.suffix in ('.svg','.png')}
        assert not set(expected.values())&foreign,'Artwork must not match a reference file byte for byte'
    import base64
    pages=0
    for page in (ROOT/'gallery').glob('*.html'):
        for encoded in re.findall(r'<img src="data:image/svg\+xml;base64,([A-Za-z0-9+/=]+)"',page.read_text(encoding='utf-8')):
            data=base64.b64decode(encoded,validate=True)
            assert digest(data) not in foreign,page.name
            assert b'Azimlib' in data and b'Created with matplotlib' not in data,page.name
            pages+=1
    checked=[]
    def check(entries,read,label):
        for name,value in expected.items():
            matches=[key for key in entries if key.endswith('/'+name) or key==name]
            assert len(matches)==1,(label,name,matches)
            assert digest(read(matches[0]))==value,(label,name)
        assert not any(any(token.lower() in name.lower() for token in removed) for name in entries),label
        for name in entries:
            if name.endswith(('.svg','.png')) and '/assets/icons/' in name:
                assert digest(read(name)) not in foreign,(label,name)
            if name.endswith(('METADATA','PKG-INFO')):
                assert b'LicenseRef-MatplotlibIcons' not in read(name),(label,name)
        checked.append(label)
    for path,label in ((wheel,'wheel'),(source_zip,'source_zip')):
        if path:
            with zipfile.ZipFile(path) as archive:
                assert archive.testzip() is None
                check([name for name in archive.namelist() if not name.endswith('/')],archive.read,label)
    if sdist:
        with tarfile.open(sdist) as archive:
            entries={entry.name:entry for entry in archive.getmembers() if entry.isfile()}
            check(entries,lambda name:archive.extractfile(entries[name]).read(),'sdist')
    report=dict(original_assets=21,license='BSD-3-Clause',geometry_sha256=manifest['geometry_sha256'],
                compared_reference_hashes=len(foreign),embedded_own_icons=pages,archives=checked,
                foreign_toolbar_assets_absent=True)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('reference-icons','wheel','sdist','source-zip','report'):parser.add_argument('--'+name,type=Path)
    args=parser.parse_args()
    report=audit(args.reference_icons,args.wheel,args.sdist,args.source_zip)
    if args.report:args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))
