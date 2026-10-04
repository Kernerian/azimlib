"""Record selected contracts directly from the installed Matplotlib Tk canvas.

Development reference only. Real withdrawn Tk widget, synthetic input;
no reference imports are included in Azimlib runtime.
"""
import argparse
import json
import platform
import tkinter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def record():
    root=tkinter.Tk();root.withdraw()
    try:
        fig=Figure(figsize=(4,3),dpi=100);ax=fig.subplots()
        ax.set_xlim(-60,-40);ax.set_ylim(-30,-10)
        canvas=FigureCanvasTkAgg(fig,master=root);widget=canvas.get_tk_widget()
        widget.pack();root.update_idletasks()
        events=[];canvas.mpl_connect('scroll_event',events.append)
        cases=[]
        for delta in (120,-240,60,0):
            event=SimpleNamespace(delta=delta,x_root=widget.winfo_rootx()+205,
                                  y_root=widget.winfo_rooty()+149,state=0,widget=widget)
            with patch.object(widget,'winfo_containing',return_value=widget):
                canvas.scroll_event_windows(event)
            actual=events[-1]
            cases.append(dict(delta=delta,step=actual.step,button=actual.button,
                              inaxes=actual.inaxes is ax,x=actual.x,y=actual.y))
        linux=[]
        for num in (4,5):
            canvas.scroll_event(SimpleNamespace(x=205,y=149,num=num,state=0))
            actual=events[-1];linux.append(dict(num=num,step=actual.step,button=actual.button))
        drawings=[];canvas.mpl_connect('draw_event',drawings.append);canvas.draw()
        calls=[]
        def first(event):
            calls.append('first');canvas.mpl_disconnect(second)
            canvas.mpl_connect('draw_event',lambda e:calls.append('new'))
        canvas.mpl_connect('draw_event',first)
        second=canvas.mpl_connect('draw_event',lambda e:calls.append('removed'))
        canvas.mpl_connect('draw_event',lambda e:calls.append('last'))
        canvas.draw();first_dispatch=list(calls);calls.clear();canvas.draw()
        return dict(matplotlib=matplotlib.__version__,python=platform.python_version(),
                    platform=platform.platform(),tk=tkinter.TkVersion,windows_scroll=cases,
                    linux_scroll=linux,draw_has_renderer=hasattr(drawings[0],'renderer'),
                    callback_dispatch=[first_dispatch,calls],
                    scope='real withdrawn TkAgg canvas, synthetic events; selected contracts only')
    finally:root.destroy()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'docs/tk-events-reference.json')
    args=parser.parse_args();report=record()
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
