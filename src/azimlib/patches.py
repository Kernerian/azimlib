"""Reusable own path symbols and editable path patches."""
from .layers import Layer
from .path import Path
from .artist import artist_mutation

class PathPatch(Layer):
    def __init__(self,path,**kwargs):
        if not isinstance(path,Path):raise TypeError('Require an Azimlib Path')
        transform=kwargs.pop('transform',None)
        from .styles import style_dict
        super().__init__('path',path,style_dict(kwargs))
        if transform is not None:self.set_transform(transform)
    def get_path(self):return self.data
    @artist_mutation
    def set_path(self,path):
        if not isinstance(path,Path):raise TypeError('Require an Azimlib Path')
        self.data=path

class Symbol:
    def __init__(self,path):
        if not isinstance(path,Path):raise TypeError('Require an Azimlib Path')
        self.path=path
    def patch(self,**kwargs):return PathPatch(self.path,**kwargs)
