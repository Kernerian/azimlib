"""Unpublished installed 0.4 packet; generated output never grants human acceptance."""
import argparse,hashlib,html,importlib.util,json,os,platform,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from publication_privacy import findings
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--native',action='store_true');a=p.parse_args()
 import azimlib as azl
 runtime=Path(azl.__file__).resolve().parent
 if not runtime.is_relative_to(Path(sys.prefix).resolve()):raise RuntimeError('Review requires an installed package')
 if azl.__version__!='0.4.0':raise RuntimeError('Wrong candidate version')
 for source in (ROOT/'src/azimlib').rglob('*'):
  if source.is_file() and '__pycache__' not in source.parts:
   if source.read_bytes()!=(runtime/source.relative_to(ROOT/'src/azimlib')).read_bytes():raise RuntimeError('Installed candidate differs from source')
 output=a.output.resolve();output.mkdir(parents=True,exist_ok=False)
 from validate_integration_040 import validate
 validate(output/'integration',installed=True,native=a.native)
 from prepare_visual_review import make
 from validate_integration_040 import load
 rows=[]
 figs=[(name,make(name,azl)) for name in ('political','physical','projections','specimens')]
 figs.append(('eclipse-experimental',load('lighting_maps').make_eclipse_map()[0]))
 spec=importlib.util.spec_from_file_location('original_pbf_fixture',ROOT/'tests/pbf_fixture.py');fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
 raw=fixture.header()+fixture.primitive(fixture.scene())
 features=azl.read_osm_pbf(raw);fig,ax=azl.subplots(figsize=(6,4))
 ax.geojson(features,facecolor='#cad9df',edgecolor='#334f60',linewidth=.8)
 ax.set_title('Original tiny PBF fixture · not planet-scale evidence',fontsize=10)
 figs.append(('pbf-original-fixture',fig))
 try:
  for name,fig in figs:
   for kind in ('png','svg','pdf'):fig.savefig(output/f'{name}.{kind}',dpi=100)
   rows.append(f'<section><h2>{name}</h2><a href="{name}.png"><img width="600" src="{name}.png"></a><object type="image/svg+xml" data="{name}.svg" width="600" height="400"></object><p><a href="{name}.pdf">PDF</a></p></section>')
 finally:azl.close('all')
 (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Azimlib 0.4.0 native review pending</title><h1>0.4.0 — human review pending</h1><p>PNG left, SVG right. Compare identically named files across Windows, Linux and macOS. No automatic human approval. No certified eclipse forecast or physical GPU budget is claimed.</p><p><a href="integration/index.html">City, native Tk/Qt, route, terrain, volumes, Sun and Moon</a></p><p>Inspect text/TeX packets from the same SHA separately: complex-text and real-tex artifacts. Synthetic PBF here supplements regional real-data tests, not planetary validation. GPU/fallback and Mesa packets are functional evidence only.</p>'+''.join(rows),encoding='utf8')
 (output/'README.md').write_text('# Native visual review — approval pending\n\nOpen index.html. Compare PNG/SVG/PDF and the same filenames across the three systems. Inspect title/tick spacing, marker aspect and legend, line weights, projection horizons, PBF geometry, route clipping, 3D depth, volume opacity, solar terminator, Moon orientation, synthetic eclipse boundaries and Tk/Qt canvas/toolbar. Review complex-text and real-tex artifacts at the identical SHA. Still captures do not establish physical input latency or scientific eclipse completeness. Natural Earth, DejaVu and optional dependencies retain their source notices.\n',encoding='utf8')
 for path in output.rglob('*'):
  if path.is_file() and findings(path.read_bytes()):raise RuntimeError('Review packet privacy failure: '+path.relative_to(output).as_posix())
 manifest=dict(version=azl.__version__,sha=os.environ.get('GITHUB_SHA'),system=platform.system(),human_acceptance=False,scientific_certification=False,planet_trial=False,physical_gpu_benchmark=False,
  runtime_sha256={p.relative_to(runtime).as_posix():digest(p) for p in runtime.rglob('*.py')},
  files={p.relative_to(output).as_posix():digest(p) for p in output.rglob('*') if p.is_file()})
 (output/'review-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
 print(json.dumps(dict(system=platform.system(),files=len(manifest['files']),human_acceptance=False)))
if __name__=='__main__':main()
