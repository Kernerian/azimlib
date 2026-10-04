"""Edit data, normalization, palette and appearance using the same handles."""
import math
from pathlib import Path
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.ticker import LongitudeFormatter,LatitudeFormatter


EXTENT=(-54,-43,-28,-18)


def field(nx,ny,center,amplitude):
    return [[amplitude*math.exp(-(((i+.5)/nx-center)**2/.07+((j+.5)/ny-.5)**2/.16))
             for i in range(nx)] for j in range(ny)]


def create():
    fig,axes=azl.subplots(1,2,figsize=(8.8,5.2),projection='mercator',layout='constrained')
    norm=Normalize(0,100)
    image=axes[0].imshow(field(12,10,.35,90),extent=EXTENT,origin='lower',norm=norm)
    x=[-54+11*i/8 for i in range(9)];y=[-28+10*j/6 for j in range(7)]
    mesh=axes[1].pcolormesh(x,y,field(8,6,.35,90),norm=norm)
    for ax,title in zip(axes,('Imagem escalar','Malha de células')):
        ax.states(fit=False,facecolor='none',edgecolor='#777777',linewidth=.4,zorder=3)
        ax.set_extent(EXTENT);ax.set_title(title)
        ax.xaxis.set_major_formatter(LongitudeFormatter());ax.yaxis.set_major_formatter(LatitudeFormatter())
        ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    bar=fig.colorbar(image,ax=axes,orientation='horizontal',label='Valor sintético')
    fig.suptitle('Campos geográficos · valores iniciais',fontsize=14)
    return fig,image,mesh,bar


def export(fig,name):
    folder=Path(__file__).resolve().parents[1]/'gallery'
    for extension in ('png','svg'):fig.savefig(folder/f'{name}.{extension}')
    fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
    print(name,flush=True)


if __name__=='__main__':
    fig,image,mesh,bar=create();export(fig,'mapping-before')
    updated=Normalize()
    image.set(data=field(16,12,.65,180),norm=updated,cmap='plasma',clim=(0,200),alpha=.9)
    azl.setp(mesh,array=field(8,6,.65,180),norm=updated,cmap='plasma',alpha=.9)
    bar.set_label('Valor sintético · intervalo atualizado')
    fig.suptitle('Campos geográficos · valores e cores atualizados',fontsize=14)
    export(fig,'mapping-after');azl.close(fig)
