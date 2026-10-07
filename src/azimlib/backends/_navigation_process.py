"""Private pixel worker: isolate raster CPU/GIL from the Tk event loop.

Only our parent/child pipe carries pickled, owned Scene snapshots. This is not
a file/network decoder. Tk and Figure/Artists never enter the child process.
"""
from pathlib import Path
import pickle,struct,subprocess,sys
from threading import RLock

_SIZE=struct.Struct('<Q')


def _read(stream,size):
    pieces=[];remaining=size
    while remaining:
        piece=stream.read(remaining)
        if not piece:raise RuntimeError('Navigation pixel worker stopped')
        pieces.append(piece);remaining-=len(piece)
    return b''.join(pieces)


def _send(stream,value):
    data=pickle.dumps(value,protocol=5)
    if len(data)>512*1024*1024:raise RuntimeError('Navigation frame exceeds the private transfer limit')
    for content in (_SIZE.pack(len(data)),data):
        view=memoryview(content)
        while view:
            count=stream.write(view)
            if not count:raise RuntimeError('Navigation pixel worker stopped')
            view=view[count:]
    stream.flush()


def _receive(stream):
    size=_SIZE.unpack(_read(stream,_SIZE.size))[0]
    if size>512*1024*1024:raise RuntimeError('Navigation frame exceeds the private transfer limit')
    return pickle.loads(_read(stream,size))


class NavigationProcess:
    def __init__(self):
        self._lock=RLock();self._closed=False
        flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
        # A dedicated module avoids re-running the user's script and does not
        # require a multiprocessing __main__ guard in ordinary plotting code.
        self.process=subprocess.Popen([sys.executable,'-I',str(Path(__file__).resolve())],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
            creationflags=flags,bufsize=0)
        self._ready=False

    def render(self,scene):
        with self._lock:
            if self._closed:raise RuntimeError('Navigation pixel worker closed')
            process=self.process
        if not self._ready:
            if _receive(process.stdout)!='ready':raise RuntimeError('Navigation pixel worker did not initialize')
            self._ready=True
        _send(process.stdin,scene)
        result=_receive(process.stdout)
        if result[0]=='error':raise RuntimeError(result[1])
        _,size,pixels=result
        from PIL import Image
        return Image.frombytes('RGBA',size,pixels)

    def close(self):
        with self._lock:
            if self._closed:return
            self._closed=True
            if self.process.poll() is None:self.process.terminate()
            for stream in (self.process.stdin,self.process.stdout):
                try:stream.close()
                except OSError:pass
            try:self.process.wait(timeout=.25)
            except subprocess.TimeoutExpired:pass


def _main():
    # -I prevents environment/user-path leakage; load this exact installed or
    # source tree before reading our own private pipe protocol.
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
    from azimlib.renderers import render_image
    from azimlib.renderers._tile_cache import TileCache
    from azimlib.renderers._interactive import InteractivePathCache
    tiles=TileCache(max_entries=512);paths=InteractivePathCache()
    incoming,outgoing=sys.stdin.buffer,sys.stdout.buffer
    _send(outgoing,'ready')
    try:
        while True:
            try:scene=_receive(incoming)
            except RuntimeError:break
            image=None
            try:
                image=render_image(scene,_interactive=True,_tile_cache=tiles,_path_cache=paths)
                _send(outgoing,('image',image.size,image.tobytes()))
            except Exception as exc:_send(outgoing,('error',str(exc)))
            finally:
                if image is not None:image.close()
    finally:tiles.close()


if __name__=='__main__':_main()
