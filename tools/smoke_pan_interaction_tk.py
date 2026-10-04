"""Live-pan integration in real withdrawn Tk; no physical-input claim."""

import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from publication_privacy import public_path,sanitize_text
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import tkinter as tk
import time
from threading import Event,get_ident
from types import SimpleNamespace
from unittest.mock import patch

import azimlib as azl
from azimlib.navigation import drag_extent
from azimlib.renderers import render_image
from azimlib.scene import Text
from PIL import Image,ImageTk

ROOT=Path(__file__).resolve().parents[1]


def run(previews=None):
    real=tk.Tk
    def hidden(*args,**kwargs):
        root=real(*args,**kwargs);root.withdraw();return root
    fig,ax=azl.subplots(figsize=(4,3),dpi=100)
    ax.map('brazil',facecolor='#eeeeee',edgecolor='#333333',linewidth=.8)
    ax.set_extent((-76,-32,-36,8));ax.set_xticks([-70,-60,-50,-40],labels=['70W','60W','50W','40W'])
    ax.set_yticks([-30,-20,-10,0]);ax.set_title('Live pan');ax.grid(linestyle=':',linewidth=.5)
    viewer=None;checks=[];frames=[]
    try:
        with patch.object(tk,'Tk',hidden):viewer=fig.show(block=False)
        viewer.flush_events();viewer.set_mode('pan')
        viewport=viewer._viewport(0);x,y,w,h=viewport.box;start=(x+w*.5,y+h*.5)
        original=ax.get_extent();before=viewer.scene
        def capture(name):
            # Navigation uses unclipped primitive tiles; independently rebuild
            # them from the displayed Scene, without reusing the viewer cache.
            from azimlib.renderers._tile_cache import TileCache
            tiles=TileCache() if name=='during' else None
            try:expected=render_image(viewer.scene,_interactive=name=='during',_tile_cache=tiles)
            finally:
                if tiles is not None:tiles.close()
            try:assert viewer._image.tobytes()==expected.tobytes()
            finally:expected.close()
            displayed=ImageTk.getimage(viewer._photo)
            try:assert displayed.tobytes()==viewer._image.tobytes()
            finally:displayed.close()
            frames.append(dict(phase=name,extent=ax.get_extent(),size=viewer._image.size,
                               rgba_sha256=hashlib.sha256(viewer._image.tobytes()).hexdigest()))
            if previews:
                previews.mkdir(parents=True,exist_ok=True)
                viewer._image.save(previews/f'pan-live-{name}.png')
        capture('before')
        viewer.press(SimpleNamespace(x=start[0],y=start[1],num=1,state=0))
        for dx,dy in ((18,-8),(30,12)):
            event=SimpleNamespace(x=start[0]+dx,y=start[1]+dy,state=256)
            with (patch.object(Image,'open',side_effect=AssertionError('no PNG decoding')),
                  patch.object(Image.Image,'save',side_effect=AssertionError('no PNG encoding'))):
                with patch.object(viewer,'_display',wraps=viewer._display) as display:
                    viewer.motion(event)
                    assert display.call_count==0,'No pasted-bitmap preview before the idle redraw'
                    assert ax.get_extent()==drag_extent(ax,viewport,start,(event.x,event.y),initial_extent=original)
                    assert viewer.drag is not None and viewer.navigation.index==0
                    viewer.flush_events();assert display.call_count==1
        checks.append('left motion updates limits and redraws full canvas while button is held, without PNG codecs/bitmap translation')
        tick_before=next(item for item in before.items if isinstance(item,Text) and item.text=='60W')
        tick_after=next(item for item in viewer.scene.items if isinstance(item,Text) and item.text=='60W')
        assert abs(tick_after.x-tick_before.x-30)<1e-7
        assert max(abs(a-b) for a,b in zip(before.maps[0]['box'],viewer.scene.maps[0]['box']))<1e-7
        capture('during')
        checks.append('longitude tick moves 30 pixels with geographic data; frame remains fixed; displayed RGBA is the freshly rendered full Scene')
        current=ax.get_extent();viewer.release(SimpleNamespace(x=event.x,y=event.y,num=1,state=0));viewer.flush_events()
        assert ax.get_extent()==current and len(viewer.navigation.history)==2
        capture('after')
        assert frames[1]['extent']==frames[2]['extent']
        checks.append('release keeps the live extent without a jump, restores exact raster quality and creates one history entry for the entire drag')
        viewer.back();viewer.flush_events();assert ax.get_extent()==original
        viewer.forward();viewer.flush_events();assert ax.get_extent()==current
        viewer.home();viewer.flush_events();assert ax.get_extent()==original
        checks.append('Back/Forward/Home restore whole views after a live drag')
        viewport=viewer._viewport(0);x,y,w,h=viewport.box;start=(x+w*.35,y+h*.45)
        right=2 if sys.platform=='darwin' else 3
        right_mask=512 if sys.platform=='darwin' else 1024
        viewer.press(SimpleNamespace(x=start[0],y=start[1],num=right,state=0))
        for dx,dy in ((18,-8),(30,-12)):
            event=SimpleNamespace(x=start[0]+dx,y=start[1]+dy,state=right_mask)
            viewer.motion(event);viewer.flush_events()
            assert ax.get_extent()==drag_extent(ax,viewport,start,(event.x,event.y),button=3,initial_extent=original)
            assert viewer.drag is not None
        live=ax.get_extent();viewer.release(SimpleNamespace(x=event.x,y=event.y,num=right,state=0));viewer.flush_events()
        assert ax.get_extent()==live
        checks.append('right-button zoom updates continuously using the frozen cursor anchor and normalized equal-aspect display scale')
        viewer.home();viewer.flush_events()
        viewport=viewer._viewport(0);x,y,w,h=viewport.box;start=(x+w*.5,y+h*.5)
        viewer.press(SimpleNamespace(x=start[0],y=start[1],num=1,state=0))
        viewer.motion(SimpleNamespace(x=start[0]+18,y=start[1]+7,state=256))
        held=ax.get_extent()
        viewer.leave(SimpleNamespace(x=-8,y=start[1],state=256))
        viewer.enter(SimpleNamespace(x=start[0]-90,y=start[1]-30,state=0))
        viewer.motion(SimpleNamespace(x=start[0]+90,y=start[1]+30,state=0))
        viewer.flush_events()
        assert ax.get_extent()==held and viewer.drag is None
        assert tuple(viewer.scene.maps[0]['extent'])==tuple(held[i] for i in (0,2,1,3))
        expected=render_image(viewer.scene)
        try:assert viewer._image.tobytes()==expected.tobytes()
        finally:expected.close()
        viewer.back();viewer.flush_events();assert ax.get_extent()==original
        checks.append('lost release outside canvas ends the old drag at its last held view; reentry/motion cannot teleport; exact pixels and Back remain correct')
        viewport=viewer._viewport(0);x,y,w,h=viewport.box;start=(x+w*.5,y+h*.5)
        viewer.press(SimpleNamespace(x=start[0],y=start[1],num=1,state=0))
        viewer.leave(SimpleNamespace(x=x-5,y=start[1],state=256))
        viewer.motion(SimpleNamespace(x=x-5,y=start[1],state=256))
        viewer.enter(SimpleNamespace(x=start[0]+10,y=start[1],state=256))
        viewer.motion(SimpleNamespace(x=start[0]+10,y=start[1],state=256))
        assert viewer.drag is not None
        assert ax.get_extent()==drag_extent(ax,viewport,start,(start[0]+10,start[1]),initial_extent=original)
        viewer.release(SimpleNamespace(x=start[0]+10,y=start[1],num=1,state=0));viewer.flush_events()
        checks.append('a genuinely held button continues outside Axes/canvas and reenters using the original frozen anchor')
        viewer.home();viewer.flush_events();viewer._raster_cache.clear()
        viewport=viewer._viewport(0);x,y,w,h=viewport.box;start=(x+w*.5,y+h*.5)
        gate=Event();started=Event();threads=[];heartbeats=[]
        original_renderer=viewer._pan_raster.preview_renderer
        def slow_renderer(scene):
            threads.append(get_ident());started.set();gate.wait(3)
            return original_renderer(scene)
        viewer._pan_raster.preview_renderer=slow_renderer
        viewer.press(SimpleNamespace(x=start[0],y=start[1],num=1,state=0))
        # Hold the raster worker deliberately. Tk must still service its own
        # timer and newer Motion requests without releasing that worker.
        try:
            viewer.motion(SimpleNamespace(x=start[0]+5,y=start[1]+3,state=256));viewer.window.update()
            assert started.wait(3)
            viewer.window.after(10,lambda:heartbeats.append(time.perf_counter()))
            for dx in range(6,16):
                viewer.motion(SimpleNamespace(x=start[0]+dx,y=start[1]+3,state=256));viewer.window.update()
            deadline=time.monotonic()+1
            while not heartbeats and time.monotonic()<deadline:viewer.window.update();time.sleep(.002)
            assert heartbeats and not gate.is_set(),'Tk must remain responsive while rasterization is blocked'
            assert ax.get_extent()==drag_extent(ax,viewport,start,(start[0]+15,start[1]+3),initial_extent=original)
            assert all(thread!=get_ident() for thread in threads)
            assert viewer._pan_waiting,'Newer views must coalesce while work is blocked'
            if viewer._pixel_process is not None:
                assert viewer._pan_prefetched and viewer._pan_raster._queued is not None
                assert viewer._pan_raster._queued[1][0]<viewer._pan_generation,'At most one prepared intermediate view, plus newest uncomposed limits'
            else:assert viewer._pan_raster._queued is None
        finally:gate.set()
        viewer.flush_events()
        viewer.release(SimpleNamespace(x=start[0]+15,y=start[1]+3,num=1,state=0));viewer.flush_events()
        viewer._pan_raster.preview_renderer=original_renderer
        checks.append('Tk timer and ten newer motions remain responsive while raster is blocked; bounded active/prepared views plus coalesced newest limits')
        viewer.home();viewer.flush_events()
        viewport=viewer._viewport(0);x,y,w,h=viewport.box
        for _ in range(6):
            viewer.wheel(SimpleNamespace(x=x+w*.5,y=y+h*.5,delta=120,state=0))
            viewer.window.update()
        deadline=time.monotonic()+5
        while viewer._wheel_pending is not None and time.monotonic()<deadline:
            viewer.window.update();time.sleep(.002)
        viewer.flush_events();assert viewer._wheel_pending is None and not viewer._async_pan
        expected=render_image(viewer.scene)
        try:assert viewer._image.tobytes()==expected.tobytes()
        finally:expected.close()
        checks.append('six wheel zoom edits coalesce and restore exact full-quality pixels after the 120ms quiet interval')
        viewer.home();viewer.flush_events();viewer.set_mode('zoom')
        viewport=viewer._viewport(0);x,y,w,h=viewport.box
        viewer.press(SimpleNamespace(x=x+w*.25,y=y+h*.25,num=1,state=0))
        viewer.motion(SimpleNamespace(x=x+w*.75,y=y+h*.75,state=256))
        viewer.release(SimpleNamespace(x=x+w*.75,y=y+h*.75,num=1,state=0))
        assert viewer._async_pan;viewer.flush_events()
        expected=render_image(viewer.scene)
        try:assert viewer._image.tobytes()==expected.tobytes()
        finally:expected.close()
        checks.append('rectangle zoom rasterizes off the Tk thread and presents exact settled pixels')
        child=viewer._pixel_process
        viewer.close();assert viewer._image is None and viewer._pending is None
        if child is not None:assert child.process.poll() is not None,'Pixel child must stop when the viewer closes'
        checks.append('closing releases the raster and pending redraw')
        assert not any(name.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj','folium') for name in sys.modules)
        import azimlib.backends.tk as backend
        import azimlib.navigation as navigation
        import azimlib.backends._pan_raster as pan_raster
        return dict(python=platform.python_version(),platform=platform.platform(),checks=checks,frames=frames,
                    sha256={name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in
                            (('backend',Path(backend.__file__)),('navigation',Path(navigation.__file__)),
                             ('pan_raster',Path(pan_raster.__file__)),('tool',Path(__file__)))},
                    independent_runtime=True,runtime_origin=public_path(Path(azl.__file__).resolve()),
                    scope='Withdrawn real Tk, synthetic handlers and inspection of our generated canvas buffers only; no desktop screenshot, physical input or presentation-latency claim.')
    finally:
        if viewer is not None:viewer.close()
        azl.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--previews',type=Path)
    args=parser.parse_args();report=run(args.previews)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f"{len(report['checks'])} live-pan Tk checks passed")
