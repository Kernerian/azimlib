"""Audit wheel/sdist content, RECORD, optional dependencies and asset provenance.

No package import or network access. Output goes outside archives to avoid
self-referential archive hashes. This does not publish/reserve a PyPI name.
"""
import argparse
import ast
import base64
import csv
from email.parser import BytesParser
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import tarfile
import zipfile
try:import tomllib
except ImportError:import tomli as tomllib

from packaging.licenses import canonicalize_license_expression
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT=Path(__file__).resolve().parents[1]
FORBIDDEN={'matplotlib','cartopy','geopandas','shapely','pyproj','folium','geographiclib','rasterio','fiona'}


def sha(data):return hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel',type=Path,required=True);parser.add_argument('--sdist',type=Path,required=True)
    parser.add_argument('--source-zip',type=Path);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();config=tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))['project']
    license_files=sorted({p.relative_to(ROOT).as_posix() for pattern in config['license-files'] for p in ROOT.glob(pattern) if p.is_file()})
    assert license_files and all(list(ROOT.glob(pattern)) for pattern in config['license-files'])
    runtime=ROOT/'src/azimlib';expected={p.relative_to(ROOT/'src').as_posix():p for p in runtime.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    imports=[]
    for path in runtime.rglob('*.py'):
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8'))):
            modules=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or ''] if isinstance(node,ast.ImportFrom) and not node.level else []
            assert not any(m.split('.')[0] in FORBIDDEN for m in modules),path
            imports.extend(modules)
    assert config['dependencies']==[]
    with zipfile.ZipFile(args.wheel) as archive:
        assert archive.testzip() is None
        names=archive.namelist();actual={n for n in names if n.startswith('azimlib/') and not n.endswith('/')}
        assert actual==set(expected),(actual-set(expected),set(expected)-actual)
        for name,path in expected.items():assert archive.read(name)==path.read_bytes(),name
        meta_names=[n for n in names if n.endswith('.dist-info/METADATA')];assert len(meta_names)==1
        metadata=BytesParser().parsebytes(archive.read(meta_names[0]))
        assert canonicalize_name(metadata['Name'])==canonicalize_name(config['name'])=='azimlib'
        assert metadata['Version']==config['version'] and metadata['Requires-Python']==config['requires-python']
        assert metadata['License-Expression']==canonicalize_license_expression(config['license'])
        assert 'BSD-3-Clause' in metadata['License-Expression'] and 'MIT' not in metadata['License-Expression']
        dependencies=[Requirement(x) for x in metadata.get_all('Requires-Dist',[])]
        assert all(r.marker is not None and 'extra' in str(r.marker) for r in dependencies)
        assert not any(canonicalize_name(r.name) in FORBIDDEN for r in dependencies)
        assert set(metadata.get_all('Provides-Extra',[]))==set(config['optional-dependencies'])
        for extra,requirements in config['optional-dependencies'].items():
            expected_requirements=[Requirement(r) for r in requirements]
            for version in ('3.10','3.11','3.14'):
                environment={'extra':extra,'python_version':version,'python_full_version':version+'.0'}
                actual={(canonicalize_name(r.name),str(r.specifier)) for r in dependencies if r.marker.evaluate(environment)}
                declared={(canonicalize_name(r.name),str(r.specifier)) for r in expected_requirements if r.marker is None or r.marker.evaluate(environment)}
                assert actual==declared,(extra,version,actual,declared)
        info=meta_names[0].rsplit('/',1)[0]
        assert set(metadata.get_all('License-File',[]))==set(license_files)
        for file in license_files:
            assert archive.read(info+'/licenses/'+file)==(ROOT/file).read_bytes(),file
        assert b'Copyright (c) 2026 Kernerian' in archive.read(info+'/licenses/LICENSE')
        records=list(csv.reader(io.StringIO(archive.read(info+'/RECORD').decode())))
        assert {r[0] for r in records}=={n for n in names if not n.endswith('/')}
        for name,digest,size in records:
            data=archive.read(name)
            if digest:
                assert digest=='sha256='+base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('='),name
                assert int(size)==len(data),name
            else:assert name==info+'/RECORD' and size=='',name
    data_manifest=json.loads((runtime/'data/manifest.json').read_text(encoding='utf-8'))
    for layer in data_manifest['layers'].values():
        path=runtime/'data'/layer['filename'];assert sha(path.read_bytes())==layer['sha256']
        decoded=json.loads(gzip.decompress(path.read_bytes()));assert len(decoded['features'])==layer['features']
    fonts=json.loads((ROOT/'docs/fonts-upstream.json').read_text(encoding='utf-8'))
    for font in fonts['files']:assert sha((runtime/'fonts'/font['file']).read_bytes())==font['sha256'] and font['identical']
    icons=json.loads((runtime/'assets/icons/manifest.json').read_text(encoding='utf-8'))
    assert icons['source']=='Original Azimlib geometry' and icons['license']=='BSD-3-Clause'
    for file,digest in icons['files_sha256'].items():assert sha((runtime/'assets/icons'/file).read_bytes())==digest
    blocked=('__pycache__','.venv','site-packages','.git','work','dist','build','.ci-results')
    def check_entries(entries):
        for name in entries:
            parts=Path(name).parts
            assert not any(p in blocked or p.endswith('.egg-info') and p!='azimlib.egg-info' for p in parts),name
            assert not any(p in FORBIDDEN for p in parts),name
            assert not name.endswith(('.shp','.shx','.dbf','.pyc')),name
            assert 'ibge-sp-original-2024.geojson' not in name and 'SP_Municipios_2024.zip' not in name,name
    with tarfile.open(args.sdist) as archive:
        members=archive.getmembers();assert all(m.isfile() or m.isdir() for m in members),'Symlinks/unexpected archive entries'
        entries={m.name.split('/',1)[1]:m for m in members if m.isfile()}
        check_entries(entries)
        for name in ('PKG-INFO','src/azimlib.egg-info/PKG-INFO'):
            package_metadata=BytesParser().parsebytes(archive.extractfile(entries[name]).read())
            for field in ('Name','Version','Requires-Python','License-Expression','Author','License-File','Provides-Extra','Requires-Dist'):
                assert package_metadata.get_all(field,[])==metadata.get_all(field,[]),(name,field)
        for name,path in expected.items():assert archive.extractfile(entries['src/'+name]).read()==path.read_bytes(),name
        # Check every deliverable file, not just the runtime or selected old docs.
        source={p.relative_to(ROOT).as_posix():p for directory in ('docs','tests','tools','examples') for p in (ROOT/directory).rglob('*')
                if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py','.md','.json','.js','.mplstyle')}
        for name,path in source.items():assert archive.extractfile(entries[name]).read()==path.read_bytes(),name
        for name in ('pyproject.toml','README.md','CHANGELOG.md','MANIFEST.in','.gitattributes','.github/workflows/tests.yml',*license_files):
            assert archive.extractfile(entries[name]).read()==(ROOT/name).read_bytes(),name
    if args.source_zip:
        with zipfile.ZipFile(args.source_zip) as archive:
            assert archive.testzip() is None
            entries=archive.namelist();check_entries(n.split('/',1)[1] for n in entries)
            for name,path in {**source,**{'src/'+n:p for n,p in expected.items()}}.items():
                assert archive.read('azimlib/'+name)==path.read_bytes(),name
            for name in ('pyproject.toml','LICENSE','THIRD_PARTY_LICENSES.md',*license_files):
                assert archive.read('azimlib/'+name)==(ROOT/name).read_bytes(),name
    report=dict(schema_version=1,name=config['name'],normalized_name=canonicalize_name(config['name']),version=config['version'],
        license_expression=metadata['License-Expression'],license_files=license_files,mandatory_dependencies=[],optional_dependencies=config['optional-dependencies'],
        wheel_record_entries=len(records),runtime_files_exact=len(expected),source_files_exact=len(source),
        natural_earth_layers=len(data_manifest['layers']),upstream_fonts_exact=len(fonts['files']),own_icons=len(icons['files_sha256']),
        forbidden_runtime_imports=False,external_original_ibge_data_excluded=True,
        archives=[dict(file=p.name,bytes=p.stat().st_size,sha256=sha(p.read_bytes())) for p in (args.wheel,args.sdist,args.source_zip) if p],
        scope='Content/metadata/RECORD/provenance audit of the named local artifacts. Does not validate a PyPI upload, trademarks, remote CI or physical GUI input.')
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='optional_dependencies'},indent=2))


if __name__=='__main__':main()
