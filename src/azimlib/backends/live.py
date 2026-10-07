"""Explicit tokenized loopback HTTP viewer; Figure mutations stay on its owner thread.

Handlers only serve frozen snapshots or enqueue a bounded input vocabulary.
No remote paths, arbitrary Python, pickle, eval, file reads or external resources.
Nonblocking users must pump flush_events on the creating thread.
"""
from collections import deque
from http.server import BaseHTTPRequestHandler,HTTPServer
from importlib.resources import files
import io,json,math,secrets,threading,time,webbrowser
from ..figure import FigureCanvas
from ..interaction import Interaction
from ..renderers.svg import render_svg
from ._common import attach,detach

class LiveCanvas(FigureCanvas):
    def __init__(self,figure):
        super().__init__(figure);self.closed=False;self.mode='';self.owner=threading.get_ident();self._dirty=True
        self._queue=deque();self._lock=threading.Lock();self._snapshot={};self._revision=0;self._error='';self.scene=None
        self.controller=Interaction(self);self.token=secrets.token_urlsafe(32)
        self.server=HTTPServer(('127.0.0.1',0),self._handler());self.server.timeout=.2
        self.url=f'http://127.0.0.1:{self.server.server_port}/{self.token}/'
        self._authority=f'127.0.0.1:{self.server.server_port}';self._origin=f'http://{self._authority}'
        self._thread=threading.Thread(target=self.server.serve_forever,kwargs=dict(poll_interval=.1),name='Azimlib-live-http',daemon=True)
    def start(self):
        self._html=self._page().encode('utf8');self.draw();self._thread.start();return self
    def _owner(self):
        if threading.get_ident()!=self.owner:raise RuntimeError('Pump or edit the Figure on the creating thread')
    def draw(self):
        self._owner()
        if self.closed or getattr(self,'_drawing',False):return
        self._drawing=True
        try:
            scene=self.figure.to_scene(cull=True,interactive=True);svg=render_svg(scene)
            from ._pan_raster import frozen_scene
            snapshot_scene=frozen_scene(scene);snapshot_scene._material_notices=list(scene._material_notices)
            self.scene=scene;self._pick_scene=scene;self._revision+=1
            state=dict(revision=self._revision,svg=svg,width=scene.width,height=scene.height,
                mode=self.mode,back=self.controller.navigation.index>0,
                forward=self.controller.navigation.index+1<len(self.controller.navigation.history),error=self._error)
            with self._lock:self._snapshot=state;self._export_scene=snapshot_scene
            self._dirty=False;self.figure._draw_complete()
            from types import SimpleNamespace
            self._dispatch('draw_event',SimpleNamespace(name='draw_event',canvas=self,renderer=scene))
        finally:self._drawing=False
    def draw_idle(self):self._dirty=True
    def _validate(self,data):
        if not isinstance(data,dict):raise ValueError('Input must be an object')
        op=data.get('op')
        if op=='command':
            if set(data)!={'op','name'} or data['name'] not in ('home','back','forward','pan','zoom'):raise ValueError('Unknown command')
        elif op=='resize':
            if set(data)!={'op','width','height'} or any(isinstance(data[k],bool) or not isinstance(data[k],(int,float)) or not math.isfinite(data[k]) or not 60<=data[k]<=4096 for k in ('width','height')):raise ValueError('Viewer dimensions must be 60..4096 pixels')
        elif op=='input':
            if set(data)-{'op','name','x','y','button','buttons','key','step'}:raise ValueError('Unknown input fields')
            if data.get('name') not in ('button_press_event','button_release_event','motion_notify_event','scroll_event','key_press_event','key_release_event'):raise ValueError('Unknown event')
            for key in ('x','y','step'):
                if data.get(key) is not None and (isinstance(data[key],bool) or not isinstance(data[key],(int,float)) or not math.isfinite(data[key]) or abs(data[key])>1e7):raise ValueError('Invalid input coordinate')
            if isinstance(data.get('button'),bool) or data.get('button') not in (None,1,2,3):raise ValueError('Invalid button')
            buttons=data.get('buttons')
            if buttons is not None and (not isinstance(buttons,list) or any(isinstance(v,bool) or v not in (1,2,3) for v in buttons) or len(buttons)>3):raise ValueError('Invalid buttons')
            if data.get('key') is not None and (not isinstance(data['key'],str) or len(data['key'])>32):raise ValueError('Invalid key')
            if data['name'] in ('button_press_event','motion_notify_event','scroll_event') and (data.get('x') is None or data.get('y') is None):raise ValueError('Mouse event needs coordinates')
        else:raise ValueError('Unknown operation')
    def enqueue(self,data):
        self._validate(data)
        data=dict(data)
        if isinstance(data.get('buttons'),list):data['buttons']=list(data['buttons'])
        with self._lock:
            if self.closed:raise RuntimeError('Viewer closed')
            if data.get('name')=='motion_notify_event' and self._queue and self._queue[-1].get('name')=='motion_notify_event':self._queue[-1]=dict(data)
            elif len(self._queue)<256:self._queue.append(dict(data))
            else:raise OverflowError('Input queue full')
    def flush_events(self):
        self._owner()
        if self.closed:return
        for _ in range(64):
            with self._lock:data=self._queue.popleft() if self._queue else None
            if data is None:break
            try:
                if data['op']=='command':self.controller.command(data['name']);self._dirty=True
                elif data['op']=='resize':self.figure.set_size_inches(data['width']/self.figure.dpi,data['height']/self.figure.dpi,forward=False);self._dirty=True
                else:
                    event=self.controller.event(**{k:v for k,v in data.items() if k!='op'})
                    if event.xdata is not None:
                        with self._lock:self._snapshot=dict(self._snapshot,coordinates=f'x={event.xdata:.4g} y={event.ydata:.4g}')
                self._error=''
            except Exception as exc:self.controller.drag=None;self._error=type(exc).__name__;self._dirty=True
        if self._dirty or self.figure.stale:self.draw()
    def mainloop(self):
        self._owner()
        try:
            while not self.closed:self.flush_events();time.sleep(.015)
        except KeyboardInterrupt:self.close()
    def _page(self):
        from html import escape
        from .._toolbar_icons import icon_svg
        root=files('azimlib').joinpath('assets');css=root.joinpath('viewer.css').read_text('utf8')
        script=root.joinpath('live-viewer.js').read_text('utf8')
        actions=(('home','Home','home'),('back','Back','back'),('forward','Forward','forward'),('pan','Pan','move'),('zoom','Zoom','zoom_to_rect'))
        buttons=''.join(f'<button data-command="{key}" title="{label}" aria-label="{label}">{icon_svg(icon)}</button>' for key,label,icon in actions)
        return '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+escape(self.figure._window_title())+' — Azimlib</title><style>'+css+'\nbutton svg{width:24px;height:24px} #status{margin-left:auto} #canvas{touch-action:none}</style></head><body><section id="figure-window"><main id="canvas" tabindex="0"></main><footer class="toolbar">'+buttons+'<a href="save.svg" download="azimlib.svg">SVG</a><a href="save.png" download="azimlib.png">PNG</a><output id="status"></output></footer></section><script>'+script+'</script></body></html>'
    def _handler(self):
        owner=self
        class Handler(BaseHTTPRequestHandler):
            def setup(self):
                super().setup();self.connection.settimeout(2.)
            def log_message(self,*args):pass
            def _reply(self,status,data,mime='application/json'):
                self.send_response(status);self.send_header('Content-Type',mime);self.send_header('Content-Length',str(len(data)))
                self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.send_header('Referrer-Policy','no-referrer')
                self.send_header('Content-Security-Policy',"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; font-src data:; img-src data:; frame-ancestors 'self' http://localhost:* http://127.0.0.1:*")
                self.end_headers()
                try:self.wfile.write(data)
                except (BrokenPipeError,ConnectionResetError):pass
            def _route(self):
                if self.headers.get('Host')!=owner._authority:return None
                prefix='/'+owner.token+'/'
                return self.path[len(prefix):] if self.path.startswith(prefix) else None
            def do_GET(self):
                route=self._route()
                if route=='':self._reply(200,owner._html,'text/html; charset=utf-8')
                elif route=='snapshot':
                    with owner._lock:data=json.dumps(owner._snapshot,allow_nan=False).encode()
                    self._reply(200,data)
                elif route in ('save.svg','save.png'):
                    with owner._lock:scene=owner._export_scene;svg=owner._snapshot['svg']
                    if route=='save.svg':self._reply(200,svg.encode(),'image/svg+xml')
                    else:
                        from ..renderers.pillow import render_png
                        stream=io.BytesIO();render_png(scene,stream);self._reply(200,stream.getvalue(),'image/png')
                else:self._reply(404,b'{}')
            def do_POST(self):
                # Drain only a bounded declared body before rejecting it. On Windows,
                # closing with unread bytes can reset even an already-written 403.
                try:length=int(self.headers.get('Content-Length','0'))
                except ValueError:length=0
                raw=b''
                if 0<length<=4096 and not self.headers.get('Transfer-Encoding'):
                    try:self.connection.settimeout(2);raw=self.rfile.read(length)
                    except (TimeoutError,OSError):self._reply(400,b'{}');return
                if self._route()!='event' or self.headers.get('Origin')!=owner._origin:self._reply(403,b'{}');return
                if self.headers.get('Content-Type','').split(';')[0]!='application/json' or self.headers.get('Transfer-Encoding'):self._reply(415,b'{}');return
                try:
                    length=int(self.headers.get('Content-Length','0'))
                    if not 0<length<=4096:raise ValueError('Input size')
                    if len(raw)!=length:raise ValueError('Incomplete input')
                    owner.enqueue(json.loads(raw))
                except OverflowError:self._reply(429,b'{}')
                except (ValueError,TypeError,TimeoutError,RuntimeError):self._reply(400,b'{}')
                else:self._reply(202,b'{"queued":true}')
        return Handler
    def close(self):
        self._owner()
        if self.closed:return
        self.closed=True
        if self._thread.is_alive():self.server.shutdown();self._thread.join(timeout=3)
        self.server.server_close()
        with self._lock:self._queue.clear();self._snapshot={}
        self._export_scene=self.scene=None;detach(self)

def show(figure,*,block=False,open_browser=True):
    viewer=getattr(figure,'_viewer',None)
    if not isinstance(viewer,LiveCanvas) or viewer.closed:
        if viewer is not None and not viewer.closed:raise RuntimeError('Close the current viewer before changing backend')
        viewer=LiveCanvas(figure);previous=attach(figure,viewer)
        try:viewer.start()
        except BaseException:viewer.close();figure.canvas=previous;raise
    else:viewer.draw()
    if open_browser:webbrowser.open(viewer.url)
    if block:viewer.mainloop()
    return viewer
