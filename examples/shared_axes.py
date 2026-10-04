"""Same region in four maps: shared view/tickers, independent layers/styles."""
from pathlib import Path
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.ticker import LongitudeFormatter,LatitudeFormatter


def create():
    fig,axes=azl.subplots(2,2,figsize=(10,8),layout='constrained',
        sharex=True,sharey=True,num='Eixos compartilhados',projection='mercator')
    titles=('Político','Hidrografia','Valores por estado','Rotas e pontos')
    for ax,title in zip(axes.flat,titles):
        ax.map('brazil',facecolor='#f4f4f4',edgecolor='#555555',linewidth=.6,fit=False)
        ax.states(facecolor='none',edgecolor='#777777',linewidth=.4,fit=False)
        ax.set_title(title);ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
        ax.xaxis.set_major_formatter(LongitudeFormatter());ax.yaxis.set_major_formatter(LatitudeFormatter())
        # label_outer remains explicit after subsequently adding axis labels.
        ax.label_outer()
    axes[0,1].rivers(color='#1f77b4',linewidth=.6,fit=False)
    states=azl.datasets.load('states',country='brazil')
    layer=axes[1,0].choropleth(states,[100*i/26 for i in range(27)],bins=None,
        norm=Normalize(0,100),cmap='viridis',edgecolor='#555555',linewidth=.4,fit=False)
    axes[1,1].plot([-51.23,-49.27,-46.63,-43.17],[-30.03,-25.43,-23.55,-22.9],
        'o--',color='#d62728',linewidth=1,markersize=4,label='Rota demonstrativa')
    axes[1,1].legend(loc='lower left',fontsize=8)
    fig.colorbar(layer,ax=list(axes.flat),orientation='horizontal',label='Indicador sintético')
    # One panel controls every member; no optional ornaments are inserted by sharing.
    axes[0,0].set_extent((-58,-38,-34,-16))
    fig.suptitle('Azimlib · quatro camadas, uma vista compartilhada',fontsize=14)
    return fig,axes


def export(fig,name):
    folder=Path(__file__).resolve().parents[1]/'gallery'
    for extension in ('png','svg'):fig.savefig(folder/f'{name}.{extension}')
    print(name,flush=True)


if __name__=='__main__':
    fig,axes=create();export(fig,'shared-axes-before')
    axes[1,1].set_extent((-54,-42,-28,-20))
    axes[1,1].set_xticks([-54,-50,-46,-42])
    axes[1,1].set_yticks([-28,-24,-20])
    fig.suptitle('Azimlib · foco editado a partir do painel de rotas',fontsize=14)
    export(fig,'shared-axes-after');azl.close(fig)
