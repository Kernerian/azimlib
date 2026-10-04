"""North arrow and eight-point compass coexist as independent Artists."""
from pathlib import Path
import azimlib as azl
from azimlib.ticker import LongitudeFormatter,LatitudeFormatter

def create():
    fig,ax=azl.subplots(figsize=(7,7),projection='mercator',layout='constrained')
    ax.state('SP',facecolor='#f3f3f3',edgecolor='#666666',linewidth=.6,label='São Paulo')
    ax.set_title('Seta de norte e rosa dos ventos')
    ax.subtitle('Dois componentes independentes',fontsize=10)
    ax.set_facecolor('#dceaf2')
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    ax.xaxis.set_major_formatter(LongitudeFormatter());ax.yaxis.set_major_formatter(LatitudeFormatter())
    arrow=ax.north_arrow(loc='upper right',size=36)
    rose=ax.compass(loc='upper left',size=36)
    ax.scale_bar(loc='lower left',fontsize=9)
    ax.legend(loc='lower right',fontsize=9)
    # Explicit controls, without changing the other orientation component.
    def toggle(event):
        component={'1':arrow,'2':rose}.get(event.key)
        if component is not None:
            component.set_visible(not component.get_visible());fig.canvas.draw_idle()
    fig.canvas.mpl_connect('key_press_event',toggle)
    return fig,arrow,rose

if __name__=='__main__':
    folder=Path(__file__).resolve().parents[1]/'gallery'
    fig,arrow,rose=create()
    for name,visible in (('orientation-both',True),('orientation-arrow-only',False)):
        rose.set_visible(visible)
        for extension in ('png','svg'):fig.savefig(folder/f'{name}.{extension}')
        fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
        print(name,flush=True)
    azl.close(fig)
