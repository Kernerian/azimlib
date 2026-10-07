"""Real withdrawn Tk: picking/widgets survive canvas replacement and cleanup."""
import argparse,json
from pathlib import Path
from types import SimpleNamespace
import azimlib as azl
from azimlib.widgets import Slider,LayerControl
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    fig,ax=azl.subplots(figsize=(4,3));ax.set_extent((-2,2,-2,2));points=ax.scatter([0],[0],label='Points');points.set_picker(True);picked=[];fig.canvas.mpl_connect('pick_event',picked.append)
    slider=Slider(fig.add_axes((.15,.01,.5,.07)),'Size',10,60,30);slider.on_changed(lambda v:points.set_sizes([v]))
    viewer=fig.show(block=False);viewer.window.withdraw();viewer.flush_events();scene=viewer.scene;meta=scene.maps[0];x,y,w,h=meta['box']
    viewer._emit('button_press_event',SimpleNamespace(x=x+w/2,y=y+h/2,num=1,state=0),0);assert picked and picked[0].ind==[0]
    slider.set_val(40);viewer.draw();assert points.get_sizes()==[40];assert any(getattr(i,'text','')=='Size' for i in viewer.scene.items)
    assert not any(getattr(i,'text','')=='Size' for i in fig.to_scene().items)
    viewer.close();assert not fig._widgets;args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(dict(passed=True,scope='Withdrawn Tk, synthetic normalized event, not human/platform visual acceptance',picking=True,slider=True,cleanup=True),indent=2)+'\n','utf8')
if __name__=='__main__':main()
