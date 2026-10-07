"""Original regional interactive map with opt-in selector/layer/size controls."""
import argparse
from pathlib import Path
import azimlib as azl
from azimlib.widgets import Slider,LayerControl,FeatureSelector,RectangleSelector

def create():
    fig,ax=azl.subplots(figsize=(8,5));fig.subplots_adjust(left=.1,right=.75,bottom=.23,top=.89)
    ax.set_extent((-54,-40,-28,-16));ax.states(facecolor='#f1f3f4',edgecolor='#9ba6ad',linewidth=.5)
    route=ax.line([(-52,-25),(-49,-23),(-46,-21),(-43,-18)],color='#d05243',linewidth=1.5,marker='^',label='Synthetic route')
    cities=ax.scatter([-50,-47,-44],[-24,-22,-19],s=[40],color='#248bb8',label='Synthetic stations')
    ax.set_title('Regional selection and layers');ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.legend();ax.grid(alpha=.25)
    layer_control=LayerControl(fig.add_axes((.78,.62,.2,.2)),[route,cities],labels=['Route','Stations'])
    slider=Slider(fig.add_axes((.18,.06,.5,.08)),'Marker area',10,100,40,valstep=5);slider.on_changed(lambda value:cities.set_sizes([value]))
    selector=FeatureSelector(ax,cities);status=fig.text(.78,.53,'Select a station',fontsize=9)
    selector.onselect=lambda indices:status.set_text('Stations: '+', '.join(str(i+1) for i in indices))
    rectangle=RectangleSelector(ax,lambda a,b:status.set_text(f'Box: {a.xdata:.1f}, {b.xdata:.1f}'),minspanx=8,minspany=8)
    # Keep widgets/selector references for callback lifecycle.
    fig.interaction_controls=(layer_control,slider,selector,rectangle)
    return fig

def main():
    p=argparse.ArgumentParser();p.add_argument('--backend',choices=('tk','qt','browser-live','notebook'),default='tk');p.add_argument('--output',type=Path);args=p.parse_args();fig=create()
    if args.output:
        args.output.mkdir(parents=True,exist_ok=True);fig.savefig(args.output/'interaction-map.png');fig.savefig(args.output/'interaction-map.svg')
        from azimlib.renderers import render_png
        render_png(fig.to_scene(interactive=True),args.output/'interaction-controls.png')
        fig.close()
    else:fig.show(backend=args.backend,block=True)
if __name__=='__main__':main()
