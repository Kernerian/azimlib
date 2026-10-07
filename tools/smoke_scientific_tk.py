"""Scientific field edits in a real withdrawn Tk window; synthetic lifecycle."""
import argparse
import json
import platform
import sys
import tkinter as tk
from pathlib import Path
from unittest.mock import patch
import azimlib as azl

def run():
    real=tk.Tk
    def hidden(*args,**kwargs):
        window=real(*args,**kwargs);window.withdraw();return window
    fig,ax=azl.subplots(figsize=(5,4),dpi=100)
    ax.set_extent((0,2,0,2))
    bands=ax.contourf([0,1,2],[0,1,2],[[0,1,2]]*3,levels=[0,1,2])
    bar=fig.colorbar(bands,orientation='horizontal');ax.legend()
    color=ax.imshow([[(.1,.4,.7,.5)]],extent=(.2,.6,.2,.6),origin='lower')
    flow=ax.flow([(.2,.4)],[(1.7,1.5)],[10],vmin=0,vmax=20)
    try:
        with patch.object(tk,'Tk',hidden):viewer=fig.show(block=False)
        viewer.flush_events();bands.set_levels([0,.5,1,2]);bands.set_cmap('sunset')
        color.set_data([[(.6,.2,.7,.5)]]);flow.set_array([15]);viewer.flush_events()
        viewer.draw();assert bar.boundaries==(0.,.5,1.,2.) and len(bands.cvalues)==3
        assert not fig.stale and viewer._image is not None
        color.set_visible(False);viewer.draw();color.remove();viewer.draw()
        viewer.close();assert viewer.closed and viewer._image is None
        assert not any(n.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj') for n in sys.modules)
        return dict(passed=True,version=azl.__version__,python=platform.python_version(),platform=platform.platform(),
                    checks=['filled levels/cmap and linked colorbar update','RGBA and geodesic flow edits',
                            'visibility/removal and real Tk redraw','window/image cleanup; independent runtime'],
                    scope='Local real withdrawn Tk; synthetic edits, no native human input/visual acceptance or remote CI claim')
    finally:azl.close(fig)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    args=parser.parse_args();report=run()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(report,indent=2))
