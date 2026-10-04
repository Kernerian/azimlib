"""Create a small repository-root archive for CI, without generated galleries.

The full development ZIP remains the offline gallery distribution. This bundle
contains original source/tests/tools/docs and .github at the repository root;
it never includes environments, downloaded inputs, credentials or built wheels.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parents[1]
DIRS={'src','tests','tools','docs','examples','.github','licenses'}
FILES={'pyproject.toml','MANIFEST.in','README.md','CHANGELOG.md','LICENSE','NOTICE_COLORMAPS','THIRD_PARTY_LICENSES.md','.gitignore','.gitattributes'}
SKIP={'__pycache__','.git','.pytest_cache','site-packages','build','dist','.ci-results'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.parent.mkdir(parents=True,exist_ok=True);entries={}
    with zipfile.ZipFile(args.output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path in sorted(ROOT.rglob('*')):
            if not path.is_file():continue
            relative=path.relative_to(ROOT)
            if any(part in SKIP or part.endswith('.egg-info') for part in relative.parts):continue
            if not (relative.parts[0] in DIRS or relative.as_posix() in FILES):continue
            assert not relative.name.endswith(('.shp','.shx','.dbf','.pyc'))
            data=path.read_bytes();entries[relative.as_posix()]=hashlib.sha256(data).hexdigest()
            archive.writestr(relative.as_posix(),data)
    with zipfile.ZipFile(args.output) as archive:
        assert archive.testzip() is None
        assert '.github/workflows/tests.yml' in archive.namelist() and 'pyproject.toml' in archive.namelist()
        assert 'THIRD_PARTY_LICENSES.md' in archive.namelist() and 'licenses/LicenseRef-ColorBrewer.txt' in archive.namelist()
        assert 'src/azimlib/__init__.py' in archive.namelist() and not any(n.startswith('gallery/') for n in archive.namelist())
    report=dict(schema_version=1,archive=args.output.name,files=len(entries),bytes=args.output.stat().st_size,
        sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),files_sha256=entries,
        scope='Source for a new repository, no GitHub upload performed. Root contains .github/pyproject.toml. Generated gallery omitted intentionally; examples can regenerate previews, full offline gallery is in the separate development ZIP. No remote CI claim.')
    args.output.with_suffix('.manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'{len(entries)} files; {args.output.stat().st_size/2**20:.2f} MiB; repository-root archive ready.')


if __name__=='__main__':main()
