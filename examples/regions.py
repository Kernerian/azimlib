"""Whole country, single state, and zoom with locator. Data work offline.

Run python examples/regions.py [--show]; keys 1..5 toggle optional artists
in the desktop example, using mpl_connect and set_visible explicitly.
"""
import argparse
from pathlib import Path
import azimlib.pyplot as plt

def create(kind):
    fig,ax=plt.subplots(figsize=(8,8) if kind=='brazil' else (9,6.5),projection='mercator')
    fig.subplots_adjust(left=.1,right=.96,bottom=.1,top=.87)
    ax.set_facecolor('#dceaf2')
    if kind=='brazil':
        ax.map('brazil',facecolor='white',edgecolor='#333333')
        ax.states(linewidth=.45,label='Limites estaduais')
        title='BRASIL — EXTENSÃO COMPLETA'
        orient=ax.compass(loc='upper left',size=32)
    else:
        ax.state('SP',facecolor='#fafafa',edgecolor='#333333',label='São Paulo')
        title='SÃO PAULO — ESTADO ISOLADO'
        orient=ax.north_arrow(loc='upper left',size=34)
        if kind=='focus':
            ax.zoom(2.3,center=(-47.4,-23.3))
            title='SÃO PAULO — VISTA AMPLIADA'
    ax.set_title(title,fontsize=17,fontweight='bold')
    ax.subtitle('Componentes opcionais · dados Natural Earth',fontsize=10)
    grid=ax.grid(step=10 if kind=='brazil' else 1,linewidth=.5,linestyle='--',alpha=.6)
    legend=ax.legend(loc='lower right',fontsize=9)
    scale=ax.scale_bar(loc='lower left',fontsize=9)
    mini=ax.overview(context='brazil',loc='upper right',width=160) if kind!='brazil' else None
    fig.text(.5,.025,'Base generalizada · a escala corresponde à latitude de sua posição',ha='center',fontsize=9,color='#555555')
    controls={'s':scale,'n':orient,'l':legend,'g':grid}
    if mini is not None:controls['m']=mini
    def toggle(event):
        artist=controls.get(event.key)
        if artist is not None:
            artist.set_visible(not artist.get_visible())
            fig.canvas.draw_idle()
    # Avoid S: the standard Matplotlib toolbar binds S to save. Use numeric
    # keys for this example so built-in navigation shortcuts are preserved.
    controls={str(i):artist for i,artist in enumerate(controls.values(),1)}
    fig.canvas.mpl_connect('key_press_event',toggle)
    return fig

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--show',action='store_true');parser.add_argument('--only',choices=['brazil','state','focus'])
    args=parser.parse_args()
    output=Path(__file__).resolve().parents[1]/'gallery';output.mkdir(exist_ok=True)
    for name in ('brazil','state','focus'):
        if args.only and name!=args.only:continue
        fig=create(name)
        fig.savefig(output/f'{name}.svg');fig.savefig(output/f'{name}.png')
        fig.show(backend='browser',open_browser=False,path=output/f'{name}.html')
        print(name,flush=True)
    if args.show:plt.show()
