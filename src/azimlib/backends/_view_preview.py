"""Bounded, explicitly provisional navigation frames. Never used by savefig.

Only geographic ink is resampled from one authoritative base (never from a
previous preview). Fixed decorations retain their original pixels. Missing
coverage is background until the complete current-generation render arrives.
"""
import math
from ..scene import Scene
from ..viewport import Viewport
from ..navigation import viewport_from_metadata


def _ticker_identity(axis):
    controllers=(axis.get_major_locator(),axis.get_major_formatter(),
                 axis.get_minor_locator(),axis.get_minor_formatter())
    # Locator/Formatter parameter edits notify their owner rather than carrying
    # an Artist serial. Exclude the owning Axis reference, retain parameters.
    return tuple((id(value),repr({k:v for k,v in vars(value).items() if k!='axis'}))
                 for value in controllers)


def _identity(figure):
    # Extent is the only permitted edit. Public content setters carry serials;
    # axes configuration is compared independently from its view-change serial.
    from ..axes import MapAxes
    seen=set();result=[];stack=[figure]
    while stack:
        artist=stack.pop()
        if id(artist) in seen:continue
        seen.add(id(artist))
        if isinstance(artist,MapAxes):
            value=repr((artist.projection,artist.position,artist.facecolor,artist.get_bearing(),
                artist._tick_params,artist._minor_tick_params,artist._frame,
                artist._grid_format,artist._longitude_wrap,artist.get_visible(),
                artist._grid_configs,artist._axisbelow,artist._title_pads,
                _ticker_identity(artist.xaxis),_ticker_identity(artist.yaxis)))
        elif artist is figure:value=repr((figure.figsize,figure.dpi,figure.facecolor))
        else:value=getattr(artist,'_change_serial',0)
        result.append((id(artist),value))
        stack.extend(artist.get_children())
    return tuple(result)


class ViewPreview:
    MAX_BYTES=32*1024**2
    def __init__(self):self.clear()
    def clear(self):
        for name in ('ink','overlay','backing'):
            image=getattr(self,name,None)
            if image is not None:image.close()
            setattr(self,name,None)
        self.identity=None;self.meta=None;self.ax=self.original=self.projection=None
        self._data=self._fixed=None
    def prepare(self,figure,scene,*,max_bytes=None,reuse=None):
        """Snapshot on the owner thread; no rendering or Figure reads in a job."""
        self.clear()
        maps=scene.maps
        if len(maps)!=1 or maps[0].get('inset') or maps[0].get('terrain3d'):return False
        width,height=round(scene.width),round(scene.height)
        if width*height*4*3>(self.MAX_BYTES if max_bytes is None else max_bytes):return False
        meta=maps[0];path=meta['axes_path']
        if len(path)!=1:return False
        ax=figure.axes[path[0]]
        excluded=set(meta.get('static_indices',()))|set(meta.get('tick_indices',()))
        ink_indices=set(range(meta['start'],meta['end']))-excluded
        if not ink_indices:return False
        data=Scene(scene.width,scene.height,None)
        fixed=Scene(scene.width,scene.height,None)
        for i,item in enumerate(scene.items):
            if i in ink_indices:data.add(item)
            elif i!=meta['background_index']:fixed.add(item)
        from PIL import Image,ImageDraw
        from ..colors import to_rgba
        color=lambda value:tuple(round(c*255) for c in to_rgba(value or 'none'))
        self.backing=Image.new('RGBA',(width,height),color(scene.background))
        x,y,w,h=meta['box'];ImageDraw.Draw(self.backing).rectangle((x,y,x+w,y+h),fill=color(ax.facecolor))
        from ._pan_raster import frozen_scene
        self._data=frozen_scene(data);self._fixed=frozen_scene(fixed)
        self._fixed_key=repr((width,height,self._fixed.items))
        if reuse is not None and reuse.overlay is not None and self._fixed_key==getattr(reuse,'_fixed_key',None):
            self.overlay=reuse.overlay.copy()
        self.meta=dict(meta);self.identity=_identity(figure)
        self.projection=ax.projection;self.ax=ax
        self.original=viewport_from_metadata(ax.projection,meta)
        return True
    def build(self,renderer,cancel=None):
        """Only owned primitives and pixels enter the background renderer."""
        try:
            if cancel is not None and cancel.is_set():self.clear();return False
            self.ink=renderer(self._data)
            if cancel is not None and cancel.is_set():self.clear();return False
            if self.overlay is None:self.overlay=renderer(self._fixed)
            if cancel is not None and cancel.is_set():self.clear();return False
            return True
        except BaseException:self.clear();raise
        finally:self._data=self._fixed=None
    def capture(self,figure,scene,renderer):
        return self.prepare(figure,scene) and self.build(renderer)
    def render(self,figure):
        if self.ink is None or self.overlay is None or self.meta is None or self.identity!=_identity(figure):
            self.clear();return None
        ax=self.ax
        if ax.projection!=self.projection or ax.get_bearing()!=self.original.bearing:
            self.clear();return None
        # Projection is unchanged, so screen coordinates differ by scale and
        # translation even for non-cylindrical maps. This does not fill newly
        # exposed geography, recompute labels or claim an exact intermediate.
        vp=Viewport(ax.projection,ax.get_extent(),self.meta['box'],bearing=ax.get_bearing())
        ratio=vp.scale/self.original.scale
        tx=vp.ox-ratio*self.original.ox;ty=vp.oy-ratio*self.original.oy
        if not math.isfinite(ratio+tx+ty) or not .125<=ratio<=8:return None
        from PIL import Image
        x,y,w,h=self.meta['box'];left,top=math.ceil(x+1),math.ceil(y+1)
        width,height=max(0,math.floor(x+w-1)-left),max(0,math.floor(y+h-1)-top)
        if not width or not height:return None
        result=self.backing.copy()
        try:
            patch=self.ink.transform((width,height),Image.Transform.AFFINE,
                (1/ratio,0,(left-tx)/ratio,0,1/ratio,(top-ty)/ratio),Image.Resampling.BILINEAR)
            try:result.alpha_composite(patch,(left,top))
            finally:patch.close()
            result.alpha_composite(self.overlay)
            return result
        except BaseException:result.close();raise


class PreviewBuilder:
    """One active and one newest queued job. Never touches a GUI/model in worker."""
    def __init__(self,renderer):
        from threading import Condition
        self.renderer=renderer;self._condition=Condition();self._queued=self._ready=None
        self._cancel=None;self._closed=False;self._epoch=0;self._thread=None
    def submit(self,figure,scene,reuse=None):
        from threading import Event,Thread
        candidate=ViewPreview()
        # At most current, active and newest queued/ready previews coexist.
        # Divide the existing byte cap; no larger cache budget is introduced.
        if not candidate.prepare(figure,scene,max_bytes=ViewPreview.MAX_BYTES//3,reuse=reuse):
            candidate.clear();return False
        with self._condition:
            if self._closed:candidate.clear();return False
            self._epoch+=1
            if self._cancel is not None:self._cancel.set()
            if self._queued is not None:self._queued[1].clear()
            if self._ready is not None:self._ready.clear();self._ready=None
            self._queued=(self._epoch,candidate)
            if self._thread is None:
                self._thread=Thread(target=self._run,name='Azimlib-preview-cache',daemon=True)
                self._thread.start()
            self._condition.notify()
        return True
    def take(self,figure):
        with self._condition:
            candidate=self._ready;self._ready=None
        if candidate is not None and candidate.identity!=_identity(figure):
            candidate.clear();return None
        return candidate
    def busy(self):
        with self._condition:return self._cancel is not None or self._queued is not None or self._ready is not None
    def close(self):
        with self._condition:
            self._closed=True;self._epoch+=1
            if self._cancel is not None:self._cancel.set()
            if self._queued is not None:self._queued[1].clear();self._queued=None
            if self._ready is not None:self._ready.clear();self._ready=None
            self._condition.notify()
    def _run(self):
        from threading import Event
        while True:
            with self._condition:
                self._condition.wait_for(lambda:self._closed or self._queued is not None)
                if self._closed:return
                epoch,candidate=self._queued;self._queued=None;self._cancel=cancel=Event()
            try:valid=candidate.build(self.renderer,cancel)
            except Exception:valid=False  # Optional preview failure cannot replace the exact frame.
            with self._condition:
                if self._closed or epoch!=self._epoch or not valid:candidate.clear()
                else:
                    if self._ready is not None:self._ready.clear()
                    self._ready=candidate
                self._cancel=None
