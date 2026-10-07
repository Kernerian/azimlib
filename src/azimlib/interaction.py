"""UI-neutral input controller: physical display pixels, shared view commands."""
from types import SimpleNamespace
from .navigation import Navigation,viewport_from_metadata,drag_extent,zoom_extent

class Interaction:
    def __init__(self,canvas):self.canvas=canvas;self.navigation=Navigation(canvas.figure);self.mode='';self.drag=None
    def _hit(self,x,y):
        scene=getattr(self.canvas,'scene',None)
        if scene is None:return None,None
        for meta in reversed(scene.maps):
            bx,by,w,h=meta['box']
            if bx<=x<=bx+w and by<=y<=by+h:
                path=meta['axes_path'];ax=self.canvas.figure.axes[path[0]]
                for index in path[1:]:ax=ax.insets[index]
                return ax,viewport_from_metadata(ax.projection,meta)
        return None,None
    def event(self,name,x=None,y=None,*,button=None,buttons=None,key=None,step=0,guiEvent=None):
        # Input uses screen Y-down; public events use bottom-up physical pixels.
        ax,vp=self._hit(x,y) if x is not None and y is not None else (None,None)
        coord=vp.inverse(x,y) if vp is not None else None
        event=SimpleNamespace(name=name,canvas=self.canvas,x=x,y=None if y is None else self.canvas.figure.figsize[1]*self.canvas.figure.dpi-y,
            inaxes=ax,xdata=coord[0] if coord else None,ydata=coord[1] if coord else None,button=button,
            buttons=None if buttons is None else frozenset(buttons),key=key,step=step,dblclick=False,modifiers=frozenset(),guiEvent=guiEvent)
        self.canvas._dispatch(name,event)
        if name=='button_press_event':
            if not self.mode:self.canvas.pick(event)
            if self.mode and ax is not None:self.drag=(ax,vp,(x,y),ax.camera if getattr(ax,'_terrain3d',False) else ax.get_extent(),button)
        elif name=='motion_notify_event' and self.drag:
            if buttons is not None and self.drag[-1] not in buttons:self.navigation.push();self.drag=None
            elif self.mode=='pan':self._drag(x,y)
        elif name=='button_release_event' and self.drag:
            if x is not None and y is not None:self._drag(x,y)
            self.navigation.push();self.drag=None;self.canvas.draw_idle()
        elif name=='scroll_event' and ax is not None:
            if self.drag:self.navigation.push();self.drag=None
            factor=1.25**max(-20,min(20,step))
            if getattr(ax,'_terrain3d',False):
                from .terrain3d import camera_zoom
                camera_zoom(ax,factor)
            else:ax.set_extent(zoom_extent(ax,factor,coord))
            self.navigation.push();self.canvas.draw_idle()
        return event
    def _drag(self,x,y):
        ax,vp,start,extent,button=self.drag
        if getattr(ax,'_terrain3d',False):
            from .terrain3d import camera_drag
            camera_drag(ax,extent,start,(x,y),vp.box,mode=self.mode,button=button);self.canvas.draw_idle();return
        result=drag_extent(ax,vp,start,(x,y),mode=self.mode,button=button,initial_extent=extent)
        if result is not None and result!=ax.get_extent():ax.set_extent(result);self.canvas.draw_idle()
    def command(self,name):
        if name in ('pan','zoom'):
            if self.drag:self.navigation.push();self.drag=None
            self.mode='' if self.mode==name else name;self.canvas.mode=self.mode
        elif name in ('home','back','forward'):
            self.drag=None;getattr(self.navigation,name)();self.canvas.draw_idle()
        else:raise ValueError('Unknown navigation command')
