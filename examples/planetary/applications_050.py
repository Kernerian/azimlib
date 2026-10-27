"""Planetary applications: authored synthetic science, source/status kept explicit."""
import argparse,math
from pathlib import Path
import azimlib as a
S=a.AssetSource('azimlib:synthetic-planetary-applications','BSD-3-Clause','Kernerian; original analytic/synthetic demonstration')

def features(body):
 context=a.PlanetaryContext.for_body(body);items=[]
 def add(ident,kind,g,name,classification=''):
  items.append(a.SurfaceFeature(ident,kind,g,(a.FeatureName(name,'en','Own synthetic nomenclature'),),S,'Synthetic epoch','synthetic',classification=classification))
 for i,(xy,name,kind) in enumerate((((-18,2),'Crater A','crater'),((10,12),'Summit B','volcano'),((22,-12),'Site C','instrument'),((-8,-8),'Landing D','landing'))):add('p'+str(i),kind,a.Geometry('Point',xy),name)
 add('unit1','mare' if body==a.MOON else 'geological-unit',a.Geometry('Polygon',(((-30,-20),(5,-20),(12,20),(-22,24),(-30,-20)),)),'Illustrative unit I','Author unit I')
 add('unit2','geological-unit',a.Geometry('Polygon',(((2,-25),(32,-25),(30,18),(10,15),(2,-25)),)),'Illustrative unit II','Author unit II')
 add('fault','fault',a.Geometry('LineString',((-25,-10),(-10,-3),(4,6),(23,12))),'Fault scenario')
 return a.FeatureCatalog(context,tuple(items),S)

def planetary(body):
 f=a.figure(figsize=(11,8),dpi=110);page=f.cartographic_page(body=body,title=body.name+' | surface-feature atlas',subtitle='Synthetic geometry and nomenclature | not an observational geological product',credits='Original synthetic scenario BSD-3-Clause | Lucide ISC / applicable Feather MIT | static declared Body frame')
 ax=page.axes;ax.set_extent((-40,40,-32,32));ax.set_theme('geological');nx,ny=44,36
 rows=[[600*math.sin(i/7)*math.cos(j/6)+150*math.cos((i+j)/4) for i in range(nx)] for j in range(ny)]
 raster=a.PlanetaryRaster(rows,(80/nx,0,-40,0,-64/ny,32),ax.get_context(),a.BodySource(S.origin,'1','Synthetic analytic DEM'),S.license,unit=a.METRE)
 ax.raster(raster,cmap='terrain',alpha=.6)
 catalog=features(body)
 def style(item):
  if item.geometry.type in ('Polygon','MultiPolygon'):return dict(facecolor='#d5a96a' if item.identifier=='unit1' else '#75a7af',edgecolor='#8b7656',alpha=.35,hatch='..' if item.identifier=='unit2' else '//')
  if item.kind=='fault':return dict(color='#9c5548',linewidth=1.2,linestyle='--')
  return dict(color='#35687b',icon_halo=a.IconHalo(width=.8))
 group=catalog.draw(ax,style=style);ax.scale_bar();ax.north_arrow(size=24);inset=page.locator(bounds=(.7,.03,.26,.22),shade=True);inset.grid(True,step=60,linewidth=.25)
 handles=tuple(l for l in group.get_children() if l.kind!='labels');page.legend(sections=[a.LegendSection('Synthetic features',handles)],fontsize=7.5,symbol_size=11)
 page.note('Crater symbols mark authored locations, not measured diameters. Unit names and boundaries are fictional. Height is an analytic field, not a mission DEM.')
 return f,dict(body=body.identifier,data='Synthetic DEM/units/sites/nomenclature',limits='Not IAU feature catalog or actual geological observation')

def comparison(pair,mode):
 c=a.compare_worlds(pair,mode=mode,figsize=(11,5.5),dpi=110)
 for ax in c.axes:
  ax.symbols([(0,0)],'microscope',size=12,color='#2b7585')
 return c.figure,dict(body=' / '.join(b.identifier for b in pair),data='Ideal reference surfaces / synthetic site',limits='Physical scale' if mode=='physical' else 'Visually normalized; not a shared physical scale')

def exploration():
 f,ax=a.subplots(body=a.MARS,figsize=(7,5),dpi=110);ax.set_extent((-12,12,-8,8));ax.set_title('Mars | illustrative finite exploration sequence');ax.set_theme('planetary-exploration');s=ax.symbols([(-8,-3)],'bot',size=22,halo=a.IconHalo(width=.7),category='Fictional rover');p=ax.cartographic_path(a.CartographicPath.polyline([(-8,-3),(-7,-2.9)],context=ax.get_context()),linewidth=1.5,color='#ac6545')
 frames=[(-8,-3),(-3,1),(2,-1),(7,3)];sequence=a.ExplorationSequence(a.TemporalSeries(range(4),[[xy] for xy in frames],unit='day'),ax.get_context(),S,'illustrative-plan','position','degree');binding=sequence.bind(s);binding.apply(0);ax.legend();f.text(.5,.02,'Author states at days0..3; no observed rover movement, interpolation or orbital propagation',ha='center',fontsize=8)
 return f,binding,p,frames

def main(out):
 out.mkdir(parents=True,exist_ok=True)
 for body in (a.MARS,a.MOON,a.VENUS,a.MERCURY):
  f,meta=planetary(body)
  for fmt in ('png','svg','pdf'):f.savefig(out/(body.identifier+'-features.'+fmt))
  a.close(f);print(body.name,flush=True)
 for pair in ((a.EARTH,a.MARS),(a.MARS,a.MOON),(a.MOON,a.MERCURY),(a.EARTH,a.VENUS)):
  for mode in ('physical','normalized'):
   f,meta=comparison(pair,mode)
   for fmt in ('png','svg','pdf'):f.savefig(out/('-'.join(b.identifier for b in pair)+'-'+mode+'.'+fmt))
   a.close(f)
 f,binding,path,frames=exploration()
 for i in range(4):
  binding.apply(i)
  if i:path.set_definition(a.CartographicPath.polyline(frames[:i+1],context=path.get_context()))
  for fmt in ('png','svg','pdf'):f.savefig(out/('exploration-'+str(i)+'.'+fmt))
 a.close(f)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
