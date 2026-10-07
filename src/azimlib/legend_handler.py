"""Own custom legend handler protocol; callbacks draw only Azimlib artists."""
from .transforms import Affine2D

def get_handler(mapping,handle):
    for key,value in mapping.items():
        if key is handle:return value
    for cls in type(handle).__mro__:
        if cls in mapping:return mapping[cls]
    return None

class HandleBox:
    def __init__(self,legend,scene,box):
        self.legend,self.scene=legend,scene
        self.x,self.y,self.width,self.height=box
        self.artists=[]
    def get_transform(self):
        f=self.legend.axes.figure
        return Affine2D().scale(f.dpi/100).translate(self.x*f.dpi/100,(f.figsize[1]*100-self.y-self.height)*f.dpi/100)
    def add_artist(self,artist):
        from .patches import PathPatch
        from .render_map import _transformed_paths
        from types import SimpleNamespace
        if not isinstance(artist,PathPatch):raise TypeError('Legend handlers currently draw own PathPatch artists')
        if artist.axes is not None:raise ValueError('Handler must return a new unattached patch')
        if getattr(artist,'_transform',None) is None:artist.set_transform(self.get_transform())
        artist._axes=self.legend.axes;artist._bind_parent(self.legend)
        _transformed_paths(artist,SimpleNamespace(box=None),self.scene)
        self.artists.append(artist);return artist

class HandlerBase:
    def create_artists(self,legend,orig_handle,xdescent,ydescent,width,height,fontsize,transform):raise NotImplementedError
    def legend_artist(self,legend,orig_handle,fontsize,handlebox):
        artists=self.create_artists(legend,orig_handle,0,0,handlebox.width,handlebox.height,fontsize,handlebox.get_transform())
        artists=list(artists)
        if not artists:raise ValueError('Handler must create at least one artist')
        for artist in artists:handlebox.add_artist(artist)
        return artists[0]

class HandlerSymbol(HandlerBase):
    def __init__(self,**style):self.style=style
    def create_artists(self,legend,orig_handle,xdescent,ydescent,width,height,fontsize,transform):
        from .patches import Symbol
        from .transforms import Affine2D
        if not isinstance(orig_handle,Symbol):raise TypeError('HandlerSymbol requires Symbol')
        return [orig_handle.patch(transform=Affine2D().scale(width,height)+transform,**self.style)]
