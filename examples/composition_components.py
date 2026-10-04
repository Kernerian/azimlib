"""Integrated layout: shared colorbar, opt-in ornaments, labels and overview.

Administrative boundaries are bundled data. Points/route/field are synthetic.
"""
from pathlib import Path
import azimlib as azl
from azimlib.colors import Normalize

ROOT=Path(__file__).resolve().parents[1]

def create(*,figsize=(9.6,5.4),dpi=100,orientation='horizontal'):
    fig,axes=azl.subplots(1,2,figsize=figsize,dpi=dpi,layout='constrained')
    left,right=axes;norm=Normalize(0,100)
    for ax in axes:
        ax.set_extent((-54,-42,-28,-16));ax.states(fc='#f4f4f4',ec='#999999',lw=.3)
        ax.set_xlabel('Longitude',labelpad=4);ax.set_ylabel('Latitude',labelpad=4)
    line,=left.plot([-52,-49,-45],[-26,-22,-19],'D--',c='#9467bd',lw=1.2,ms=5,label='Rota sintética')
    points=left.scatter([-51,-47],[-24,-20],c=[20,80],s=[36,64],norm=norm)
    legend=left.legend(loc='upper left',facecolor='white',fontsize=8)
    scale=left.scale_bar(length=100,fontsize=8,facecolor='white')
    north=left.north_arrow(loc='upper right',size=30)
    compass=left.compass(loc='lower right',size=30)
    left.grid(True,linestyle=':',linewidth=.4)
    left.set_title('Pontos e rota\nDados sintéticos',size=11)
    field=right.imshow([[0,20,40],[30,50,70],[60,80,100]],extent=(-54,-42,-28,-16),origin='lower',norm=norm,alpha=.7)
    right.set_title('Campo e área em foco',size=11)
    overview=right.overview(context='brazil',width=85,loc='upper right')
    bar=fig.colorbar(field,ax=list(axes),orientation=orientation,shrink=.85,label='Índice sintético')
    bar.ax.tick_params(labelsize=8)
    heading=fig.suptitle('Composição cartográfica integrada',size=13)
    return fig,dict(axes=axes,line=line,points=points,legend=legend,scale=scale,north=north,compass=compass,
                    field=field,overview=overview,bar=bar,heading=heading)

def main():
    for orientation in ('horizontal','vertical'):
        fig,_=create(orientation=orientation)
        try:
            for ext in ('png','svg'):fig.savefig(ROOT/f'gallery/composition-matrix-{orientation}.{ext}')
            (ROOT/f'gallery/composition-matrix-{orientation}.html').write_text(fig.to_html(),encoding='utf-8')
        finally:azl.close(fig)

if __name__=='__main__':main()
