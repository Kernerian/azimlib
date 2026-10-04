"""Exact cached/uncached pixels and canvas event/history contracts in real Tk."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import tkinter
from unittest.mock import patch
import azimlib as azl
from azimlib import renderers
from azimlib.backends import tk as backend
from PIL import Image

def run():
    original=tkinter.Tk;checks=[];viewer=None
    def hidden(*args,**kwargs):
        root=original(*args,**kwargs);root.withdraw();return root
    fig,ax=azl.subplots(figsize=(4,3));ax.set_extent((-54,-42,-28,-16))
    line,=ax.plot([-52,-48,-44],[-26,-22,-18],'D--',label='Route')
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.legend();ax.scale_bar(length=100)
    north=ax.north_arrow();ax.compass(loc='lower right')
    digest=lambda image:hashlib.sha256(image.tobytes()).hexdigest()
    try:
        with patch.object(tkinter,'Tk',hidden):viewer=backend.FigureWindow(fig)
        fig._viewer=viewer;fig.canvas=viewer;home=ax.get_extent();first=digest(viewer._image)
        events=[];viewer.mpl_connect('draw_event',events.append)
        with patch.object(renderers,'render_image',wraps=renderers.render_image) as raster:
            viewer.draw();viewer.draw()
            assert raster.call_count==0 and len(events)==2 and digest(viewer._image)==first
        checks.append('unchanged redraws reuse exact RGBA while emitting each draw_event')
        for change in (lambda:ax.zoom(1.5),lambda:ax.pan(.3,.2)):
            change();viewer.navigation.push();viewer.draw()
        previous_calls=viewer._raster_cache.hits
        with patch.object(renderers,'render_image',wraps=renderers.render_image) as raster:
            viewer.back();viewer.flush_events();viewer.forward();viewer.flush_events();viewer.home();viewer.flush_events()
            assert raster.call_count==0 and viewer._raster_cache.hits>=previous_calls+3
        assert ax.get_extent()==home and digest(viewer._image)==first
        checks.append('back/forward/home reuse visited frames and restore exact original pixels')
        with patch.object(renderers,'render_image',wraps=renderers.render_image) as raster:
            line.set_color('red');viewer.draw();assert raster.call_count==1
            before=digest(viewer._image);north.set_visible(False);viewer.draw();assert raster.call_count==2
            assert digest(viewer._image)!=before
        checks.append('style and visibility edits rerasterize changed scenes')
        # Reference must bypass the viewer cache and match its latest pixels.
        fresh=renderers.render_image(viewer.scene)
        try:assert digest(fresh)==digest(viewer._image)
        finally:fresh.close()
        stream=io.BytesIO();fig.savefig(stream,format='png');stream.seek(0)
        with Image.open(stream) as image:assert digest(image.convert('RGBA'))==digest(viewer._image)
        checks.append('direct raster and static PNG equal cached current-view pixels')
        fig.set_dpi(120);viewer.draw();assert viewer._image.size==(480,360)
        assert viewer._raster_cache.bytes<=viewer._raster_cache.max_bytes
        assert len(viewer._raster_cache._images)<=viewer._raster_cache.max_entries
        checks.append('DPI changes invalidate dimensions and LRU respects retained pixel limits')
        with patch.object(viewer._raster_cache,'store',side_effect=MemoryError('optional retention failed')):
            ax.set_title('New frame');viewer.draw();assert viewer._image is not None and not fig.stale
        checks.append('optional cache retention failure still displays a fresh rendered frame')
        with patch.object(viewer._raster_cache,'lookup',side_effect=MemoryError('optional lookup copy failed')):
            viewer.draw();assert viewer._image is not None and not fig.stale
        checks.append('optional cache lookup allocation failure falls back to direct raster')
    finally:
        if viewer is not None:
            viewer.close();assert viewer._raster_cache.bytes==0 and not viewer._raster_cache._images
        azl.close(fig)
    checks.append('closing releases active and all retained cached RGBA frames')
    assert not any(name.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj') for name in sys.modules)
    return dict(python=platform.python_version(),platform=platform.platform(),tk=tkinter.TkVersion,checks=checks,
                scope='Real withdrawn Tk with programmatic input; no visible presentation or physical-input timing.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    args=parser.parse_args();report=run()
    if args.output:args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))
