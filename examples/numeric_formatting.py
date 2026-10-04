"""Scientific colorbars, optional offsets and editable numeric label artists."""
from pathlib import Path
import azimlib as azl

ROOT=Path(__file__).resolve().parents[1]
LON=[-52,-50,-48,-44];LAT=[-26,-24,-22,-20]

def build(orientation='vertical',*,module=azl):
    fig,axes=module.subplots(1,2,figsize=(9.6,5.4),layout='constrained')
    bars=[];points=[]
    for index,ax in enumerate(axes):
        ax.set_xlim(-54,-42);ax.set_ylim(-28,-16)
        if module is not azl:ax.set_aspect('equal')
        ax.set_facecolor('#f3f4f5');ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
        ax.set_xticks([-52,-48,-44],['52°W','48°W','44°W'])
        ax.set_yticks([-26,-22,-18],['26°S','22°S','18°S'])
        values=[0,.5e6,1e6,2e6] if index==0 else [100000,100000.002,100000.004,100000.006]
        point=ax.scatter(LON,LAT,c=values,s=100,cmap='viridis',vmin=values[0],vmax=values[-1])
        bar=fig.colorbar(point,ax=ax,orientation=orientation,label='Quantidade sintética' if index==0 else 'Leitura sintética',ticks=values)
        axis=bar.ax.yaxis if orientation=='vertical' else bar.ax.xaxis
        axis.get_offset_text().set_color('#444444')
        ax.set_title('Escala científica' if index==0 else 'Offset aditivo')
        bars.append(bar);points.append(point)
    fig.suptitle('Formatação numérica nos mapas\nPontos e valores são exemplos sintéticos',fontsize=12)
    return fig,axes,bars,points

def main():
    for orientation in ('vertical','horizontal'):
        fig,axes,bars,points=build(orientation)
        try:
            for ext in ('png','svg'):fig.savefig(ROOT/f'gallery/numeric-{orientation}.{ext}')
            (ROOT/f'gallery/numeric-{orientation}.html').write_text(fig.to_html(),encoding='utf-8')
        finally:azl.close(fig)

if __name__=='__main__':main()
