"""Edit geographic text, annotation coordinates and component titles in place."""
from pathlib import Path
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.cm import ScalarMappable


def build():
    fig,ax=azl.subplots(figsize=(7,6),layout='constrained')
    ax.states(facecolor='#eeeeee',edgecolor='#888888',linewidth=.4,fit=False)
    ax.set_extent((-54,-42,-28,-16));ax.set_title('Texto e componentes editáveis')
    line,=ax.plot([-52,-48,-44],[-25,-22,-20],color='#d65f45',linewidth=1,label='Rota de pesquisa')
    text=ax.text(-49,-23,'Local inicial',color='#115577',ha='center',fontsize=10)
    note=ax.annotate('Destino inicial',(-48,-22),(18,20),textcoords='offset points',color='#553377',fontsize=10)
    legend=ax.legend(loc='lower right',fontsize=9,title='Pesquisa')
    bar=fig.colorbar(ScalarMappable(Normalize(0,100)),ax=ax,orientation='horizontal',label='Indicador inicial')
    ax.scale_bar(loc='lower left',fontsize=8)
    return fig,text,note,legend,bar


def edit(text,note,legend,bar):
    text.set(position=(-50,-24),text='Local editado',ha='right',va='top',color='#1f77b4',fontsize=11)
    note.set(xy=(-44,-20),position=(-100,-26),text='Destino editado',fontweight='bold')
    legend.set_title('Pesquisa atualizada',fontsize=10,color='#333333')
    bar.set_label('Indicador atualizado',labelpad=6,fontsize=11)


if __name__=='__main__':
    folder=Path(__file__).resolve().parents[1]/'gallery'
    fig,text,note,legend,bar=build()
    for phase in ('before','after'):
        if phase=='after':edit(text,note,legend,bar)
        fig.savefig(folder/f'component-text-edits-{phase}.png')
        fig.savefig(folder/f'component-text-edits-{phase}.svg')
        fig.show(backend='browser',open_browser=False,path=folder/f'component-text-edits-{phase}.html')
    azl.close(fig)
