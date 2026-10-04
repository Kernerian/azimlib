"""Real hydrography at three extents; optional obstacles and own label layout."""
from pathlib import Path
import azimlib as azl
from azimlib import datasets
from azimlib.ticker import LongitudeFormatter,LatitudeFormatter


def hydrography(extent,title,*,regional=False):
    fig,ax=azl.subplots(figsize=(7.8,6.4) if regional else (7.8,9),
                        projection='mercator',layout='tight')
    ax.set_facecolor('#dceaf5')
    west,east,south,north=extent
    context=azl.read_geojson(datasets.load('countries'))
    neighbors=[f for f in context if f.geometry and
               f.geometry.bounds[0]<=east and f.geometry.bounds[2]>=west and
               f.geometry.bounds[1]<=north and f.geometry.bounds[3]>=south]
    ax.geojson(azl.FeatureCollection(tuple(neighbors)),facecolor='#e9e9e9',edgecolor='#aaaaaa',linewidth=.4)
    ax.map('brazil',facecolor='white',edgecolor='#555555',linewidth=.6)
    ax.states(edgecolor='#b5b5b5',linewidth=.3)
    ax.lakes(facecolor='#b4d6ec',edgecolor='#6b9fbd',linewidth=.3)
    rivers=ax.rivers(color='#3c83aa',linewidth=.65,label='Rios e eixos de lagos')
    names=datasets.load('rivers',country='brazil')
    for feature in names['features']:
        # scalerank is a cartographic importance field, not navigability.
        feature['properties']['label_priority']=10-float(feature['properties'].get('scalerank',10) or 0)
    ax.labels(names,placement='line',priority_field='label_priority',
              fontsize=9 if regional else 8,color='#245f7d',halo='white',halo_width=3,padding=3)
    city={'type':'Feature','properties':{'name':'Manaus'},
          'geometry':{'type':'Point','coordinates':[-60.02,-3.12]}}
    ax.scatter([-60.02],[-3.12],s=14,color='#333333',zorder=5)
    ax.labels(city,fontsize=9,max_span=30,priority=20,leader=True)
    if regional:
        ax.annotate('Posição aproximada\nde Manaus',(-60.02,-3.12),xytext=(25,-50),
                    fontsize=8,background='white',color='#444444',linewidth=.6)
        ax.overview(context='brazil',loc='lower right',width=105)
    ax.set_extent(extent)
    ax.set_title(title,fontsize=14)
    ax.subtitle('Natural Earth · sem classificação de navegabilidade',fontsize=9)
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    ax.xaxis.set_major_formatter(LongitudeFormatter());ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.legend(loc='upper left',fontsize=8)
    ax.scale_bar(fontsize=8)
    ax.north_arrow(loc='upper right',size=26)
    return fig


def obstacles():
    fig,ax=azl.subplots(figsize=(8,7),layout='tight')
    points=[]
    for i,(x,y) in enumerate((x,y) for y in (-7,-3,1,5,8) for x in (-8,-4,0,4,8)):
        points.append({'type':'Feature','properties':{'name':f'P{i+1:02d}','priority':i},
                       'geometry':{'type':'Point','coordinates':[x,y]}})
    ax.scatter([f['geometry']['coordinates'][0] for f in points],
               [f['geometry']['coordinates'][1] for f in points],s=12,color='#356b91')
    ax.labels({'type':'FeatureCollection','features':points},fontsize=10,leader=True)
    ax.annotate('Annotation explícita\nRótulos procuram espaço',(0,0),xytext=(0,0),
                arrow=False,ha='center',va='center',fontsize=12,background='#f4e5bf')
    child=ax.inset_axes((.66,.66,.29,.29));child.set_extent((-1,1,-1,1))
    child.line([(-.8,-.5),(.5,.6)],color='#e17744',linewidth=1.5)
    child.set_title('Inset opcional',fontsize=9)
    ax.set_extent((-10,10,-10,10))
    ax.set_title('Rótulos · colisões e prioridades',fontsize=14)
    ax.subtitle('Pontos sintéticos · annotation e inset são obstáculos',fontsize=9)
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    return fig


if __name__=='__main__':
    folder=Path(__file__).resolve().parents[1]/'gallery'
    cases=(('labels-brazil',lambda:hydrography((-75,-32,-35,7),'Brasil · hidrografia e rótulos')),
           ('labels-amazon',lambda:hydrography((-73,-47,-12,4),'Amazônia · direção local dos rios',regional=True)),
           ('labels-focus',lambda:hydrography((-64,-52,-8,0),'Foco regional · rótulos recalculados',regional=True)),
           ('label-obstacles',obstacles))
    for name,make in cases:
        fig=make()
        for ext in ('png','svg'):fig.savefig(folder/f'{name}.{ext}')
        fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
        azl.close(fig);print(name,flush=True)
