"""Real Qt widget input/paint and cleanup; no Matplotlib or synthetic canvas mocks."""
import argparse,json,time,platform,importlib.metadata
from pathlib import Path
import azimlib as azl
from azimlib.widgets import Slider
from PySide6 import QtCore,QtTest
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--image',type=Path);args=p.parse_args()
    fig,ax=azl.subplots(figsize=(5,3));ax.set_extent((-2,2,-2,2));line=ax.line([(-1,-1),(0,0),(1,.5)],linewidth=.8,color='#cf5147');points=ax.scatter([0],[0],label='Station');points.set_picker(True)
    slider=Slider(fig.add_axes((.2,.015,.5,.065)),'Size',10,80,36);slider.on_changed(lambda v:points.set_sizes([v]));picked=[];fig.canvas.mpl_connect('pick_event',picked.append)
    v=fig.show(backend='qt');v.flush_events();QtTest.QTest.qWait(160);v.flush_events();v.draw();m=v.scene.maps[0];x,y,w,h=m['box'];ratio=v.widget.devicePixelRatioF();point=QtCore.QPoint(round((x+w/2)/ratio),round((y+h/2)/ratio))
    QtTest.QTest.mouseClick(v.widget,QtCore.Qt.MouseButton.LeftButton,pos=point);assert picked and picked[0].ind==[0]
    original=ax.get_extent();v.command('pan');QtTest.QTest.mousePress(v.widget,QtCore.Qt.MouseButton.LeftButton,pos=point)
    QtTest.QTest.mouseMove(v.widget,point+QtCore.QPoint(15,5));QtTest.QTest.mouseRelease(v.widget,QtCore.Qt.MouseButton.LeftButton,pos=point+QtCore.QPoint(15,5));assert ax.get_extent()!=original
    v.command('home');assert ax.get_extent()==original;v.command('back');assert ax.get_extent()!=original;v.command('forward');assert ax.get_extent()==original
    slider.set_val(50);assert points.get_sizes()==[50];v.draw();assert any(getattr(i,'text','')=='Size' for i in v.scene.items)
    widths=[i.style.get('stroke_width') for i in v.scene.items if i.style.get('stroke')=='#cf5147'];assert widths and all(abs(a-.8*fig.dpi/72)<1e-9 for a in widths)
    v.subplots_dialog();v.flush_events()
    if args.image:args.image.parent.mkdir(parents=True,exist_ok=True);v.window.grab().save(str(args.image))
    v.close();v.application.processEvents();assert not fig._widgets and not v.timer.isActive() and not v.resize_timer.isActive()
    deadline=time.monotonic()+5
    while v.worker._thread is not None and v.worker._thread.is_alive() and time.monotonic()<deadline:time.sleep(.01)
    assert v.worker._thread is None or not v.worker._thread.is_alive()
    import hashlib,sys
    runtime=Path(azl.__file__).resolve().parent
    assert runtime.is_relative_to(Path(sys.prefix).resolve()),'Install the package before this proof'
    fingerprint=dict(version=azl.__version__,runtime_origin='<environment>/site-packages/azimlib',
        runtime_sha256={p.relative_to(runtime).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(runtime.rglob('*.py'))},
        tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(dict(**fingerprint,passed=True,platform=platform.system(),qt=importlib.metadata.version('PySide6_Essentials'),qpa=v.application.platformName(),scope='Real Qt widget QTest input/paint, not human visual acceptance',picking=True,pan=True,history=True,widgets=True,stroke_points=True,cleanup=True),indent=2)+'\n','utf8')
if __name__=='__main__':main()
