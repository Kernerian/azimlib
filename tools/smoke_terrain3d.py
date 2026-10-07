"""Installed own 3D camera proof on native Tk or Qt; no human acceptance claim."""
import argparse,json,hashlib,sys,platform,time
from pathlib import Path
from types import SimpleNamespace
import azimlib as azl

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--backend',choices=('tk','qt'),default='tk');p.add_argument('--image',type=Path);a=p.parse_args()
    runtime=Path(azl.__file__).resolve().parent;assert runtime.is_relative_to(Path(sys.prefix).resolve()),'Install the package before this proof'
    fig,ax=azl.subplots(figsize=(4,3),subplot_kw={'projection':'3d'});surface=ax.plot_surface([0,100,200],[0,100,200],[[0,10,0],[10,80,10],[0,10,0]])
    ax.set_title('Own terrain camera');initial=ax.camera;events=[];fig.canvas.mpl_connect('button_press_event',events.append)
    v=fig.show(backend=a.backend,block=False);v.flush_events();v.draw();x,y,w,h=v.scene.maps[0]['box']
    if a.backend=='tk':
        v.window.withdraw();initial_pixels=v._image.tobytes();v.set_mode('pan')
        def event(x,y,state=256):return SimpleNamespace(x=x,y=y,num=1,state=state)
        v.press(event(x+w/2,y+h/2,0));v.motion(event(x+w/2+20,y+h/2+10));v.release(event(x+w/2+20,y+h/2+10,0));assert ax.camera!=initial
        v.draw();assert v._image.tobytes()!=initial_pixels
        v.home();assert ax.camera==initial;v.back();assert ax.camera!=initial;v.forward();assert ax.camera==initial
        v.wheel(SimpleNamespace(x=x+w/2,y=y+h/2,delta=120,state=0));assert ax.camera.zoom>1
        v.draw();surface.set_visible(False);v.draw();surface.set_visible(True);v.draw()
        v.set_mode('zoom');v.press(event(x+w/2,y+h/2,0));v.motion(event(x+w/2,y+h/2-15));v.release(event(x+w/2,y+h/2-15,0))
    else:
        from PySide6 import QtCore,QtTest
        ratio=v.widget.devicePixelRatioF();point=QtCore.QPoint(round((x+w/2)/ratio),round((y+h/2)/ratio));delta=QtCore.QPoint(20,10)
        initial_pixels=bytes(v._qimage.constBits())
        v.command('pan');QtTest.QTest.mousePress(v.widget,QtCore.Qt.MouseButton.LeftButton,pos=point);QtTest.QTest.mouseMove(v.widget,point+delta);QtTest.QTest.mouseRelease(v.widget,QtCore.Qt.MouseButton.LeftButton,pos=point+delta);assert ax.camera!=initial
        v.draw();assert bytes(v._qimage.constBits())!=initial_pixels
        v.command('home');assert ax.camera==initial;v.command('back');assert ax.camera!=initial;v.command('forward');assert ax.camera==initial
        v.draw();QtTest.QTest.qWait(100);v.flush_events()
        if a.image:a.image.parent.mkdir(parents=True,exist_ok=True);v.window.grab().save(str(a.image))
    assert events and events[0].xdata is None and events[0].ydata is None
    v.close()
    if a.backend=='qt':
        v.application.processEvents();assert not v.timer.isActive()
        deadline=time.monotonic()+5
        while v.worker.busy() and time.monotonic()<deadline:time.sleep(.01)
    assert v.closed
    report=dict(passed=True,version=azl.__version__,platform=platform.system(),backend=a.backend,scope='Native toolkit, programmatic input/paint; not human or other-platform acceptance',orbit=True,zoom=a.backend=='tk',history=True,cleanup=True,runtime_origin='<environment>/site-packages/azimlib',runtime_sha256={p.relative_to(runtime).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(runtime.rglob('*.py'))},tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
if __name__=='__main__':main()
