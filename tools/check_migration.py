"""Execute the original self-contained migration examples in a private output folder."""
import argparse,hashlib,json,os,re,sys
from pathlib import Path
import azimlib as azl
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=True)
    source=ROOT/'docs/migration-0.3.md';codes=re.findall(r'^```python\s*\n(.*?)^```',source.read_text('utf8'),re.M|re.S);assert len(codes)==3
    previous=Path.cwd()
    try:
        os.chdir(a.output)
        for i,code in enumerate(codes):exec(compile(code,f'migration-0.3.md:{i+1}','exec'),{})
        outputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(a.output.iterdir()) if p.suffix in ('.svg','.pdf')}
        assert set(outputs)=={'migration-map.svg','migration-colors.svg','migration-atlas.pdf'}
        assert b'/Count 2' in (a.output/'migration-atlas.pdf').read_bytes()
    finally:azl.close('all');os.chdir(previous)
    forbidden={'matplotlib','cartopy','shapely','pyproj','geopandas','folium','rasterio','fiona'}
    assert not any(n.split('.')[0] in forbidden for n in sys.modules)
    report=dict(passed=True,version=azl.__version__,snippets=len(codes),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),files=outputs,forbidden_imports=[])
    (a.output/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
