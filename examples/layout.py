"""Automatic decoration margins with the compact azl import alias."""
from pathlib import Path
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.ticker import LongitudeFormatter,LatitudeFormatter,MultipleLocator


def atlas():
    fig,axes=azl.subplots(2,2,figsize=(10,8),layout='constrained')
    fig.suptitle('Atlas regional · margens automáticas',fontsize=16)
    regions=(('SP','São Paulo',(-54,-44,-26,-19)),
             ('RJ','Rio de Janeiro',(-45,-40,-24,-20)),
             ('MG','Minas Gerais',(-52,-39,-25,-14)),
             ('PR','Paraná',(-56,-47,-28,-21)))
    norm=Normalize(0,100)
    for ax,(code,name,extent) in zip(axes.flat,regions):
        ax.states(facecolor='#f1f1f1',edgecolor='#888888',linewidth=.4)
        ax.state(code,facecolor='#e2e6e9',edgecolor='#333333',linewidth=.7)
        # Marker colors are demonstrative values, not population statistics.
        west,east,south,north=extent
        values=ax.scatter([west+(east-west)*t for t in (.35,.5,.65)],
                          [south+(north-south)*t for t in (.4,.5,.6)],
                          c=[20,50,80],s=[16,28,40],cmap='viridis',norm=norm,
                          edgecolor='white',linewidth=.4)
        ax.set_extent(extent)
        ax.set_title(name,fontsize=12)
        ax.subtitle('Foco regional · '+code,fontsize=9)
        ax.xaxis.set_major_formatter(LongitudeFormatter())
        ax.yaxis.set_major_formatter(LatitudeFormatter())
        ax.tick_params(labelsize=9,labelrotation=25)
        ax.set_xlabel('Longitude',fontsize=10);ax.set_ylabel('Latitude',fontsize=10)
        ax.grid(labels=False,linewidth=.4,color='#b0b0b0',linestyle=':')
    bar=fig.colorbar(values,ax=axes,orientation='horizontal',label='Indicador sintético · sem significado estatístico',fraction=.08,pad=.10,shrink=.85)
    bar.locator=MultipleLocator(20)
    return fig


def external_legend():
    fig,ax=azl.subplots(figsize=(8,6),projection='mercator',layout='tight')
    ax.states(facecolor='#f1f1f1',edgecolor='#888888',linewidth=.4)
    ax.state('SP',facecolor='#e4d7b4',edgecolor='#444444',linewidth=.7)
    ax.plot([-50.2,-48.3,-46.63],[-22.5,-22.1,-23.55],color='#d65f45',linewidth=1.5,linestyle='--',label='Rota demonstrativa')
    ax.scatter([-46.63],[-23.55],color='#356da3',s=28,label='São Paulo')
    ax.set_extent((-54,-43,-26,-19))
    ax.set_title('São Paulo · legenda externa\nEspaço calculado pelos componentes',fontsize=14)
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    ax.xaxis.set_major_formatter(LongitudeFormatter());ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.legend(loc='center left',bbox_to_anchor=(1.02,.5),fontsize=10)
    # Grid, scale, north and overview only appear when explicitly added.
    return fig


if __name__=='__main__':
    folder=Path(__file__).resolve().parents[1]/'gallery'
    for name,make in (('layout-atlas',atlas),('layout-legend',external_legend)):
        fig=make()
        for ext in ('png','svg'):fig.savefig(folder/f'{name}.{ext}')
        fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
        azl.close(fig);print(name,flush=True)
