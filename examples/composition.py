"""Legends and shared colorbars composed by Azimlib's own engine.

All thematic values and routes are illustrative, not official indicators.
Run python examples/composition.py to export PNG/SVG/HTML examples.
"""
from pathlib import Path
import azimlib.pyplot as plt
from azimlib import datasets
from azimlib.colors import Normalize

def legend_columns():
    fig,ax=plt.subplots(figsize=(7.5,7))
    fig.subplots_adjust(bottom=.23,top=.87)
    land=ax.states(facecolor='#f7f7f7',edgecolor='#555555',linewidth=.5)
    water=ax.rivers(color='#427cb6',linewidth=.6)
    route=ax.route([(-60,-3),(-47,-16),(-46.63,-23.55)],color='#d85b40',linestyle='--',linewidth=1.1)
    cities=ax.scatter([-60,-47,-46.63],[-3,-16,-23.55],s=24,color='#d85b40')
    area=ax.polygon([(-59,-10),(-54,-10),(-54,-15),(-59,-15)],facecolor='none',
                    edgecolor='#5f8063',hatch='//',linewidth=.5,zorder=2)
    ax.set_title('Legenda composta · duas colunas',fontsize=14)
    ax.subtitle('Base Natural Earth · rota e área ilustrativas',fontsize=9)
    legend=ax.legend([land,water,(route,cities),area],
                     ['Estados','Rios','Rota e pontos','Área de estudo'],ncols=2,
                     loc='upper center',bbox_to_anchor=(.5,-.06),fontsize=10,
                     title='Camadas',columnspacing=2)
    legend.get_frame().set_edgecolor('#b0b0b0')
    return fig

def atlas_shared():
    fig,axs=plt.subplots(2,2,figsize=(9,8))
    fig.subplots_adjust(top=.86,bottom=.14,wspace=.20,hspace=.38)
    data=datasets.load('states',country='brazil')
    norm=Normalize(0,100)
    values=[100*i/(len(data['features'])-1) for i in range(len(data['features']))]
    regions=(('Brasil',(-75,-32,-35,7)),('Norte',(-74,-44,-14,6)),
             ('Sudeste',(-55,-38,-27,-13)),('Sul',(-59,-47,-35,-22)))
    layers=[]
    for ax,(title,extent) in zip(axs.flat,regions):
        layers.append(ax.choropleth(data,values,bins=None,cmap='viridis',norm=norm,
                                   edgecolor='white',linewidth=.35))
        ax.set_extent(extent);ax.set_title(title,fontsize=12)
        ax.tick_params(labelsize=8)
    fig.suptitle('Atlas · uma normalização e uma colorbar',fontsize=15)
    bar=fig.colorbar(layers[0],ax=axs,orientation='horizontal',fraction=.08,pad=.12,
                    shrink=.8,label='Indicador sintético · mesma escala em todos os mapas')
    bar.set_ticks([0,25,50,75,100]);bar.ax.tick_params(labelsize=9)
    return fig

def colorbar_cax():
    fig,axs=plt.subplots(1,2,figsize=(9,5))
    fig.subplots_adjust(left=.07,right=.82,bottom=.15,top=.82,wspace=.25)
    data=datasets.load('states',country='brazil');norm=Normalize(0,100)
    values=[100*i/(len(data['features'])-1) for i in range(len(data['features']))]
    for ax,title,extent in zip(axs.flat,('Brasil','São Paulo'),((-75,-32,-35,7),(-54,-43,-26,-19))):
        layer=ax.choropleth(data,values,bins=None,norm=norm,cmap='plasma',edgecolor='white',linewidth=.4)
        ax.set_extent(extent);ax.set_title(title,fontsize=12);ax.tick_params(labelsize=8)
    cax=fig.add_axes((.87,.18,.025,.60))
    bar=fig.colorbar(layer,ax=axs,cax=cax)
    cax.set_yticks([0,25,50,75,100]);cax.tick_params(labelsize=9)
    cax.set_ylabel('Indicador sintético',fontsize=10)
    bar.outline.set_linewidth(.6)
    fig.suptitle('Colorbar em eixos explícitos · cax',fontsize=15)
    return fig

if __name__=='__main__':
    folder=Path(__file__).resolve().parents[1]/'gallery'
    for name,make in (('legend-columns',legend_columns),('atlas-shared',atlas_shared),('colorbar-cax',colorbar_cax)):
        fig=make()
        for ext in ('png','svg'):fig.savefig(folder/f'{name}.{ext}')
        fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
        plt.close(fig);print(name,flush=True)
