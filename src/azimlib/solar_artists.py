"""Solar handles built on Azimlib's own geographic and physical 3D Artists."""
import math
from .solar import SunPosition,SunDirection,SolarModel,SolarPath,_number,_unit,_cross
from .geometry import Feature,FeatureCollection,Geometry
from .layers import Layer
from .field_artists import MeshCollection
from .artist import artist_mutation
from .styles import style_dict,text_style
from .colors import ListedColormap,Normalize
from .terrain_axes import SurfaceArtist
from .terrain3d import Mesh,LocalFrame


def state(value,model=None,observer=None,offsets=None):
    if isinstance(value,(SunPosition,SunDirection)):
        if observer is not None and value.observer!=observer:raise ValueError('Solar state observer differs from requested observer')
        return value
    return (model or SolarModel()).position(value,observer,offsets=offsets)


def collection(value,role,samples):
    if role=='point':geometry=Geometry('Point',value.subsolar)
    elif role=='terminator' and isinstance(value,SunPosition):geometry=value.terminator(samples=samples)
    else:raise ValueError('A terminator requires a calculated SunPosition')
    properties={'solar_role':role,'model':value.model if isinstance(value,SunPosition) else 'manual-direction'}
    if isinstance(value,SunPosition):properties['utc']=value.instant.utc.isoformat()
    return FeatureCollection((Feature(geometry,properties,'sun'),))


class SunArtist(Layer):
    _solar_artist=True
    def __init__(self,value,*,model=None,observer=None,offsets=None,role='point',samples=361,annotation=None,annotation_style=None,**style):
        value=state(value,model,observer,offsets)
        data=collection(value,role,samples)
        self.role,self.samples,self.state=role,samples,value
        self.model=model or SolarModel();self.observer=value.observer;self.offsets=offsets
        self.annotation=None if annotation is None else str(annotation)
        self.annotation_style=dict(annotation_style or {});text_style(self.annotation_style)
        defaults=dict(color='#e89b24',markersize=9,zorder=6) if role=='point' else dict(color='#263f5a',linewidth=.8,zorder=4)
        super().__init__('geometry',data,style_dict({**defaults,**style}),dict(fit=False))
    def _prepare_solar(self,value):
        if not isinstance(value,(SunPosition,SunDirection)):raise TypeError('Require calculated SunPosition or manual SunDirection')
        if value.observer!=self.observer:raise ValueError('Solar updates must preserve observer/frame identity')
        return collection(value,self.role,self.samples)
    @artist_mutation
    def set_position(self,value):
        data=self._prepare_solar(value);self.state=value;self.data=data
    def set_time(self,instant,*,offsets=None):
        return self.set_position(self.model.position(instant,self.observer,offsets=self.offsets if offsets is None else offsets))
    def set_manual(self,azimuth,elevation):return self.set_position(SunDirection(azimuth,elevation,self.observer))
    def get_position(self):return self.state
    @artist_mutation
    def set_annotation(self,text):self.annotation=None if text is None else str(text)


class SolarNightshade(MeshCollection):
    _solar_artist=True
    def __init__(self,value,*,model=None,observer=None,offsets=None,step=5.,color='#192b45',alpha=.28,zorder=3):
        value=state(value,model,observer,offsets);step=_number(step)
        if not 1<=step<=30:raise ValueError('Nightshade step must be 1..30 geographic degrees')
        nx,ny=math.ceil(360/step),math.ceil(180/step)
        self.lon=tuple(-180+360*i/nx for i in range(nx+1));self.lat=tuple(-90+180*j/ny for j in range(ny+1))
        self.state=value;self.model=model or SolarModel();self.observer=value.observer;self.offsets=offsets
        rows=self._rows(value)
        super().__init__('mesh',(self.lon,self.lat,rows),style_dict(dict(edgecolor='none',linewidth=0,alpha=alpha,zorder=zorder)),{})
        self.set_cmap(ListedColormap([color]));self.set_norm(Normalize(0,1));self.set_array(rows)
    def _visible_cell(self,projection,west,east,south,north):
        if projection.name!='orthographic':return True
        # Exact extrema of dot(view_normal, geographic cell) on this bounded
        # lon/lat rectangle. A cell behind/tangent to the limb has zero visible
        # area; do not feed its coincident horizon edges into polygon topology.
        longitudes=[west,east]
        first=math.ceil((west-projection.central_longitude)/360)
        last=math.floor((east-projection.central_longitude)/360)
        longitudes.extend(projection.central_longitude+360*k for k in range(first,last+1))
        center=math.radians(projection.central_latitude);maximum=-1.
        for lon in longitudes:
            a=math.cos(center)*math.cos(math.radians(lon-projection.central_longitude));b=math.sin(center)
            angles=[math.radians(south),math.radians(north)]
            critical=math.atan2(b,a)
            angles.extend(t for t in (critical,critical-math.pi,critical+math.pi) if angles[0]<=t<=angles[1])
            maximum=max(maximum,*(a*math.cos(t)+b*math.sin(t) for t in angles))
        return maximum>1e-12
    def _rows(self,value):
        if not isinstance(value,SunPosition):raise TypeError('Nightshade requires calculated SunPosition')
        n=value.fixed_direction
        def cell(lon,lat):
            l,p=math.radians(lon),math.radians(lat)
            point=(math.cos(p)*math.cos(l),math.cos(p)*math.sin(l),math.sin(p))
            return 1. if sum(a*b for a,b in zip(n,point))<=0 else None
        return tuple(tuple(cell((a+b)/2,(c+d)/2) for a,b in zip(self.lon,self.lon[1:])) for c,d in zip(self.lat,self.lat[1:]))
    def _prepare_solar(self,value):
        if not isinstance(value,SunPosition):raise TypeError('Nightshade requires calculated SunPosition')
        if value.observer!=self.observer:raise ValueError('Solar updates must preserve observer identity')
        return self._rows(value)
    @artist_mutation
    def set_position(self,value):
        rows=self._prepare_solar(value);self.set_array(rows);self.state=value
    def set_time(self,instant,*,offsets=None):
        return self.set_position(self.model.position(instant,self.observer,offsets=self.offsets if offsets is None else offsets))
    def get_position(self):return self.state


def _disc(value,radius,size):
    if value.observer is None:raise ValueError('A local sky marker requires an observer')
    if radius<=0 or not 0<size<radius:raise ValueError('Require positive visual radius and smaller symbol radius')
    direction=SunDirection(value.azimuth or 0,value.elevation,value.observer).lighting_direction
    a=_unit(_cross(direction,(0,0,1) if abs(direction[2])<.9 else (1,0,0)));b=_cross(direction,a)
    center=tuple(radius*v for v in direction);vertices=[center]
    for i in range(24):
        angle=2*math.pi*i/24;vertices.append(tuple(center[k]+size*(a[k]*math.cos(angle)+b[k]*math.sin(angle)) for k in range(3)))
    return Mesh(tuple(vertices),tuple((0,i+1,(i+1)%24+1) for i in range(24)))


class SkySunArtist(SurfaceArtist):
    _solar_artist=True
    def __init__(self,value,*,model=None,observer=None,offsets=None,visual_radius=1000.,symbol_radius=40.,color='#eea52d'):
        value=state(value,model,observer,offsets)
        self.visual_radius,self.symbol_radius=_number(visual_radius),_number(symbol_radius)
        mesh=_disc(value,self.visual_radius,self.symbol_radius)
        self.state,self.model,self.observer,self.offsets=value,model or SolarModel(),value.observer,offsets
        super().__init__(mesh,color=color,shade=False,elevation_reference='visual sky sphere, not physical Sun distance')
    def _prepare_solar(self,value):
        if not isinstance(value,(SunPosition,SunDirection)) or value.observer!=self.observer:raise ValueError('Sky updates require the same observer')
        return _disc(value,self.visual_radius,self.symbol_radius)
    @artist_mutation
    def set_position(self,value):
        mesh=self._prepare_solar(value);mapping=self._prepare_mapping({},array=[p[2] for p in mesh.vertices])
        self.mesh,self.state=mesh,value;self._apply_mapping(mapping)
    def set_time(self,instant,*,offsets=None):
        return self.set_position(self.model.position(instant,self.observer,offsets=self.offsets if offsets is None else offsets))
    def get_position(self):return self.state


def attach_sun(axes,value,**options):
    if getattr(axes,'_terrain3d',False):
        artist=SkySunArtist(value,**options);frame=LocalFrame(artist.observer.longitude,artist.observer.latitude)
        if axes.layers and axes.local_frame!=frame:raise ValueError('Sky diagram and terrain must use the same observer LocalFrame')
        axes._attach(artist);axes.local_frame=frame;return artist
    artist=SunArtist(value,**options);artist._axes=axes;artist._bind_parent(axes);axes.layers.append(artist);axes._changed();return artist


def attach_night(axes,value,**options):
    if getattr(axes,'_terrain3d',False):raise ValueError('Nightshade is a geographic map layer, not a local 3D plane')
    artist=SolarNightshade(value,**options);artist._axes=axes;artist._bind_parent(axes);axes.layers.append(artist);axes._changed();return artist


def attach_path(axes,path,*,visual_radius=1000.,width=8.,color='#d77924'):
    if not isinstance(path,SolarPath) or not getattr(axes,'_terrain3d',False):raise ValueError('Apparent sky paths require a SolarPath and 3D ENU axes')
    frame=LocalFrame(path.observer.longitude,path.observer.latitude)
    if axes.layers and axes.local_frame!=frame:raise ValueError('Sky path and terrain require the same observer LocalFrame')
    artist=SurfaceArtist(path.mesh(visual_radius=visual_radius,width=width),color=color,shade=False,elevation_reference='visual sky sphere')
    result=axes._attach(artist);axes.local_frame=frame;return result


class SolarBinding:
    """Prevalidate solar states and observer identity before frame mutation."""
    def __init__(self,series,artist,*,scale='global',norm=None):
        if scale!='global' or norm is not None:raise ValueError('Solar direction bindings have no scalar norm; use global/default')
        if artist.axes is None:raise ValueError('Solar binding requires an attached Artist')
        self.series,self.artist=series,artist;self.index=None
        for frame in series:
            artist._prepare_solar(frame.data)
            if series.kind=='date' and isinstance(frame.data,SunPosition) and frame.time!=frame.data.instant.utc:
                raise ValueError('Solar frame date must match its calculated instant')
    def apply(self,index):
        if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<len(self.series):raise IndexError('Invalid solar frame index')
        if self.artist.axes is None:raise RuntimeError('Solar Artist was removed')
        self.artist.set_position(self.series[index].data);self.index=index;return self.artist
