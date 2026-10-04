"""A regional atlas with editable shared labels; no reference dependencies."""
from pathlib import Path
import azimlib as azl
from azimlib.cm import ScalarMappable
from azimlib.colors import Normalize


def atlas():
    fig,axes=azl.subplots(1,2,figsize=(9,6),layout='constrained')
    for index,ax in enumerate(axes.flat):
        ax.states(facecolor='#eeeeee',edgecolor='#777777',linewidth=.4,fit=False)
        ax.set_extent((-54,-42,-28,-16))
        ax.set_title(f'Área {index+1}',fontsize=11)
        ax.tick_params(labelsize=9,labelrotation=25)
        ax.plot([-52,-48,-44],[-25,-22,-20],color='#d65f45',linestyle='--',linewidth=1,label='Rota demonstrativa')
    axes[0].scale_bar(loc='lower left',fontsize=8)
    axes[1].north_arrow(loc='upper right')
    axes[1].legend(loc='lower right',fontsize=8)
    bar=fig.colorbar(ScalarMappable(Normalize(0,100)),ax=axes,orientation='horizontal',label='Indicador sintético')
    bar.ax.tick_params(labelsize=9)
    fig.suptitle('Atlas regional\nComponentes adicionados explicitamente',fontsize=14)
    fig.supxlabel('Longitude geográfica')
    fig.supylabel('Latitude geográfica')
    return fig


if __name__=='__main__':
    folder=Path(__file__).resolve().parents[1]/'gallery'
    fig=atlas()
    fig.savefig(folder/'figure-labels-atlas.png')
    fig.savefig(folder/'figure-labels-atlas.svg')
    fig.show(backend='browser',open_browser=False,path=folder/'figure-labels-atlas.html')
    azl.close(fig)
