"""Shared colors and explicit data/view updates, implemented by Azimlib."""
from pathlib import Path
import azimlib as azl
from azimlib.colors import Normalize
from azimlib import ticker as t


def background(ax):
    ax.map('brazil',fit=False,facecolor='#f4f4f4',edgecolor='#777777',linewidth=.5)
    ax.states(fit=False,edgecolor='#999999',linewidth=.35)
    ax.state('SP',fit=False,facecolor='#e9edf0',edgecolor='#7a8996',linewidth=.5)
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    ax.xaxis.set_major_formatter(t.LongitudeFormatter())
    ax.yaxis.set_major_formatter(t.LatitudeFormatter())
    ax.grid(True,color='#cccccc',linestyle='--',linewidth=.4)


def shared_colors():
    fig,axs=azl.subplots(1,2,figsize=(10.4,5.4),projection='mercator',layout='constrained')
    norm=Normalize(0,100)
    for ax,title,values in zip(axs,('Cenário A','Cenário B'),([25,60,90,100],[40,75,100,150])):
        background(ax);ax.set_extent((-54,-43,-27,-19));ax.set_title(title)
        layer=ax.scatter([-51.38,-49.4,-46.63,-45.88],[-22.12,-24.1,-23.55,-23.18],
                         s=[65]*4,c=values,norm=norm,edgecolor='white',linewidth=.5)
    bar=fig.colorbar(layer,ax=axs,orientation='horizontal',label='Intensidade sintética · normalização compartilhada')
    bar.locator=t.MultipleLocator(50);bar.minorlocator=t.AutoMinorLocator(5)
    fig.suptitle('Dois mapas · a mesma escala de cores',fontsize=13)
    return fig,norm


def limits():
    fig,axs=azl.subplots(1,2,figsize=(10.4,5.4),projection='mercator',layout='constrained')
    lines=[]
    for ax,title in zip(axs,('Vista automática','Vista manual preservada')):
        background(ax)
        line,=ax.plot([-53,-50,-46.63],[-26,-21,-23.55],'o--',color='#1f77b4',linewidth=1.3,markersize=4,label='Rota esquemática')
        lines.append(line);ax.set_title(title)
        ax.legend(loc='upper left',fontsize=8)
        ax.scale_bar(loc='lower right',fontsize=8)
    axs[0].margins(.1);axs[1].set_extent((-54,-43,-28,-17))
    fig.suptitle('Edição dos dados · controle da vista',fontsize=13)
    return fig,axs,lines


def export(fig,name):
    folder=Path(__file__).resolve().parents[1]/'gallery'
    for extension in ('png','svg'):fig.savefig(folder/f'{name}.{extension}')
    fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
    print(name,flush=True)


if __name__=='__main__':
    fig,norm=shared_colors();export(fig,'shared-norm-before')
    norm.vmax=200  # Both layers and the shared colorbar receive this signal.
    export(fig,'shared-norm-after');azl.close(fig)
    fig,axs,lines=limits();export(fig,'data-limits-before')
    for ax,line in zip(axs,lines):
        line.set_data([-54,-50,-47,-43],[-28,-24,-20,-18])
        line.set(color='#d62728',linestyle='-.')
        ax.relim();ax.autoscale_view()
    export(fig,'data-limits-after');azl.close(fig)
