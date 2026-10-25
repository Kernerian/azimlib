"""Real withdrawn Tk contract: symbols, groups, native paint and picking."""
import argparse,json,platform
from pathlib import Path
from types import SimpleNamespace
import azimlib as a

def main(output):
 f,ax=a.subplots(body=a.MARS,figsize=(4,3));ax.set_extent((-2,2,-2,2));g=ax.group(name='Sites');s=g.add(ax.symbols([(0,0)],'rover',size=24));s.set_picker(True);picked=[];f.canvas.mpl_connect('pick_event',picked.append)
 icon=a.SymbolDefinition.from_png(Path(__file__).resolve().parents[1]/'examples/thematic/assets/sample.png',source=a.AssetSource('azimlib:own-example','BSD-3-Clause','Kernerian'));g.add(ax.symbols([(1,1)],icon,size=14))
 v=f.show(block=False);v.window.withdraw();v.flush_events();v.draw();assert any(type(i).__name__=='RasterIcon' for i in v.scene.items);m=v.scene.maps[0];x,y,w,h=m['box'];v._emit('button_press_event',SimpleNamespace(x=x+w/2,y=y+h/2,num=1,state=0),0)
 assert picked and picked[0].artist is s
 g.set_visible(False);v.draw();assert not any(owner is s for owner,_,_,_ in v.scene._pick_records)
 g.set_visible(True);s.set_size(18);v.draw();assert any(owner is s for owner,_,_,_ in v.scene._pick_records)
 g.remove();v.draw();assert s.axes is None;v.close()
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(dict(passed=True,platform=platform.system(),version=a.__version__,scope='Native withdrawn Tk, synthetic normalized picking/paint; not human visual acceptance',group_toggle=True,removal=True,picking=True),indent=2)+'\n',encoding='utf8')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);main(p.parse_args().output)
