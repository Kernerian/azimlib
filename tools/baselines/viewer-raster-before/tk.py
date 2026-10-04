"""Native Tk figure window, implemented without any Matplotlib imports.

Tk provides widgets and input events, Pillow a raster buffer and font drawing;
all geometry, projections, layout, style and rendering come from Azimlib.
"""
from __future__ import annotations
import io
import math
import weakref
from pathlib import Path

from ..navigation import Navigation,drag_extent,zoom_extent,viewport_from_metadata
from ._tk_input import key_name,modifiers,mouse_button,pressed_buttons
from ..config import rcParams

_windows=[]


def _imports():
    try:
        import tkinter as tk
        from tkinter import filedialog,messagebox
        from PIL import Image,ImageTk,ImageDraw
    except ImportError as exc:
        raise ImportError("Desktop show() needs Tk and Pillow. Install azimlib[gui], or use show(backend='browser').") from exc
    return tk,filedialog,messagebox,Image,ImageTk,ImageDraw


def show(figure,*,block=True):
    viewer=getattr(figure,'_viewer',None)
    if viewer is None or viewer.closed:
        old_canvas=figure.canvas
        viewer=FigureWindow(figure)
        if hasattr(old_canvas,'_callbacks'):
            viewer._event_callbacks.update(old_canvas._callbacks)
            viewer._callback_id=old_canvas._next_id
        figure._viewer=viewer
        figure.canvas=viewer
        _windows.append(viewer)
    else:
        viewer.draw()
        viewer.window.deiconify()
    if block:
        mainloop()
    return viewer


def mainloop():
    living=[viewer for viewer in _windows if not viewer.closed]
    if living:
        living[0].window.mainloop()


class FigureWindow:
    def __init__(self,figure):
        tk,self.filedialog,self.messagebox,self.Image,self.ImageTk,self.ImageDraw=_imports()
        self.tk=tk
        self.figure=figure
        self.closed=False
        self.mode=''
        self.constraint=None
        self.drag=None
        self._pending=None
        self._resize_pending=None
        self._event_callbacks={}
        self._callback_id=0
        self._key=self._button=None
        self._last_axes_ref=None
        self.active=next((i for i,a in enumerate(figure.axes) if a._colorbar_artist is None),0)
        try:
            self.window=tk.Tk()
        except tk.TclError as exc:
            raise RuntimeError("A desktop display is unavailable. Use show(backend='browser') or savefig().") from exc
        self.window.title(figure._window_title())
        self.window.protocol('WM_DELETE_WINDOW',self.close)
        self.navigation=Navigation(figure)
        self.toolbar=tk.Frame(self.window,borderwidth=2,height=50)
        self.toolbar.pack(side=tk.BOTTOM,fill=tk.X)
        self.toolbar.pack_propagate(False)
        self.buttons={}
        self._icons=[]
        self._tooltip=None
        self.message=tk.StringVar(self.window,value='')
        actions=[('Home','Reset original view',self.home),('Back','Back to previous view',self.back),
                 ('Forward','Forward to next view',self.forward),None,
                 ('Pan','Pan axes with left mouse, zoom with right',lambda:self.set_mode('pan')),
                 ('Zoom','Zoom to rectangle',lambda:self.set_mode('zoom')),None,
                 ('Subplots','Configure subplots',self.configure_subplots),('Save','Save the figure',self.save)]
        for action in actions:
            if action is None:
                tk.Frame(self.toolbar,width=1,height='18p',relief=tk.RIDGE,bg='DarkGray').pack(side=tk.LEFT,padx='3p')
                continue
            name,tip,callback=action
            photo=self._icon(name)
            button=tk.Button(self.toolbar,image=photo,command=callback,relief=tk.FLAT,overrelief=tk.RAISED,borderwidth=1,padx=2,pady=2)
            button.pack(side=tk.LEFT)
            button.bind('<Enter>',lambda event,text=tip:self._show_tip(event.widget,text))
            button.bind('<Leave>',lambda event:self._hide_tip())
            self.buttons[name]=button
        tk.Label(self.toolbar,text='\u00a0\n\u00a0',font=('',10)).pack(side=tk.RIGHT)
        tk.Label(self.toolbar,textvariable=self.message,font=('',10),justify=tk.RIGHT).pack(side=tk.RIGHT)
        width,height=[round(v*figure.dpi) for v in figure.figsize]
        self.widget=tk.Canvas(self.window,width=width,height=height,borderwidth=0,highlightthickness=0,bg='white')
        self.widget.pack(side=tk.TOP,fill=tk.BOTH,expand=True)
        self.widget.bind('<Motion>',self.motion)
        self.widget.bind('<Enter>',self.enter)
        self.widget.bind('<Leave>',self.leave)
        self.widget.bind('<ButtonPress-1>',self.press)
        self.widget.bind('<ButtonPress>',self.press)
        self.widget.bind('<ButtonPress-2>',self.press)
        self.widget.bind('<ButtonPress-3>',self.press)
        self.widget.bind('<Double-Button-1>',lambda event:self.press(event,dblclick=True))
        self.widget.bind('<Double-Button-2>',lambda event:self.press(event,dblclick=True))
        self.widget.bind('<Double-Button-3>',lambda event:self.press(event,dblclick=True))
        self.widget.bind('<ButtonRelease-1>',self.release)
        self.widget.bind('<ButtonRelease>',self.release)
        self.widget.bind('<ButtonRelease-2>',self.release)
        self.widget.bind('<ButtonRelease-3>',self.release)
        self.widget.bind('<MouseWheel>',self.wheel)
        self.widget.bind('<Button-4>',lambda event:self.wheel(event,1))
        self.widget.bind('<Button-5>',lambda event:self.wheel(event,-1))
        self.widget.bind('<KeyPress>',self.key)
        self.widget.bind('<KeyRelease>',self.key_up)
        self.widget.bind('<Configure>',self.resize)
        self._image_id=None
        self._photo=None
        self._image=None
        self._overview_photo=None
        self._overview_box=None
        self._initial_scene=None
        self._initial_image=None
        self._drawing=False
        self.draw()
        self.window.update_idletasks()
        self.widget.focus_set()

    def _icon(self,name):
        # Own compact monochrome icon drawings; no Matplotlib asset files.
        im=self.Image.new('RGBA',(72,72),(0,0,0,0))
        d=self.ImageDraw.Draw(im)
        def line(points,width=6):d.line([(x*3,y*3) for x,y in points],fill='#111111',width=width,joint='curve')
        if name=='Home':
            line([(3,11),(12,3),(21,11)],7)
            d.polygon([(6*3,10*3),(12*3,5*3),(18*3,10*3),(18*3,21*3),(14*3,21*3),(14*3,14*3),(10*3,14*3),(10*3,21*3),(6*3,21*3)],fill='#111111')
        elif name in ('Back','Forward'):
            points=[(13,5),(6,12),(13,19)]
            if name=='Forward':points=[(24-x,y) for x,y in points]
            line(points,9);line([(5,12),(21,12)],9)
        elif name=='Pan':
            line([(12,2),(12,22)]);line([(2,12),(22,12)])
            for points in [[(8,6),(12,2),(16,6)],[(8,18),(12,22),(16,18)],[(6,8),(2,12),(6,16)],[(18,8),(22,12),(18,16)]]:line(points)
        elif name=='Zoom':
            d.ellipse((9,9,48,48),outline='#111111',width=8);line([(15,15),(22,22)],9)
        elif name=='Subplots':
            for x,y in [(5,7),(12,16),(19,10)]:
                line([(x,2),(x,22)],4);line([(x-3,y),(x+3,y)],10)
        elif name=='Save':
            line([(3,3),(18,3),(21,6),(21,21),(3,21),(3,3)],5)
            line([(7,3),(7,10),(17,10),(17,3)],5)
            line([(7,21),(7,14),(17,14),(17,21)],5)
        size=max(18,round(self.window.winfo_fpixels('18p')))
        photo=self.ImageTk.PhotoImage(im.resize((size,size),self.Image.Resampling.LANCZOS),master=self.window)
        self._icons.append(photo)
        return photo

    def _show_tip(self,widget,text):
        self._hide_tip()
        def show_tip():
            if self.closed:return
            self._tooltip=self.tk.Toplevel(self.window)
            self._tooltip.wm_overrideredirect(True)
            self._tooltip.wm_geometry(f'+{widget.winfo_rootx()+5}+{widget.winfo_rooty()+widget.winfo_height()+2}')
            self.tk.Label(self._tooltip,text=text,bg='#ffffe0',relief=self.tk.SOLID,borderwidth=1,padx=3,pady=2).pack()
        self._tooltip_after=self.window.after(550,show_tip)

    def _hide_tip(self):
        if getattr(self,'_tooltip_after',None):
            self.window.after_cancel(self._tooltip_after)
            self._tooltip_after=None
        if self._tooltip is not None:
            self._tooltip.destroy();self._tooltip=None

    def get_tk_widget(self):return self.widget

    def get_width_height(self):return self.widget.winfo_width(),self.widget.winfo_height()

    def draw(self):
        if self.closed or self._drawing:return
        from ..renderers import render_png
        self._drawing=True
        try:
            self.scene=self.figure.to_scene(cull=True)
            stream=io.BytesIO()
            render_png(self.scene,stream)
            stream.seek(0)
            self._image=self.Image.open(stream).convert('RGBA')
            if self._initial_scene is None:
                self._initial_scene=self.scene
                self._initial_image=self._image.copy()
            self._display(self._image)
            self.buttons['Back'].config(state=self.tk.NORMAL if self.navigation.index>0 else self.tk.DISABLED)
            self.buttons['Forward'].config(state=self.tk.NORMAL if self.navigation.index+1<len(self.navigation.history) else self.tk.DISABLED)
            self._draw_overview()
            self.figure._draw_complete()
            self._emit('draw_event')
        finally:self._drawing=False

    def _display(self,image):
        self._photo=self.ImageTk.PhotoImage(image,master=self.window)
        if self._image_id is None:self._image_id=self.widget.create_image(0,0,anchor='nw',image=self._photo)
        else:self.widget.itemconfigure(self._image_id,image=self._photo)
        self.widget.tag_lower(self._image_id)

    def draw_idle(self):
        if not self.closed and self._pending is None:
            self._pending=self.window.after_idle(self._redraw)

    def _redraw(self):
        self._pending=None
        try:self.draw()
        except (ValueError,RuntimeError) as exc:self.message.set(str(exc))

    def flush_events(self):
        if not self.closed:self.window.update()

    def _metadata(self):
        return [m for m in self.scene.maps if not m.get('inset',False)]

    def _hit(self,x,y):
        for meta in self._metadata():
            index=meta['axes_index']
            bx,by,bw,bh=meta['box']
            if bx<=x<=bx+bw and by<=y<=by+bh and index<len(self.figure.axes):return index
        return None

    def _viewport(self,index):
        meta=next(m for m in self._metadata() if m['axes_index']==index)
        return viewport_from_metadata(self.figure.axes[index].projection,meta)

    def motion(self,event):
        index=self._hit(event.x,event.y)
        if index is not None:
            coordinate=self._viewport(index).inverse(event.x,event.y)
            self.message.set((f'{self.mode}\n' if self.mode else '')+(f'x={coordinate[0]:.2f} y={coordinate[1]:.2f}' if coordinate else ''))
        elif not self.drag:self.message.set(self.mode)
        if self.drag:
            d=self.drag
            if self.mode=='zoom':
                self.widget.delete('rubberband')
                x0,y0=d['start'];x1,y1=event.x,event.y
                bx,by,bw,bh=d['viewport'].box
                x1,y1=max(bx,min(bx+bw,x1)),max(by,min(by+bh,y1))
                if self.constraint=='x':y0,y1=by,by+bh
                if self.constraint=='y':x0,x1=bx,bx+bw
                self.widget.create_rectangle(x0,y0,x1,y1,outline='black',tags='rubberband')
                self.widget.create_rectangle(x0,y0,x1,y1,outline='white',dash=(3,3),tags='rubberband')
            elif d['button']==1:
                # Fast rubber-sheet preview only during dragging. On release,
                # geometry, tick coordinates and all ornaments are recomputed.
                x,y,w,h=map(round,d['viewport'].box)
                dx,dy=event.x-d['start'][0],event.y-d['start'][1]
                if self.constraint=='x':dy=0
                if self.constraint=='y':dx=0
                preview=self._image.copy()
                region=self.Image.new('RGBA',(w,h),self.figure.axes[d['index']].facecolor)
                region.paste(self._image.crop((x,y,x+w,y+h)),(dx,dy))
                preview.paste(region,(x,y))
                self._display(preview)
        self._emit('motion_notify_event',event,index)

    def enter(self,event):
        self._emit('figure_enter_event',event,self._hit(event.x,event.y))

    def leave(self,event):
        self.message.set('')
        self._emit('figure_leave_event',event,self._hit(event.x,event.y))

    def press(self,event,*,dblclick=False):
        self.widget.focus_set()
        index=self._hit(event.x,event.y)
        button=mouse_button(event)
        self._emit('button_press_event',event,index,dblclick=dblclick)
        if self.closed:return
        action={8:'back',9:'forward'}.get(button)
        if action and 'MouseButton.'+button.name in rcParams['keymap.'+action]:
            getattr(self,action)();return
        if self._overview_box and self._overview_click(event):return
        if index is None or not self.mode or button not in (1,3):return
        self.active=index
        self.drag=dict(index=index,start=(event.x,event.y),button=button,viewport=self._viewport(index))

    def release(self,event):
        self.widget.delete('rubberband')
        if not self.drag:
            self._emit('button_release_event',event,self._hit(event.x,event.y))
            return
        d,self.drag=self.drag,None
        ax=self.figure.axes[d['index']]
        extent=drag_extent(ax,d['viewport'],d['start'],(event.x,event.y),mode=self.mode,button=d['button'],constraint=self.constraint)
        if extent is not None:
            ax.set_extent(extent);self.navigation.push()
        self.draw_idle()
        self._emit('button_release_event',event,d['index'])

    def wheel(self,event,direction=None):
        # Tk Windows reports multiples of 120, including fractional steps.
        # Button-4/5 bindings supply the unit step explicitly on Linux.
        step=float(direction) if direction is not None else getattr(event,'delta',0)/120
        index=self._hit(event.x,event.y)
        if index is not None and step:
            self.active=index
            ax=self.figure.axes[index]
            ax.set_extent(zoom_extent(ax,1.2**step,self._viewport(index).inverse(event.x,event.y)))
            self.navigation.push();self.draw_idle()
        self._emit('scroll_event',event,index,step=step)

    def set_mode(self,mode):
        self.mode='' if self.mode==mode else mode
        self.buttons['Pan'].config(relief=self.tk.SUNKEN if self.mode=='pan' else self.tk.FLAT)
        self.buttons['Zoom'].config(relief=self.tk.SUNKEN if self.mode=='zoom' else self.tk.FLAT)
        self.widget.config(cursor='fleur' if self.mode=='pan' else 'crosshair' if self.mode=='zoom' else '')
        self.message.set(self.mode)

    def home(self):self.navigation.home();self.draw_idle()
    def back(self):self.navigation.back();self.draw_idle()
    def forward(self):self.navigation.forward();self.draw_idle()

    def key(self,event):
        key=key_name(event)
        self._key=key
        index=self._hit(event.x,event.y) if hasattr(event,'x') and hasattr(event,'y') else None
        if index is not None:self.active=index
        # Deliver the normalized input before handling a shortcut, including quit.
        self._emit('key_press_event',event,index)
        if self.closed:return
        mapped=lambda action:key in rcParams['keymap.'+action]
        if key in ('x','y'):self.constraint=key
        elif mapped('home'):self.home()
        elif mapped('back'):self.back()
        elif mapped('forward'):self.forward()
        elif mapped('pan'):self.set_mode('pan')
        elif mapped('zoom'):self.set_mode('zoom')
        elif mapped('save'):self.save()
        elif mapped('grid') and index is not None:self._cycle_grid(self.figure.axes[index],'major')
        elif mapped('grid_minor') and index is not None:self._cycle_grid(self.figure.axes[index],'minor')
        elif mapped('fullscreen'):self.window.attributes('-fullscreen',not bool(self.window.attributes('-fullscreen')))
        elif mapped('quit'):self.close()
        elif key in ('+','=','-') and index is not None:
            ax=self.figure.axes[self.active]
            ax.set_extent(zoom_extent(ax,1/1.5 if key=='-' else 1.5));self.navigation.push();self.draw_idle()

    def _cycle_grid(self,ax,which):
        def visible(kind,name):
            return any(layer.kind=='grid' and layer.visible and layer.options.get('which','major')==kind
                       and layer.options.get('axes_config',{}).get(name,{}).get('visible',False) for layer in ax.layers)
        states=(visible(which,'x'),visible(which,'y'))
        cycle=((False,False),(True,False),(True,True),(False,True))
        next_state=cycle[(cycle.index(states)+1)%4]
        with ax._mutation():
            for name,enabled in zip(('x','y'),next_state):
                ax.grid(enabled,which='both' if which=='minor' or not enabled else 'major',axis=name)
        self.draw_idle()

    def key_up(self,event):
        if getattr(event,'keysym','').lower()==self.constraint:self.constraint=None
        index=self._hit(event.x,event.y) if hasattr(event,'x') and hasattr(event,'y') else None
        self._emit('key_release_event',event,index)
        self._key=None

    def resize(self,event):
        if self.closed or event.width<100 or event.height<100 or self._drawing:return
        current=tuple(round(v*self.figure.dpi) for v in self.figure.figsize)
        if current==(event.width,event.height):return
        self.figure.figsize=(event.width/self.figure.dpi,event.height/self.figure.dpi)
        if self._resize_pending:self.window.after_cancel(self._resize_pending)
        self._resize_pending=self.window.after(180,self._resize_redraw)
        self._emit('resize_event',event)

    def _resize_redraw(self):
        self._resize_pending=None
        self.draw_idle()

    def save(self):
        path=self.filedialog.asksaveasfilename(parent=self.window,title='Save the figure',initialfile='Figure_1.png',defaultextension='.png',filetypes=[('Portable Network Graphics','*.png'),('Scalable Vector Graphics','*.svg')])
        if path:
            try:self.figure.savefig(path)
            except Exception as exc:self.messagebox.showerror('Save failed',str(exc),parent=self.window)

    def configure_subplots(self):
        window=self.tk.Toplevel(self.window);window.title('Subplot configuration')
        values={}
        defaults=self.figure.subplotpars
        def apply():
            try:self.figure.subplots_adjust(**{k:v.get() for k,v in values.items()});self.draw_idle()
            except ValueError as exc:self.message.set(str(exc))
        for name,value in defaults.items():
            var=self.tk.DoubleVar(window,value=value);values[name]=var
            self.tk.Scale(window,from_=0,to=1,resolution=.01,orient=self.tk.HORIZONTAL,label=name,variable=var,length=300).pack(fill=self.tk.X)
        self.tk.Button(window,text='Apply',command=apply).pack(side=self.tk.LEFT,padx=8,pady=8)
        self.tk.Button(window,text='Close',command=window.destroy).pack(side=self.tk.RIGHT,padx=8,pady=8)

    def _draw_overview(self):
        # Locator is already rendered into the scene, just like the static
        # export. Retain only hit-test metadata for interactive recentering.
        self._overview_box=None
        for meta in self._metadata():
            index=meta['axes_index']
            mini=meta.get('overview_map')
            if mini:
                vp=viewport_from_metadata(self.figure.axes[index].projection,mini)
                if self._overview_box is None:self._overview_box=[]
                self._overview_box.append((index,*mini['box'],vp))

    def _overview_click(self,event):
        hit=next((item for item in self._overview_box if item[1]<=event.x<=item[1]+item[3] and item[2]<=event.y<=item[2]+item[4]),None)
        if hit is None:return False
        self.active,x,y,w,h,vp=hit
        bx,by,bw,bh=vp.box
        center=vp.inverse(bx+(event.x-x)*bw/w,by+(event.y-y)*bh/h)
        if center:
            ax=self.figure.axes[self.active]
            west,east,south,north=ax.get_extent()
            from ..navigation import bounded_extent
            ax.set_extent(bounded_extent(center[0]-(east-west)/2,center[0]+(east-west)/2,center[1]-(north-south)/2,center[1]+(north-south)/2))
            self.navigation.push();self.draw_idle()
        return True

    def mpl_connect(self,name,callback):
        """Familiar event connection API implemented locally."""
        if not callable(callback):raise TypeError('callback must be callable')
        self._callback_id+=1;self._event_callbacks[self._callback_id]=(name,callback)
        return self._callback_id

    def mpl_disconnect(self,connection_id):self._event_callbacks.pop(connection_id,None)

    def _emit(self,name,event=None,index=None,*,step=0,dblclick=False):
        from types import SimpleNamespace
        ax=self.figure.axes[index] if index is not None else None
        coord=self._viewport(index).inverse(event.x,event.y) if ax is not None and event else None
        x=getattr(event,'x',None)
        y=self.scene.height-event.y if event and hasattr(event,'y') else None
        payload=SimpleNamespace(name=name,canvas=self,inaxes=ax,x=int(x) if x is not None else None,
                                y=int(y) if y is not None else None,
                                xdata=coord[0] if coord else None,ydata=coord[1] if coord else None,
                                button=None,key=None,guiEvent=event,modifiers=frozenset(modifiers(event)))
        if name in ('key_press_event','key_release_event'):
            payload.key=key_name(event);payload.modifiers=frozenset()
        elif name in ('button_press_event','button_release_event','motion_notify_event','scroll_event'):
            payload.key=getattr(self,'_key',None)
            payload.step=step;payload.dblclick=dblclick;payload.buttons=None
            if name in ('button_press_event','button_release_event'):
                payload.button=mouse_button(event)
                self._button=payload.button if name=='button_press_event' else None
            elif name=='motion_notify_event':
                payload.button=getattr(self,'_button',None)
                payload.buttons=pressed_buttons(event)
        if name=='draw_event':payload.renderer=self.scene
        if name=='scroll_event':
            payload.step=step
            payload.button='up' if step>0 else 'down' if step<0 else None
        if name=='motion_notify_event':self._axes_transition(payload,event)
        self._dispatch(name,payload)
        return payload

    def _axes_transition(self,payload,event):
        previous_ref=getattr(self,'_last_axes_ref',None)
        previous=previous_ref() if previous_ref else None
        self._last_axes_ref=weakref.ref(payload.inaxes) if payload.inaxes else None
        if previous is payload.inaxes:return
        if previous is not None and previous in self.figure.axes:
            from types import SimpleNamespace
            index=self.figure.axes.index(previous)
            coord=self._viewport(index).inverse(payload.x,self.scene.height-payload.y)
            leaving=SimpleNamespace(**vars(payload))
            leaving.name='axes_leave_event';leaving.inaxes=previous
            leaving.xdata,leaving.ydata=coord if coord else (None,None)
            self._dispatch('axes_leave_event',leaving)
        if payload.inaxes is not None:self._dispatch('axes_enter_event',payload)

    def _dispatch(self,name,payload):
        # Like Matplotlib, dispatch uses the subscribers captured at the start.
        # Connect/disconnect inside a callback applies to the next event.
        for event_name,callback in tuple(self._event_callbacks.values()):
            if event_name==name:callback(payload)

    def close(self):
        if self.closed or getattr(self,'_closing',False):return
        self._closing=True
        try:self._emit('close_event')
        finally:
            self._hide_tip()
            self.closed=True
            for token in (self._pending,self._resize_pending):
                if token:self.window.after_cancel(token)
            self._pending=self._resize_pending=None
            self.window.destroy()
            self._photo=self._image=self._initial_image=self._initial_scene=None
            if self in _windows:_windows.remove(self)
            self.figure._closed=True
            from .. import _figures
            if self.figure in _figures:_figures.remove(self.figure)
