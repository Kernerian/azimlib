"""Native CPU Tk/Qt: Lucide effects, locators, labels, lifecycle and pan/zoom."""
import argparse,json,platform,time
from pathlib import Path
from types import SimpleNamespace
import azimlib as a

def main(backend,output):
 f,ax=a.subplots(body=a.MARS,figsize=(6,4),dpi=100);ax.set_extent((-10,10,-7,7));ax.set_theme('atlas');g=ax.group(name='Sites');s=g.add(ax.symbols([(0,0)],'bot',size=22,halo=a.IconHalo(width=.7),shadow=a.IconShadow(blur=.5)));s.set_picker(True);g.add(s.labels_for('Synthetic site',fontsize=8));inset=ax.inset((.72,.03,.24,.25));inset.set_extent((-180,180,-90,90));locator=inset.locator(ax,shade=True);ax.legend(sections=[a.LegendSection('Sites',(s,),('Synthetic rover',))],fontsize=8);picked=[];f.canvas.mpl_connect('pick_event',picked.append)
 viewer=f.show(backend=backend,block=False);viewer.flush_events();viewer.draw();scene=viewer.scene;meta=next(m for m in scene.maps if not m.get('inset'));x,y,w,h=meta['box'];center=(x+w/2,y+h/2)
 if backend=='tk':
  viewer.window.withdraw();viewer._emit('button_press_event',SimpleNamespace(x=center[0],y=center[1],num=1,state=0),0)
 else:
  from PySide6 import QtCore,QtTest
  ratio=viewer.widget.devicePixelRatioF();point=QtCore.QPoint(round(center[0]/ratio),round(center[1]/ratio));QtTest.QTest.mouseClick(viewer.widget,QtCore.Qt.MouseButton.LeftButton,pos=point)
 assert picked and picked[-1].artist is s
 before=locator.footprint();ax.pan(1,0);viewer.draw();assert before!=locator.footprint();ax.zoom(1.2);viewer.draw();assert s.axes is ax
 g.set_visible(False);viewer.draw();assert not any(owner is s for owner,_,_,_ in viewer.scene._pick_records)
 g.set_visible(True);viewer.draw();image=output.with_suffix('.png');image.parent.mkdir(parents=True,exist_ok=True)
 if backend=='qt':viewer.window.grab().save(str(image))
 else:
  from azimlib.renderers.pillow import render_png
  render_png(viewer.scene,image)
 g.remove();viewer.draw();assert s.axes is None;inset.remove();viewer.draw();viewer.close()
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(dict(passed=True,version=a.__version__,platform=platform.system(),backend=backend,picking=True,locator_update=True,pan_zoom=True,group_toggle=True,lifecycle=True,scope='Native widgets with synthetic test input; not human visual approval'),indent=2)+'\n',encoding='utf8')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=('tk','qt'),required=True);p.add_argument('--output',type=Path,required=True);v=p.parse_args();main(v.backend,v.output)
