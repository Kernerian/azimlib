"""Nonpublishing consolidated actual Azimlib gallery with hashes and source SHA."""
import argparse,hashlib,html,importlib.util,json,platform,subprocess,sys,time
from pathlib import Path
import azimlib as a
ROOT=Path(__file__).resolve().parents[1]
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main(output,real_data=None):
 sys.path.insert(0,str(ROOT/'examples/thematic'));e=module(ROOT/'examples/thematic/editorial_050.py','editorial_gallery');l=module(ROOT/'examples/thematic/lucide_050.py','lucide_gallery');p=module(ROOT/'examples/planetary/applications_050.py','planetary_gallery');b=module(ROOT/'examples/planetary/surfaces_050.py','surfaces_gallery');c=module(ROOT/'examples/thematic/_scenes.py','thematic_gallery')
 output.mkdir(parents=True,exist_ok=True)
 sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();rows=[]
 def wrapped(factory,data):return lambda:(factory(),dict(data=data,limits='Documented static rendering contract'))
 cases=[('lucide-catalog',wrapped(l.catalog,'Official unmodified Lucide1.61.0 / ISC and applicable Feather MIT')),('lucide-effects',wrapped(l.effects,'Optional original/halo/shadow/both; source stroke independent')),('historical-atlas',e.historical),('mars-field-atlas',lambda:e.mars(real_data)),('locator-cases',e.locator_cases),('regions-bands-gradient',c.regions),('editorial-geodesic-paths',c.paths)]
 for body in (a.MOON,a.VENUS,a.MERCURY):cases.append((body.identifier+'-features',lambda body=body:p.planetary(body)))
 for pair,mode in (((a.EARTH,a.MARS),'physical'),((a.MARS,a.MOON),'normalized'),((a.MOON,a.MERCURY),'physical'),((a.EARTH,a.VENUS),'normalized')):cases.append(('-'.join(q.identifier for q in pair)+'-'+mode,lambda pair=pair,mode=mode:p.comparison(pair,mode)))
 cases.extend([('mars-terrain-light',lambda:b.terrain(a.MARS,textured=False)),('moon-elevation-profile',b.lunar_profile)])
 for name,create in cases:
  start=time.perf_counter();fig,meta=create();scene=fig.to_scene();files=[]
  for fmt in ('png','svg','pdf'):
   path=output/(name+'.'+fmt);fig.savefig(path);files.append(dict(file=path.name,bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
  rows.append(dict(name=name,source_revision=sha,metadata=meta,seconds=time.perf_counter()-start,dpi=fig.dpi,pixels=[round(v*fig.dpi) for v in fig.figsize],primitives=len(scene.items),files=files));a.close(fig);print(name,flush=True)
 fig,binding,path,frames=p.exploration()
 for i in (0,3):
  binding.apply(i)
  if i:path.set_definition(a.CartographicPath.polyline(frames[:i+1],context=path.get_context()))
  name='exploration-frame-'+str(i);files=[]
  for fmt in ('png','svg','pdf'):
   f=output/(name+'.'+fmt);fig.savefig(f);files.append(dict(file=f.name,bytes=f.stat().st_size,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
  rows.append(dict(name=name,source_revision=sha,metadata=dict(data='Fictional finite rover scenario; no actual mission movement',limits='Discrete authored states; no orbital/scientific forecast'),files=files))
 a.close(fig)
 report=dict(version=a.__version__,source_revision=sha,platform=platform.system(),python=platform.python_version(),scenes=rows,human_acceptance=False,publication=False)
 (output/'gallery.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');cards=[]
 for row in rows:
  name=row['name'];meta=row['metadata'];links=' | '.join('<a href="'+name+'.'+fmt+'">'+fmt.upper()+'</a>' for fmt in ('png','svg','pdf'));cards.append('<section><h2>'+html.escape(name)+'</h2><p>'+html.escape(str(meta))+'</p><p>'+links+'</p><a href="'+name+'.png"><img loading="lazy" src="'+name+'.png" alt="'+name+'"></a></section>')
 (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Azimlib0.5 development review</title><style>body{font:16px system-ui;max-width:1500px;margin:35px auto;padding:0 20px;background:#f5f8fa;color:#243d48}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(480px,1fr));gap:18px}section{background:white;border:1px solid #d9e1e4;padding:18px;border-radius:9px}img{width:100%}p{line-height:1.5}</style><h1>Azimlib0.5.0.dev0 | Lucide + editorial + Beyond Earth</h1><p>SHA '+sha+' | '+platform.system()+' | CPU PNG/SVG/PDF. All outputs actually rendered by Azimlib. Human review pending; no publication. Thematic/mission/geology overlays are synthetic unless explicitly identified otherwise. Optional real orbital background is not elevation. Preserved older galleries provide comparisons.</p><div class="grid">'+''.join(cards)+'</div>',encoding='utf8')
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--real-data',type=Path);args=parser.parse_args();main(args.output,args.real_data)
