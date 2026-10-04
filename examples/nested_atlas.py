"""One country panel and a nested group of regional maps, all composed locally."""
from pathlib import Path
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.ticker import LongitudeFormatter,LatitudeFormatter


def create():
    arrangement=[['Brasil',[['Sudeste','Nordeste'],['Sul','Nordeste']]]]
    fig,maps=azl.subplot_mosaic(arrangement,num='Atlas aninhado',figsize=(12,9),
        layout='constrained',width_ratios=[1.3,1],subplot_kw={'projection':'mercator'})
    data=azl.datasets.load('states',country='brazil');norm=Normalize(0,100)
    extents={'Brasil':(-76,-33,-35,7),'Sudeste':(-54,-39,-26,-14),
             'Sul':(-59,-46,-35,-22),'Nordeste':(-49,-33,-18,0)}
    layers={}
    for name,ax in maps.items():
        layers[name]=ax.choropleth(data,[100*i/26 for i in range(27)],bins=None,norm=norm,
                                  cmap='viridis',edgecolor='#666666',linewidth=.4)
        ax.set_extent(extents[name]);ax.set_title(name)
        ax.xaxis.set_major_formatter(LongitudeFormatter());ax.yaxis.set_major_formatter(LatitudeFormatter())
        ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    maps['Brasil'].map('brazil',facecolor='none',edgecolor='black',linewidth=.55,fit=False)
    maps['Brasil'].north_arrow(size=24)
    maps['Sudeste'].scale_bar(length=200,fontsize=8)
    maps['Nordeste'].compass(size=24)
    maps['Sul'].scale_bar(length=200,fontsize=8)
    fig.colorbar(layers['Sudeste'],ax=[maps[name] for name in ('Sudeste','Sul','Nordeste')],
                 orientation='horizontal',label='Indicador regional sintético')
    fig.suptitle('Azimlib · um país e um grupo de mapas regionais',fontsize=15)
    return fig,maps


def export(fig,name):
    folder=Path(__file__).resolve().parents[1]/'gallery'
    for extension in ('png','svg'):fig.savefig(folder/f'{name}.{extension}')
    fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
    print(name,flush=True)


if __name__=='__main__':
    fig,maps=create();export(fig,'nested-atlas-before')
    child=maps['Sudeste'].get_gridspec()
    child.set_width_ratios([1.3,1]);child.set_height_ratios([1,1.2])
    child.update(wspace=.1,hspace=.15)
    maps['Sudeste'].set_title('Sudeste\nPainel redimensionado')
    maps['Sul'].set_title('Sul\nPesos editados no grid filho')
    fig.suptitle('Azimlib · pesos e títulos editados na mesma hierarquia',fontsize=15)
    export(fig,'nested-atlas-after');azl.close(fig)
