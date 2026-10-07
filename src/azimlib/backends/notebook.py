"""Explicit updatable SVG display using IPython's public display/event interfaces."""
import threading
from ..figure import FigureCanvas
from ._common import attach,detach

class NotebookCanvas(FigureCanvas):
    def __init__(self,figure,shell,display):
        super().__init__(figure);self.shell=shell;self.display=display;self.closed=False;self.owner=threading.get_ident();self.handle=None;self._dirty=True
        self._hook=lambda result:self.flush_events()
    def start(self):self.shell.events.register('post_run_cell',self._hook);self.draw();return self
    def draw(self):
        if threading.get_ident()!=self.owner:raise RuntimeError('Notebook updates must run on the kernel thread')
        if self.closed or getattr(self,'_drawing',False):return
        self._drawing=True
        try:
            scene=self.figure.to_scene();from ..renderers.svg import render_svg
            payload={'image/svg+xml':render_svg(scene)}
            if self.handle is None:self.handle=self.display(payload,raw=True,display_id=True)
            else:self.handle.update(payload,raw=True)
            self.scene=scene;self._dirty=False;self.figure._draw_complete()
            from types import SimpleNamespace
            self._dispatch('draw_event',SimpleNamespace(name='draw_event',canvas=self,renderer=scene))
        finally:self._drawing=False
    def draw_idle(self):self._dirty=True
    def flush_events(self):
        if not self.closed and (self._dirty or self.figure.stale):self.draw()
    def close(self):
        if self.closed:return
        if threading.get_ident()!=self.owner:raise RuntimeError('Close on the kernel thread')
        self.shell.events.unregister('post_run_cell',self._hook);self.handle=None;detach(self)

def show(figure,*,block=False):
    try:
        from IPython import get_ipython
        from IPython.display import display
    except ImportError as exc:raise ImportError('Notebook updates require azimlib[notebook]') from exc
    shell=get_ipython()
    if shell is None or not hasattr(shell,'events'):raise RuntimeError('An active IPython kernel/shell is required')
    viewer=getattr(figure,'_viewer',None)
    if not isinstance(viewer,NotebookCanvas) or viewer.closed:
        if viewer is not None and not viewer.closed:raise RuntimeError('Close the current viewer before changing backend')
        viewer=NotebookCanvas(figure,shell,display);previous=attach(figure,viewer)
        try:viewer.start()
        except BaseException:
            try:viewer.close()
            finally:figure.canvas=previous
            raise
    else:viewer.draw()
    return viewer
