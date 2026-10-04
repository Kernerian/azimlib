"""One background raster job plus the newest pending view; never calls Tk."""
from copy import deepcopy
from dataclasses import replace
from threading import Condition,Thread

from ..scene import Path,Scene


def frozen_scene(scene):
    """Own the render primitives; do not send Figure/Artists to the renderer."""
    result=Scene(scene.width,scene.height,scene.background)
    for item in scene.items:
        options=dict(style=deepcopy(dict(item.style)))
        if isinstance(item,Path):options['paths']=tuple(tuple(tuple(point) for point in part) for part in item.paths)
        result.add(replace(item,**options))
    return result


class PanRaster:
    def __init__(self,renderer,preview_renderer=None):
        self.renderer=renderer;self.preview_renderer=preview_renderer;self._condition=Condition()
        self._queued=self._ready=None;self._active=False;self._closed=False
        self._epoch=0;self._thread=None

    def submit(self,token,scene,key=None,*,preview=False):
        snapshot=frozen_scene(scene)
        with self._condition:
            if self._closed:return
            self._queued=(self._epoch,token,scene,snapshot,key,preview)
            if self._thread is None:
                self._thread=Thread(target=self._run,name='Azimlib-pan-raster',daemon=True)
                self._thread.start()
            self._condition.notify()

    def take(self):
        with self._condition:
            result=self._ready;self._ready=None
            return result

    def busy(self):
        with self._condition:return self._active or self._queued is not None or self._ready is not None

    def clear(self):
        with self._condition:
            self._epoch+=1;self._queued=None
            if self._ready is not None and self._ready[2] is not None:self._ready[2].close()
            self._ready=None

    def close(self):
        with self._condition:
            self._closed=True;self.clear();self._condition.notify()

    def _run(self):
        while True:
            with self._condition:
                self._condition.wait_for(lambda:self._closed or self._queued is not None)
                if self._closed:return
                epoch,token,scene,snapshot,key,preview=self._queued
                self._queued=None;self._active=True
            image=error=None
            try:image=(self.preview_renderer if preview and self.preview_renderer is not None else self.renderer)(snapshot)
            except Exception as exc:error=exc
            with self._condition:
                self._active=False
                if self._closed or epoch!=self._epoch:
                    if image is not None:image.close()
                else:
                    if self._ready is not None and self._ready[2] is not None:self._ready[2].close()
                    self._ready=(token,scene,image,error,key)
                self._condition.notify_all()
