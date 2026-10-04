"""Real Tk widgets/event loop, with withdrawn windows and no external data.

Run after installing azimlib[gui]. Linux needs a display, e.g. xvfb-run.
This is an integration check, not a screenshot/OS appearance comparison.
"""
import argparse
import json
import platform
import sys
import tempfile
import time
import tkinter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import azimlib as azl
from PIL import Image
from azimlib.backends import tk
from azimlib.backend_bases import MouseButton
from azimlib.scene import Text


def run():
    checks=[];timings={}
    original=tkinter.Tk
    def hidden_root(*args,**kwargs):
        root=original(*args,**kwargs);root.withdraw();return root
    fig,axes=azl.subplots(1,2,figsize=(6,3),sharex=True)
    ax,right=axes
    for a in axes:
        a.set_extent((-60,-40,-30,-10))
        a.geojson({'type':'Polygon','coordinates':[[[-59,-29],[-41,-29],[-41,-11],[-59,-11],[-59,-29]]]},
                  facecolor='#eeeeee',edgecolor='#777777',linewidth=.5,fit=False)
    line,=ax.plot([-55,-50,-45],[-25,-20,-15],label='Route')
    title=ax.set_title('Before');legend=ax.legend(loc='upper right')
    scale=ax.scale_bar();ax.north_arrow();ax.compass(loc='upper left')
    overview=ax.overview(loc='lower right',extent=(-80,-30,-40,10),width=75)
    points=right.scatter(lon=[-55,-45],lat=[-25,-15],c=[0,1])
    bar=fig.colorbar(points,ax=right,orientation='horizontal')
    bar.set_label('Value')
    drawings=[];old_canvas=fig.canvas
    old_canvas.mpl_connect('draw_event',drawings.append)
    start=time.perf_counter()
    try:
        with patch.object(Image.Image,'save',side_effect=AssertionError('viewer must not encode PNG')):
            with patch.object(Image,'open',side_effect=AssertionError('viewer must not decode PNG')):
                with patch.object(tkinter,'Tk',hidden_root):viewer=fig.show(block=False)
        timings['first_draw_seconds']=time.perf_counter()-start
        viewer.flush_events()
        assert len(viewer.buttons)==7 and viewer.widget.cget('highlightthickness')=='0'
        assert fig.canvas is viewer and viewer in tk._windows
        assert viewer._overview_box and not ax._north is ax._compass
        assert viewer.widget.find_all() and viewer.window.state()=='withdrawn'
        checks.append('real widgets, toolbar, canvas, optional components, callback transfer')
        assert viewer._initial_image is None and viewer._initial_scene is None
        previous_image=viewer._image

        with azl.ion():
            title.set_text('After');pending=viewer._pending
            line.set_color('red');scale.set_visible(False);legend.set_visible(False)
            assert pending is not None and viewer._pending==pending
        before=len(drawings);viewer.flush_events()
        assert len(drawings)==before+1 and not fig.stale
        try:previous_image.getpixel((0,0))
        except ValueError:pass
        else:raise AssertionError('previous owned image must be closed after replacement')
        assert drawings[-1].renderer is viewer.scene
        assert any(isinstance(item,Text) and item.text=='After' for item in viewer.scene.items)
        scale.set_visible(True);legend.set_visible(True)
        checks.append('batched edits, visibility and live own Scene in draw_event')
        checks.append('direct RGBA without PNG codec/initial copy; previous image closed')

        def center():
            x,y,w,h=viewer._viewport(0).box
            return round(x+w/2),round(y+h/2)
        mouse=[];viewer.mpl_connect('motion_notify_event',mouse.append)
        assert viewer.widget.bind('<Motion>')
        x,y=center();viewer.motion(SimpleNamespace(x=x,y=y))
        viewer.flush_events()
        assert mouse[-1].inaxes is ax and 'x=' in viewer.message.get()
        checks.append('registered Motion binding and synthetic cursor coordinates')

        keys=[];viewer.mpl_connect('key_press_event',keys.append)
        def key(symbol,char='',state=0,position=None):
            px,py=position if position is not None else center()
            return SimpleNamespace(x=px,y=py,keysym=symbol,char=char,state=state)
        viewer.key(key('p','p',4));viewer.key(key('P','P',1))
        assert viewer.mode=='' and keys[-2].key=='ctrl+p' and keys[-1].key=='P'
        viewer.key(key('p','p'));assert viewer.mode=='pan'
        viewer.key(key('p','p'));assert viewer.mode==''
        with azl.rc_context({'keymap.pan':['ctrl+p']}):
            viewer.key(key('p','p',4));assert viewer.mode=='pan'
            viewer.key(key('p','p',4));assert viewer.mode==''
        with patch.object(viewer.filedialog,'asksaveasfilename',return_value='') as dialog:
            viewer.key(key('s','s',4));dialog.assert_called_once()
        viewer.key_up(key('s','s',4))
        assert viewer.widget.bind('<KeyPress>') and viewer.widget.bind('<KeyRelease>')
        checks.append('normalized keys/modifiers, editable keymap and Ctrl+S cancellation')

        presses=[];viewer.mpl_connect('button_press_event',presses.append)
        number=3 if sys.platform=='darwin' else 2
        viewer.set_mode('pan');viewer.press(SimpleNamespace(x=x,y=y,num=number,state=0),dblclick=True)
        assert presses[-1].button is MouseButton.MIDDLE and presses[-1].dblclick and viewer.drag is None
        viewer.release(SimpleNamespace(x=x,y=y,num=number,state=0));viewer.set_mode('pan')
        assert viewer.widget.bind('<Double-Button-1>') and viewer.widget.bind('<ButtonPress-2>')
        checks.append('middle/double-click input exposed without starting a pan drag')

        transitions=[]
        for channel in ('axes_enter_event','axes_leave_event','figure_enter_event','figure_leave_event'):
            viewer.mpl_connect(channel,lambda e,channel=channel:transitions.append((channel,e.inaxes)))
        bx,by,bw,bh=viewer._viewport(1).box;other=(round(bx+bw/2),round(by+bh/2))
        viewer.motion(SimpleNamespace(x=other[0],y=other[1],state=0))
        assert transitions[:2]==[('axes_leave_event',ax),('axes_enter_event',right)]
        count=len(transitions);viewer.motion(SimpleNamespace(x=other[0]+1,y=other[1],state=0))
        assert len(transitions)==count
        for character in ('g','g','g','g','G','G','G','G'):
            viewer.key(key(character,character,1 if character=='G' else 0,other))
            viewer.flush_events()
            assert not any(layer.kind=='grid' for layer in ax.layers)
        assert not any(layer.kind=='grid' for layer in right.layers)
        viewer.key(key('a','a',4,other));assert keys[-1].inaxes is right and keys[-1].key=='ctrl+a'
        viewer.key_up(key('a','a',4,other))
        viewer.motion(SimpleNamespace(x=0,y=0,state=0))
        viewer.leave(SimpleNamespace(x=0,y=0,state=0));assert viewer.message.get()==''
        assert viewer.widget.bind('<Enter>') and viewer.widget.bind('<Leave>')
        checks.append('axes/figure transitions, cursor-targeted keys and major/minor grid cycles')

        home=ax.get_extent();right_home=right.get_extent()
        viewer.buttons['Pan'].invoke()
        viewer.press(SimpleNamespace(x=x,y=y,num=1))
        viewer.motion(SimpleNamespace(x=x+12,y=y+5,num=1))
        viewer.release(SimpleNamespace(x=x+12,y=y+5,num=1))
        viewer.flush_events();panned=ax.get_extent()
        assert panned!=home and right.get_xlim()==ax.get_xlim()
        assert right.get_ylim()==right_home[2:]
        assert viewer.buttons['Back'].cget('state')=='normal'
        viewer.buttons['Back'].invoke();viewer.flush_events();assert ax.get_extent()==home
        viewer.buttons['Forward'].invoke();viewer.flush_events();assert ax.get_extent()==panned
        viewer.buttons['Home'].invoke();viewer.flush_events();assert ax.get_extent()==home
        checks.append('pan preview/recomposition, shared axes, Home/Back/Forward toolbar')

        viewer.buttons['Zoom'].invoke();vp=viewer._viewport(0);x,y,w,h=vp.box
        start_pair=(round(x+w*.2),round(y+h*.2));end_pair=(round(x+w*.8),round(y+h*.8))
        viewer.press(SimpleNamespace(x=start_pair[0],y=start_pair[1],num=1))
        viewer.motion(SimpleNamespace(x=end_pair[0],y=end_pair[1],num=1))
        assert viewer.widget.find_withtag('rubberband')
        viewer.release(SimpleNamespace(x=end_pair[0],y=end_pair[1],num=1));viewer.flush_events()
        assert not viewer.widget.find_withtag('rubberband')
        assert ax.get_extent()[1]-ax.get_extent()[0]<home[1]-home[0]
        viewer.home();viewer.flush_events()
        scroll=[];viewer.mpl_connect('scroll_event',scroll.append)
        x,y=center();viewer.wheel(SimpleNamespace(x=x,y=y,delta=60));viewer.flush_events()
        assert scroll[-1].step==.5 and scroll[-1].button=='up'
        assert right.get_xlim()==ax.get_xlim()
        viewer.home();viewer.flush_events()
        checks.append('rectangle zoom, rubberband cleanup and fractional scroll')

        item=viewer._overview_box[0];_,mx,my,mw,mh,_=item
        assert viewer._overview_click(SimpleNamespace(x=mx+mw*.25,y=my+mh*.5))
        viewer.flush_events();assert ax.get_extent()!=home
        overview.set_visible(False);viewer.draw();assert viewer._overview_box is None
        overview.set_visible(True);viewer.home();viewer.flush_events()
        checks.append('overview recentering, focus and optional visibility')

        resizes=[];viewer.mpl_connect('resize_event',resizes.append)
        assert viewer.widget.bind('<Configure>')
        viewer.resize(SimpleNamespace(width=620,height=320))
        first=viewer._resize_pending
        viewer.resize(SimpleNamespace(width=640,height=340))
        assert viewer._resize_pending is not None and viewer._resize_pending!=first
        wait=tkinter.IntVar(viewer.window,value=0)
        viewer.window.after(220,lambda:wait.set(1));viewer.window.wait_variable(wait)
        viewer.flush_events()
        assert viewer._resize_pending is None
        assert (viewer.scene.width,viewer.scene.height)==(640,340)
        assert fig.figsize==(6.4,3.4) and len(resizes)==2
        checks.append('registered Configure binding, real debounce timer and resized scene')

        with tempfile.TemporaryDirectory() as folder:
            for extension in ('png','svg'):
                path=Path(folder)/('figure.'+extension)
                with patch.object(viewer.filedialog,'asksaveasfilename',return_value=str(path)):
                    viewer.buttons['Save'].invoke()
                assert path.is_file() and path.stat().st_size>100
                if extension=='png':
                    with viewer.Image.open(path) as image:assert image.size==(640,340)
                else:
                    content=path.read_text(encoding='utf-8')
                    assert '<svg' in content and '<script' not in content and 'toolbar' not in content
            with patch.object(viewer.filedialog,'asksaveasfilename',return_value=''):
                viewer.save()
        checks.append('Save toolbar writes static PNG/SVG; dialog cancellation')

        closes=[];viewer.mpl_connect('close_event',closes.append)
        viewer.draw_idle();viewer.resize(SimpleNamespace(width=650,height=350))
        viewer.close();viewer.close()
        assert len(closes)==1 and viewer.closed and viewer not in tk._windows
        assert viewer._pending is None and viewer._resize_pending is None
        assert viewer._image is None and viewer._photo is None
        checks.append('close cancels pending work, unregisters window and releases images')
        assert not any(name.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj') for name in sys.modules)
        return dict(python=platform.python_version(),platform=platform.platform(),
                    tk=tkinter.TkVersion,checks=checks,timings=timings,
                    scope='withdrawn real Tk windows; synthetic input; not visual OS comparison')
    finally:
        azl.close(fig);azl.ioff()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();report=run()
    if args.output:args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))
