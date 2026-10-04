"""One national map spans two rows beside two regional maps.

The same synthetic values and normalization are shown at three geographic
scales. Ornament components are explicitly added, never layout defaults.
"""
from pathlib import Path
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.ticker import LongitudeFormatter,LatitudeFormatter,MultipleLocator


def create():
    fig=azl.figure(figsize=(12,8),layout='constrained')
    gs=fig.add_gridspec(2,3,width_ratios=[2.3,1,1],height_ratios=[1,1])
    brazil=fig.add_subplot(gs[:,0],projection='mercator')
    minas=fig.add_subplot(gs[0,1:],projection='mercator')
    sao_paulo=fig.add_subplot(gs[1,1:],projection='mercator')
    axes=[brazil,minas,sao_paulo]
    states=azl.datasets.load('states',country='brazil')
    values=[(i*17)%101 for i in range(len(states['features']))]
    norm=Normalize(0,100)
    fields=[]
    for ax in axes:
        ax.ocean('#edf4f8')
        fields.append(ax.choropleth(states,values,bins=None,cmap='viridis',norm=norm,
                                    edgecolor='#777777',linewidth=.4))
        ax.xaxis.set_major_formatter(LongitudeFormatter())
        ax.yaxis.set_major_formatter(LatitudeFormatter())
        ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    brazil.map('brazil',fit=False,facecolor='none',edgecolor='#333333',linewidth=.7,zorder=4)
    brazil.set_extent((-76,-32,-36,8));brazil.set_title('Brasil · mapa nacional')
    # Independent compass rose and north arrow coexist in distinct positions.
    brazil.compass(loc='upper left',size=23);brazil.north_arrow(loc='upper right',size=23)
    brazil.grid(labels=False,color='#b0b0b0',linewidth=.4,linestyle=':')
    minas.state('MG',facecolor='none',edgecolor='#222222',linewidth=.8,zorder=4)
    minas.set_title('Minas Gerais · foco regional')
    minas.scale_bar(length=200,loc='lower left',fontsize=8)
    sao_paulo.state('SP',facecolor='none',edgecolor='#222222',linewidth=.8,zorder=4)
    sao_paulo.set_title('São Paulo · foco regional')
    sao_paulo.scale_bar(length=100,loc='lower left',fontsize=8)
    bar=fig.colorbar(fields[0],ax=axes,orientation='horizontal',fraction=.055,pad=.10,
                     label='Indicador sintético por estado · exemplo sem significado estatístico')
    bar.locator=MultipleLocator(20)
    fig.suptitle('Atlas geográfico · GridSpec e painéis com spans',fontsize=15)
    return fig,gs,axes


if __name__=='__main__':
    folder=Path(__file__).resolve().parents[1]/'gallery'
    fig,gs,axes=create()
    for extension in ('png','svg'):fig.savefig(folder/f'gridspec-atlas.{extension}')
    fig.show(backend='browser',open_browser=False,path=folder/'gridspec-atlas.html')
    print('gridspec-atlas',flush=True);azl.close(fig)
