"""Optional major/minor graticules and editable horizontal/log colorbars."""
from pathlib import Path
import math
import azimlib as azl
from azimlib import ticker as t
from azimlib.colors import Normalize,LogNorm


def region(title):
    fig,ax=azl.subplots(figsize=(7.4,6.2),projection='mercator',layout='tight')
    ax.map('brazil',facecolor='#f5f5f5',edgecolor='#777777',linewidth=.5)
    ax.states(edgecolor='#999999',linewidth=.4)
    ax.set_extent((-54,-44,-26,-19))
    ax.set_title(title,fontsize=13)
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    ax.xaxis.set_major_locator(t.MultipleLocator(2));ax.yaxis.set_major_locator(t.MultipleLocator(2))
    ax.xaxis.set_major_formatter(t.LongitudeFormatter());ax.yaxis.set_major_formatter(t.LatitudeFormatter())
    return fig,ax


def grid():
    fig,ax=region('São Paulo · ticks e grades independentes')
    ax.state('SP',facecolor='#e0edf5',edgecolor='#4c6d83',linewidth=.6)
    ax.xaxis.set_minor_locator(t.AutoMinorLocator(4));ax.yaxis.set_minor_locator(t.AutoMinorLocator(4))
    ax.tick_params(which='major',length=3.5,width=.8)
    ax.tick_params(which='minor',length=2,width=.6)
    ax.grid(True,which='major',labels=False,color='#aaaaaa',linestyle='--',linewidth=.5)
    ax.grid(True,which='minor',color='#dddddd',linestyle=':',linewidth=.3)
    ax.scatter([-46.63],[-23.55],s=14,color='#334a5b')
    ax.annotate('São Paulo',(-46.63,-23.55),xytext=(-70,-20),fontsize=9,color='#334a5b',linewidth=.6)
    ax.scale_bar(length=200,fontsize=8)
    return fig


def colorbar(*,logarithmic=False):
    fig,ax=region('Colorbar logarítmica · subdivisões' if logarithmic else 'Colorbar horizontal · ticks menores')
    lon=[-54+i*.5 for i in range(21)];lat=[-26+j*.5 for j in range(15)]
    values=[[((1+math.sin(i*.4)*math.cos(j*.3))/2)*99+1 for i in range(20)] for j in range(14)]
    if logarithmic:values=[[10**(v*3/100) for v in row] for row in values]
    layer=ax.pcolormesh(lon,lat,values,norm=LogNorm(1,1000) if logarithmic else Normalize(0,100),cmap='viridis')
    ax.states(edgecolor='#eeeeee',linewidth=.5)
    bar=fig.colorbar(layer,ax=ax,orientation='vertical' if logarithmic else 'horizontal',label='Campo sintético · unidades arbitrárias')
    if not logarithmic:bar.locator=t.MultipleLocator(25)
    bar.minorticks_on()
    bar.ax.tick_params(which='minor',length=2,width=.6,direction='out')
    ax.minorticks_on()  # No grid or minimap is added implicitly.
    return fig


if __name__=='__main__':
    folder=Path(__file__).resolve().parents[1]/'gallery'
    for name,make in (('minor-grid',grid),('minor-colorbar-horizontal',colorbar),
                      ('minor-colorbar-log',lambda:colorbar(logarithmic=True))):
        fig=make()
        for extension in ('png','svg'):fig.savefig(folder/f'{name}.{extension}')
        fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
        azl.close(fig);print(name,flush=True)
