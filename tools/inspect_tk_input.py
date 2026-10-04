"""Record keyboard/pointer/shortcut contracts from installed Matplotlib TkAgg.

Other platform mask tables are exercised by substituting sys.platform only
while calling the installed normalizers; this is not native OS validation.
"""
import argparse,json,platform,sys,tkinter
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backend_bases import LocationEvent,KeyEvent,key_press_handler


def raw(**kwargs):return SimpleNamespace(x=205,y=149,state=0,char='',keysym='',num=1,**kwargs)


def record():
    root=tkinter.Tk();root.withdraw()
    try:
        fig=Figure(figsize=(4,3),dpi=100);ax=fig.subplots()
        ax.set_xlim(-60,-40);ax.set_ylim(-30,-10)
        canvas=FigureCanvasTkAgg(fig,master=root);canvas.get_tk_widget().pack();root.update_idletasks()
        keyboard=[];pointer=[];states=[]
        key_cases=[('p','p',0),('P','P',1),('p','p',4),('s','s',4),('','Return',0),
                   ('','KP_Enter',0),('','Prior',0),('','Page_Down',0),('','Shift_L',1),
                   ('','Control_R',4),('','Alt_L',0),('','Meta_L',8),('é','eacute',0),
                   ('€','EuroSign',1),('\x03','c',4),('','F1',0),('+','plus',1),
                   ('','Tab',1),('','Escape',0),('','',0)]
        received=[];canvas.mpl_connect('key_press_event',received.append)
        for system in ('win32','linux','darwin'):
            for char,symbol,state in key_cases:
                event=raw();event.char=char;event.keysym=symbol;event.state=state
                with patch.object(sys,'platform',system):canvas.key_press(event)
                payload=received[-1]
                keyboard.append(dict(system=system,char=char,keysym=symbol,state=state,key=payload.key,
                                     modifiers=sorted(payload.modifiers),inaxes=payload.inaxes is ax,
                                     x=payload.x,y=payload.y))
            masks=(0,1,4,8,16,64,131072,1|4|8|16|64|131072)
            for state in masks:
                event=raw();event.state=state
                with patch.object(sys,'platform',system):
                    states.append(dict(system=system,state=state,modifiers=canvas._mpl_modifiers(event),
                                       buttons=sorted(int(b) for b in canvas._mpl_buttons(event))))
            for number in (1,2,3,8,9):
                events=[]
                cid=canvas.mpl_connect('button_press_event',events.append)
                event=raw();event.num=number;event.state=1|4
                with patch.object(sys,'platform',system):canvas.button_press_event(event,dblclick=True)
                payload=events[-1];canvas.mpl_disconnect(cid)
                pointer.append(dict(system=system,num=number,state=event.state,button=int(payload.button),
                                    modifiers=sorted(payload.modifiers),dblclick=payload.dblclick,step=payload.step))
        # Explicit multi-button motion masks, including platform-specific swap.
        for system in ('win32','linux','darwin'):
            for state in (256,512,1024,256|512|1024|2048|4096):
                event=raw();event.state=state
                with patch.object(sys,'platform',system):
                    states.append(dict(system=system,state=state,modifiers=canvas._mpl_modifiers(event),
                                       buttons=sorted(int(b) for b in canvas._mpl_buttons(event))))

        traces=[]
        axes_fig=Figure(figsize=(6,3),dpi=100);axes=axes_fig.subplots(1,2)
        axes_canvas=FigureCanvasTkAgg(axes_fig,master=root)
        for channel in ('figure_enter_event','figure_leave_event','axes_enter_event','axes_leave_event','motion_notify_event'):
            def callback(event,channel=channel):
                traces.append(dict(channel=channel,name=event.name,inaxes=next((i for i,a in enumerate(axes) if event.inaxes is a),None),
                                   x=event.x,y=event.y,modifiers=sorted(event.modifiers)))
            axes_canvas.mpl_connect(channel,callback)
        inputs=[('enter_notify_event',10,10),('motion_notify_event',150,150),('motion_notify_event',155,150),
                ('motion_notify_event',450,150),('motion_notify_event',0,0),('leave_notify_event',0,0)]
        with patch.object(LocationEvent,'_last_axes_ref',None):
            for method,x,y in inputs:
                event=raw();event.x=x;event.y=y;event.state=1
                getattr(axes_canvas,method)(event)

        grid=[];canvas._key=None
        for key in ('g','g','g','g','G','G','G','G'):
            event=KeyEvent('key_press_event',canvas,key,205,151)
            key_press_handler(event,canvas,toolbar=None)
            grid.append(dict(key=key,major=[any(t.gridline.get_visible() for t in axis.majorTicks) for axis in (ax.xaxis,ax.yaxis)],
                             minor=[any(t.gridline.get_visible() for t in axis.minorTicks) for axis in (ax.xaxis,ax.yaxis)]))
        keymaps={k:v for k,v in matplotlib.rcParams.items() if k in ('keymap.home','keymap.back','keymap.forward',
                'keymap.pan','keymap.zoom','keymap.save','keymap.quit','keymap.fullscreen','keymap.grid','keymap.grid_minor')}
        return dict(matplotlib=matplotlib.__version__,python=platform.python_version(),platform=platform.platform(),
                    keyboard=keyboard,modifier_states=states,pointer=pointer,transition_inputs=inputs,transitions=traces,
                    grid_cycle=grid,keymaps=keymaps,
                    scope='real withdrawn TkAgg in Windows; other platform normalizer masks substituted, not native OS runs')
    finally:root.destroy()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'docs/tk-input-reference.json')
    args=parser.parse_args();report=record()
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Recorded:',len(report['keyboard']),'keys,',len(report['modifier_states']),'state masks,',
          len(report['pointer']),'buttons,',len(report['transitions']),'transitions,',len(report['grid_cycle']),'grid steps.')
