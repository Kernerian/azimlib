"""Validate installed exports and retain original synthetic gallery provenance."""
from pathlib import Path
import hashlib,json,re,shutil,struct,sys,xml.etree.ElementTree as ET
import azimlib as azl
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,required=True,help='Parent of gallery-installed and composition-installed exports')
args=parser.parse_args()
R=Path(__file__).resolve().parents[1]
OUT=args.output.resolve();OUT.mkdir(parents=True,exist_ok=True)
runtime=Path(azl.__file__).resolve().parent
assert runtime.is_relative_to(Path(sys.prefix).resolve())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
exports=[];files=[]
for name in ('scientific-atlas','color-raster','weighted-flows'):
    for extension in ('png','svg','html'):
        p=OUT/'gallery-installed'/f'{name}.{extension}';data=p.read_bytes()
        if extension=='png':
            assert data[:8]==b'\x89PNG\r\n\x1a\n'
            pixels=struct.unpack('>II',data[16:24]);assert min(pixels)>400
            shutil.copyfile(p,R/'docs/_static/scientific'/p.name)
            files.append(dict(file=p.name,sha256=sha(p),pixels=pixels,generator='examples/scientific_atlas.py',generator_sha256=sha(R/'examples/scientific_atlas.py')))
        elif extension=='svg':
            ET.fromstring(data);assert b'<script' not in data and not re.search(rb'(?<![A-Za-z])(?:nan|inf)(?![A-Za-z])',data,re.I)
        else:assert b'Figure navigation' in data
        exports.append(dict(file=p.name,bytes=len(data),sha256=sha(p)))
manifest=dict(source='Own Azimlib renderer; original synthetic terrain/pixels/points/flows; Natural Earth public-domain background boundaries in weighted-flows',original_code_license='BSD-3-Clause',copyright='Copyright (c) 2026 Kernerian',files=files)
(R/'docs/_static/scientific/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8',newline='\n')
atlas=OUT/'composition-installed/composition-atlas.png'
shutil.copyfile(atlas,R/'docs/_static/composition'/atlas.name)
path=R/'docs/_static/composition/manifest.json';manifest=json.loads(path.read_text(encoding='utf8'))
entry=next(f for f in manifest['files'] if f['file']==atlas.name);entry['sha256']=sha(atlas)
path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8',newline='\n')
for extension in ('png','svg','html'):
    p=OUT/'composition-installed'/f'composition-atlas.{extension}'
    exports.append(dict(file=p.name,bytes=p.stat().st_size,sha256=sha(p)))
from azimlib.scientific import histogram,area
from azimlib.tri import _incircle
import random
cases=[]
r=azl.GeoRaster([[1,3,5],[4,6,8],[7,9,11]],(1,0,0,0,1,0))
for i in range(21):
    for j in range(21):
        x=.5+i/10;y=.5+j/10;error=abs(r.sample(x,y,method='bilinear')-(2*x+3*y-1.5));assert error<1e-12
        cases.append(dict(kind='analytic-affine-bilinear',error=error))
for smoothing in (0,.5,2,5):
    for mode in ('count','probability','density'):
        x,y,z=histogram([0,.5,1,2],[0,.5,1,2],weights=[1,2,4,100],bins=(3,4),extent=(0,1,0,1),smoothing=smoothing,normalization=mode)
        error=abs(sum(map(sum,z))*(1/12 if mode=='density' else 1)-(7 if mode=='count' else 1));assert error<1e-12
        cases.append(dict(kind='weighted-mass-conservation',error=error))
rng=random.Random(503);x=[rng.uniform(-2,2) for _ in range(30)];y=[rng.uniform(-2,2) for _ in x];tri=azl.Triangulation(x,y)
interpolation=azl.LinearTriInterpolator(tri,[2*a+3*b+1 for a,b in zip(x,y)])
for triangle in tri.triangles:
    cx=sum(x[i]/3 for i in triangle);cy=sum(y[i]/3 for i in triangle)
    error=abs(interpolation(cx,cy)-(2*cx+3*cy+1));assert error<1e-11
    cases.append(dict(kind='barycentric-analytic-plane',error=error))
fig,ax=azl.subplots();z=[[1]*5 for _ in range(5)];z[2][2]=None
b=ax.contourf(range(5),range(5),z,levels=[0,2]);assert len(b.data[0].geometry.coordinates)==2
assert sum(area(list(r)) for r in b.data[0].geometry.coordinates)==12;azl.close(fig)
assert not any(n.split('.')[0] in ('matplotlib','cartopy','shapely','geopandas','pyproj','contourpy','scipy') for n in sys.modules)
report=dict(passed=True,version=azl.__version__,analytic_cases=len(cases),max_error=max(c['error'] for c in cases),inner_ring_area=12,exports=exports,
    scope='Installed own analytic plane/mass/interpolation fixtures and structural PNG/SVG/HTML exports; visual PNG previews inspected. Not an external oracle, benchmark at maximum limits, human desktop approval or new remote CI.')
(OUT/'scientific-evidence.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
(R/'docs/scientific-evidence-0.3.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps({k:v for k,v in report.items() if k!='exports'},indent=2))
