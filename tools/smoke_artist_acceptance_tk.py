"""Real withdrawn Tk for checklist 1.10/1.11; does not measure physical input."""
import argparse
import hashlib
import importlib.util
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

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('artist_case',ROOT/'tools/artist_acceptance_case.py')
case_tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(case_tool)


def run():
    original=tkinter.Tk;checks=[]
    def hidden(*args,**kwargs):
        root=original(*args,**kwargs);root.withdraw();return root
    def check_frame(fig,viewer):
        with renderers.render_image(viewer.scene) as image:assert image.tobytes()==viewer._image.tobytes()
        png=io.BytesIO();svg=io.StringIO()
        with patch.object(tkinter,'Tk',side_effect=AssertionError('savefig creates no UI')):
            fig.savefig(png,format='png');fig.savefig(svg,format='svg')
        png.seek(0)
        with Image.open(png) as image:
            with image.convert('RGBA') as rgba:assert rgba.tobytes()==viewer._image.tobytes()
        assert '<svg ' in svg.getvalue() and '<script' not in svg.getvalue()
    for dpi,orientation in ((100,'horizontal'),(200,'vertical')):
        case=case_tool.build(dpi=dpi,orientation=orientation);fig=case['fig'];viewer=None
        name=f'{dpi}dpi-{orientation}'
        try:
            with patch.object(tkinter,'Tk',hidden):viewer=backend.FigureWindow(fig)
            fig._viewer=viewer;fig.canvas=viewer;viewer.flush_events();home=case['ax'].get_extent()
            assert all(item.norm is case['norm'] for item in case_tool.mappables(case))
            check_frame(fig,viewer);checks.append(name+': six shared mappables; direct RGBA, PNG and Tk match; static export creates no UI')
            events=[];viewer.mpl_connect('draw_event',events.append)
            with azl.ion():case_tool.edit(case)
            viewer.flush_events();assert len(events)==1,len(events)
            assert case['ax'].get_extent()==home;check_frame(fig,viewer)
            checks.append(name+': multi-Artist edits and shared norm produce one scheduled Tk draw; manual extent retained')
            first=viewer._image.tobytes()
            with azl.ion():
                for item in case_tool.mappables(case):item.set_visible(False)
            viewer.flush_events();assert viewer._image.tobytes()!=first
            with azl.ion():
                for item in case_tool.mappables(case):item.set_visible(True)
            viewer.flush_events();assert viewer._image.tobytes()==first
            checks.append(name+': hiding/restoring all six layers restores exact edited pixels')
            before_draws=len(events);source=case['scatter'].data
            with azl.ion():
                try:case['scatter'].set(offsets=[[-51,-24],[-47,-21],[-43,-18]],visible=False,c='red',color='blue')
                except TypeError:pass
                else:raise AssertionError('Alias conflict must fail')
            viewer.flush_events();assert len(events)==before_draws and viewer._image.tobytes()==first
            assert case['scatter'].data is source and case['scatter'].visible
            checks.append(name+': rejected alias batch changes no data/control/pixels/draw count')
            case['ax'].set_extent((-52,-44,-26,-18));viewer.navigation.push();viewer.draw();check_frame(fig,viewer)
            viewer.home();viewer.flush_events();assert case['ax'].get_extent()==home
            checks.append(name+': focus/Home preserve manual view and current edits')
            case_tool.dispose(case);viewer.draw();before=viewer._image.tobytes();before_draws=len(events)
            with azl.ion():case['norm'].vmax=7
            viewer.flush_events();assert len(events)==before_draws and viewer._image.tobytes()==before
            assert all(label.get_figure() is None for label in case['labels'])
            checks.append(name+': removed layers/labels/bar stop invalidating former figure')
        finally:
            if viewer is not None:viewer.close();assert viewer._raster_cache.bytes==0
            azl.close(fig);azl.ioff()
        checks.append(name+': closing releases raster cache')
    assert not any(name.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj') for name in sys.modules)
    files=['src/azimlib/'+name+'.py' for name in ('artist','axes','layers','styles','components','figure_text')]
    files+=['tools/artist_acceptance_case.py','tools/smoke_artist_acceptance_tk.py']
    hashes={}
    for name in files:
        path=ROOT/name
        if name.startswith('src/azimlib/'):
            module=__import__('azimlib.'+Path(name).stem,fromlist=['__file__'])
            path=Path(module.__file__)
        hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    return dict(python=platform.python_version(),platform=platform.platform(),checks=checks,
        sha256=hashes,runtime_origin=str(Path(azl.__file__).resolve().parent),
        independent_runtime=True,scope='Real withdrawn Tk; bundled generalized Natural Earth states, synthetic values/fields; programmatic edits/navigation. Not native appearance or physical input/paint latency.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=run();args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'{len(report["checks"])} Tk checks passed')
