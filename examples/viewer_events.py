"""Independent desktop callbacks; optionally export a static SVG/PNG instead.

Ctrl+left click: position an annotation. Ctrl+N/R/E/L: toggle north,
compass rose, scale and legend independently. Default toolbar keys remain.
"""
import argparse
from pathlib import Path
import azimlib as azl
from azimlib.backend_bases import MouseButton


def build():
    fig,ax=azl.subplots(figsize=(6.4,4.8))
    ax.states(facecolor='#eeeeee',edgecolor='#999999',linewidth=.4,fit=False)
    ax.set_extent((-54,-41,-27,-16))
    ax.plot([-52,-49,-46],[-25,-23,-21],'r--o',label='Route')
    ax.set_title('Editable viewer components')
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    components={'ctrl+l':ax.legend(loc='lower right'),
                'ctrl+e':ax.scale_bar(),
                'ctrl+n':ax.north_arrow(),
                'ctrl+r':ax.compass()}
    note=ax.annotate('Selected position',xy=(-49,-23),xytext=(12,10),textcoords='offset points')
    note.set_visible(False)
    def on_key(event):
        component=components.get(event.key)
        if component is not None:
            component.set_visible(not component.get_visible());fig.canvas.draw_idle()
    def on_click(event):
        if event.inaxes is ax and event.button==MouseButton.LEFT and 'ctrl' in event.modifiers and event.xdata is not None:
            note.xy=(event.xdata,event.ydata)
            note.set_text(f'{event.xdata:.2f}, {event.ydata:.2f}')
            note.set_visible(True);fig.canvas.draw_idle()
    fig.canvas.mpl_connect('key_press_event',on_key)
    fig.canvas.mpl_connect('button_press_event',on_click)
    return fig,ax,components,note


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export',type=Path)
    args=parser.parse_args();fig,*_=build()
    if args.export:fig.savefig(args.export);azl.close(fig)
    else:azl.show()
