"""Real Tk globe/terrain navigation, static exports and collapsed-marker edits."""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import sys
import tkinter
from unittest.mock import patch
import azimlib as azl
from azimlib import renderers
from azimlib.backends import tk as backend
from azimlib.renderers import coverage,pillow
from PIL import Image

def run():
    original=tkinter.Tk;checks=[]
    def hidden(*args,**kwargs):
        root=original(*args,**kwargs);root.withdraw();return root
    def check_pixels(fig,viewer):
        with renderers.render_image(viewer.scene) as fresh:assert fresh.tobytes()==viewer._image.tobytes()
        png=io.BytesIO();svg=io.StringIO()
        with patch.object(tkinter,'Tk',side_effect=AssertionError('Static exports must not create UI')):
            fig.savefig(png,format='png');fig.savefig(svg,format='svg')
        png.seek(0)
        with Image.open(png) as source:
            with source.convert('RGBA') as image:assert image.tobytes()==viewer._image.tobytes()
        assert '<svg ' in svg.getvalue() and '<script' not in svg.getvalue()
    for name in ('globe','terrain'):
        options=dict(projection='orthographic',projection_kw=dict(central_longitude=-60,central_latitude=10)) if name=='globe' else dict(projection='mercator')
        fig,ax=azl.subplots(figsize=(4.2,3.6),dpi=100,layout='constrained',**options);viewer=None
        try:
            if name=='globe':
                ax.countries(facecolor='#f4f4f4',edgecolor='#777777',linewidth=.4)
                ax.route([(-46,-23),(-.12,51.5)],arrow=False,color='#b45c32',label='Synthetic route')
                ax.set_extent((-180,180,-89,89));ax.grid(step=30,linewidth=.4)
                focus=(-105,-20,-40,65);point=(-60,10)
            else:
                z=[[math.sin(i/3)+math.cos(j/3) for i in range(12)] for j in range(12)]
                field=ax.imshow(z,extent=(-54,-44,-26,-18),origin='lower',vmin=-2,vmax=2)
                fig.colorbar(field,ax=ax,label='Synthetic field',orientation='horizontal')
                ax.plot([-52,-48,-46],[-24,-20,-23],'D--',color='#b45c32',label='Synthetic route')
                ax.set_extent((-54,-44,-26,-18));ax.scale_bar(length=100);ax.grid(linestyle=':',linewidth=.4)
                focus=(-52,-46,-25,-19);point=(-48,-22)
            ax.set_title(name);ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.legend();ax.north_arrow()
            duplicate,=ax.plot([point[0]]*2,[point[1]]*2,color='magenta',solid_capstyle='projecting',marker='None')
            with patch.object(tkinter,'Tk',hidden):viewer=backend.FigureWindow(fig)
            fig._viewer=viewer;fig.canvas=viewer;home=ax.get_extent();first=viewer._image.tobytes()
            check_pixels(fig,viewer);checks.append(f'{name}: direct raster, static PNG and current Tk match; PNG/SVG create no UI')
            ax.set_extent(focus);viewer.navigation.push();viewer.draw();check_pixels(fig,viewer)
            viewer.home();viewer.flush_events();assert ax.get_extent()==home and viewer._image.tobytes()==first
            checks.append(f'{name}: regional focus and Home preserve exact view/pixels')
            duplicate.set_marker('D');viewer.draw();check_pixels(fig,viewer)
            assert any(p.style.get('fill')=='magenta' or p.style.get('stroke')=='magenta' for p in viewer.scene.items)
            checks.append(f'{name}: explicit marker edit appears on a collapsed projecting-cap line')
            duplicate.set_visible(False);viewer.draw();assert viewer._image.tobytes()==first
            checks.append(f'{name}: hiding the marker restores exact original frame')
            fig.set_dpi(200);viewer.draw();assert viewer._image.size==(840,720);check_pixels(fig,viewer)
            checks.append(f'{name}: 200 DPI resize and static/current-view RGBA remain consistent')
        finally:
            if viewer is not None:
                viewer.close();assert viewer._raster_cache.bytes==0
            azl.close(fig)
        checks.append(f'{name}: closing releases retained raster frames')
    assert not any(name.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj') for name in sys.modules)
    return dict(python=platform.python_version(),platform=platform.platform(),checks=checks,
        runtime_sha256={m.__name__:hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in (coverage,pillow,backend)},
        independent_runtime=True,scope='Real withdrawn Tk, programmatic input/edits, synthetic fields/routes. Not visible painting or physical input latency.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=run();args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'{len(report["checks"])} Tk checks passed')
