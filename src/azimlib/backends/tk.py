"""Native Tk figure window, implemented without any Matplotlib imports.

Tk provides widgets and input events, Pillow a raster buffer and font drawing;
all geometry, projections, layout, style and rendering come from Azimlib.
"""
from __future__ import annotations
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
    if viewer is not None and not viewer.closed and not isinstance(viewer,FigureWindow):raise RuntimeError('Close the current viewer before changing backend')
    if viewer is None or viewer.closed:
        old_canvas=figure.canvas
        viewer=FigureWindow(figure,initial_draw=False)
        if hasattr(old_canvas,'_callbacks'):
            viewer._event_callbacks.update(old_canvas._callbacks)
            viewer._callback_id=old_canvas._next_id
        elif hasattr(old_canvas,'_event_callbacks'):
            viewer._event_callbacks.update(old_canvas._event_callbacks)
            viewer._callback_id=old_canvas._callback_id
        figure._viewer=viewer
        figure.canvas=viewer
        _windows.append(viewer)
        from .. import _figures
        was_registered=figure in _figures;was_closed=figure._closed
        figure._closed=False
        try:
            viewer.draw()
            if not viewer.closed:
                viewer.window.update_idletasks()
                viewer.widget.focus_set()
        except BaseException:
            try:viewer.close()
            except BaseException:pass  # Preserve the original draw/callback error.
            figure._viewer=None;figure.canvas=old_canvas;figure._closed=was_closed
            if was_registered and figure not in _figures:_figures.append(figure)
            raise
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
    def __init__(self,figure,*,initial_draw=True):
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
        self.toolbar=tk.Frame(self.window,borderwidth=2,width=round(figure.figsize[0]*figure.dpi),height=50,bg='#fafafa')
        self.toolbar.pack(side=tk.BOTTOM,fill=tk.X)
        self.toolbar.pack_propagate(False)
        self.buttons={}
        self._icons=[]
        self._tooltip=None
        self.message=tk.StringVar(self.window,value='')
        actions=[('Home','Reset original view',self.home),('Back','Back to previous view',self.back),
                 ('Forward','Forward to next view',self.forward),None,
                 ('Pan','Left: pan, right: zoom\nx/y: fix axis, Ctrl: keep aspect',lambda:self.set_mode('pan')),
                 ('Zoom','Zoom to rectangle\nx/y: fix axis',lambda:self.set_mode('zoom')),
                 ('Subplots','Configure subplots',self.configure_subplots),None,('Save','Save the figure',self.save)]
        for action in actions:
            if action is None:
                tk.Frame(self.toolbar,width=1,height='18p',relief=tk.RIDGE,bg='DarkGray').pack(side=tk.LEFT,padx='3p')
                continue
            name,tip,callback=action
            photo=self._icon(name)
            if name in ('Pan','Zoom'):
                variable=tk.IntVar(master=self.toolbar,value=0)
                button=tk.Checkbutton(self.toolbar,image=photo,command=callback,
                    indicatoron=False,variable=variable,offrelief=tk.FLAT,
                    overrelief=tk.FLAT,relief=tk.FLAT,borderwidth=1,width='18p',height='18p',
                    bg='#fafafa',activebackground='#e8e8e8',selectcolor='#dce5ef',highlightbackground='#fafafa')
                button.var=variable
            else:
                button=tk.Button(self.toolbar,image=photo,command=callback,
                    relief=tk.FLAT,overrelief=tk.FLAT,borderwidth=1,width='18p',height='18p',
                    bg='#fafafa',activebackground='#e8e8e8',highlightbackground='#fafafa')
            button.pack(side=tk.LEFT)
            button.bind('<Enter>',lambda event,text=tip:self._show_tip(event.widget,text))
            button.bind('<Leave>',lambda event:self._hide_tip())
            self.buttons[name]=button
        tk.Label(self.toolbar,text='\u00a0\n\u00a0',font=('',10),bg='#fafafa').pack(side=tk.RIGHT)
        tk.Label(self.toolbar,textvariable=self.message,font=('',10),bg='#fafafa',justify=tk.RIGHT).pack(side=tk.RIGHT)
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
        from ._raster_cache import RasterCache
        self._raster_cache=RasterCache()
        self._drawing=False
        from ._pan_raster import PanRaster
        from ..renderers import render_image
        from ..renderers._interactive import InteractivePathCache
        from ..renderers._tile_cache import TileCache
        path_cache=InteractivePathCache()
        self._pan_tiles=TileCache(max_entries=512);self._pan_warmed=False
        self._pixel_process=None
        try:import aggdraw
        except ImportError:pass
        else:
            from ._navigation_process import NavigationProcess
            self._pixel_process=NavigationProcess()
        self._pan_raster=PanRaster(render_image,
            self._pixel_process.render if self._pixel_process is not None else
                lambda scene:render_image(scene,_interactive=True,_path_cache=path_cache,_tile_cache=self._pan_tiles),
            lambda scene,cancel:render_image(scene,_cancel=cancel))
        self._pan_poll=None;self._async_pan=False;self._pan_generation=0
        self._pan_waiting=False;self._wheel_pending=None
        self._pan_prefetched=False
        if initial_draw:
            self.draw()
            self.window.update_idletasks()
            self.widget.focus_set()

    def _icon(self,name):
        # Original vector geometry; direct RGBA without foreign assets/codecs.
        from .._toolbar_icons import icon_image
        names={'Home':'home','Back':'back','Forward':'forward','Pan':'move',
               'Zoom':'zoom_to_rect','Subplots':'subplots','Save':'filesave'}
        size=max(18,round(self.window.winfo_fpixels('18p')))
        im=icon_image(names[name],size)
        photo=self.ImageTk.PhotoImage(im,master=self.window)
        im.close()
        self._icons.append(photo)
        return photo

    def set_toolbar_labels(self,visible=True):
        """Show names under icons; default keeps the reference's icon-only bar."""
        for name,button in self.buttons.items():
            button.configure(text=name if visible else '',compound=self.tk.TOP,
                             font=('',8),height='30p' if visible else '18p',width='30p' if visible else '18p')
        self.window.update_idletasks()
        height=max(50,max(button.winfo_reqheight() for button in self.buttons.values())+4)
        self.toolbar.configure(height=height)

    def _show_tip(self,widget,text):
        self._hide_tip()
        if self.closed or not text:return
        self._tooltip=self.tk.Toplevel(widget)
        self._tooltip.wm_overrideredirect(True)
        self._tooltip.wm_geometry(f'+{widget.winfo_rootx()+widget.winfo_width()}+{widget.winfo_rooty()}')
        self.tk.Label(self._tooltip,text=text,justify=self.tk.LEFT,
                      relief=self.tk.SOLID,borderwidth=1).pack(ipadx=1)

    def _hide_tip(self):
        if self._tooltip is not None:
            self._tooltip.destroy();self._tooltip=None

    def get_tk_widget(self):return self.widget

    def get_width_height(self):return self.widget.winfo_width(),self.widget.winfo_height()

    def draw(self):
        if self.closed or self._drawing:return
        from ..renderers import render_image
        self._pan_raster.clear();self._async_pan=False;self._pan_waiting=False
        self._drawing=True
        try:
            scene=self.figure.to_scene(cull=True,interactive=True)
            if not self._pan_warmed:
                # Warm the child while the precise first frame is rasterized;
                # the first mouse gesture should not pay process/font startup.
                self._pan_raster.submit((0,True),scene,preview=True)
            try:key,image=self._raster_cache.lookup(scene)
            except MemoryError:key,image=None,None
            if image is None:
                image=render_image(scene)
                if key is not None:
                    try:self._raster_cache.store(key,image)
                    except MemoryError:pass  # Retaining an extra frame is optional.
                    except BaseException:image.close();raise
            self._present(scene,image)
            if self._pan_raster.busy() and self._pan_poll is None:
                self._pan_poll=self.window.after(4,self._poll_pan)
        finally:self._drawing=False

    def _present(self,scene,image,*,complete=True):
        self.scene=scene;previous=self._image;self._image=image
        self._display(image)
        if previous is not None:previous.close()
        self.buttons['Back'].config(state=self.tk.NORMAL if self.navigation.index>0 else self.tk.DISABLED)
        self.buttons['Forward'].config(state=self.tk.NORMAL if self.navigation.index+1<len(self.navigation.history) else self.tk.DISABLED)
        self._draw_overview()
        if complete:self.figure._draw_complete()
        self._emit('draw_event')

    def _draw_pan_async(self):
        # Coalesce view edits BEFORE composition, hashing and snapshot copying.
        # A busy worker needs only the latest limits, not N prepared Scenes.
        if self._pan_raster.busy():
            prefetch=(getattr(self,'_pixel_process',None) is not None and
                      not getattr(self,'_pan_prefetched',False) and
                      self._pan_raster.can_prefetch() is True and
                      getattr(self,'drag',None) is not None and self.mode=='pan')
            if not prefetch:
                self._pan_waiting=True
                if self._pan_poll is None:self._pan_poll=self.window.after(4,self._poll_pan)
                return
            self._pan_prefetched=True
        self._pan_waiting=False
        preview=(self.drag is not None and self.mode=='pan') or self._wheel_pending is not None
        scene=self.figure.to_scene(cull=True,interactive=True)
        key=image=None
        if not preview:
            try:key,image=self._raster_cache.lookup(scene)
            except MemoryError:pass
        if image is not None:
            self._pan_raster.clear();self._present(scene,image)
            if self.drag is None:self._async_pan=False
        else:self._pan_raster.submit((self._pan_generation,preview),scene,key,preview=preview)
        if self._pan_poll is None:self._pan_poll=self.window.after(4,self._poll_pan)

    def _poll_pan(self):
        self._pan_poll=None
        if self.closed:return
        result=self._pan_raster.take()
        if result is not None:
            self._pan_prefetched=False
            (token,preview),scene,image,error,key=result
            if token==0 and error is None:self._pan_warmed=True
            latest=token==self._pan_generation and self._async_pan
            # Completed intermediate full views keep a held drag moving. After
            # release/Home/resize, only the newest settled view may be painted.
            moving=(self.drag is not None and self.mode=='pan' or self._wheel_pending is not None) and self._async_pan
            current_size=tuple(round(v*self.figure.dpi) for v in self.figure.figsize)
            usable=token>0 and (latest or moving) and (round(scene.width),round(scene.height))==current_size
            if error is not None:
                if latest:self.message.set(str(error))
            elif image is not None:
                if usable:
                    if key is not None:
                        try:self._raster_cache.store(key,image)
                        except MemoryError:pass
                    self._drawing=True
                    try:self._present(scene,image,complete=latest and not preview)
                    finally:self._drawing=False
                else:image.close()
        if self.closed:return
        if self._pan_waiting and not self._pan_raster.busy():self._draw_pan_async()
        if self._pan_raster.busy():
            if self._pan_poll is None:self._pan_poll=self.window.after(4,self._poll_pan)
        elif self.drag is None and self._pending is None and self._wheel_pending is None:self._async_pan=False

    def _display(self,image):
        self._photo=self.ImageTk.PhotoImage(image,master=self.window)
        if self._image_id is None:self._image_id=self.widget.create_image(0,0,anchor='nw',image=self._photo)
        else:self.widget.itemconfigure(self._image_id,image=self._photo)
        self.widget.tag_lower(self._image_id)

    def draw_idle(self):
        if getattr(self,'_async_pan',False):self._pan_generation+=1
        if not self.closed and self._pending is None:
            self._pending=self.window.after_idle(self._redraw)

    def _redraw(self):
        self._pending=None
        try:
            if self._async_pan:self._draw_pan_async()
            else:self.draw()
        except (ValueError,RuntimeError) as exc:self.message.set(str(exc))

    def flush_events(self):
        if self.closed:return
        self.window.update()
        # Explicit flush drains a requested pan frame while continuing to pump
        # Tk input/timers; the normal mainloop never waits for the raster worker.
        import time
        deadline=time.monotonic()+30
        while not self.closed and self._pan_raster.busy() and time.monotonic()<deadline:
            self.window.update();time.sleep(.002)

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
        ax=self.figure.axes[index]
        if tuple(ax._get_extent())!=tuple(meta['extent']) or ax.get_bearing()!=meta.get('bearing',0):
            from ..viewport import Viewport,_geometry_projected_bounds
            box=meta.get('navigation_box',meta['box'])
            extent=ax._get_extent()
            bounds=_geometry_projected_bounds(ax.projection,extent) if not ax.get_bearing() else None
            if bounds is not None:
                # Monotonic cylindrical bounds need only their endpoints.
                # Cursor callbacks run before a new Scene is painted; sampling
                # 1,225 projected points here for every Motion stalls input.
                x,y,w,h=box;px0,py0,px1,py1=bounds
                scale=min(w/(px1-px0),h/(py1-py0))
                width,height=(px1-px0)*scale,(py1-py0)*scale
                bx,by=x+(w-width)/2,y+(h-height)/2
                scale=min(width/(px1-px0),height/(py1-py0))
                return viewport_from_metadata(ax.projection,dict(
                    extent=extent,box=(bx,by,width,height),projected_bounds=bounds,
                    scale=scale,ox=bx+(width-(px1-px0)*scale)/2-px0*scale,
                    oy=by+(height-(py1-py0)*scale)/2+py1*scale))
            vp=Viewport(ax.projection,ax._get_extent(),box,bearing=ax.get_bearing())
            x,y,w,h=box;px0,py0,px1,py1=vp.projected_bounds
            width,height=(px1-px0)*vp.scale,(py1-py0)*vp.scale
            return Viewport(ax.projection,ax._get_extent(),(x+(w-width)/2,y+(h-height)/2,width,height),bearing=ax.get_bearing())
        return viewport_from_metadata(self.figure.axes[index].projection,meta)

    def motion(self,event):
        self._check_drag_buttons(event)
        index=self._hit(event.x,event.y)
        self._sync_cursor(index)
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
            elif self.mode=='pan':
                # Change the view, never translate a clipped bitmap (and its
                # spines). Each idle draw includes ticks, grid and components.
                self._pan_to(event)
        self._emit('motion_notify_event',event,index)

    def _drag_constraint(self,event):
        if self.constraint:return self.constraint
        held=modifiers(event)
        if 'ctrl' in held:return 'control'
        if 'shift' in held:return 'shift'
        return None

    def _pan_to(self,event):
        d=self.drag
        ax=self.figure.axes[d['index']]
        extent=drag_extent(ax,d['viewport'],d['start'],(event.x,event.y),
                           mode='pan',button=d['button'],constraint=self._drag_constraint(event),
                           initial_extent=d['extent'])
        if extent is not None and extent!=ax.get_extent():
            ax.set_extent(extent)
            self.draw_idle()
        return extent

    def enter(self,event):
        self._check_drag_buttons(event)
        self._emit('figure_enter_event',event,self._hit(event.x,event.y))

    def _check_drag_buttons(self,event):
        # A release outside the canvas (or a lost window grab) may never reach
        # its ButtonRelease binding. Keep the last held view; the reentry
        # position must not become the last point of that old gesture. Unknown
        # Tk substitutions carry no button information and cannot end a drag.
        if not self.drag:return
        try:int(event.state)
        except (AttributeError,TypeError,ValueError):return
        if self.drag['button'] in pressed_buttons(event):return
        if self.mode=='pan':self.navigation.push()
        self.drag=None;self._button=None
        self.widget.delete('rubberband')
        if hasattr(self,'_pan_raster'):
            self._pan_raster.discard_queued_preview();self._async_pan=True
        self.draw_idle()

    def leave(self,event):
        self.message.set('')
        self._sync_cursor(None)
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
        self.navigation.push()
        if hasattr(self,'_pan_raster'):
            # Retire ready/in-flight frames from the preceding gesture too.
            # Their completion must not briefly restore an older view when
            # the user grabs the map again before rasterization has finished.
            self._pan_raster.clear();self._pan_prefetched=False
            if self.mode=='pan':self._async_pan=True
        self.drag=dict(index=index,start=(event.x,event.y),button=button,
                       viewport=self._viewport(index),extent=self.figure.axes[index].get_extent())

    def release(self,event):
        self.widget.delete('rubberband')
        if not self.drag:
            self._emit('button_release_event',event,self._hit(event.x,event.y))
            return
        d=self.drag
        if self.mode=='pan':
            self._pan_to(event)
            self.navigation.push()
        elif self.mode=='zoom':
            ax=self.figure.axes[d['index']]
            extent=drag_extent(ax,d['viewport'],d['start'],(event.x,event.y),mode='zoom',button=d['button'],constraint=self.constraint)
            if extent is not None:
                ax.set_extent(extent);self.navigation.push()
        self.drag=None
        if hasattr(self,'_pan_raster'):
            self._pan_raster.discard_queued_preview();self._async_pan=True
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
            self.navigation.push()
            if hasattr(self,'_pan_raster'):
                self._pan_raster.interrupt_exact()
                self._async_pan=True
                if self._wheel_pending:self.window.after_cancel(self._wheel_pending)
                self._wheel_pending=self.window.after(120,self._finish_wheel)
            self.draw_idle()
        self._emit('scroll_event',event,index,step=step)

    def set_mode(self,mode):
        self.mode='' if self.mode==mode else mode
        for name,tool in (('Pan','pan'),('Zoom','zoom')):
            if self.mode==tool:self.buttons[name].select()
            else:self.buttons[name].deselect()
        self._sync_cursor(getattr(self,'_cursor_index',None))
        self.message.set(self.mode)

    def _sync_cursor(self,index):
        # Like the reference toolbar, navigation cursors belong to the Axes,
        # not the margins around the canvas or the toolbar itself.
        self._cursor_index=index
        cursor=('fleur' if self.mode=='pan' else 'crosshair' if self.mode=='zoom' else '') if index is not None else ''
        if self.widget.cget('cursor')!=cursor:self.widget.config(cursor=cursor)

    def _finish_wheel(self):
        self._wheel_pending=None
        if not self.closed:self.draw_idle()

    def _navigation_draw(self):
        if hasattr(self,'_pan_raster'):
            self._pan_raster.interrupt_exact()
            self._async_pan=True
            if self._wheel_pending:self.window.after_cancel(self._wheel_pending);self._wheel_pending=None
        self.draw_idle()

    def home(self):self.navigation.home();self._navigation_draw()
    def back(self):self.navigation.back();self._navigation_draw()
    def forward(self):self.navigation.forward();self._navigation_draw()

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

    def resize_figure(self,width,height):
        """Forward Figure inch/DPI edits to the native canvas, after validation."""
        if self.closed:return
        if self._resize_pending:
            self.window.after_cancel(self._resize_pending);self._resize_pending=None
        self.widget.config(width=width,height=height)
        self.window.geometry(f'{width}x{height+self.toolbar.winfo_reqheight()}')
        from types import SimpleNamespace
        self._emit('resize_event',SimpleNamespace(width=width,height=height))
        self.draw_idle()

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
        path=self.filedialog.asksaveasfilename(parent=self.window,title='Save the figure',initialfile='Figure_1.png',defaultextension='.png',filetypes=[('Portable Network Graphics','*.png'),('Scalable Vector Graphics','*.svg'),('Portable Document Format','*.pdf')])
        if path:
            try:self.figure.savefig(path)
            except Exception as exc:self.messagebox.showerror('Save failed',str(exc),parent=self.window)

    def configure_subplots(self):
        dialog=getattr(self,'_subplot_dialog',None)
        if dialog is not None and dialog.window is not None and dialog.window.winfo_exists():
            dialog.window.lift();return dialog
        if dialog is not None:dialog.dispose()
        from ._subplots import SubplotEditor
        self._subplot_dialog=SubplotEditor(self)
        return self._subplot_dialog

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
            ax.set_extent(bounded_extent(center[0]-(east-west)/2,center[0]+(east-west)/2,center[1]-(north-south)/2,center[1]+(north-south)/2,longitude_center=ax.projection.central_longitude if ax._longitude_wrap else 0))
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
        if name=='button_press_event' and not self.mode:
            from ..picking import pick
            pick(self,payload)
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
            if hasattr(self,'_pan_raster'):self._pan_raster.close()
            if hasattr(self,'_pan_tiles'):self._pan_tiles.close()
            if getattr(self,'_pixel_process',None) is not None:self._pixel_process.close()
            for token in (self._pending,self._resize_pending,getattr(self,'_pan_poll',None),getattr(self,'_wheel_pending',None)):
                if token:self.window.after_cancel(token)
            self._pending=self._resize_pending=None
            self._pan_poll=None
            self._wheel_pending=None
            if self._image is not None:self._image.close()
            self._raster_cache.clear()
            self._photo=self._image=self._initial_image=self._initial_scene=None
            # A closed Figure/canvas cycle can be collected by a raster thread.
            # Drop every owned Tk reference now, on the UI thread, rather than
            # leaving Variable/PhotoImage/Tcl interpreter finalizers in that cycle.
            dialog=getattr(self,'_subplot_dialog',None)
            if dialog is not None:dialog.dispose()
            self._subplot_dialog=None
            self.window.destroy()
            for button in getattr(self,'buttons',{}).values():
                if hasattr(button,'var'):button.var=None
            if hasattr(self,'buttons'):self.buttons.clear()
            if hasattr(self,'_icons'):self._icons.clear()
            self.message=self._overview_photo=None
            self.widget=self.toolbar=self.window=None
            if self in _windows:_windows.remove(self)
            self.figure._closed=True
            from .. import _figures
            if self.figure in _figures:_figures.remove(self.figure)
