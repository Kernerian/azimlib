"""Record pan contracts from installed Matplotlib; development reference only.

Real withdrawn TkAgg canvas and synthetic events, never physical input or a
visible-window inspection. Runtime Azimlib imports no reference implementation.
"""
import hashlib
import json
from pathlib import Path
import platform
import tkinter as tk

import azimlib as azl
from azimlib.navigation import drag_extent,viewport_from_metadata
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backend_bases import MouseEvent

ROOT=Path(__file__).resolve().parents[1]


def inspect():
    initial=(-76.,-32.,-36.,8.)
    fig,ax=azl.subplots(figsize=(6.4,4.8),dpi=100);ax.set_extent(initial)
    viewport=viewport_from_metadata(ax.projection,fig.to_scene().maps[0])
    root=tk.Tk();root.withdraw()
    try:
        ref=Figure(figsize=(6.4,4.8),dpi=100);native=ref.subplots()
        native.set_aspect('equal',adjustable='box')
        canvas=FigureCanvasTkAgg(ref,master=root)
        bar=NavigationToolbar2Tk(canvas,root)
        native.set_xlim(*initial[:2]);native.set_ylim(*initial[2:]);canvas.draw()
        box=(native.bbox.x0,480-native.bbox.y1,native.bbox.width,native.bbox.height)
        assert max(abs(a-b) for a,b in zip(box,viewport.box))<1e-8,(box,viewport.box)
        cases=[];max_error=0.
        for button in (1,3):
            for key in (None,'x','y','control','shift'):
                for anchor in ((.35,.45),(.7,.3)):
                    for delta in ((30.,15.),(20.,-40.),(-24.,12.)):
                        native.set_xlim(*initial[:2]);native.set_ylim(*initial[2:]);canvas.draw()
                        x,y,w,h=box;start=(x+w*anchor[0],y+h*anchor[1]);end=(start[0]+delta[0],start[1]+delta[1])
                        if not bar.mode:bar.pan()
                        press=MouseEvent('button_press_event',canvas,start[0],480-start[1],button=button,key=key)
                        bar.press_pan(press)
                        # MouseEvent exposes integer display coordinates. Use
                        # those same input pixels for the independent calculation.
                        motion=MouseEvent('motion_notify_event',canvas,end[0],480-end[1],key=key,buttons={button})
                        bar.drag_pan(motion)
                        before_release=tuple(float(v) for v in (*native.get_xlim(),*native.get_ylim()))
                        root.update_idletasks()
                        bar.release_pan(None)
                        actual=tuple(float(v) for v in (*native.get_xlim(),*native.get_ylim()))
                        assert before_release==actual,'Reference limits change during motion, not only at release'
                        actual_start=(press.x,480-press.y);actual_end=(motion.x,480-motion.y)
                        own=drag_extent(ax,viewport,actual_start,actual_end,button=button,constraint=key,initial_extent=initial)
                        error=max(abs(a-b) for a,b in zip(own,actual));max_error=max(max_error,error)
                        assert error<1e-8,(button,key,delta,own,actual,error)
                        cases.append(dict(button=button,key=key,start=actual_start,end=actual_end,extent=actual,
                                          changed_before_release=actual!=initial,error_degrees=error))
        return dict(matplotlib=matplotlib.__version__,python=platform.python_version(),platform=platform.platform(),
                    initial_extent=initial,viewport_box=viewport.box,cases=cases,max_error_degrees=max_error,
                    sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
                            ('src/azimlib/navigation.py','src/azimlib/backends/tk.py','tools/inspect_pan_interaction.py')},
                    scope='60 equal-aspect longitude/latitude cases, selected left/right pan and x/y/Ctrl/Shift contracts. Withdrawn TkAgg and synthetic events; not physical input or projection equivalence.')
    finally:
        root.destroy();azl.close(fig)


if __name__=='__main__':
    report=inspect()
    (ROOT/'docs/pan-interaction-reference.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f"{len(report['cases'])} native pan cases; max limit error {report['max_error_degrees']:.3g} degrees")
