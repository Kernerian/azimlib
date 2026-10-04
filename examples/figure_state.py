"""Named atlas, shared colors and explicit pyplot figure/axes selection."""
from pathlib import Path
import azimlib as azl
import azimlib.pyplot as plt
from azimlib.colors import Normalize
from azimlib.ticker import LongitudeFormatter,LatitudeFormatter


def create():
    fig,maps=azl.subplot_mosaic([['Brasil','Brasil'],['São Paulo','Amazonas']],
        num='Atlas',figsize=(10,10),layout='constrained',height_ratios=[2,1.4],
        subplot_kw={'projection':'mercator'})
    data=azl.datasets.load('states',country='brazil')
    values=[100*i/26 for i in range(27)];norm=Normalize(0,100);layers=[]
    for name,ax in maps.items():
        layer=ax.choropleth(data,values,bins=None,norm=norm,cmap='viridis',edgecolor='#555555',linewidth=.35)
        layers.append(layer)
        if name=='Brasil':ax.map('brazil',facecolor='none',edgecolor='black',linewidth=.6)
        else:ax.state('SP' if name=='São Paulo' else 'AM',facecolor='none',edgecolor='black',linewidth=.6)
        ax.set_title(name)
        ax.xaxis.set_major_formatter(LongitudeFormatter())
        ax.yaxis.set_major_formatter(LatitudeFormatter())
    maps['Brasil'].north_arrow(size=22)
    maps['São Paulo'].scale_bar(length=100,fontsize=8)
    maps['Amazonas'].compass(size=24)
    fig.colorbar(layers[0],ax=list(maps.values()),orientation='horizontal',
                 label='Indicador sintético por estado')
    fig.suptitle('Azimlib · atlas com mapas nomeados',fontsize=15)
    return fig,maps,norm


def export(fig,name):
    folder=Path(__file__).resolve().parents[1]/'gallery'
    for extension in ('png','svg'):fig.savefig(folder/f'{name}.{extension}')
    fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
    print(name,flush=True)


if __name__=='__main__':
    fig,maps,norm=create();export(fig,'figure-state-before')
    other,other_ax=azl.subplots(num='Outra figura')
    # Restore the atlas and choose São Paulo, without rebuilding/reordering axes.
    plt.sca(maps['São Paulo'])
    route,=plt.plot([-49.8,-47.1,-46.63],[-22.2,-22.9,-23.55],'o--',
             color='#d62728',linewidth=1.1,markersize=4,label='Rota demonstrativa')
    plt.legend(handles=[route],fontsize=8,loc='upper right')
    plt.title('São Paulo · eixo selecionado')
    assert plt.gcf() is fig and not other_ax.layers
    norm.vmax=120
    fig.suptitle('Azimlib · seleção explícita e escala compartilhada',fontsize=15)
    export(fig,'figure-state-after')
    azl.close('Outra figura');azl.close('Atlas')
