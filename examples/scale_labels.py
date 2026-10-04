"""Scale graduations adapt to map width without shrinking type or distance."""
from pathlib import Path
import azimlib as azl
from azimlib.ticker import LongitudeFormatter,LatitudeFormatter


def create():
    fig,axes=azl.subplots(1,3,figsize=(13,5.5),width_ratios=[4,2,1],layout='constrained')
    for ax,title in zip(axes,('Mapa largo','Mapa médio','Mapa estreito')):
        ax.states(fit=False,facecolor='#eeeeee',edgecolor='#888888',linewidth=.4)
        ax.set_extent((-54,-43,-26,-19));ax.set_title(title,fontsize=11)
        ax.xaxis.set_major_formatter(LongitudeFormatter());ax.yaxis.set_major_formatter(LatitudeFormatter())
        ax.scale_bar(length=100,fontsize=9)
    fig.suptitle('Escala adaptativa · mesma distância e mesma fonte',fontsize=14)
    return fig


if __name__=='__main__':
    fig=create();folder=Path(__file__).resolve().parents[1]/'gallery'
    for ext in ('png','svg'):fig.savefig(folder/f'scale-labels.{ext}')
    fig.show(backend='browser',open_browser=False,path=folder/'scale-labels.html')
    azl.close(fig);print('scale-labels',flush=True)
