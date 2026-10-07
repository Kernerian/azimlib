"""Subfigures, rotation, gaps, reusable symbols and independent orientation."""
import argparse
from pathlib import Path
import azimlib as azl
from azimlib.transforms import Affine2D,blended_transform_factory
from azimlib.legend_handler import HandlerSymbol

def create():
    with azl.style.context('default'):
        fig=azl.figure(figsize=(12,5.8),dpi=130,layout='constrained')
        west,east=fig.subfigures(1,2,wspace=.04)
        axes=[west.subplots(),east.subplots()]
        symbol=azl.Symbol(azl.Path([(0,0),(.5,1),(1,0),(0,0)],
                                  [azl.Path.MOVETO,azl.Path.LINETO,azl.Path.LINETO,azl.Path.CLOSEPOLY]))
        for i,ax in enumerate(axes):
            ax.map('brazil',facecolor='#f2f2f2',edgecolor='#666666',linewidth=.6)
            ax.states(edgecolor='#9ba5ac',linewidth=.3)
            ax.set_extent((-74,-34,-34,6));ax.set_bearing(i*35)
            ax.set_title('North up' if i==0 else 'Clockwise bearing: 35 degrees')
            ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
            ax.grid(True,linewidth=.4,color='#c3cbd0',linestyle=':')
            route,=ax.plot([-60,-54,float('nan'),-49,-43],[-3,-12,float('nan'),-20,-25],
                          color='#bc5045',linewidth=1.2,marker='o',markersize=3,label='Synthetic route with gap')
            collection=ax.add_collection(azl.LineCollection([[(-68,-8),(-63,-14)],[(-53,-7),(-48,-10)]],
                                 colors=['#277ea4','#26966c'],linewidths=[.8,1.2],linestyles=['--',':']))
            collection.set_label('Synthetic segments')
            ax.add_patch(symbol.patch(transform=Affine2D().scale(.035,.035).translate(.72,.18)+ax.transAxes,
                                      facecolor='#277ea4',edgecolor='white',linewidth=.5))
            ax.text(-60,.55,'Mixed X / Y spaces',
                    transform=blended_transform_factory(ax.transData,ax.transAxes),ha='center',fontsize=8)
            ax.north_arrow(loc='upper right',size=26)
            ax.compass(loc='upper left',size=30)
            ax.scale_bar(length=500,loc='lower left',fontsize=7)
            ax.legend(handles=[route,symbol],labels=['Synthetic route','Reusable station symbol'],
                      handler_map={azl.Symbol:HandlerSymbol(facecolor='#277ea4',edgecolor='white')},
                      fontsize=7,loc='lower right')
        west.suptitle('Geographic view',fontsize=12)
        east.suptitle('Rotated view',fontsize=12)
        fig.text(.5,.015,'Natural Earth (public domain) · synthetic paths/symbols · own Azimlib renderer',
                 ha='center',va='bottom',fontsize=8,color='#60717a')
    return fig

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('gallery/composition'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    fig=create()
    for extension in ('png','svg'):fig.savefig(args.output/f'composition-atlas.{extension}')
    (args.output/'composition-atlas.html').write_text(fig.to_html(),encoding='utf8',newline='\n')
    azl.close(fig)
