"""Azimlib-rendered Phase C gallery; no implicit data acquisition."""
import argparse,hashlib,html,json,platform,subprocess,time
from pathlib import Path
import azimlib as a
from _scenes import historical,mars,catalog,regions,paths,groups,worlds

def main(output,real_data=None,only=None):
 output.mkdir(parents=True,exist_ok=True);rows=[]
 try:sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=Path(__file__).resolve().parents[2],text=True).strip()
 except (OSError,subprocess.CalledProcessError):sha='unavailable'
 cases=[('historical-trade-map',historical),('mars-exploration-map',lambda:mars(real_data)),('symbol-catalog',catalog),('thematic-regions',regions),('cartographic-paths',paths),('groups-visible',groups),('groups-hidden',lambda:groups(True)),('earth-mars-primitives',worlds)]
 if only:cases=[pair for pair in cases if pair[0] in only]
 for name,create in cases:
  start=time.perf_counter();f,meta=create();scene=f.to_scene();files=[]
  for fmt in ('png','svg','pdf'):
   p=output/(name+'.'+fmt);f.savefig(p);files.append(dict(file=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
  rows.append(dict(name=name,**meta,source_revision=sha,version=a.__version__,primitives=len(scene.items),pixels=[round(x*f.dpi) for x in f.figsize],dpi=f.dpi,seconds=time.perf_counter()-start,files=files));a.close(f);print(name,flush=True)
 report=dict(version=a.__version__,source_revision=sha,platform=platform.platform(),python=platform.python_version(),method='Actual Azimlib CPU PNG/SVG/PDF; native L toggles where shown; no browser thematic navigation claim',scenes=rows)
 (output/'gallery.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
 cards=[]
 for r in rows:
  links=' | '.join(f'<a href="{r["name"]}.{fmt}">{fmt.upper()}</a>' for fmt in ('png','svg','pdf'))
  cards.append('<section><h2>'+html.escape(r['name'])+'</h2><p>'+html.escape(str(r['data']))+'</p><p>'+html.escape(str(r['limits']))+'</p><p>'+links+'</p><a href="'+r['name']+'.png"><img loading="lazy" src="'+r['name']+'.png" alt="'+r['name']+'"></a></section>')
 (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Azimlib Phase C gallery</title><style>body{font:16px system-ui;max-width:1450px;margin:40px auto;padding:0 20px;background:#f7f9fa;color:#253a47}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(480px,1fr));gap:20px}section{background:white;border:1px solid #d8e0e4;padding:20px;border-radius:10px}img{width:100%}p{line-height:1.5}</style><h1>Azimlib '+a.__version__+' | Phase C</h1><p>SHA '+html.escape(sha)+'. Original synthetic thematic data; Natural Earth and optional explicitly supplied Viking background keep their own provenance. No historical reconstruction or actual mission route is claimed. Phase D composition is not delivered.</p><div class="grid">'+''.join(cards)+'</div>','utf8')

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--real-data',type=Path);p.add_argument('--only',action='append');args=p.parse_args();main(args.output,args.real_data,args.only)
