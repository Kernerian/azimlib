"""Optional independent Qt widget canvas. Qt handles UI; Azimlib owns every pixel."""
import time
from types import SimpleNamespace
from ..figure import FigureCanvas
from ..interaction import Interaction
from ._common import attach,detach
_windows=[];_application=None

def _imports():
    try:
        from PySide6 import QtCore,QtGui,QtWidgets
        from PIL import Image
    except ImportError as exc:raise ImportError('Qt show() requires azimlib[qt] (PySide6 and Pillow)') from exc
    return QtCore,QtGui,QtWidgets

class QtCanvas(FigureCanvas):
    def __init__(self,figure):
        C,G,W=_imports();self.C,self.G,self.W=C,G,W
        global _application
        _application=W.QApplication.instance() or W.QApplication([]);self.application=_application
        if C.QThread.currentThread()!=self.application.thread():raise RuntimeError('Qt canvas must be created on the GUI thread')
        super().__init__(figure);self.closed=False;self.mode='';self.scene=None;self._image=None;self._qimage=None;self._dirty=True;self._generation=0;self._last_presented=0;self._resize_size=None
        self.controller=Interaction(self)
        from ..renderers.pillow import render_image
        from ._pan_raster import PanRaster
        from ..renderers._interactive import InteractivePathCache
        from ..renderers._tile_cache import TileCache
        self._paths=InteractivePathCache();self._tiles=TileCache(max_entries=512)
        self.worker=PanRaster(render_image,lambda scene:render_image(scene,_interactive=True,_path_cache=self._paths,_tile_cache=self._tiles),lambda scene,cancel:render_image(scene,_cancel=cancel))
        owner=self
        class Window(W.QMainWindow):
            def closeEvent(self,event):owner.close();event.accept()
        class Surface(W.QWidget):
            def __init__(self):super().__init__();self.setMouseTracking(True);self.setFocusPolicy(C.Qt.FocusPolicy.StrongFocus);self.setMinimumSize(60,60)
            def paintEvent(self,event):
                painter=G.QPainter(self)
                try:
                    painter.fillRect(self.rect(),C.Qt.GlobalColor.white)
                    if owner._qimage is not None:painter.drawImage(self.rect(),owner._qimage)
                finally:painter.end()
            def resizeEvent(self,event):
                owner._resize_size=(round(self.width()*self.devicePixelRatioF()),round(self.height()*self.devicePixelRatioF()))
                owner.resize_timer.start(120)
            def _event(self,name,event):
                position=event.position();ratio=self.devicePixelRatioF()
                button={C.Qt.MouseButton.LeftButton:1,C.Qt.MouseButton.MiddleButton:2,C.Qt.MouseButton.RightButton:3}.get(event.button()) if hasattr(event,'button') else None
                buttons=[v for k,v in ((C.Qt.MouseButton.LeftButton,1),(C.Qt.MouseButton.MiddleButton,2),(C.Qt.MouseButton.RightButton,3)) if hasattr(event,'buttons') and event.buttons()&k]
                payload=owner.controller.event(name,position.x()*ratio,position.y()*ratio,button=button,buttons=buttons,guiEvent=event)
                if payload.xdata is not None:owner.status.setText(f'x={payload.xdata:.3g} y={payload.ydata:.3g}')
            def mousePressEvent(self,event):self._event('button_press_event',event)
            def mouseMoveEvent(self,event):self._event('motion_notify_event',event)
            def mouseReleaseEvent(self,event):self._event('button_release_event',event)
            def wheelEvent(self,event):
                p=event.position();d=self.devicePixelRatioF();owner.controller.event('scroll_event',p.x()*d,p.y()*d,step=event.angleDelta().y()/120,guiEvent=event)
            def keyPressEvent(self,event):
                key=event.text() or {C.Qt.Key.Key_Left:'left',C.Qt.Key.Key_Right:'right'}.get(event.key(),'')
                command={'h':'home','p':'pan','o':'zoom','left':'back','right':'forward'}.get(key)
                if command:owner.command(command)
                owner.controller.event('key_press_event',key=key,guiEvent=event)
            def focusOutEvent(self,event):
                if owner.controller.drag:owner.controller.navigation.push();owner.controller.drag=None
                super().focusOutEvent(event)
        self.window=Window()
        from ..typography import font_path
        fontid=G.QFontDatabase.addApplicationFont(str(font_path({})))
        families=G.QFontDatabase.applicationFontFamilies(fontid)
        if families:self.window.setFont(G.QFont(families[0],9))
        self._fontid=fontid
        self.widget=Surface();self.window.setCentralWidget(self.widget);self.window.setWindowTitle(figure._window_title())
        self.toolbar=W.QToolBar();self.toolbar.setMovable(False);self.toolbar.setIconSize(C.QSize(24,24));self.window.addToolBar(C.Qt.ToolBarArea.BottomToolBarArea,self.toolbar)
        self.window.setStyleSheet('QToolBar { background: #fafafa; border: 1px solid #dddddd; spacing: 2px; } QToolButton { color: #222222; background: transparent; } QToolButton:checked { background: #dce5ef; } QToolButton:hover { background: #e8e8e8; } QToolBar QLabel { color: #222222; background: #fafafa; }')
        self.buttons={}
        from .._toolbar_icons import icon_image
        actions=(('Home','home','home'),('Back','back','back'),('Forward','forward','forward'),('Pan','pan','move'),('Zoom','zoom','zoom_to_rect'),('Subplots','subplots','subplots'),('Save','save','filesave'))
        for label,command,icon in actions:
            if label in ('Pan','Save'):self.toolbar.addSeparator()
            image=icon_image(icon,24);qimage=self._to_qimage(image);image.close()
            action=self.toolbar.addAction(G.QIcon(G.QPixmap.fromImage(qimage)),label);action.setToolTip(label)
            if command in ('pan','zoom'):action.setCheckable(True)
            action.triggered.connect(lambda checked=False,name=command:self.command(name));self.buttons[label]=action
        spacer=W.QWidget();spacer.setSizePolicy(W.QSizePolicy.Policy.Expanding,W.QSizePolicy.Policy.Preferred);self.toolbar.addWidget(spacer)
        self.status=W.QLabel();self.toolbar.addWidget(self.status)
        self.timer=C.QTimer(self.window);self.timer.setInterval(8);self.timer.timeout.connect(self._tick)
        self.resize_timer=C.QTimer(self.window);self.resize_timer.setSingleShot(True);self.resize_timer.timeout.connect(self._resize)
        width,height=(round(v*figure.dpi) for v in figure.figsize);self.window.resize(width,height+45)
    def _to_qimage(self,image):
        rgba=image.convert('RGBA')
        try:return self.G.QImage(rgba.tobytes(),rgba.width,rgba.height,rgba.width*4,self.G.QImage.Format.Format_RGBA8888).copy()
        finally:rgba.close()
    def start(self):self.draw();self.timer.start();self.window.show();return self
    def _owner(self):
        if self.C.QThread.currentThread()!=self.application.thread():raise RuntimeError('Qt updates require the GUI thread')
    def _present(self,scene,image,complete=True):
        self.scene=scene;self._pick_scene=scene;self._qimage=self._to_qimage(image);image.close();self.widget.update()
        n=self.controller.navigation
        self.buttons['Back'].setEnabled(n.index>0);self.buttons['Forward'].setEnabled(n.index+1<len(n.history))
        for name in ('Pan','Zoom'):self.buttons[name].setChecked(self.mode==name.lower())
        if complete:self.figure._draw_complete()
        self._dispatch('draw_event',SimpleNamespace(name='draw_event',canvas=self,renderer=scene))
    def draw(self):
        self._owner()
        if self.closed or getattr(self,'_drawing',False):return
        from ..renderers.pillow import render_image
        self._drawing=True
        try:
            self.worker.clear();self._generation+=1
            scene=self.figure.to_scene(cull=True,interactive=True);self._dirty=False;self._present(scene,render_image(scene))
        finally:self._drawing=False
    def draw_idle(self):
        if not self.closed:self._dirty=True;self._generation+=1
    def _tick(self):
        if self.closed:return
        result=self.worker.take()
        if result is not None:
            token,scene,image,error,key=result
            if error:self.status.setText(type(error).__name__)
            elif image is not None:
                # Held drags may present complete intermediate scenes, never shifted bitmaps.
                if token==self._generation or self.controller.drag is not None and token>self._last_presented:
                    self._present(scene,image,complete=token==self._generation);self._last_presented=token
                else:image.close()
        if self._dirty and not self.worker.busy():
            try:
                scene=self.figure.to_scene(cull=True,interactive=True);self._dirty=False
                self.worker.submit(self._generation,scene,preview=self.controller.drag is not None)
            except Exception as exc:self._dirty=False;self.status.setText(type(exc).__name__)
    def flush_events(self):self._owner();self.application.processEvents();self._tick()
    def resize_figure(self,width,height):
        ratio=self.widget.devicePixelRatioF();self.window.resize(round(width/ratio),round(height/ratio)+self.toolbar.height())
    def _resize(self):
        if self.closed or self._resize_size is None:return
        w,h=self._resize_size
        if min(w,h)<60:return
        if (w,h)!=self.get_width_height():self.figure.set_size_inches(w/self.figure.dpi,h/self.figure.dpi,forward=False);self.draw_idle();self._dispatch('resize_event',SimpleNamespace(name='resize_event',canvas=self,width=w,height=h))
    def command(self,name):
        if name=='save':
            path,_=self.W.QFileDialog.getSaveFileName(self.window,'Save figure','azimlib.png','PNG (*.png);;SVG (*.svg);;PDF (*.pdf)')
            if path:self.figure.savefig(path)
        elif name=='subplots':self.subplots_dialog()
        else:self.controller.command(name);self.draw_idle()
    def subplots_dialog(self):
        W=self.W;dialog=W.QDialog(self.window);dialog.setWindowTitle('Configure subplots');layout=W.QFormLayout(dialog);fields={}
        for name,value in self.figure.subplotpars.items():
            field=W.QDoubleSpinBox();field.setRange(0,1 if name not in ('wspace','hspace') else 2);field.setDecimals(3);field.setSingleStep(.01);field.setValue(value);layout.addRow(name,field);fields[name]=field
        status=W.QLabel();layout.addRow(status);apply=W.QPushButton('Apply');layout.addRow(apply)
        def update():
            try:self.figure.subplots_adjust(**{k:v.value() for k,v in fields.items()});self.draw_idle();status.setText('')
            except ValueError:status.setText('Invalid subplot margins')
        apply.clicked.connect(update);dialog.setAttribute(self.C.Qt.WidgetAttribute.WA_DeleteOnClose);dialog.show();self._dialog=dialog
        return dialog
    def close(self):
        self._owner()
        if self.closed:return
        self.closed=True;self.timer.stop();self.resize_timer.stop();self.worker.close();self._tiles.close();self._qimage=self.scene=None
        try:detach(self)
        finally:
            self.window.hide();self.window.deleteLater()
            if self._fontid>=0:self.G.QFontDatabase.removeApplicationFont(self._fontid)
            if self in _windows:_windows.remove(self)

def show(figure,*,block=False):
    viewer=getattr(figure,'_viewer',None)
    if not isinstance(viewer,QtCanvas) or viewer.closed:
        if viewer is not None and not viewer.closed:raise RuntimeError('Close the current viewer before changing backend')
        viewer=QtCanvas(figure);previous=attach(figure,viewer);_windows.append(viewer)
        try:viewer.start()
        except BaseException:viewer.close();figure.canvas=previous;raise
    else:viewer.draw();viewer.window.show()
    if block:mainloop()
    return viewer
def mainloop():
    if _windows:_windows[0].application.exec()
