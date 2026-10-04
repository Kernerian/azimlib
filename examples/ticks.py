"""Editable geographic tick objects and a percentage colorbar, own rendering."""
from pathlib import Path
import azimlib.pyplot as plt
from azimlib import datasets
from azimlib.colors import Normalize
from azimlib.ticker import MultipleLocator,LongitudeFormatter,LatitudeFormatter,StrMethodFormatter

def geographic_ticks():
    fig,ax=plt.subplots(figsize=(7,6),projection='mercator')
    ax.states(facecolor='#eeeeee',edgecolor='#888888',linewidth=.4)
    ax.state('SP',facecolor='#dfb871',edgecolor='#333333',linewidth=.7)
    ax.set_extent((-55,-42,-27,-18))
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.yaxis.set_major_locator(MultipleLocator(2))
    ax.xaxis.set_major_formatter(LongitudeFormatter())
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.grid(labels=False,color='#b0b0b0',linewidth=.5,linestyle='--')
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    ax.set_title('Ticks geográficos · passo de 2°',fontsize=14)
    ax.subtitle('São Paulo · componentes editáveis',fontsize=9)
    return fig

def dms_ticks():
    fig,ax=plt.subplots(figsize=(7,5.5),projection='mercator')
    ax.state('SP',facecolor='#efefef',edgecolor='#444444',linewidth=.6)
    ax.set_extent((-47.5,-45.5,-24.5,-22.5))
    ax.scatter([-46.6333],[-23.5505],s=28,color='#d85b40')
    ax.annotate('São Paulo',(-46.6333,-23.5505),xytext=(10,-15),fontsize=9)
    ax.xaxis.set_major_locator(MultipleLocator(.5))
    ax.yaxis.set_major_locator(MultipleLocator(.5))
    ax.xaxis.set_major_formatter(LongitudeFormatter(dms=True))
    ax.yaxis.set_major_formatter(LatitudeFormatter(dms=True))
    ax.grid(labels=False,linestyle=':',linewidth=.5)
    ax.set_title('Graus e minutos · foco regional',fontsize=14)
    return fig

def percentage_bar():
    fig,ax=plt.subplots(figsize=(7,6))
    data=datasets.load('states',country='brazil')
    values=[100*i/(len(data['features'])-1) for i in range(len(data['features']))]
    layer=ax.choropleth(data,values,bins=None,cmap='viridis',norm=Normalize(0,100),edgecolor='white',linewidth=.4)
    ax.xaxis.set_major_formatter(LongitudeFormatter());ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.set_title('Colorbar · locator e formatter',fontsize=14)
    ax.subtitle('Percentuais sintéticos · não representam estatísticas reais',fontsize=9)
    bar=fig.colorbar(layer,orientation='horizontal',label='Indicador sintético')
    bar.locator=MultipleLocator(25);bar.formatter=StrMethodFormatter('{x:.0f}%')
    bar.update_ticks()
    return fig

if __name__=='__main__':
    folder=Path(__file__).resolve().parents[1]/'gallery'
    for name,make in (('geographic-ticks',geographic_ticks),('dms-ticks',dms_ticks),('percentage-colorbar',percentage_bar)):
        fig=make()
        for ext in ('png','svg'):fig.savefig(folder/f'{name}.{ext}')
        fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
        plt.close(fig);print(name,flush=True)
