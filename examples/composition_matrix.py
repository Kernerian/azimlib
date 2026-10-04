"""Map, atlas and nested composition; numeric station values are synthetic."""
from pathlib import Path
import azimlib as azl

SIZES={'single':[(5.6,4.6),(6.4,4.8),(8,6)],
       'atlas':[(8,5.6),(10,6),(12,7.2)],'nested':[(8,7.2),(10,8),(12,9)]}


def build(kind='single',layout='constrained',size=None,dpi=100,*,module=azl,real_data=False):
    own=module is azl;size=size or SIZES[kind][1]
    fig=module.figure(figsize=size,dpi=dpi,layout=layout)
    if kind=='single':axes=[fig.add_subplot(111)]
    elif kind=='atlas':axes=list(fig.subplots(1,2,sharex=True).flat)
    elif kind=='nested':
        root=fig.add_gridspec(2,1,height_ratios=[1.1,1]);child=root[1].subgridspec(1,2)
        axes=[fig.add_subplot(root[0]),fig.add_subplot(child[0]),fig.add_subplot(child[1])]
    else:raise ValueError('kind must be single, atlas or nested')
    mapping=None
    for i,ax in enumerate(axes):
        if real_data:
            if own:ax.states(facecolor='#eeeeee',edgecolor='#999999',linewidth=.35,fit=False)
            else:
                from matplotlib.patches import Polygon
                for feature in azl.datasets.load('states',country='brazil')['features']:
                    geometry=feature['geometry']
                    polygons=[geometry['coordinates']] if geometry['type']=='Polygon' else geometry['coordinates']
                    for ring in polygons:ax.add_patch(Polygon(ring[0],facecolor='#eeeeee',edgecolor='#999999',linewidth=.35))
        else:
            ring=[[-53,-27],[-43,-27],[-44,-18],[-51,-20],[-53,-27]]
            if own:ax.polygon(ring,facecolor='#eeeeee',edgecolor='#999999',linewidth=.35)
            else:
                from matplotlib.patches import Polygon
                ax.add_patch(Polygon(ring,facecolor='#eeeeee',edgecolor='#999999',linewidth=.35))
        ax.set_xlim(-54,-42);ax.set_ylim(-28,-16)
        if not own:ax.set_aspect('equal')
        # Explicit compact typography for the small lower maps in the gallery.
        title_size=6 if real_data and kind=='nested' and i else 9
        ax.set_title(f'Painel {i+1}',loc='left',fontsize=title_size,pad=8)
        ax.set_title('Rota',loc='center',fontsize=title_size,pad=8)
        ax.set_title('Estudo',loc='right',fontsize=title_size,pad=8)
        ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
        ax.set_xticks([-52,-48,-44],['52°W','48°W','44°W'])
        ax.set_yticks([-26,-23,-20],['26°S','23°S','20°S'])
        ax.tick_params(labelrotation=25,labelsize=9)
        line,=ax.plot([-52,-49,-45],[-25,-23,-20],color='#115577',linewidth=1,linestyle='--',marker='o',markersize=3,label='Rota')
        mapping=ax.scatter(*([-51,-48,-46],[-24,-22,-21]),c=[0,50,100],s=22,cmap='viridis',vmin=0,vmax=100)
        ax.legend([line],['Rota'],loc='upper left',fontsize=8)
        if own:
            ax.scale_bar(length=100,fontsize=8)
            ax.north_arrow(loc='upper right',size=22)
        if kind=='atlas' and i==1:ax.label_outer()
    fig.suptitle('Composição geográfica\nValores de estações sintéticos',fontsize=12)
    fig.supxlabel('Eixo geográfico comum',fontsize=10)
    fig.supylabel('Latitude dos mapas',fontsize=10)
    orientation='vertical' if kind=='single' else 'horizontal'
    bar=fig.colorbar(mapping,ax=axes[0] if kind=='single' else axes,orientation=orientation,pad=.12)
    bar.set_label('Valor sintético',fontsize=9)
    bar.set_ticks([0,50,100],labels=['0','50','100'])
    return fig,axes,bar


def main():
    output=Path(__file__).resolve().parents[1]/'gallery';output.mkdir(exist_ok=True)
    for kind in SIZES:
        fig,axes,bar=build(kind,real_data=True)
        try:
            for ext in ('svg','png'):fig.savefig(output/f'composition-{kind}.{ext}')
            (output/f'composition-{kind}.html').write_text(fig.to_html(),encoding='utf-8')
        finally:azl.close(fig)


if __name__=='__main__':main()
