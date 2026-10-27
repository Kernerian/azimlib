"""Own demonstrative thematic geography; no historical reconstruction or mission plan."""
import json,math
from pathlib import Path
import azimlib as a
from azimlib.colors import Normalize,Colormap
ASSETS=Path(__file__).resolve().parent/'assets'

def asset(filename):
    p=ASSETS/filename;row=json.loads((ASSETS/'provenance.json').read_text('utf8'))[filename]
    source=a.AssetSource(row['origin'],row['license'],row['credit'],row['sha256'])
    return a.SymbolDefinition.from_svg(p,source=source) if p.suffix=='.svg' else a.SymbolDefinition.from_png(p,source=source)

def area(ax,points,category='',holes=(),**options):
    return a.RegionDefinition.polygon(points,context=ax.get_context(),category=category,holes=holes,**options)

def native_controls(fig,group):
    def toggle(event):
        if getattr(event,'key','')=='l':group.set_visible(not group.get_local_visible());fig.canvas.draw_idle()
    fig.canvas.mpl_connect('key_press_event',toggle)

def historical():
    f,ax=a.subplots(figsize=(12,7.5),dpi=110);f.subplots_adjust(left=.07,right=.70,bottom=.17,top=.84)
    ax.set_extent((-20,14,0,31));ax.map('world',fit=False,facecolor='#eee8d7',edgecolor='#9da9a4',linewidth=.55)
    ax.set_facecolor('#e6f0f4');layers=ax.group(name='Illustrative thematic layers')
    zones=ax.group(name='Regions',parent=layers,zorder=1)
    zones.add(ax.region(area(ax,[(-16,9),(-11,20),(-3,25),(9,18),(7,8),(-4,5)],'Illustrative influence'),facecolor='#e8bb66',edgecolor='#a97c32',alpha=.28))
    zones.add(ax.region(area(ax,[(-11,12),(-8,19),(-1,18),(3,14),(-4,10)],'Illustrative core'),facecolor='#c9703b',edgecolor='#8d472c',alpha=.5))
    zones.add(ax.region(area(ax,[(-15,4),(-5,3),(2,7),(-4,12),(-12,10)],'Illustrative coastal zone'),facecolor='#83b39d',edgecolor='#4d897a',alpha=.45,hatch='//',hatch_spacing=10,hatch_linewidth=.3))
    routes=ax.group(name='Routes',parent=layers,zorder=3)
    p=a.CartographicPath.bezier([(-16,12),(-13,25),(-1,18),(5,23)],context=ax.get_context());routes.add(ax.cartographic_path(p,color='#b64b3a',linewidth=1.7,linestyle='--',arrow='end',label='Editorial trade curve'))
    p=a.CartographicPath.spline([(-12,7),(-8,12),(-2,13),(6,10)],context=ax.get_context());routes.add(ax.cartographic_path(p,color='#5b7f89',linewidth=1.3,linestyle=':',label='Illustrative secondary route'))
    cities=ax.group(name='Cities',parent=layers,zorder=6)
    cities.add(ax.symbols([(-16,12),(-10,8),(-5,16),(4,23),(6,10)],'city',size=11,color='#3e4b54',labels=['Port A','Town B','City C','Market D','Town E']))
    resources=ax.group(name='Resources',parent=layers,zorder=5)
    for icon,positions,color,label in [('gold',[(-9,14),(-3,8)],'#b48424','Gold (illustrative)'),('salt',[(-8,23),(0,21)],'#7a7193','Salt (illustrative)'),('ivory',[(-7,6),(0,6)],'#6c7753','Ivory (illustrative)'),('port',[(-17,10)],'#357f91','Port')]:
        resources.add(ax.symbols(positions,icon,size=16,color=color,category=label,halo=a.IconHalo(width=.6)))
    ax.grid(True,step=10,linewidth=.35,color='#afbab8',alpha=.5)
    ax.set_title('Didactic atlas | West Africa',fontsize=17);ax.subtitle('Real geographic base; all territories, towns and routes are fictional',fontsize=10)
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.scale_bar(length=400,units='km');ax.north_arrow()
    ax.legend(loc='upper left',bbox_to_anchor=(1.02,1),fontsize=8.5)
    f.text(.5,.08,'Structure inspired by historical atlas conventions; not a reconstruction of the Mali Empire.',ha='center',fontsize=10)
    f.text(.5,.04,'Natural Earth public-domain base | original synthetic thematic data and symbols | CPU; press L in native viewer to toggle themes',ha='center',fontsize=8)
    native_controls(f,layers)
    return f,dict(body='Earth',data='Natural Earth base; fictional thematic geometry/locations/resources',limits='Not historical evidence; advanced labels, locator maps and atlas composition await Phase D')

def mars(real_data=None):
    image=None;body=a.MARS;source_text='Synthetic analytic reference-surface field'
    if real_data is not None:
        root=Path(real_data);products=json.loads((root/'provenance.json').read_text('utf8'))['products'];p=next(p for p in products if p['id']=='mars-viking')
        source=a.BodySource(p['source_page'],p['edition'],p['kind'],p['sha256'])
        body=a.Body('Mars',identifier='mars-viking-source-grid',axes=p['axes_m'],frame=p['frame'],datum='MDIM21 image reference surface',orientation='Static source grid; no IAU/mission frame conversion',provenance=(source,))
        ctx=a.PlanetaryContext.for_body(body);image=a.PlanetaryRaster.from_image(root/p['file'],affine=p['pixel_affine'],context=ctx,source=source,license=p['license'],copyright=p['credit']).crop((-75,-20,-30,15));source_text='Real colorized Viking MDIM 2.1 overview | NASA Ames / USGS / NASA-JPL Trek'
    f,ax=a.subplots(body=body,figsize=(12,7.5),dpi=110);f.subplots_adjust(left=.07,right=.70,bottom=.17,top=.84);ax.set_extent((-75,-20,-30,15))
    if image is not None:ax.raster(image,alpha=.72)
    else:
        rows=[[math.sin(i/8)*math.cos(j/7) for i in range(48)] for j in range(40)]
        ax.imshow(rows,extent=(-75,-20,-30,15),cmap=Colormap('own-mars-earth-tones',('#3f292a','#b68d6c','#ead9b8')),alpha=.55)
    themes=ax.group(name='Scientific scenario');regions=ax.group(parent=themes,name='Author thematic zones',zorder=1)
    regions.add(ax.region(area(ax,[(-65,-20),(-64,3),(-43,7),(-35,-12),(-44,-24)],'Zone A (fictional)'),facecolor='#cda34c',edgecolor='#ae8036',alpha=.30))
    regions.add(ax.region(area(ax,[(-56,-18),(-45,-1),(-28,-4),(-29,-24),(-45,-27)],'Zone B (fictional)'),facecolor='#559cac',edgecolor='#28798c',alpha=.25,hatch='..',hatch_spacing=12))
    routes=ax.group(parent=themes,name='Exploration paths',zorder=4)
    definition=a.CartographicPath.spline([(-65,-15),(-59,-10),(-51,-12),(-44,-6),(-35,-9)],context=ax.get_context());routes.add(ax.cartographic_path(definition,color='#a13936',linewidth=2,arrow='end',path_symbol='arrow',spacing=55,symbol_size=6,label='Editorial exploration curve'))
    definition=a.CartographicPath.geodesic([(-65,-15),(-35,-9)],context=ax.get_context());routes.add(ax.cartographic_path(definition,color='#f0e9d0',linewidth=1.1,linestyle='--',label='Surface geodesic comparison'))
    objects=ax.group(parent=themes,name='Sites and instruments',zorder=7)
    objects.add(ax.symbols([(-65,-15)],'landing',color='#3c596a',size=18,labels=['Base A'],category='Landing site (fictional)'))
    objects.add(ax.symbols([(-52,-11)],'rover',color='#a42d36',size=20,category='Rover (fictional)'))
    objects.add(ax.symbols([(-44,-6),(-35,-9)],'instrument',color='#246d7d',size=16,labels=['Site B','Site C'],category='Instrument (fictional)'))
    objects.add(ax.symbols([(-59,-10),(-51,-12),(-44,-6)],'village',size=5,color='#4d3134',category='Waypoints'))
    ax.set_title('Mars | thematic exploration prototype',fontsize=17);ax.subtitle('Fictional regions, sites and traversal; not a mission or a navigation plan',fontsize=10)
    ax.set_xlabel('East longitude');ax.set_ylabel('Planetocentric latitude');ax.scale_bar(length=500,units='km');ax.legend(loc='upper left',bbox_to_anchor=(1.02,1),fontsize=8.5)
    # Deliberately no dense geographic graticule over the orbital texture.
    f.text(.5,.075,source_text,ha='center',fontsize=9);f.text(.5,.035,'No height inferred from brightness; ideal reference surface | same Artists as the Earth atlas | L toggles the scenario',ha='center',fontsize=8)
    native_controls(f,themes)
    return f,dict(body=body.identifier,data=source_text+'; thematic overlays are original fiction',limits='Regional overview, not measured terrain/mission navigation; no invented geological interpretation')

def catalog():
    f,ax=a.subplots(figsize=(12,7),dpi=110);ax.set_extent((0,10,0,7));ax.set_axis_off()
    for i,(name,symbol) in enumerate(a.symbol_catalog().items()):
        x=.6+(i%6)*1.6;y=6-(i//6)*1.05;ax.symbols([(x,y)],symbol,size=23,color=('#a87328','#427c86','#966471')[i%3],labels=[name.replace('scientific-point','science point')],fontsize=8)
    ax.symbols([(1.5,.7)],asset('observation.svg'),size=26,labels=['Original safe SVG'])
    ax.symbols([(6,.7)],asset('sample.png'),size=26,rotation=25,labels=['Own PNG with partial alpha'])
    ax.set_title('Original cartographic catalog + user assets',fontsize=16)
    f.text(.5,.03,'Lucide 1.61.0 / ISC + applicable Feather MIT | own custom SVG/PNG BSD-3-Clause | aspect-preserving vectors',ha='center',fontsize=9)
    return f,dict(body='Earth',data='Official pinned Lucide icons / own custom SVG and PNG',limits='Bounded SVG subset; upstream license/provenance preserved; no remote resources')

def regions():
    f,axes=a.subplots(1,3,figsize=(12,4.8),dpi=110);f.subplots_adjust(left=.05,right=.97,top=.82,bottom=.17,wspace=.35)
    for ax in axes:ax.set_extent((-6,6,-6,6));ax.set_axis_off()
    r=area(axes[0],[(-5,-5),(4,-5),(5,4),(-4,5)],holes=[[(-1,-1),(-1,2),(2,2),(2,-1)]],category='Area with hole')
    extra=area(axes[0],[(5.2,-.5),(5.9,-.5),(5.9,1),(5.2,1)])
    multi=a.RegionDefinition(a.Geometry('MultiPolygon',(r.geometry.coordinates,extra.geometry.coordinates)),axes[0].get_context())
    axes[0].region(multi,facecolor='#99bdac',edgecolor='#366b61',hatch='//',hatch_spacing=9);axes[0].set_title('Components, hole and hatch')
    bands=[]
    for size,color in ((5,'#e9d3aa'),(3.5,'#d9a268'),(2,'#a96040')):
        bands.append((area(axes[1],[(-size,-size),(size,-size),(size,size),(-size,size)]),dict(facecolor=color,edgecolor='white',linewidth=.6)))
    axes[1].region_bands(bands,name='Author bands');axes[1].set_title('Explicit decorative steps')
    r=area(axes[2],[(-5,-5),(4,-5),(5,4),(-4,5)],holes=[[(-1,-1),(-1,2),(2,2),(2,-1)]])
    gradient=a.LinearGradient((-5,-5),(5,5),('#eac78c','#3b8597'),'decorative',steps=32)
    axes[2].region(r,gradient=gradient,edgecolor='#31545d',linewidth=.8);axes[2].set_title('Declared linear gradient')
    f.text(.5,.04,'Author geometry and decorative intensity; not historical control, probability, uncertainty or measured scientific data',ha='center',fontsize=9)
    return f,dict(body='Earth',data='Original synthetic polygons and explicit decorative function',limits='Angular regional straight edges; gradient sampled into 32 bounded strips, not a newly inferred field')

def paths():
    f,axes=a.subplots(1,2,figsize=(11,5.5),dpi=110)
    for ax in axes:ax.set_extent((-9,9,-7,8));ax.grid(True,step=5,linewidth=.3,color='#d2dbdd')
    c=axes[0].get_context();controls=[(-7,-4),(-8,7),(6,8),(7,-4)]
    axes[0].cartographic_path(a.CartographicPath.bezier(controls,context=c),color='#af5f42',linewidth=2,arrow='end',path_symbol='arrow',spacing=40,symbol_size=6,label='Cubic Bezier')
    axes[0].plot([p[0] for p in controls],[p[1] for p in controls],color='#aaa',linestyle=':',linewidth=.7,marker='o',markersize=3,label='Author controls');axes[0].set_title('Geographic editorial Bezier');axes[0].legend(fontsize=8)
    pts=[(-7,-4),(-2,2),(3,-1),(7,5)];axes[1].cartographic_path(a.CartographicPath.spline(pts,context=axes[1].get_context()),color='#428b8e',linewidth=2,arrow='end',label='Cardinal spline')
    axes[1].cartographic_path(a.CartographicPath.geodesic([pts[0],pts[-1]],context=axes[1].get_context()),color='#88687a',linestyle='--',linewidth=1,label='Surface geodesic');axes[1].set_title('Editorial vs surface geometry');axes[1].legend(fontsize=8)
    f.text(.5,.03,'No orbital motion or implied physical path length for editorial curves. Surface distance and visual length are separate.',ha='center',fontsize=9)
    return f,dict(body='Earth',data='Original control points; independent BodySurface geodesic',limits='Geographic interpolation for editorial curves; sampled surface paths; no curve-following labels')

def groups(hidden=False):
    f,axes=a.subplots(1,2,body=a.MARS,figsize=(10,5.5),dpi=110)
    for ax in axes:ax.set_extent((-6,6,-5,5));ax.set_axis_off()
    g=axes[0].group(name='Shared definitions',style={'color':'#3b8395','alpha':.8});g.add(axes[0].region(area(axes[0],[(-4,-3),(4,-3),(4,3),(-4,3)]),alpha=.3))
    child=axes[0].group(parent=g,name='Sites');child.add(axes[0].symbols([(-2,0),(2,1)],'rover',size=22,labels=['A','B']))
    child.add(axes[0].cartographic_path(a.CartographicPath.spline([(-3,-2),(0,1),(3,0)],context=axes[0].get_context()),arrow='end',linewidth=1.6))
    cloned=g.instantiate(axes[1]);cloned.set_style(color='#ad6e47',alpha=.8)
    if hidden:child.set_visible(False)
    axes[0].set_title('Original: '+('sites hidden' if hidden else 'sites visible'));axes[1].set_title('Independent viewport instance')
    f.text(.5,.035,'Immutable data/definitions shared; mutable Artists, callbacks and ownership independent. L toggles original group.',ha='center',fontsize=9);native_controls(f,g)
    return f,dict(body='Mars',data='Original demonstration geometry; independent visual instances',limits='Cloning requires matching declared Body/context; no multi-Axes ownership of mutable Artists')

def worlds():
    f=a.figure(figsize=(11,5.7),dpi=110);axes=[f.add_subplot(1,2,1,body=a.EARTH),f.add_subplot(1,2,2,body=a.MARS)]
    for ax in axes:
        ax.set_extent((-6,6,-5,5));r=area(ax,[(-4,-3),(4,-3),(4,3),(-4,3)])
        ax.region(r,facecolor='#e2b56f',edgecolor='#b38242',alpha=.4)
        ax.symbols([(-2,-1),(2,1)],'instrument',size=18,color='#378091',labels=['Point A','Point B'])
        ax.cartographic_path(a.CartographicPath.bezier([(-2,-1),(-1,3),(1,3),(2,1)],context=ax.get_context()),color='#aa5d48',linewidth=1.5,arrow='end')
        ax.set_title(ax.get_body().name+' | same thematic primitives');ax.scale_bar(length=100,units='km')
    f.text(.5,.025,'Same API and visual size; explicitly different physical scales and independent contexts. All overlay geometry is synthetic.',ha='center',fontsize=9)
    return f,dict(body='Earth + Mars',data='Original identical angular demonstration geometry',limits='Coordinates are redeclared per Body, never transformed implicitly between planets')
