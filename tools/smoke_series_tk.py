"""Series/cycle/style integration in real Tk; synthetic routes and hidden UI."""
import argparse,importlib.util,json,math,platform,tempfile,tkinter
from pathlib import Path
from unittest.mock import patch
import azimlib as azl

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('series_example',ROOT/'examples/series_styles.py')
example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)


def run():
    azl.ioff();azl.rcdefaults();checks=[];original=tkinter.Tk
    def hidden_root(*args,**kwargs):
        window=original(*args,**kwargs);window.withdraw();return window
    for theme in ('light','dark'):
        fig,axes,lines,named=example.build(theme,real_data=False);draws=[]
        fig.canvas.mpl_connect('draw_event',lambda event:draws.append(event.renderer))
        try:
            with patch.object(tkinter,'Tk',hidden_root):viewer=fig.show(block=False)
            viewer.flush_events();assert draws and not fig.stale
            checks.append(theme+': matrix/data lines, independent scatter, styled legends and native widgets')
            extent=axes[0].get_extent();before=len(draws)
            with azl.ion():example.edit(axes,lines,named,theme)
            viewer.flush_events();assert len(draws)==before+1 and axes[0].get_extent()==extent
            assert lines[1].get_color()=='#9467bd' and not lines[2].get_visible()
            assert len(axes[0].get_legend().get_texts())==4
            expected='white' if theme=='dark' else 'black'
            assert axes[0].get_legend().get_texts()[0].get_color()==expected
            checks.append(theme+': batch editing/visibility/new cycle/legend reconstruction renders one frame')
            before=len(draws);count=len(axes[0].layers);index=axes[0]._plot_index
            with azl.ion():
                try:axes[0].plot([-52,-48],[-24,-22],[-50,-46],[-25,95])
                except ValueError:pass
                else:raise AssertionError('invalid latitude accepted')
            viewer.flush_events();assert len(draws)==before and len(axes[0].layers)==count and axes[0]._plot_index==index
            checks.append(theme+': later invalid group leaves no layers, view changes, cycle consumption or frame')
            x=[-52+i for i in range(9)]
            y=[[-22+1.2*math.sin(i*.4+j*.12) for j in range(48)] for i in range(9)]
            before=len(draws)
            with azl.ion():many=axes[0].plot(x,y,linewidth=.25,marker='None',alpha=.3,label='_auxiliary')
            viewer.flush_events();assert len(many)==48 and len(draws)==before+1 and axes[0].get_extent()==extent
            assert all(line.axes is axes[0] for line in many)
            checks.append(theme+': 48-column synthetic route batch creates editable handles in one frame')
            snapshot=viewer.navigation.snapshot();axes[0].set_xlim(-51,-45);viewer.navigation.push();viewer.draw()
            assert axes[1].get_xlim()==axes[0].get_xlim()
            viewer.navigation.back();viewer.draw();assert viewer.navigation.snapshot()==snapshot
            checks.append(theme+': shared navigation/back preserve all routes and original geographic view')
            with tempfile.TemporaryDirectory() as folder:
                svg=Path(folder)/'map.svg';fig.savefig(svg)
                assert '<svg' in svg.read_text(encoding='utf-8') and '<script' not in svg.read_text(encoding='utf-8')
            checks.append(theme+': static SVG excludes UI; closing releases current raster')
        finally:
            azl.close(fig)
            assert viewer._image is None
    assert not any(name.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj') for name in __import__('sys').modules)
    return dict(python=platform.python_version(),platform=platform.platform(),tk=tkinter.TkVersion,
                checks=checks,scope='real withdrawn Tk, programmatic edits/navigation and synthetic 48-column routes; no physical input, native appearance or latency benchmark')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    args=parser.parse_args();report=run()
    if args.output:args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))
