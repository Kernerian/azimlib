"""Figure sizing/title/layout integration in real withdrawn Tk windows."""
import argparse,importlib.util,json,platform,tempfile,tkinter
from pathlib import Path
from unittest.mock import patch
import azimlib as azl
from azimlib.backends import tk
from azimlib.scene import Text
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('composition_example',ROOT/'examples/composition_matrix.py')
example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)


def run():
    azl.ioff();checks=[];original=tkinter.Tk
    def hidden_root(*args,**kwargs):
        window=original(*args,**kwargs);window.withdraw();return window
    for kind in example.SIZES:
        fig,axes,bar=example.build(kind,'constrained');drawings=[];resizes=[]
        def drawn(event):
            assert fig.canvas is event.canvas and fig._viewer is event.canvas and event.canvas in tk._windows
            assert not fig.stale
            drawings.append(event)
        fig.canvas.mpl_connect('draw_event',drawn);fig.canvas.mpl_connect('resize_event',resizes.append)
        try:
            with patch.object(tkinter,'Tk',hidden_root):viewer=fig.show(block=False)
            assert drawings and drawings[0].renderer is viewer.scene
            viewer.flush_events();checks.append(kind+': callback observes registered first draw')
            extent=axes[0].get_extent();before=len(drawings)
            with azl.ion():
                fig.set_size_inches(example.SIZES[kind][0])
                axes[0].set_title('Painel\nEditado',loc='left',fontsize=9,pad=12)
                fig._supxlabel.set_visible(False)
            viewer.flush_events()
            assert len(drawings)==before+1 and resizes and axes[0].get_extent()==extent
            assert viewer._image.size==tuple(round(v*fig.get_dpi()) for v in fig.get_size_inches())
            checks.append(kind+': grouped size/title/visibility edits update physical raster and preserve extent')
            fig.set_dpi(150);viewer.flush_events()
            assert viewer._image.size==tuple(round(v*150) for v in fig.get_size_inches())
            center=next(i for i in viewer.scene.items if isinstance(i,Text) and i.text=='Rota' and abs(i.style['font_size']-9*150/72)<1e-6)
            assert center and not fig.stale
            checks.append(kind+': DPI updates native canvas and typography')
            requested=(viewer.widget.cget('width'),viewer.widget.cget('height'))
            fig.set_size_inches(example.SIZES[kind][1],forward=False);viewer.draw();viewer.flush_events()
            assert requested==(viewer.widget.cget('width'),viewer.widget.cget('height'))
            with tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/'static.png';fig.savefig(path,dpi=200)
                with Image.open(path) as image:assert image.size==tuple(round(v*200) for v in fig.get_size_inches())
            assert fig.get_dpi()==150
            checks.append(kind+': forward=False preserves widget request; static save DPI is temporary')
        finally:azl.close(fig)
    fig,ax=azl.subplots(figsize=(4,3));captured=[]
    def failing(event):captured.append(event.canvas);raise ValueError('first callback failed')
    cid=fig.canvas.mpl_connect('draw_event',failing);old=fig.canvas
    try:
        with patch.object(tkinter,'Tk',hidden_root):
            try:fig.show(block=False)
            except ValueError as error:assert str(error)=='first callback failed'
            else:raise AssertionError('first callback must run during show')
        assert captured[0].closed and captured[0]._image is None
        assert fig.canvas is old and fig._viewer is None and not fig._closed and fig in azl._figures
        old.mpl_disconnect(cid)
        with patch.object(tkinter,'Tk',hidden_root):viewer=fig.show(block=False)
        assert not viewer.closed
        checks.append('failed first callback releases window, restores canvas/registry and permits retry')
    finally:azl.close(fig)
    fig,ax=azl.subplots(figsize=(4,3));closed=[]
    def closing(event):closed.append(event.canvas);event.canvas.close()
    fig.canvas.mpl_connect('draw_event',closing)
    with patch.object(tkinter,'Tk',hidden_root):viewer=fig.show(block=False)
    assert closed==[viewer] and viewer.closed and viewer not in tk._windows
    checks.append('first draw callback can close its window without later widget access')
    assert not any(name.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj') for name in __import__('sys').modules)
    return dict(python=platform.python_version(),platform=platform.platform(),tk=tkinter.TkVersion,checks=checks,
                scope='real withdrawn Tk; programmatic dimension/title edits; no physical input or perceptual latency')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    args=parser.parse_args();report=run()
    if args.output:args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))
