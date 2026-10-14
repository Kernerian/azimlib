"""Explicit, hash-pinned acquisition of optional Noto validation fonts.

This tool does not run during imports, installation, rendering or tests.
Fonts and notices are placed in a new destination and are never packaged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import urllib.request

ROOT=Path(__file__).resolve().parents[1]


def acquire(output):
    records=json.loads((ROOT/'src/azimlib/data/optional-fonts.json').read_text('utf8'))['fonts']
    output=Path(output)
    if output.exists():raise FileExistsError('Font acquisition requires a new output directory')
    output.parent.mkdir(parents=True,exist_ok=True)
    total=sum(r['size']+1024*1024 for r in records)
    if total>128*1024*1024 or shutil.disk_usage(output.parent).free-total<15*1024**3:
        raise OSError('Optional fonts exceed resource budget or 15 GiB system reserve')
    def fetch(url,limit,expected):
        request=urllib.request.Request(url,headers={'User-Agent':'Azimlib-optional-font-acquisition'})
        with urllib.request.urlopen(request,timeout=60) as response:raw=response.read(limit+1)
        if len(raw)>limit or hashlib.sha256(raw).hexdigest()!=expected:
            raise ValueError('Optional font/notice size or SHA-256 mismatch')
        return raw
    with tempfile.TemporaryDirectory(prefix='azimlib-fonts-',dir=output.parent) as folder:
        temporary=Path(folder)
        for record in records:
            name=record['filename']
            raw=fetch(record['url'],record['size'],record['sha256'])
            if len(raw)!=record['size']:raise ValueError('Unexpected font size')
            license_raw=fetch(record['license_url'],1024*1024,record['license_sha256'])
            (temporary/name).write_bytes(raw)
            (temporary/(name+'.license.txt')).write_bytes(license_raw)
        (temporary/'manifest.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf8',newline='\n')
        # Same-volume rename commits the complete acquisition; errors clean temps.
        temporary.rename(output)
    return output


def register_acquired(directory):
    """Verify bytes and all provenance against the shipped allowlist, then register."""
    from azimlib.text_engine import register_font
    directory=Path(directory)
    expected=json.loads((ROOT/'src/azimlib/data/optional-fonts.json').read_text('utf8'))['fonts']
    records=json.loads((directory/'manifest.json').read_text('utf8'))
    if records!=expected:raise ValueError('Font manifest differs from the pinned allowlist')
    result=[]
    for record in records:
        font=directory/record['filename'];notice=directory/(record['filename']+'.license.txt')
        if font.stat().st_size!=record['size'] or hashlib.sha256(font.read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('Optional font hash mismatch')
        license_raw=notice.read_bytes()
        if hashlib.sha256(license_raw).hexdigest()!=record['license_sha256']:raise ValueError('Font license hash mismatch')
        result.append(register_font(font,family=record['family'],source=record['source'],license_id=record['license_id'],
                                    license_text=license_raw.decode('utf8'),allow_outlines=True))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();acquire(args.output)
    print('Optional Noto fonts and complete notices acquired and SHA-256 verified.')
