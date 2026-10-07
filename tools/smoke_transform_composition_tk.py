"""Own transforms/SubFigure/rotation smoke in real withdrawn Tk, synthetic input."""
import argparse
import json
import platform
import sys
import tkinter as tk
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import azimlib as azl
from azimlib.navigation import drag_extent

def run():
    real=tk.Tk
    def hidden(*args,**kwargs):
        window=real(*args,**kwargs);window.withdraw();return window
    fig=azl.figure(figsize=(8,4),dpi=100)
    left,right=fig.subfigures(1,2)
    a,b=left.subplots(),right.subplots()
    for ax in (a,b):
        ax.set_extent((-54,-42,-28,-16))
        ax.geojson({'type':'Polygon','coordinates':[[[-53,-27],[-43,-27],[-43,-17],[-53,-17],[-53,-27]]]},
                   facecolor='#eeeeee',edgecolor='#666666',linewidth=.6,fit=False)
        ax.plot([-52,-49,float('nan'),-46,-44],[-25,-23,float('nan'),-21,-19],color='red')
        ax.grid(True);ax.north_arrow();ax.compass()
    b.set_bearing(35);viewer=None
    try:
        with patch.object(tk,'Tk',hidden):viewer=fig.show(block=False)
        viewer.flush_events();viewer.set_mode('pan')
        assert [m['bearing'] for m in viewer.scene.maps]==[0.,35.]
        vp=viewer._viewport(1);x,y,w,h=vp.box;start=(x+w/2,y+h/2)
        original=b.get_extent();expected=drag_extent(b,vp,start,(start[0]+12,start[1]+8),initial_extent=original)
        viewer.press(SimpleNamespace(x=start[0],y=start[1],num=1,state=0))
        viewer.motion(SimpleNamespace(x=start[0]+12,y=start[1]+8,state=256))
        viewer.flush_events();assert b.get_extent()==expected
        viewer.release(SimpleNamespace(x=start[0]+12,y=start[1]+8,num=1,state=0));viewer.flush_events()
        assert abs(b._north.get_angle()-35)<1e-6 and abs(b._compass.get_angle()-35)<1e-6
        viewer.back();viewer.flush_events();assert b.get_extent()==original
        viewer.forward();viewer.flush_events();assert b.get_extent()==expected
        b.set_bearing(60);viewer.navigation.push();viewer.draw()
        viewer.back();viewer.flush_events();assert b.get_bearing()==35
        viewer.forward();viewer.flush_events();assert b.get_bearing()==60
        viewer.home();viewer.flush_events();assert b.get_bearing()==35 and b.get_extent()==original
        assert all(abs(q-v)<1e-7 for q,v in zip(b.transData.inverted().transform_point(b.transData.transform_point((-48,-22))),(-48,-22)))
        viewer.close();assert viewer.closed and viewer._image is None
        assert not any(n.split('.')[0] in ('matplotlib','cartopy','geopandas','shapely','pyproj') for n in sys.modules)
        return dict(passed=True,version=azl.__version__,python=platform.python_version(),platform=platform.platform(),
                    checks=['SubFigure root canvas and rotated metadata','rotated pan preserves geographic spans',
                            'local north and compass follow bearing','Back/Forward/Home restore bearing and limits',
                            'live display transform inverse','window/image lifecycle and independent runtime'],
                    scope='Real withdrawn Tk windows, synthetic events; no human visual/input acceptance or remote CI claim')
    finally:azl.close(fig)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path)
    args=parser.parse_args();report=run()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(report,indent=2))
