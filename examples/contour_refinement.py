"""Per-level colors, unfilled contour bars and reversible inline labels."""
import math
from pathlib import Path
import azimlib as azl
from azimlib.colors import ListedColormap
from azimlib.ticker import LongitudeFormatter,LatitudeFormatter


def field():
    x=[-54+11*i/36 for i in range(37)]
    y=[-28+10*j/36 for j in range(37)]
    z=[[100*math.exp(-((lon+48)**2/9+(lat+23)**2/12)) for lon in x] for lat in y]
    return x,y,z


def create():
    fig,axes=azl.subplots(1,2,figsize=(10,5.8),projection='mercator',layout='constrained')
    contours=[];labels=[]
    x,y,z=field()
    for ax,spacing in zip(axes,('uniform','proportional')):
        ax.set_extent((-54,-43,-28,-18))
        ax.set_title('Isolinhas · '+spacing)
        ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
        ax.xaxis.set_major_formatter(LongitudeFormatter())
        ax.yaxis.set_major_formatter(LatitudeFormatter())
        ax.set_facecolor('#eef2f5')
        ax.states(facecolor='none',edgecolor='#999999',linewidth=.35,fit=False)
        cs=ax.contour(x,y,z,levels=[20,40,80],colors=['#225ea8','#1b9e77','#c75b12'],
                      linewidths=[.65,.85,1.05],linestyles=['--',':','-'],zorder=3)
        texts=ax.clabel(cs,fmt='%g',fontsize=9,inline=False,halo=None,padding=1)
        bar=fig.colorbar(cs,ax=ax,orientation='horizontal',spacing=spacing,
                         label='Intensidade sintética · valores por nível')
        bar.ax.tick_params(labelsize=9)
        contours.append(cs);labels.append(texts)
    fig.suptitle('Azimlib · contornos e colorbars de linhas',fontsize=14)
    return fig,contours,labels


def export(fig,name):
    folder=Path(__file__).resolve().parents[1]/'gallery'
    for extension in ('png','svg'):fig.savefig(folder/f'{name}.{extension}')
    fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
    print(name,flush=True)


if __name__=='__main__':
    fig,contours,labels=create()
    export(fig,'contour-refinement-before')
    for cs,texts in zip(contours,labels):
        cs.set(cmap=ListedColormap(['#7b3294','#008837','#d95f02']),linewidths=[.7,.9,1.1])
        azl.setp(texts,inline=True,inline_spacing=5,fontsize=9)
    fig.suptitle('Azimlib · cortes sob rótulos e paleta atualizada',fontsize=14)
    export(fig,'contour-refinement-after');azl.close(fig)
