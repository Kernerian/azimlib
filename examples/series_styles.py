"""Real boundaries, synthetic routes; optional ornaments are explicit."""
from pathlib import Path
import azimlib as azl

ROOT=Path(__file__).resolve().parents[1]
SHEET=Path(__file__).parent/'styles/routes.mplstyle'
LON=[-52,-50,-48,-46,-44]
LAT=[[-26,-24,-23],[-25.5,-23.5,-22.5],[-24,-22.5,-22],[-23,-21.5,-21],[-22,-20,-19.5]]


def build(theme='light',*,module=azl,real_data=True):
    own=module is azl
    styles=['default' if theme=='light' else 'dark_background',SHEET]
    with module.style.context(styles):
        fig,axes=module.subplots(1,2,sharex=True,sharey=True,figsize=(9.6,5.6),layout='constrained')
        for i,ax in enumerate(axes):
            if real_data:
                if own:ax.states(fit=False,facecolor='#242b33' if theme=='dark' else '#f3f4f5',edgecolor='#808890',linewidth=.35)
                else:
                    from matplotlib.patches import Polygon
                    for feature in azl.datasets.load('states',country='brazil')['features']:
                        geometry=feature['geometry'];polygons=[geometry['coordinates']] if geometry['type']=='Polygon' else geometry['coordinates']
                        for polygon in polygons:ax.add_patch(Polygon(polygon[0],facecolor='#242b33' if theme=='dark' else '#f3f4f5',edgecolor='#808890',linewidth=.35))
            ax.set_xlim(-54,-42);ax.set_ylim(-28,-16)
            if not own:ax.set_aspect('equal')
            ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
            ax.set_xticks([-52,-48,-44],['52°W','48°W','44°W'])
            ax.set_yticks([-26,-22,-18],['26°S','22°S','18°S']);ax.tick_params(labelsize=9)
            if i==0:
                lines=ax.plot(LON,LAT,label=['Trajeto A','Trajeto B','Trajeto C'])
                ax.grid(True,color='#888888',linewidth=.4,linestyle='--',alpha=.45)
                ax.set_title('Séries por coluna')
            else:
                named=ax.plot('longitude','latitude',data={'longitude':LON,'latitude':[r[0] for r in LAT]},label='Trajeto por nome')
                ax.scatter([-51,-47],[-24,-21],s=24,label='Estações sintéticas')
                ax.set_title('data= e ciclo dos pontos')
            ax.legend(loc='upper left')
            if own:
                ax.scale_bar(length=100,fontsize=8,facecolor=ax.facecolor,color='white' if theme=='dark' else 'black')
                ax.north_arrow(size=22,color='white' if theme=='dark' else 'black')
        fig.suptitle('Traçados e estilos geográficos\nRotas e estações são exemplos sintéticos',fontsize=12)
    return fig,axes,lines,named


def edit(axes,lines,named,theme='light',*,module=azl):
    lines[1].set(color='#9467bd',linewidth=1.3,marker='D')
    lines[2].set_visible(False)
    named[0].set_data([-51,-49,-47,-44],[-25,-23,-21,-19])
    axes[0].set_prop_cycle(color=['#8c564b'])
    axes[0].plot([-52,-48,-44],[-27,-26.5,-26],linewidth=.8,label='Nova série')
    # Rebuild a legend explicitly; it is not implicitly regenerated on hide/edit.
    with module.style.context(['default' if theme=='light' else 'dark_background',SHEET]):
        for ax in axes:ax.legend(loc='upper left')


def main():
    output=ROOT/'gallery'
    for theme in ('light','dark'):
        fig,axes,lines,named=build(theme)
        try:
            for phase in ('before','after'):
                if phase=='after':edit(axes,lines,named,theme)
                for ext in ('png','svg'):fig.savefig(output/f'series-{theme}-{phase}.{ext}')
                (output/f'series-{theme}-{phase}.html').write_text(fig.to_html(),encoding='utf-8')
        finally:azl.close(fig)


if __name__=='__main__':main()
