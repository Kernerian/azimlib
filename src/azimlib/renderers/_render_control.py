"""Cooperative interruption of owned desktop raster jobs; never used by savefig."""
from .coverage import CoverageDraw


class RasterCancelled(Exception):pass


class _InterruptibleStroke(CoverageDraw):
    def __init__(self,mask,control):super().__init__(mask);self.control=control;self.calls=0
    def polygon(self,points,fill=255,**kwargs):
        self.calls+=1
        if self.calls%32==0:self.control.check()
        return super().polygon(points,fill,**kwargs)


class RasterControl:
    def __init__(self,event):self.event=event;self.buffers=[]
    def check(self):
        if self.event.is_set():raise RasterCancelled()
    def images(self,module):
        control=self
        class Images:
            def __getattr__(self,name):return getattr(module,name)
            def new(self,*args,**kwargs):
                image=module.new(*args,**kwargs);control.buffers.append(image);return image
        return Images()
    def stroke_draw(self,mask):return _InterruptibleStroke(mask,self)
    def close(self,result=None):
        for image in self.buffers:
            if image is not result:image.close()
        self.buffers.clear()
