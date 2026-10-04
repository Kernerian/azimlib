"""Edit geographic positions, proportional marker areas and mapped values."""
from pathlib import Path
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.ticker import LongitudeFormatter,LatitudeFormatter,MultipleLocator


def create():
    fig,ax=azl.subplots(figsize=(7,6),projection='mercator',layout='constrained')
    ax.map('brazil',fit=False,facecolor='#f5f5f5',edgecolor='#888888',linewidth=.5)
    ax.states(fit=False,edgecolor='#999999',linewidth=.4)
    ax.state('SP',fit=False,facecolor='#e9eef2',edgecolor='#667788',linewidth=.6)
    points=ax.scatter([-51.38,-49.4,-46.63],[-25.0,-21.8,-23.55],s=[36,100,196],
                      c=[25,60,90],norm=Normalize(0,100),edgecolor='white',linewidth=.5,label='Estações sintéticas')
    ax.set_title('Scatter · posições e áreas iniciais')
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    ax.xaxis.set_major_formatter(LongitudeFormatter());ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.grid(True,color='#cccccc',linestyle='--',linewidth=.4)
    ax.legend(loc='upper left',fontsize=9)
    bar=fig.colorbar(points,ax=ax,orientation='horizontal',label='Valor sintético')
    bar.locator=MultipleLocator(25)
    ax.scale_bar(loc='lower right',fontsize=8)
    ax.margins(.25)
    return fig,ax,points


def export(fig,name):
    folder=Path(__file__).resolve().parents[1]/'gallery'
    for extension in ('png','svg'):fig.savefig(folder/f'{name}.{extension}')
    fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
    print(name,flush=True)


if __name__=='__main__':
    fig,ax,points=create();export(fig,'scatter-before')
    azl.setp(points,offsets=[[-52,-25.6],[-49,-21.8],[-46.63,-23.55],[-45.88,-23.18]],
             sizes=[64,144,256,100],array=[15,45,75,100])
    ax.set_title('Scatter · posições, áreas e valores editados')
    ax.relim();ax.autoscale_view()
    export(fig,'scatter-after');azl.close(fig)
