"""Actual Azimlib atlas pages, geographic locators and Body-independent Artists."""
import argparse,importlib.util,math
from pathlib import Path
import azimlib as a
from _scenes import area,mars as phase_c_mars

def historical():
 f=a.figure(figsize=(12,8.4),dpi=120);page=f.cartographic_page(title='West Africa | an illustrative trade atlas',subtitle='Real geographic base; fictional territories, resources and routes',credits='Natural Earth public domain | synthetic thematic data | Lucide ISC / applicable Feather MIT')
 ax=page.axes;ax.set_theme('historical');ax.set_extent((-20,14,0,31));ax.map('world',fit=False,facecolor='#eee7d6',edgecolor='#a9aaa0',linewidth=.45)
 regions=ax.group(name='Territories',zorder=1)
 for points,label,color in (([(-16,9),(-11,20),(-3,25),(9,18),(7,8),(-4,5)],'Influence zone','#dfb774'),([(-11,12),(-8,19),(-1,18),(3,14),(-4,10)],'Central region','#c5754d'),([(-15,4),(-5,3),(2,7),(-4,12),(-12,10)],'Coastal region','#80ad9a')):
  r=regions.add(ax.region(area(ax,points,category=label),facecolor=color,edgecolor=color,alpha=.45,label=label));r.labels_for(label.upper(),fontsize=9,fontweight='bold',color='#664b3b',priority=8)
 cities=ax.group(name='Settlements',zorder=5);cities.add(ax.symbols([(-16,12),(-10,8),(-5,16),(4,23),(6,10)],'city',size=12,color='#3d5a60',labels=['Port A','Town B','City C','Market D','Town E'],category='Illustrative cities',halo=a.IconHalo(width=.6)))
 resources=ax.group(name='Resources',zorder=6)
 for name,positions,color,label in [('gold',[(-9,14),(-3,8)],'#b07c1c','Gold'),('salt',[(-8,23),(0,21)],'#736583','Salt'),('ivory',[(-7,6),(0,6)],'#667c51','Ivory'),('port',[(-17,10)],'#2f7a8c','Ports')]:resources.add(ax.symbols(positions,name,size=16,color=color,category=label,halo=a.IconHalo(width=.8)))
 routes=ax.group(name='Routes',zorder=3)
 p=routes.add(ax.cartographic_path(a.CartographicPath.bezier([(-16,12),(-13,25),(-1,18),(5,23)],context=ax.get_context()),color='#a44e3c',linewidth=1.7,arrow='end',label='Main trade curve'));p.labels_for('TRADE CORRIDOR',placement='curve',fontsize=8,color='#7f4536',halo='white',halo_width=1)
 routes.add(ax.cartographic_path(a.CartographicPath.spline([(-12,7),(-8,12),(-2,13),(6,10)],context=ax.get_context()),color='#427b86',linewidth=1.2,linestyle=':',label='Secondary connection'))
 ax.grid(True,step=10,linewidth=.3,alpha=.4);ax.scale_bar(length=400);ax.north_arrow(size=28)
 inset=page.locator(bounds=(.67,.03,.29,.22),shade=True);inset.map('world',fit=False,facecolor='#dadfd8',edgecolor='#8b9f9f',linewidth=.2)
 page.legend(sections=[a.LegendSection.from_group(regions,title='Territories'),a.LegendSection.from_group(routes,title='Connections'),a.LegendSection.from_group(resources,title='Illustrative resources')],fontsize=8.5,symbol_size=12)
 page.note('A didactic scenario inspired by atlas structures. No historical boundary, mineral deposit or trade volume is claimed. Letters identify fictional settlements.')
 return f,dict(body='Earth',data='Natural Earth + original fictional overlays',limits='No historical reconstruction; regional angular thematic boundaries',theme='historical')

def mars(real_data=None):
 original,meta=phase_c_mars(real_data);old=original.axes[0]
 f=a.figure(figsize=(12,8.4),dpi=120);page=f.cartographic_page(body=old.get_body(),title='Mars | exploration field atlas',subtitle='Fictional scientific sites and traversal over an explicitly identified surface',credits=meta['data']+' | Lucide ISC / applicable Feather MIT')
 ax=page.axes;ax.set_extent((-75,-20,-30,15));ax.set_theme('planetary-exploration')
 # Reuse immutable raster/scalar data, not a mutable Artist from the source Figure.
 base=old.layers[0]
 if base.options.get('planetary_raster') is not None:ax.raster(base.options['planetary_raster'],alpha=.78)
 elif base.kind=='mesh':ax.imshow(base.get_data() if hasattr(base,'get_data') else [[math.sin(i/7)*math.cos(j/6) for i in range(40)] for j in range(32)],extent=(-75,-20,-30,15),cmap='terrain',alpha=.6)
 else:
  ax.imshow([[math.sin(i/7)*math.cos(j/6) for i in range(40)] for j in range(32)],extent=(-75,-20,-30,15),cmap='terrain',alpha=.6)
 groups=[]
 for group in old._groups:
  if group._group is None:groups.append(group.instantiate(ax))
 a.close(original)
 regions=[l for l in ax.layers if l.kind=='thematic_region'];paths=[l for l in ax.layers if l.kind=='thematic_path'];symbols=[l for l in ax.layers if l.kind=='thematic_symbols']
 for i,r in enumerate(regions):r.labels_for('ZONE '+chr(65+i),fontsize=12,fontweight='bold',color='#5d4433')
 for s in symbols:s.set_halo(a.IconHalo(width=.8));s.set_shadow(a.IconShadow(alpha=.15,offset=(.5,.6)))
 if paths:paths[0].labels_for('EXPLORATION SCENARIO',placement='curve',fontsize=7.5,color='#853f33')
 ax.scale_bar(length=500);ax.north_arrow(size=28);ax.set_xlabel('East longitude');ax.set_ylabel('Planetocentric latitude')
 inset=page.locator(bounds=(.67,.03,.29,.22),shade=True);inset.set_facecolor('#c4a68d');inset.grid(True,step=60,linewidth=.25,alpha=.4);inset.symbols([(-47,-8)],'map-pin',size=8,color='#805544')
 page.legend(sections=[a.LegendSection('Author regions',tuple(regions)),a.LegendSection('Paths',tuple(paths)),a.LegendSection('Fictional sites',tuple(symbols))],fontsize=8,symbol_size=12)
 page.note('No actual rover movement, geological measurement or operational navigation is inferred. A bright pixel is not elevation. Global locator uses the declared static Body/frame.')
 return f,meta

def locator_cases():
 f=a.figure(figsize=(11,7),dpi=110)
 for i,(body,projection,extent,title) in enumerate(((a.MOON,'orthographic',(-180,180,-90,90),'Moon global + regional'),(a.MARS,'stereographic',(-180,180,55,89),'Mars polar + global'))):
  ax=f.add_subplot(1,2,i+1,body=body,projection=projection,projection_kw={'central_latitude':90} if projection=='stereographic' else {});ax.set_extent(extent);ax.set_axis_off();ax.set_title(title)
  if i==0:
   ax.grid(True,step=30,linewidth=.35);child=ax.inset((.65,.05,.3,.3));child.set_extent((-25,25,-20,20));child.symbols([(0,0)],'flag',size=12);ax.locator(child,shade=True,connectors=True)
  else:
   ax.grid(True,step=30,linewidth=.35);ax.symbols([(0,75),(100,70)],'map-pin',size=11);child=ax.inset((.67,.05,.28,.25));child.set_extent((-180,180,-90,90));child.locator(ax)
 f.text(.5,.03,'Geographic footprints are sampled from inverse projection; no cross-Body locator transform is inferred.',ha='center',fontsize=9)
 return f,dict(body='Moon / Mars',data='Synthetic graticules/sites only',limits='Bounded convex footprint boundary; polar/global fill not asserted')

def main(out,real_data=None):
 out.mkdir(parents=True,exist_ok=True)
 for name,create in (('historical-atlas',historical),('mars-field-atlas',lambda:mars(real_data)),('locator-cases',locator_cases)):
  f,meta=create()
  for fmt in ('png','svg','pdf'):f.savefig(out/(name+'.'+fmt))
  a.close(f);print(name,flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--real-data',type=Path);args=p.parse_args();main(args.output,args.real_data)
