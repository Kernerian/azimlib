"""Own finite frame playback/export; compatible call vocabulary, no external animator."""
from contextlib import contextmanager
from pathlib import Path
import math
import os
import re
import shutil
import subprocess
import tempfile
from .temporal import TemporalSeries,freeze,bounded
from .timers import Timer

def frame_index(value,length):
    if isinstance(value,bool) or not isinstance(value,int) or not 0<=value<length:raise IndexError('Invalid frame index')
    return value

def fps_value(value):
    value=float(value)
    if not math.isfinite(value) or not .1<=value<=100:raise ValueError('fps must be in [0.1, 100]')
    return value

class FuncAnimation:
    """Finite callback animation on an existing Figure.

    Keep this handle. frames is a count, bounded sequence or TemporalSeries;
    generators, blitting and infinite frame sources are deliberately unsupported.
    Callback(frame, *fargs) edits existing Artists. Its arbitrary side effects
    cannot be rolled back; successful exports restore the selected frame, not
    arbitrary external state. The same callback must reproduce any requested frame.
    """
    def __init__(self,fig,func,frames,*,init_func=None,fargs=(),interval=200,repeat=True,event_source=None,autoplay=True):
        from collections.abc import Sequence
        from .figure import Figure
        if not isinstance(fig,Figure) or fig._closed:raise ValueError('Animation requires an open Azimlib Figure')
        interval=float(interval)
        if not math.isfinite(interval) or not 1<=interval<=86400000:raise ValueError('interval must be 1..86400000 milliseconds')
        if not callable(func) or init_func is not None and not callable(init_func):raise TypeError('Animation callbacks must be callable')
        if isinstance(frames,bool):raise ValueError('frames must be a count or bounded sequence')
        if isinstance(frames,int):
            if not 1<=frames<=10000:raise ValueError('frames count must be 1..10000')
            values=tuple(range(frames))
        elif isinstance(frames,TemporalSeries):values=tuple(frames)
        elif bounded(frames):
            if not 1<=len(frames)<=10000:raise ValueError('frames count must be 1..10000')
            values=tuple(freeze(v) for v in frames)
        else:raise TypeError('frames require a bounded sequence; iterators/generators are unsupported')
        source=Timer(fig,interval) if event_source is None else event_source
        if not all(callable(getattr(source,k,None)) for k in ('start','stop','add_callback','remove_callback')):raise TypeError('event_source requires timer methods')
        if getattr(source,'figure',fig) is not fig:raise ValueError('event_source must belong to the animation figure')
        self._owns_source=event_source is None
        self.figure,self.func,self.frames,self.fargs=fig,func,values,tuple(fargs)
        self.repeat,self.autoplay=bool(repeat),bool(autoplay);self.index=None;self.closed=False;self._playing=False;self._busy=False;self._saving=False;self._started=False
        self.event_source=source;self.event_source.interval=interval;self.controls=[]
        self._draw_cid=fig.canvas.mpl_connect('draw_event',self._drawn)
        self._close_cid=fig.canvas.mpl_connect('close_event',lambda event:self.close())
        self.event_source.add_callback(self._tick)
        try:
            if init_func is not None:init_func()
            self.seek(0,draw=False)
        except BaseException:self.close();raise
    @property
    def playing(self):return self._playing
    def _drawn(self,event):
        if self.autoplay and not self._started and not self._saving and not self.closed:
            from .backends.tk import FigureWindow
            from .backends.qt import QtCanvas
            if isinstance(self.figure.canvas,(FigureWindow,QtCanvas)):self.resume()
    def _update(self,index,draw):
        if self.closed:raise RuntimeError('Animation is closed')
        if self._busy:raise RuntimeError('Recursive frame updates are unsupported')
        self._busy=True
        try:
            self.func(self.frames[index],*self.fargs)
            self.index=index
            for controls in self.controls:controls.sync()
            self.figure.stale=True
            if draw:self.figure.canvas.draw_idle()
        finally:self._busy=False
    def seek(self,index,*,draw=True):
        index=frame_index(index,len(self.frames));self._update(index,draw);return self.frames[index]
    def step(self):
        if self.closed:raise RuntimeError('Animation is closed')
        next_index=0 if self.index is None else self.index+1
        if next_index==len(self.frames):
            if not self.repeat:self.pause();return False
            next_index=0
        self.seek(next_index);return True
    def _tick(self):
        if not self._playing or self.closed:return False
        try:self.step()
        except BaseException:self.pause();raise
        # Keep the registered callback across pause/resume; source.stop cancels.
        return None
    def pause(self):
        self.event_source.stop();self._playing=False;self._started=True
        for controls in self.controls:controls.sync()
    def resume(self):
        if self.closed:raise RuntimeError('Animation is closed')
        if self._saving:raise RuntimeError('Playback cannot start during export')
        if not self._playing:
            self.event_source.start();self._playing=True;self._started=True
        for controls in self.controls:controls.sync()
    def set_interval(self,milliseconds):
        self.event_source.interval=milliseconds
        if self.playing:self.event_source.start()
    def add_controls(self,slider_ax,play_ax=None,*,label='Frame'):
        controls=PlaybackControls(self,slider_ax,play_ax,label=label);self.controls.append(controls);return controls
    def close(self):
        if self.closed:return
        self.pause();self.event_source.remove_callback(self._tick)
        if self._owns_source:self.event_source.close()
        for controls in tuple(self.controls):controls.close()
        self.figure.canvas.mpl_disconnect(self._draw_cid);self.figure.canvas.mpl_disconnect(self._close_cid);self.closed=True
    @contextmanager
    def _exporting(self):
        if self.closed or self._saving:raise RuntimeError('Animation is closed or already exporting')
        original=self.index;was_playing=self.playing;self.pause();self._saving=True
        try:yield
        finally:
            try:
                if not self.closed and original is not None:self.seek(original,draw=False)
            finally:
                self._saving=False
                if was_playing and not self.closed:self.resume()
    def save_frames(self,directory,*,prefix='frame',dpi=None):
        from .atlas import export_directory
        if not re.fullmatch(r'[A-Za-z0-9_-]+',prefix):raise ValueError('prefix requires ASCII letters, numbers, underscore or dash')
        with self._exporting():
            def export(folder):
                for i in range(len(self.frames)):
                    self.seek(i,draw=False);self.figure.savefig(folder/f'{prefix}-{i:05}.png',dpi=dpi)
            return export_directory(directory,export)
    def save(self,filename,*,writer=None,fps=None,dpi=None):
        """Write GIF by default; a video encoder must be explicitly supplied."""
        from .renderers.pillow import render_image
        fps=fps_value(1000/self.event_source.interval if fps is None else fps)
        if writer is None:
            if Path(filename).suffix.lower()!='.gif':raise ValueError('Non-GIF output requires an explicit FrameWriter')
            writer=PillowWriter()
        if not all(callable(getattr(writer,k,None)) for k in ('setup','write_frame','finish','abort')):raise TypeError('writer must implement setup/write_frame/finish/abort')
        density=self.figure.dpi if dpi is None else float(dpi)
        if not math.isfinite(density) or density<=0:raise ValueError('dpi must be finite and positive')
        width,height=(round(v*density) for v in self.figure.figsize)
        if min(width,height)<1 or width*height>8000000:raise ValueError('Animation frame budget is 8 million pixels')
        target=Path(filename);target.parent.mkdir(parents=True,exist_ok=True)
        fd,temp=tempfile.mkstemp(prefix='.azimlib-',suffix=target.suffix,dir=target.parent);os.close(fd)
        try:
            with self._exporting():
                try:
                    writer.setup(Path(temp),width,height,fps,len(self.frames))
                    for i in range(len(self.frames)):
                        self.seek(i,draw=False)
                        image=render_image(self.figure.to_scene(cull=False,simplify=False).scaled(density/self.figure.dpi))
                        try:writer.write_frame(image)
                        finally:image.close()
                    writer.finish()
                except BaseException:writer.abort();raise
            if not Path(temp).stat().st_size:raise RuntimeError('Encoder produced an empty file')
            os.replace(temp,target)
        finally:
            if Path(temp).exists():Path(temp).unlink()
        return target

class PlaybackControls:
    def __init__(self,animation,slider_ax,play_ax=None,*,label='Frame'):
        from .widgets import Slider,CheckButtons
        fig=animation.figure
        if slider_ax.figure is not fig or play_ax is not None and play_ax.figure is not fig:raise ValueError('Controls must belong to the animation figure')
        if len(animation.frames)<2:raise ValueError('A frame slider requires at least two frames')
        if play_ax is slider_ax:raise ValueError('Slider and Play require distinct axes')
        for ax in (slider_ax,) if play_ax is None else (slider_ax,play_ax):
            if getattr(ax,'_widget_owner',None) or ax.layers or ax.insets or ax._colorbar_artist:raise ValueError('Controls require distinct empty axes')
        self.animation=animation;self.closed=False
        self.slider=Slider(slider_ax,label,0,len(animation.frames)-1,valinit=animation.index,valstep=1)
        self.slider_cid=self.slider.on_changed(self._seek);self.play=None
        try:
            if play_ax is not None:
                self.play=CheckButtons(play_ax,['Play'],[animation.playing]);self.play_cid=self.play.on_clicked(self._toggle)
        except BaseException:self.slider.disconnect_events();raise
    def _seek(self,value):self.animation.pause();self.animation.seek(round(value))
    def _toggle(self,label):
        try:self.animation.resume() if self.play.get_status()[0] else self.animation.pause()
        except BaseException:self.sync();raise
    def sync(self):
        if self.closed:return
        slider=self.slider;previous=slider.eventson;drawon=slider.drawon;slider.eventson=False;slider.drawon=False
        try:
            if self.animation.index is not None:slider.set_val(self.animation.index)
            if self.play is not None:self.play._status=[self.animation.playing]
        finally:slider.eventson=previous;slider.drawon=drawon
    def close(self):
        if self.closed:return
        self.slider.disconnect(self.slider_cid);self.slider.disconnect_events()
        if self.play:self.play.disconnect(self.play_cid);self.play.disconnect_events()
        if self in self.animation.controls:self.animation.controls.remove(self)
        self.closed=True

class PillowWriter:
    """Generic Pillow GIF encoder; GIF times are quantized to 10 milliseconds."""
    def setup(self,path,width,height,fps,count):
        if count>1000 or width*height*count>100000000:raise ValueError('GIF budget: 1000 frames and 100 million total pixels')
        self.path=path;self.images=[];self.duration=max(10,round(1000/fps/10)*10)
    def write_frame(self,image):self.images.append(image.convert('RGB'))
    def finish(self):
        if not self.images:raise ValueError('No frames')
        try:self.images[0].save(self.path,format='GIF',save_all=True,append_images=self.images[1:],duration=self.duration,loop=0,disposal=2,optimize=False)
        finally:self.abort()
    def abort(self):
        for image in getattr(self,'images',[]):image.close()
        self.images=[]

class FFMpegWriter:
    """Explicit external FFmpeg process; no shell, downloads or bundled encoder.

    The executable/build/codecs keep their own licenses. This writer requests
    libx264 MP4 with even dimensions; availability is not promised by Azimlib.
    """
    def __init__(self,*,executable='ffmpeg'):self.executable=str(executable);self.process=None;self.stderr=None
    def setup(self,path,width,height,fps,count):
        resolved=shutil.which(self.executable)
        if resolved is None:raise RuntimeError('FFmpeg executable not found; install your chosen encoder separately')
        if width%2 or height%2:raise ValueError('This MP4 encoder requires even frame dimensions')
        if Path(path).suffix.lower()!='.mp4':raise ValueError('FFMpegWriter supports .mp4 only')
        self.size=(width,height);self.stderr=tempfile.TemporaryFile()
        args=[resolved,'-nostdin','-loglevel','error','-f','rawvideo','-pixel_format','rgba','-video_size',f'{width}x{height}','-framerate',str(fps),'-i','pipe:0','-an','-c:v','libx264','-pix_fmt','yuv420p','-y',str(path)]
        try:self.process=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=self.stderr,shell=False)
        except BaseException:self.abort();raise
    def write_frame(self,image):
        if image.size!=self.size:raise ValueError('Encoder frame size changed')
        converted=image.convert('RGBA')
        try:self.process.stdin.write(converted.tobytes())
        finally:converted.close()
    def finish(self):
        try:
            self.process.stdin.close();code=self.process.wait(timeout=30)
            if code:
                self.stderr.seek(0);message=self.stderr.read(1500).decode('utf8','replace');raise RuntimeError('FFmpeg failed: '+message)
        finally:self.abort()
    def abort(self):
        if self.process is not None:
            if self.process.poll() is None:
                self.process.terminate()
                try:self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=5)
            if self.process.stdin is not None and not self.process.stdin.closed:
                try:self.process.stdin.close()
                except OSError:pass
            self.process=None
        if self.stderr is not None:self.stderr.close();self.stderr=None
