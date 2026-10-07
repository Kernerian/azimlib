"""Opt-in scene widgets and selectors, drawn and handled entirely by Azimlib."""
import math
from types import SimpleNamespace
from .artist import Artist
from .callbacks import CallbackRegistry
from .scene import Rect,Text,Path

def _finite(value):
    value=float(value)
    if not math.isfinite(value):raise ValueError('Require finite numbers')
    return value

class AxesWidget(Artist):
    def __init__(self,ax,*,occupy=True):
        if occupy and (getattr(ax,'_widget_owner',None) or ax.layers or ax.insets or ax._colorbar_artist):raise ValueError('Widget requires distinct empty axes')
        Artist.__init__(self,ax);self.ax=ax;self._active=self._visible=True;self.eventson=self.drawon=True;self._cids=[]
        if occupy:ax._widget_owner=self
        self._occupy=occupy;ax.figure._widgets.append(self)
        self.connect_event('close_event',lambda e:self.disconnect_events())
    @property
    def canvas(self):return self.ax.figure.canvas
    def connect_event(self,name,callback):self._cids.append(self.canvas.mpl_connect(name,callback))
    def disconnect_events(self):
        for cid in self._cids:self.canvas.mpl_disconnect(cid)
        self._cids.clear()
        if self in self.ax.figure._widgets:self.ax.figure._widgets.remove(self)
        if self._occupy and getattr(self.ax,'_widget_owner',None) is self:self.ax._widget_owner=None
        self.ax.figure.stale=True
    def get_active(self):return self._active
    def set_active(self,value):self._active=bool(value)
    active=property(get_active,set_active)
    def get_visible(self):return self._visible and self.ax.get_visible()
    def set_visible(self,value):self._visible=bool(value);self._redraw()
    def _box(self,scale=100):
        w,h=(v*scale for v in self.ax.figure.figsize);x,y,b,c=self.ax.position
        return x*w,(1-y-c)*h,b*w,c*h
    def _local(self,event):
        if not self._active or not self.get_visible() or event.x is None or event.y is None:return None
        x,y,w,h=self._box(self.ax.figure.dpi);sx,sy=event.x,self.ax.figure.figsize[1]*self.ax.figure.dpi-event.y
        return ((sx-x)/w,(sy-y)/h) if x<=sx<=x+w and y<=sy<=y+h else None
    def _redraw(self):
        self.ax.figure.stale=True
        if self.drawon:self.canvas.draw_idle()

class Slider(AxesWidget):
    def __init__(self,ax,label,valmin,valmax,valinit=None,*,valstep=None,orientation='horizontal'):
        low,high=_finite(valmin),_finite(valmax)
        if low>=high or orientation not in ('horizontal','vertical'):raise ValueError('Invalid slider range/orientation')
        step=None if valstep is None else _finite(valstep)
        if step is not None and step<=0:raise ValueError('valstep must be positive')
        self.valmin,self.valmax,self.valstep,self.orientation=low,high,step,orientation
        self.label=str(label);self.valinit=self._value(low if valinit is None else valinit);self.val=self.valinit
        self._observers=CallbackRegistry(('changed',));self._held=False
        super().__init__(ax)
        for name in ('button_press_event','motion_notify_event','button_release_event'):self.connect_event(name,self._event)
    def _value(self,value):
        value=max(self.valmin,min(self.valmax,_finite(value)))
        if self.valstep:value=self.valmin+round((value-self.valmin)/self.valstep)*self.valstep
        return max(self.valmin,min(self.valmax,value))
    def set_val(self,value):
        value=self._value(value)
        if value==self.val:return
        self.val=value;self._redraw()
        if self.eventson:self._observers.process('changed',value)
    def on_changed(self,callback):return self._observers.connect('changed',callback)
    def disconnect(self,cid):self._observers.disconnect(cid)
    def reset(self):self.set_val(self.valinit)
    def _event(self,event):
        if event.name=='button_release_event':self._held=False;return
        local=self._local(event)
        if event.name=='button_press_event':self._held=event.button==1 and local is not None
        if not self._held or local is None:return
        if event.name=='motion_notify_event' and event.buttons is not None and 1 not in event.buttons:self._held=False;return
        fraction=(local[0]-.15)/.7 if self.orientation=='horizontal' else (1-local[1]-.15)/.7
        self.set_val(self.valmin+(self.valmax-self.valmin)*fraction)
    def _render(self,scene):
        x,y,w,h=self._box();q=(self.val-self.valmin)/(self.valmax-self.valmin)
        scene.add(Rect(x,y,w,h,dict(fill='white',stroke='#cccccc',stroke_width=.7)))
        if self.orientation=='horizontal':
            a=x+.15*w;b=y+h*.52
            scene.add(Rect(a,b-2,w*.7,4,dict(fill='#dddddd')));scene.add(Rect(a,b-2,w*.7*q,4,dict(fill='#248bb8')))
            scene.add(Rect(a+w*.7*q-2,b-7,4,14,dict(fill='#333333')))
        else:
            a=x+w*.5;b=y+h*.15
            scene.add(Rect(a-2,b,4,h*.7,dict(fill='#dddddd')));scene.add(Rect(a-2,b+h*.7*(1-q),4,h*.7*q,dict(fill='#248bb8')))
            scene.add(Rect(a-7,b+h*.7*(1-q)-2,14,4,dict(fill='#333333')))
        scene.add(Text(x+w*.04,y+h*.25,self.label,dict(font_size=10,fill='black')))
        scene.add(Text(x+w*.96,y+h*.85,f'{self.val:g}',dict(font_size=10,fill='black',anchor='end')))

class CheckButtons(AxesWidget):
    def __init__(self,ax,labels,actives=None):
        self.labels=tuple(str(v) for v in labels);self._status=list(actives) if actives is not None else [False]*len(self.labels)
        if not self.labels or len(self._status)!=len(self.labels):raise ValueError('Require one state per label')
        self._status=[bool(v) for v in self._status];self._observers=CallbackRegistry(('clicked',));super().__init__(ax)
        self.connect_event('button_press_event',self._event)
    def get_status(self):return list(self._status)
    def set_active(self,index):
        if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<len(self.labels):raise ValueError('Invalid check index')
        self._status[index]=not self._status[index];self._redraw()
        if self.eventson:self._observers.process('clicked',self.labels[index])
    def on_clicked(self,callback):return self._observers.connect('clicked',callback)
    def disconnect(self,cid):self._observers.disconnect(cid)
    def _event(self,event):
        p=self._local(event)
        if event.button==1 and p is not None:self.set_active(min(len(self.labels)-1,int(p[1]*len(self.labels))))
    def _render(self,scene):
        x,y,w,h=self._box();scene.add(Rect(x,y,w,h,dict(fill='white',stroke='#cccccc',stroke_width=.7)))
        for i,label in enumerate(self.labels):
            cy=y+h*(i+.5)/len(self.labels);size=min(10,h/len(self.labels)*.45)
            scene.add(Rect(x+8,cy-size/2,size,size,dict(fill='#248bb8' if self._status[i] else 'white',stroke='black',stroke_width=.7)))
            scene.add(Text(x+size+14,cy+3,label,dict(font_size=10,fill='black')))

class LayerControl(CheckButtons):
    def __init__(self,ax,layers,labels=None):
        self.layers=tuple(layers)
        if not self.layers or any(layer.get_figure() is not ax.figure for layer in self.layers):raise ValueError('Layers must belong to this figure')
        names=tuple(labels) if labels is not None else tuple(layer.get_label() or layer.kind for layer in self.layers)
        if len(set(names))!=len(names):raise ValueError('Layer labels must be unique')
        super().__init__(ax,names,[layer.get_visible() for layer in self.layers]);self.on_clicked(self._toggle)
    def _toggle(self,label):
        index=self.labels.index(label);self.layers[index].set_visible(self._status[index]);self._redraw()
    def _render(self,scene):
        self._status=[layer.get_visible() for layer in self.layers];super()._render(scene)

class RectangleSelector(AxesWidget):
    def __init__(self,ax,onselect,*,minspanx=0,minspany=0):
        if not callable(onselect):raise TypeError('onselect must be callable')
        self.minspanx,self.minspany=_finite(minspanx),_finite(minspany)
        if min(self.minspanx,self.minspany)<0:raise ValueError('Spans must be nonnegative pixels')
        self.onselect=onselect;self._start=self._end=None;self.extents=None;super().__init__(ax,occupy=False)
        for name in ('button_press_event','motion_notify_event','button_release_event'):self.connect_event(name,self._event)
    def _event(self,event):
        if not self._active or not self.get_visible() or getattr(self.canvas,'mode',''):return
        if event.name=='button_press_event':
            self._start=event if event.inaxes is self.ax and event.button==1 and event.xdata is not None else None;self._end=self._start
        elif self._start is not None:
            if event.name=='motion_notify_event' and event.buttons is not None and 1 not in event.buttons:self._start=self._end=None;self._redraw();return
            if event.inaxes is self.ax and event.xdata is not None:self._end=event
            if event.name=='button_release_event':
                a,b=self._start,self._end;self._start=None
                if b is not None and abs(a.x-b.x)>=self.minspanx and abs(a.y-b.y)>=self.minspany:
                    self.extents=(*sorted((a.xdata,b.xdata)),*sorted((a.ydata,b.ydata)))
                    if self.eventson:self.onselect(a,b)
            self._redraw()
    def _render(self,scene):
        if self._start is None or self._end is None:return
        ratio=100/self.ax.figure.dpi;a,b=self._start,self._end
        x,y=min(a.x,b.x)*ratio,self.ax.figure.figsize[1]*100-max(a.y,b.y)*ratio
        scene.add(Rect(x,y,abs(a.x-b.x)*ratio,abs(a.y-b.y)*ratio,dict(fill='#248bb833',stroke='black',stroke_width=.7)))


class FeatureSelector(AxesWidget):
    """Maintain a feature-index selection and an optional interactive highlight."""
    def __init__(self,ax,layer,onselect=None,*,tolerance=5):
        from .simplify import _tolerance
        tolerance=_tolerance(tolerance)
        if layer.axes is not ax or layer.kind not in ('geometry','scatter'):raise ValueError('Select a geometry/scatter layer owned by these axes')
        if onselect is not None and not callable(onselect):raise TypeError('onselect must be callable')
        self.layer=layer;self.indices=();self.onselect=onselect;self._previous_picker=layer.get_picker()
        super().__init__(ax,occupy=False);layer.set_picker(tolerance);self.connect_event('pick_event',self._pick)
    def set_selection(self,indices):
        indices=tuple(sorted(set(indices)))
        if any(isinstance(i,bool) or not isinstance(i,int) or not 0<=i<len(self.layer.data) for i in indices):raise ValueError('Invalid feature indices')
        self.indices=indices;self._redraw()
        if self.eventson and self.onselect is not None:self.onselect(indices)
    def get_selection(self):return self.indices
    def get_features(self):return tuple(self.layer.data[i] for i in self.indices if i<len(self.layer.data))
    def _pick(self,event):
        if self._active and self.get_visible() and event.artist is self.layer:self.set_selection(event.ind)
    def disconnect_events(self):
        if self._cids:self.layer.set_picker(self._previous_picker)
        super().disconnect_events()
    def _render(self,scene):
        if not self.layer.get_visible():return
        from .render_map import _geometry,_marker,_transformed_geometry
        vp=self.ax._active_viewport
        if vp is None:return
        for index in self.indices:
            if index>=len(self.layer.data):continue
            if self.layer.kind=='geometry':
                geometry=self.layer.data[index].geometry
                if geometry is None:continue
                style=dict(facecolor='#ffc85733',edgecolor='#dd9900',linewidth=2,markersize=9,color='#dd9900')
                if getattr(self.layer,'_transform',None) is not None:_transformed_geometry(geometry,style,self.layer.get_transform(),self.ax.figure,vp,scene)
                else:_geometry(geometry,style,vp,scene)
            else:
                point=vp.project(*self.layer.data[index])
                if point:_marker(point,10,dict(color='#dd9900',marker='o',markerfacecolor='none',markeredgecolor='#dd9900',markeredgewidth=2),scene,vp.box)
