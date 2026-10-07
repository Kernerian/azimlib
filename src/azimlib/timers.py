"""Owned GUI timers: callbacks run on the Tk/Qt event-loop thread, never workers."""
import math

class Timer:
    def __init__(self,figure,interval=200,callbacks=None):
        self.figure=figure;self.callbacks=[];self.single_shot=False;self.running=False
        self._handle=None;self._generation=0;self._closed=False;self.interval=interval
        for row in callbacks or ():self.add_callback(*row)
        self._cid=figure.canvas.mpl_connect('close_event',lambda event:self.close())
    @property
    def interval(self):return self._interval
    @interval.setter
    def interval(self,value):
        value=float(value)
        if not math.isfinite(value) or not 1<=value<=86400000:raise ValueError('interval must be 1..86400000 milliseconds')
        self._interval=round(value)
    def add_callback(self,func,*args,**kwargs):
        if not callable(func):raise TypeError('Timer callback must be callable')
        self.callbacks.append((func,args,kwargs));return func
    def remove_callback(self,func,*args,**kwargs):
        self.callbacks=[row for row in self.callbacks if not (row[0]==func and (not args and not kwargs or row[1:]==(args,kwargs)))]
    def _backend(self):
        canvas=self.figure.canvas
        from .backends.tk import FigureWindow
        # Importing this class does not import Tk/Pillow or create a window.
        if isinstance(canvas,FigureWindow) and not canvas.closed:return 'tk',canvas
        from .backends.qt import QtCanvas
        if isinstance(canvas,QtCanvas) and not canvas.closed:return 'qt',canvas
        raise RuntimeError('Automatic playback requires an open Tk/Qt viewer; use step/seek or export elsewhere')
    def start(self,interval=None):
        if self._closed or self.figure._closed:raise RuntimeError('Timer is closed')
        backend,canvas=self._backend()
        if interval is not None:self.interval=interval
        self.stop();self.running=True;self._schedule(backend,canvas)
    def _schedule(self,backend,canvas):
        generation=self._generation
        if backend=='tk':self._handle=('tk',canvas.window,canvas.window.after(self.interval,lambda:self._fire(generation)))
        else:
            canvas._owner();timer=canvas.C.QTimer(canvas.window);timer.setSingleShot(True)
            timer.timeout.connect(lambda:self._fire(generation));timer.start(self.interval)
            self._handle=('qt',timer,None)
    def _discard(self):
        handle=self._handle;self._handle=None
        if handle is None:return
        if handle[0]=='tk':handle[1].after_cancel(handle[2])
        else:handle[1].stop();handle[1].deleteLater()
    def _fire(self,generation):
        if not self.running or generation!=self._generation:return
        self._discard()
        try:
            for row in tuple(self.callbacks):
                if row in self.callbacks and row[0](*row[1],**row[2]) is False:self.callbacks.remove(row)
        except BaseException:self.stop();raise
        if self.running and generation==self._generation:
            if self.single_shot or not self.callbacks:self.stop()
            else:self._schedule(*self._backend())
    def stop(self):
        self.running=False;self._generation+=1;self._discard()
    def close(self):
        if self._closed:return
        self.stop();self.figure.canvas.mpl_disconnect(self._cid);self.callbacks.clear();self._closed=True
