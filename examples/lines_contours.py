"""Five related Artist advances: routes, markers, contour styling and labels."""
import math
from pathlib import Path
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.ticker import LongitudeFormatter,LatitudeFormatter


def create():
    fig,axes=azl.subplots(1,2,figsize=(10,5.8),projection='mercator',layout='constrained')
    route_ax,terrain_ax=axes
    extent=(-54,-43,-28,-18)
    for ax,title in zip(axes,('Rotas e marcadores','Campo sintético e isolinhas')):
        ax.set_extent(extent)
        ax.set_title(title)
        ax.xaxis.set_major_formatter(LongitudeFormatter())
        ax.yaxis.set_major_formatter(LatitudeFormatter())
        ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    route_ax.states(facecolor='#f3f3f3',edgecolor='#999999',linewidth=.4,fit=False)
    main,=route_ax.plot([-52,-49,-46],[-25,-24,-21],'o-',color='#d62728',linewidth=1.2,label='Rota principal')
    alternate,=route_ax.plot([-52,-50,-47,-44],[-25,-21,-20,-19],'s--',color='#2ca02c',linewidth=1.,markersize=4,label='Alternativa')
    route_ax.legend(loc='upper left',fontsize=9)
    route_ax.scale_bar(length=200,fontsize=8)
    route_ax.north_arrow(size=22)
    x=[-54+11*i/24 for i in range(25)];y=[-28+10*j/24 for j in range(25)]
    z=[[100*math.exp(-((lon+48)**2/9+(lat+23)**2/12)) for lon in x] for lat in y]
    field=terrain_ax.imshow(z,extent=extent,origin='lower',norm=Normalize(0,100),cmap='terrain')
    terrain_ax.states(facecolor='none',edgecolor='#777777',linewidth=.4,fit=False,zorder=3)
    contours=terrain_ax.contour(x,y,z,levels=[20,40,60,80],colors='#333333',linewidths=[.45,.6,.75,.9],zorder=4)
    labels=contours.clabel(fmt='%g',fontsize=8,colors='black',halo='white',padding=1)
    fig.colorbar(field,ax=terrain_ax,orientation='horizontal',label='Intensidade sintética')
    fig.suptitle('Azimlib · linhas e contornos editáveis',fontsize=14)
    return fig,main,alternate,contours,labels


def export(fig,name):
    folder=Path(__file__).resolve().parents[1]/'gallery'
    for extension in ('png','svg'):fig.savefig(folder/f'{name}.{extension}')
    fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
    print(name,flush=True)


if __name__=='__main__':
    fig,main,alternate,contours,labels=create()
    export(fig,'lines-contours-before')
    main.set(data=([-52,-50,-47,-44],[-25,-26,-23,-20]),marker='^',markersize=5,
        markerfacecolor='white',markeredgecolor='#d62728',markeredgewidth=.7,
        linewidth=1.1,solid_capstyle='butt',solid_joinstyle='round')
    azl.setp(alternate,linestyle=':',marker='s',markersize=4,dash_capstyle='round')
    contours.set(colors=['#225ea8','#1d91c0','#41b6c4','#084081'],
        linewidths=[.55,.75,.95,1.15],linestyles=['--',':','-.','-'])
    azl.setp(labels,fontsize=8,fontweight='bold')
    labels[0].set_text('20*')
    labels[-1].set_visible(False)
    fig.suptitle('Azimlib · mesmos handles, propriedades atualizadas',fontsize=14)
    export(fig,'lines-contours-after');azl.close(fig)
