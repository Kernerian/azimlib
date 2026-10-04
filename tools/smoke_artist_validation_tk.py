"""Integrated edits and rejected batches in actual withdrawn Tk widgets."""
import argparse,importlib.util,json,platform,sys,tkinter
from pathlib import Path
from unittest.mock import patch
import azimlib as azl
from azimlib.colors import Normalize

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('artist_validation_example',ROOT/'examples/artist_validation.py')
example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)


def run():
    azl.ioff();azl.rcdefaults();original=tkinter.Tk;checks=[];draws=[];viewer=None
    def hidden(*args,**kwargs):
        root=original(*args,**kwargs);root.withdraw();return root
    fig,handles=example.create()
    fig.canvas.mpl_connect('draw_event',lambda event:draws.append(event.renderer))
    try:
        with patch.object(tkinter,'Tk',hidden):viewer=fig.show(block=False)
        viewer.flush_events();assert draws
        checks.append('initial integrated lines/scatter/raster/contours/shared bar/scale/legend compose in real Tk')
        first=len(draws)
        with azl.ion():example.edit(handles)
        viewer.flush_events();assert len(draws)==first+1
        checks.append('mixed data, shared norm, text, frame, scale, outline and dash-generator edits produce one frame')
        assert handles['points'].norm is handles['image'].norm is handles['bar'].norm
        assert (handles['bar'].norm.vmin,handles['bar'].norm.vmax)==(0,6)
        checks.append('shared normalization stays coherent with colorbar after edits')
        assert handles['line'].get_linestyle()==(4.,2.);viewer.draw();assert handles['line'].get_linestyle()==(4.,2.)
        checks.append('owned generator dash remains renderable across repeated draws')
        before=len(draws);image=viewer._image;svg=fig.to_svg()
        attempts=[lambda:handles['title'].set(text='Invalid',fontstyle='sideways'),
                  lambda:handles['axes'][0].spines['left'].set(color='red',linewidth=-1),
                  lambda:handles['legend'].get_frame().set(facecolor='red',linewidth=-1),
                  lambda:handles['scale'].set(length=50,fontsize=0),
                  lambda:handles['bar'].ax.tick_params(labelsize=0,colors='red'),
                  lambda:handles['image'].set(norm=Normalize(0,100),visible=False,fontweight='unknown')]
        with azl.ion():
            for attempt in attempts:
                try:attempt()
                except ValueError:pass
                else:raise AssertionError('invalid edit was accepted')
        viewer.flush_events();assert len(draws)==before and viewer._image is image and fig.to_svg()==svg and not fig.stale
        checks.append('six rejected edits preserve raster, SVG, model and pending draw count')
        handles['title'].set_fontsize('13');viewer.draw()
        assert '<script' not in fig.to_svg() and 'AzimlibComponents' in fig.to_html()
        checks.append('valid edits remain usable after failures; static SVG and portable HTML stay separate')
    finally:
        azl.close(fig)
        if viewer is not None:assert viewer._image is None
    checks.append('closing releases owned Tk raster')
    assert not any(name.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj') for name in sys.modules)
    return dict(python=platform.python_version(),platform=platform.platform(),tk=tkinter.TkVersion,checks=checks,
                scope='Real withdrawn Tk, programmatic edits, synthetic field/routes. No physical input, visible OS comparison or performance claim.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    args=parser.parse_args();report=run()
    if args.output:args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))
