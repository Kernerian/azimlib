"""Edit optional components and discard old handles without recreating a map."""
from pathlib import Path
import azimlib as azl


def build():
    fig,ax=azl.subplots(figsize=(8,5.8),layout='tight')
    ax.states(facecolor='#eeeeee',edgecolor='#999999',linewidth=.35,fit=False)
    ax.set_extent((-54,-43,-27,-19))
    title=ax.set_title('Componentes: antes',fontsize=13)
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    ax.set_xticks([-52,-48,-44],['52°W','48°W','44°W'])
    ax.set_yticks([-26,-23,-20],['26°S','23°S','20°S'])
    route,=ax.plot([-52,-49,-46],[-25,-23,-21],color='#d65f45',linewidth=1,
                   linestyle='--',label='Rota de estudo')
    points=ax.scatter(lon=[-51,-48,-46.5],lat=[-24,-22,-20.5],c=[0,50,100],
                      s=30,cmap='viridis',vmin=0,vmax=100,label='Estações')
    legend=ax.legend(title='Camadas',loc='upper left',fontsize=9)
    scale=ax.scale_bar(length=200)
    ax.compass(loc='upper right',size=34);ax.north_arrow(loc='lower right',size=28)
    bar=fig.colorbar(points,ax=ax,orientation='horizontal',pad=.16)
    bar.set_label('Valor por estação');bar.set_ticks([0,50,100],labels=['0','50','100'])
    return fig,ax,dict(title=title,route=route,points=points,legend=legend,scale=scale,bar=bar)


def edit(ax,handles):
    handles['title'].set_text('Componentes: edição, visibilidade e substituição')
    handles['route'].set(color='#115577',linestyle='-.')
    handles['legend'].get_title().set_visible(False)
    previous_scale=handles['scale']
    handles['scale']=ax.scale_bar(length=100,fontsize=9)
    previous_bar=handles['bar']
    handles['bar']=ax.colorbar(handles['points'],orientation='horizontal',pad=.16)
    handles['points'].set_clim(0,150)
    handles['bar'].set_label('Valor por estação — escala atualizada')
    handles['bar'].set_ticks([0,50,100,150],labels=['0','50','100','150'])
    assert previous_scale.get_figure() is None and previous_bar.get_figure() is None
    previous_scale.set_visible(True)  # Already discarded: cannot rejoin the map.
    previous_bar.set_label('Barra descartada')
    return previous_scale,previous_bar


def main():
    output=Path(__file__).resolve().parents[1]/'gallery';output.mkdir(exist_ok=True)
    fig,ax,handles=build()
    try:
        for stage in ('before','after'):
            if stage=='after':edit(ax,handles)
            for format in ('svg','png'):
                fig.savefig(output/f'component-lifecycle-{stage}.{format}')
            (output/f'component-lifecycle-{stage}.html').write_text(fig.to_html(),encoding='utf-8')
    finally:azl.close(fig)


if __name__=='__main__':main()
