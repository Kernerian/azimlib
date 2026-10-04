"""Integrated editable 2D artists; synthetic values and routes."""
from pathlib import Path
import azimlib as azl
from azimlib.colors import Normalize

ROOT=Path(__file__).resolve().parents[1]


def create():
    fig,axes=azl.subplots(1,2,figsize=(10,5.5),layout='constrained')
    norm=Normalize(0,4)
    left,right=axes
    for ax in axes:
        ax.set_extent((-54,-42,-28,-16));ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
        ax.states(facecolor='#f5f5f5',edgecolor='#aaaaaa',linewidth=.35)
    line,=left.plot([-52,-49,-45],[-26,-22,-19],'o--',label='Rota sintética')
    points=left.scatter([-51,-47],[-24,-20],c=[1,3],s=[36,64],norm=norm)
    title=left.set_title('Dados e estilos editáveis')
    text=left.text(-50,-26,'Estações sintéticas',fontsize=8,halo='white',halo_width=2)
    legend=left.legend(loc='upper left',facecolor='white');scale=left.scale_bar(length=100)
    image=right.imshow([[0,1,2],[1,2,3],[2,3,4]],extent=(-54,-42,-28,-16),origin='lower',norm=norm,alpha=.6)
    contour=right.contour([-54,-48,-42],[-28,-22,-16],[[0,1,2],[1,2,3],[2,3,4]],levels=[1,2,3],colors='black',linewidths=.6)
    right.clabel(contour,inline=False,fontsize=8)
    right.set_title('Campo e contornos sintéticos')
    bar=fig.colorbar(image,ax=list(axes),orientation='horizontal',shrink=.85,label='Valor sintético')
    fig.suptitle('Auditoria integrada de Artists 2D',fontsize=14)
    return fig,dict(axes=axes,line=line,points=points,title=title,text=text,legend=legend,scale=scale,image=image,contour=contour,bar=bar)


def edit(handles):
    left,right=handles['axes']
    handles['line'].set(data=([-53,-50,-46,-43],[-27,-24,-21,-18]),linewidth='1.4',
                        linestyle=(v for v in (4,2)),marker='D',markersize='5',color='#7f4fa2')
    handles['points'].set(offsets=[[-52,-23],[-46,-19]],sizes=[49,81],array=[2,5],clim=(0,6))
    handles['title'].set(text='Edição validada',fontsize='12',fontweight=700)
    handles['text'].set(text='Estações atualizadas',position=(-50,-25.5),fontstyle='italic')
    handles['legend'].get_frame().set(facecolor='white',edgecolor='#888888',linewidth=.6,alpha=.95)
    handles['scale'].set(length='100',fontsize='9',framealpha=.95)
    left.spines['left'].set(color='#555555',linewidth='1.1')
    handles['contour'].set(linestyles=[(v for v in (3,2))],linewidths=[.5,.8,1])
    handles['bar'].outline.set(color='#555555',linewidth='.6')
    handles['bar'].ax.tick_params(labelsize='9',length='4')


def main():
    fig,handles=create()
    try:
        for phase in ('before','after'):
            if phase=='after':edit(handles)
            for ext in ('png','svg'):fig.savefig(ROOT/f'gallery/artist-validation-{phase}.{ext}')
            (ROOT/f'gallery/artist-validation-{phase}.html').write_text(fig.to_html(),encoding='utf-8')
    finally:azl.close(fig)


if __name__=='__main__':main()
