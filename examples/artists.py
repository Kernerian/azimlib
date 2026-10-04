"""Edit the same map's artists; no Matplotlib imports or backend."""
from pathlib import Path
import azimlib as azl
from azimlib import ticker


def create():
    fig,ax=azl.subplots(figsize=(8,5.7),projection='mercator',layout='tight')
    ax.map('brazil',facecolor='#f4f4f4',edgecolor='#888888',linewidth=.5)
    ax.states(edgecolor='#999999',linewidth=.35)
    ax.state('SP',facecolor='#e6edf3',edgecolor='#6e879b',linewidth=.6)
    ax.set_extent((-54,-43,-26.5,-19))
    title=ax.set_title('Artists · mapa inicial',fontsize=13)
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    ax.xaxis.set_major_formatter(ticker.LongitudeFormatter())
    ax.yaxis.set_major_formatter(ticker.LatitudeFormatter())
    line,=ax.plot([-52,-49,-46.63],[-24.7,-23.3,-23.55],'o--',
                 color='#1f77b4',linewidth=1.3,markersize=4,label='Rota demonstrativa')
    points=ax.scatter([-51.38,-46.63],[-22.12,-23.55],s=[30,55],c=[20,80],vmin=0,vmax=100)
    ax.annotate('São Paulo',(-46.63,-23.55),xytext=(-45,-28),fontsize=9,linewidth=.6)
    legend=ax.legend(handles=[line],loc='upper right',fontsize=9)
    scale=ax.scale_bar(length=200,loc='lower left',fontsize=8)
    north=ax.north_arrow(loc='lower right',size=22)
    bar=fig.colorbar(points,ax=ax,orientation='horizontal',label='Valores sintéticos')
    bar.locator=ticker.MultipleLocator(25)
    return fig,dict(ax=ax,title=title,line=line,points=points,legend=legend,scale=scale,north=north,bar=bar)


def edit(fig,artists):
    a=artists
    a['title'].set_text('Artists · o mesmo mapa após edição')
    a['line'].set_data([-52,-50,-48,-46.63],[-24.7,-25,-24,-23.55])
    azl.setp(a['line'],color='#d62728',linestyle='-.',linewidth=1.5)
    a['legend'].get_frame().set_edgecolor('#999999')
    a['scale'].set_length(100)
    a['north'].set_visible(False)
    a['points'].set_array([45,120]);a['points'].set_clim(0,150)
    a['bar'].locator=ticker.MultipleLocator(50)
    a['bar'].set_label('Valores sintéticos · escala atualizada')
    a['ax'].minorticks_on()
    fig.canvas.draw_idle()


if __name__=='__main__':
    folder=Path(__file__).resolve().parents[1]/'gallery'
    fig,artists=create();changes=[]
    cid=artists['line'].add_callback(lambda artist:changes.append(artist.get_color()))
    for name in ('artists-before','artists-after'):
        if name.endswith('after'):edit(fig,artists)
        for extension in ('png','svg'):fig.savefig(folder/f'{name}.{extension}')
        fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
        print(name,flush=True)
    artists['line'].remove_callback(cid)
    print(f'Line changes notified: {len(changes)}',flush=True)
    azl.close(fig)
