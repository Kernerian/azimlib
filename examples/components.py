"""Cartographic counterpart of a multi-series Matplotlib figure.

The three routes are schematic examples, not classified waterways.
Run: python examples/components.py [--show]
"""
from pathlib import Path
import argparse
import azimlib.pyplot as plt

def create():
    with plt.rc_context({'font.family':'DejaVu Sans','lines.linewidth':2,'axes.titlesize':17}):
        fig,ax=plt.subplots(figsize=(9,10),subplot_kw={'projection':'mercator'})
        fig.subplots_adjust(left=.1,right=.97,bottom=.09,top=.88)
        ax.set_facecolor('#dbeaf5')
        neighbors=ax.countries(facecolor='#dddddd',edgecolor='#888888',linewidth=.6,linestyle='--',label='Países vizinhos')
        ax.map('brazil',facecolor='white',edgecolor='#202020',linewidth=.9)
        states=ax.states(edgecolor='#777777',linewidth=.5,label='Limites estaduais')
        ax.rivers(color='#9bbac8',linewidth=.55)
        ax.set_extent((-76,-32,-36,8))
        ax.set_title('BRASIL — COMPONENTES CARTOGRÁFICOS',fontweight='bold')
        ax.subtitle('Camadas, linhas, marcadores e componentes independentes',fontsize=11,color='#333333')
        routes=[([-67,-60,-52],[-8,-3,-1],'o-','#ef4444','Rota A · contínua'),
                ([-63,-58,-52,-47],[-16,-20,-23,-24],'s--','#22c55e','Rota B · tracejada'),
                ([-48,-44,-40,-36],[-16,-12,-8,-5],'^:','#3b82f6','Rota C · pontilhada')]
        handles=[]
        for lon,lat,fmt,color,label in routes:
            line,=ax.plot(lon,lat,fmt,color=color,markersize=6,label=label)
            handles.append(line)
        ax.grid(step=10,linestyle='--',linewidth=.6,alpha=.65)
        ax.set_xticks([-70,-60,-50,-40])
        ax.set_yticks([-30,-20,-10,0])
        ax.tick_params(direction='out',labelsize=9,length=4)
        ax.set_xlabel('Longitude',fontsize=10)
        ax.set_ylabel('Latitude',fontsize=10)
        ax.legend(handles+[states,neighbors],title='Legenda',loc='lower right',fontsize=9,facecolor='white',framealpha=.95)
        ax.compass(loc='upper left',size=30,color='#202020')
        ax.scale_bar(loc='lower left',facecolor='white',framealpha=.95)
        ax.text(-38,-1,'OCEANO\nATLÂNTICO',fontsize=12,color='#4c6597',fontstyle='italic',ha='center')
        ax.annotate('Manaus',(-60.02,-3.12),xytext=(-45,25),fontsize=9,halo='white',halo_width=2,color='#333333')
        fig.text(.5,.025,'Rotas esquemáticas · não indicam navegabilidade | Base territorial: Natural Earth',ha='center',fontsize=9,color='#555555')
    return fig

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--show',action='store_true')
    args=parser.parse_args()
    folder=Path(__file__).resolve().parents[1]/'gallery';folder.mkdir(exist_ok=True)
    fig=create()
    fig.savefig(folder/'components.svg')
    fig.savefig(folder/'components.png')
    fig.show(backend='browser',open_browser=False,path=folder/'components.html')
    if args.show:plt.show()
