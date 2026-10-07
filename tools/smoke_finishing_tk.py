"""Real withdrawn Tk lifecycle for curved names and own expression layout."""
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
    def hidden(*args,**kwargs):window=real(*args,**kwargs);window.withdraw();return window
    f,a=azl.subplots(figsize=(5,4));a.set_extent((0,10,0,8))
    line={'type':'Feature','properties':{'name':'River'},'geometry':{'type':'LineString','coordinates':[[0,3],[4,4],[10,3]]}}
    a.geojson(line,color='#258bb0');labels=a.labels(line,placement='curve',repeat=80)
    title=a.set_title(r'$x_0^2$');a.scale_bar(length=100)
    try:
        with patch.object(tk,'Tk',hidden):viewer=f.show(block=False)
        viewer.flush_events();title.set_text(r'$\frac{1}{2}$');viewer.draw()
        assert viewer._image is not None and not f.stale
        labels.set_visible(False);viewer.draw();labels.set_visible(True);a.set_bearing(20);viewer.draw()
        viewer.close();assert viewer.closed and viewer._image is None
        assert 'matplotlib' not in sys.modules
        return dict(passed=True,version=azl.__version__,python=platform.python_version(),platform=platform.platform(),
                    checks=['Math title edit and redraw','Curved labels visibility and bearing','Tk/image cleanup; independent runtime'],
                    scope='Withdrawn Tk with synthetic edits; not native human visual/input approval or remote CI')
    finally:azl.close(f)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);args=p.parse_args();report=run()
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))
