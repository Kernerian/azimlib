"""Optional geometric occultation scalar layers; explicit approximation consent."""
import math
from .eclipse import EclipseGeometry
from .field_artists import MeshCollection
from .solar_artists import SolarNightshade
from ._frames import Observer
from .colors import Normalize
from .styles import style_dict
from .artist import artist_mutation

class EclipseMapArtist(MeshCollection):
    _eclipse_artist=True
    _visible_cell=SolarNightshade._visible_cell
    def __init__(self,geometry,*,allow_approximate=False,step=4.,mode='estimate',cmap='viridis',alpha=.75,zorder=4):
        step=float(step)
        if not math.isfinite(step) or not 2<=step<=30:raise ValueError('Eclipse grid step must be 2..30 degrees')
        if mode not in ('estimate','possible'):raise ValueError('Eclipse map mode is estimate or possible')
        self.allow_approximate=bool(allow_approximate);self.mode=mode
        self.geometry=geometry;self._check(geometry)
        nx,ny=math.ceil(360/step),math.ceil(180/step)
        self.lon=tuple(-180+360*i/nx for i in range(nx+1));self.lat=tuple(-90+180*i/ny for i in range(ny+1))
        rows=self._prepare_eclipse(geometry)
        super().__init__('mesh',(self.lon,self.lat,rows),style_dict(dict(linewidth=0,edgecolor='none',alpha=alpha,zorder=zorder)),{})
        self.set_norm(Normalize(0,1));self.set_cmap(cmap);self.set_array(rows)
    def _check(self,geometry):
        if not isinstance(geometry,EclipseGeometry):raise TypeError('Require EclipseGeometry')
        geometry.require_visual_permission(self.allow_approximate)
    def _prepare_eclipse(self,geometry):
        self._check(geometry)
        def value(lon,lat):
            observer=Observer(lon,lat)
            if observer.azimuth_elevation(geometry.sun.center)[1]<=0:return None
            result=geometry.solar(observer)
            blocked=1-(result.visible_fraction if self.mode=='estimate' else result.fraction_bounds[0])
            return blocked if blocked>1e-10 else None
        return tuple(tuple(value((a+b)/2,(c+d)/2) for a,b in zip(self.lon,self.lon[1:])) for c,d in zip(self.lat,self.lat[1:]))
    @artist_mutation
    def set_geometry(self,geometry):
        rows=self._prepare_eclipse(geometry);self.set_array(rows);self.geometry=geometry
    def get_geometry(self):return self.geometry

def attach_eclipse(axes,geometry,**options):
    if getattr(axes,'_terrain3d',False):raise ValueError('Eclipse scalar map requires geographic axes; use Earth--Moon bodies for 3D')
    artist=EclipseMapArtist(geometry,**options);artist._axes=axes;artist._bind_parent(axes);axes.layers.append(artist);axes._changed();return artist

class EclipseBinding:
    def __init__(self,series,artist,*,scale='global',norm=None):
        if scale!='global' or norm is not None or artist.axes is None:raise ValueError('Eclipse binding requires an attached handle and no scalar norm')
        self.series,self.artist,self.index=series,artist,None
        for frame in series:
            artist._prepare_eclipse(frame.data)
            if series.kind=='date' and frame.data.instant is not None and frame.time!=frame.data.instant.utc:raise ValueError('Eclipse frame time differs from geometry instant')
    def apply(self,index):
        if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<len(self.series):raise IndexError('Invalid eclipse frame index')
        if self.artist.axes is None:raise RuntimeError('Eclipse Artist was removed')
        self.artist.set_geometry(self.series[index].data);self.index=index;return self.artist
