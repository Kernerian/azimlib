"""Scientific labels and marker edits in real withdrawn Tk widgets."""
import argparse,importlib.util,json,platform,tkinter
from pathlib import Path
from unittest.mock import patch
import azimlib as azl
from azimlib.ticker import EngFormatter

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('numeric_example',ROOT/'examples/numeric_formatting.py')
example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)

def run():
    azl.ioff();azl.rcdefaults();original=tkinter.Tk;checks=[]
    def hidden(*args,**kwargs):
        root=original(*args,**kwargs);root.withdraw();return root
    for orientation in ('vertical','horizontal'):
        fig,axes,bars,points=example.build(orientation);viewer=None;draws=[]
        fig.canvas.mpl_connect('draw_event',lambda event:draws.append(event.renderer))
        try:
            with patch.object(tkinter,'Tk',hidden):viewer=fig.show(block=False)
            viewer.flush_events();assert draws and bars[0].formatter.get_offset()=='1e6'
            checks.append(orientation+': initial scientific/offset labels rendered in native Tk widgets')
            longaxis=bars[0].ax.yaxis if orientation=='vertical' else bars[0].ax.xaxis
            offset=longaxis.get_offset_text();before=len(draws)
            with azl.ion():offset.set(visible=False,color='purple',fontsize=8)
            viewer.flush_events();assert len(draws)==before+1 and not offset.get_visible()
            checks.append(orientation+': editable offset visibility/style invalidates one frame')
            before=len(draws)
            with azl.ion():
                offset.set_visible(True);points[0].set_clim(0,2e7)
                bars[0].set_ticks([0,1e7,2e7]);axes[0].set_ylabel('Latitude',labelpad=10)
                axes[0].plot(example.LON,example.LAT,marker='d',color='purple',label='Rota sintética')
                axes[0].legend(loc='upper left')
            viewer.flush_events();assert len(draws)==before+1 and offset.get_text()=='1e7'
            checks.append(orientation+': clim, ticks, labelpad and narrow diamond/legend edits compose one frame')
            bars[0].formatter=EngFormatter(unit='m');viewer.draw()
            assert not longaxis.get_offset_text().get_text()
            checks.append(orientation+': formatter replacement clears stale scientific offset')
            snapshot=viewer.navigation.snapshot();axes[0].set_xlim(-51,-45)
            viewer.navigation.push();viewer.draw();viewer.navigation.back();viewer.draw()
            assert viewer.navigation.snapshot()==snapshot
            assert '<script' not in fig.to_svg()
            checks.append(orientation+': navigation/back and static SVG preserve independent export path')
        finally:
            azl.close(fig)
            if viewer is not None:assert viewer._image is None
    assert not any(name.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj') for name in __import__('sys').modules)
    return dict(python=platform.python_version(),platform=platform.platform(),tk=tkinter.TkVersion,checks=checks,
                scope='real withdrawn Tk; programmatic artist/navigation edits; no physical input or native appearance/latency equivalence')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    args=parser.parse_args();report=run()
    if args.output:args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))
