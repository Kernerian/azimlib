"""Scale, north and compass staying independent while the browser navigates."""
from pathlib import Path
import azimlib as azl

folder=Path(__file__).resolve().parents[1]/'gallery'

if __name__=='__main__':
    fig,axes=azl.subplots(1,2,sharex=True,sharey=True,figsize=(10,5),
                          subplot_kw={'projection':'mercator'},layout='constrained')
    for ax in axes:
        ax.map('brazil',facecolor='#f3f3f3',edgecolor='#777777',linewidth=.5,fit=False)
        ax.states(facecolor='none',edgecolor='#888888',linewidth=.4,fit=False)
        ax.set_extent((-54,-42,-28,-16))
        ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    axes[0].set_title('Escala adaptativa · km')
    axes[0].scale_bar(units='km',loc='lower left',fontsize=9)
    axes[0].north_arrow(loc='upper right',size=26)
    axes[0].compass(loc='upper left',size=26)
    axes[1].set_title('Outra escala · milhas')
    axes[1].scale_bar(units='mi',loc='lower right',fontsize=10,facecolor='#fff8e8')
    axes[1].north_arrow(loc='upper left',size=26)
    axes[1].compass(loc='upper right',size=26)
    fig.suptitle('Azimlib · componentes acompanhando pan e zoom')
    for extension in ('png','svg'):fig.savefig(folder/f'portable-components.{extension}')
    fig.show(backend='browser',open_browser=False,path=folder/'portable-components.html')
    print('portable-components',flush=True)
    azl.close(fig)
    fig,ax=azl.subplots(projection='mercator')
    ax.set_extent((-54,-42,-28,-16))
    ax.map('brazil',fit=False,facecolor='#f3f3f3',linewidth=.5)
    ax.scale_bar(length=100);ax.north_arrow(size=26)
    ax.set_title('Comprimento explícito: 100 km')
    fig.show(backend='browser',open_browser=False,path=folder/'portable-fixed-scale.html')
