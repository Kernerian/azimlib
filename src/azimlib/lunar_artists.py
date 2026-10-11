"""Own optional lunar handles and globally framed Earth--Moon surfaces."""
import math
from .lunar import LunarModel,MoonPosition,MoonDirection,LunarPath,MOON_RADIUS_M,_number,_unit,_dot,_length
from .geometry import Geometry,Feature,FeatureCollection
from .layers import Layer
from .styles import style_dict,text_style
from .artist import artist_mutation
from .terrain_axes import SurfaceArtist
from .terrain3d import Mesh,transform_point
from ._frames import EARTH_FIXED
from .colors import to_rgba

def state(value,model=None,observer=None,offsets=None):
    if isinstance(value,(MoonPosition,MoonDirection)):
        if observer is not None and observer!=value.observer:raise ValueError('Lunar observer differs from requested observer')
        return value
    return (model or LunarModel()).position(value,observer,offsets=offsets)

def collection(value):
    properties={'lunar_role':'point','frame':'earth-fixed','distance_unit':'metre','calculated':isinstance(value,MoonPosition)}
    if isinstance(value,MoonPosition):properties.update(utc=value.instant.utc.isoformat(),distance_m=value.distance_m,illuminated_fraction=value.illuminated_fraction,model=value.model)
    else:properties['slant_range_m']=value.distance_m
    return FeatureCollection((Feature(Geometry('Point',value.sublunar),properties,'moon'),))

class LunarHandle:
    _lunar_artist=True
    def get_position(self):return self.state
    def set_time(self,instant,*,offsets=None):return self.set_position(self.model.position(instant,self.observer,offsets=self.offsets if offsets is None else offsets))
    def set_manual(self,azimuth,elevation,distance_m):return self.set_position(MoonDirection(azimuth,elevation,distance_m,self.observer))
    def _check(self,value):
        if not isinstance(value,(MoonPosition,MoonDirection)):raise TypeError('Require MoonPosition or finite manual MoonDirection')
        if value.observer!=self.observer:raise ValueError('Lunar updates must preserve observer identity')

class MoonArtist(LunarHandle,Layer):
    def __init__(self,value,*,model=None,observer=None,offsets=None,annotation=None,annotation_style=None,**style):
        value=state(value,model,observer,offsets)
        self.state=value;self.observer=value.observer;self.model=model or LunarModel();self.offsets=offsets
        self.role='point';self.annotation=None if annotation is None else str(annotation)
        self.annotation_style=dict(annotation_style or {});text_style(self.annotation_style)
        super().__init__('geometry',collection(value),style_dict({'color':'#77869a','marker':'o','markersize':8,'zorder':6,**style}),dict(fit=False))
    @property
    def annotation_coordinate(self):return self.state.sublunar
    def _prepare_lunar(self,value):self._check(value);return collection(value)
    @artist_mutation
    def set_position(self,value):
        data=self._prepare_lunar(value);self.state,self.data=value,data
    @artist_mutation
    def set_annotation(self,text):self.annotation=None if text is None else str(text)

def _sphere(center,radii,segments=40,rings=20):
    """Indexed ellipsoid with separate polar caps and outward triangles."""
    vertices=[tuple(center[k]+(radii[2] if k==2 else 0) for k in range(3))];normals=[(0,0,1)];triangles=[]
    for j in range(1,rings):
        p=math.pi*j/rings
        for i in range(segments):
            a=2*math.pi*i/segments;n=(math.sin(p)*math.cos(a),math.sin(p)*math.sin(a),math.cos(p))
            vertices.append(tuple(center[k]+radii[k]*n[k] for k in range(3)))
            normals.append(_unit(tuple(n[k]/radii[k] for k in range(3))))
    south=len(vertices);vertices.append((center[0],center[1],center[2]-radii[2]));normals.append((0,0,-1))
    for i in range(segments):triangles.append((0,1+i,1+(i+1)%segments))
    for j in range(rings-2):
        for i in range(segments):
            a=1+j*segments+i;b=1+j*segments+(i+1)%segments;c=a+segments;d=b+segments
            triangles.extend(((a,c,b),(b,c,d)))
    for i in range(segments):triangles.append((south,south-segments+(i+1)%segments,south-segments+i))
    return vertices,triangles,normals

class EarthMoonArtist(LunarHandle,SurfaceArtist):
    """Earth-fixed metres; visual scales never enter phase/light calculations.

    Own depth painter handles body occlusion. Optional finite-source geometry
    supplies physical shadow fractions; precise event prediction is unsupported.
    A manual target has no inferred Sun; it is unlit unless calculated separately.
    """
    def __init__(self,value,*,model=None,observer=None,offsets=None,include_earth=True,distance_scale=1.,moon_radius_scale=1.,earth_color='#47869b',moon_color='#c3c5ca',ambient=.12,shade=True):
        value=state(value,model,observer,offsets)
        self.observer=value.observer;self.model=model or LunarModel();self.offsets=offsets
        self.include_earth=bool(include_earth);self.earth_color=self._color(earth_color);self.moon_color=self._color(moon_color)
        self.ambient=_number(ambient)
        if not 0<=self.ambient<=1:raise ValueError('Ambient fraction must lie in 0..1')
        mesh,normals,bodies,scale,rscale=self._geometry(value,distance_scale,moon_radius_scale)
        self.state=value;self.distance_scale=scale;self.moon_radius_scale=rscale;self._normals=normals;self._bodies=bodies
        super().__init__(mesh,color=moon_color,shade=shade,elevation_reference='Earth-fixed metre coordinates; declared visual scales')
        self.eclipse_geometry=None;self._allow_approximate_eclipses=False
    @staticmethod
    def _color(value):
        c=to_rgba(value)
        if c[3]!=1:raise ValueError('Earth--Moon bodies require opaque colors')
        return c
    def _geometry(self,value,scale,rscale):
        self._check(value);scale,rscale=_number(scale),_number(rscale)
        if not 1e-4<=scale<=1e4 or not 1e-4<=rscale<=1e4:raise ValueError('Visual scales must lie in 1e-4..1e4')
        center=tuple(v*scale for v in value.fixed.xyz);radius=MOON_RADIUS_M*rscale
        if self.include_earth and _length(center)<=6378137.+radius:raise ValueError('Visual body volumes intersect; increase distance scale or reduce radius scale')
        vertices=[];normals=[];triangles=[];bodies=[]
        for body,c,r in ((('earth',(0,0,0),(6378137.,6378137.,6356752.314245)),) if self.include_earth else ())+(('moon',center,(radius,)*3),):
            vs,ts,ns=_sphere(c,r);offset=len(vertices);vertices.extend(vs);normals.extend(ns)
            triangles.extend(tuple(i+offset for i in face) for face in ts);bodies.extend([body]*len(ts))
        return Mesh(tuple(vertices),tuple(triangles)),tuple(normals),tuple(bodies),scale,rscale
    @property
    def physical_centers(self):return {'earth':(0.,0.,0.),'moon':self.state.fixed.xyz}
    @property
    def display_centers(self):return {'earth':(0.,0.,0.),'moon':tuple(v*self.distance_scale for v in self.state.fixed.xyz)}
    def _prepare_lunar(self,value):
        if self.eclipse_geometry is not None and value is not self.state and not isinstance(value,MoonPosition):raise ValueError('Disable eclipse geometry before a manual lunar update')
        return self._geometry(value,self.distance_scale,self.moon_radius_scale)
    def _install(self,value,prepared):
        mesh,normals,bodies,scale,rscale=prepared
        geometry=None
        if self.eclipse_geometry is not None and value is self.state:geometry=self.eclipse_geometry
        elif self.eclipse_geometry is not None:
            from .eclipse import EclipseGeometry
            if not isinstance(value,MoonPosition):raise ValueError('Disable eclipse geometry before switching to a manual lunar state')
            geometry=EclipseGeometry.from_moon(value);geometry.require_visual_permission(self._allow_approximate_eclipses)
        mapping=self._prepare_mapping({},array=[v[2] for v in mesh.vertices])
        self.mesh,self._normals,self._bodies,self.state,self.distance_scale,self.moon_radius_scale=mesh,normals,bodies,value,scale,rscale
        self.eclipse_geometry=geometry
        self._apply_mapping(mapping)
    @artist_mutation
    def set_position(self,value):self._install(value,self._prepare_lunar(value))
    @artist_mutation
    def set_scales(self,*,distance_scale=None,moon_radius_scale=None):
        self._install(self.state,self._geometry(self.state,self.distance_scale if distance_scale is None else distance_scale,self.moon_radius_scale if moon_radius_scale is None else moon_radius_scale))
    @artist_mutation
    def set_color(self,value):self.moon_color=self._color(value)
    @artist_mutation
    def set_eclipse_geometry(self,geometry,*,allow_approximate=False):
        if geometry is not None:
            from .eclipse import EclipseGeometry
            if not isinstance(geometry,EclipseGeometry):raise TypeError('Require EclipseGeometry or None')
            geometry.require_visual_permission(allow_approximate)
            if math.dist(geometry.moon.center.xyz,self.state.fixed.xyz)>1e-5:raise ValueError('Eclipse geometry Moon differs from physical body center')
            if isinstance(self.state,MoonPosition) and geometry.instant!=self.state.instant:raise ValueError('Eclipse geometry instant differs from lunar instant')
            if abs(geometry.moon.radius_m-MOON_RADIUS_M)>1e-6:raise ValueError('Eclipse sphere radius differs from physical Moon radius')
        self.eclipse_geometry=geometry;self._allow_approximate_eclipses=bool(allow_approximate)
    def set_texture(self,texture,uv=None):raise ValueError('Earth--Moon bodies do not support a shared texture; use body colors')
    def faces(self,camera,bounds,aspect,exaggeration,*,with_uv=False):
        matrix=camera.matrix(bounds,aspect,exaggeration);projected=tuple(transform_point(matrix,v) for v in self.mesh.vertices);result=[]
        directions=None
        sun=self.eclipse_geometry.sun.center.xyz if self.eclipse_geometry is not None else self.state.sun.fixed.xyz if isinstance(self.state,MoonPosition) else None
        if sun is not None:
            directions={body:_unit(tuple(s-c for s,c in zip(sun,center))) for body,center in self.physical_centers.items()}
        for face,body in zip(self.mesh.triangles,self._bodies):
            c=self.earth_color if body=='earth' else self.moon_color;strength=1.
            if self.shade and directions is not None:
                n=_unit(tuple(sum(self._normals[i][k] for i in face) for k in range(3)))
                visibility=1.
                if self.eclipse_geometry is not None:
                    from ._frames import Coordinates
                    if body=='moon':point=tuple(self.state.fixed.xyz[k]+MOON_RADIUS_M*n[k] for k in range(3))
                    else:point=tuple(sum(self.mesh.vertices[i][k] for i in face)/3 for k in range(3))
                    visibility=self.eclipse_geometry.at(Coordinates(point,EARTH_FIXED),occulter='earth' if body=='moon' else 'moon').visible_fraction
                strength=self.ambient+(1-self.ambient)*max(0,_dot(n,directions[body]))*visibility
            rgba=tuple(round(x*strength*255) for x in c[:3])+(255,)
            item=(tuple(projected[i] for i in face),rgba);result.append((*item,None) if with_uv else item)
        return result

def attach_moon(axes,value,**options):
    if getattr(axes,'_terrain3d',False):return attach_earth_moon(axes,value,include_earth=False,**options)
    artist=MoonArtist(value,**options);artist._axes=axes;artist._bind_parent(axes);axes.layers.append(artist);axes._changed();return artist

def attach_earth_moon(axes,value,**options):
    if not getattr(axes,'_terrain3d',False):raise ValueError('Earth--Moon composition requires projection="3d"')
    if axes.layers and axes.local_frame!=EARTH_FIXED:raise ValueError('Earth--Moon bodies require global Earth-fixed metres; cannot mix local terrain')
    if axes.vertical_exaggeration!=1:raise ValueError('Global bodies require vertical_exaggeration=1')
    artist=EarthMoonArtist(value,**options);axes._attach(artist);axes.local_frame=EARTH_FIXED;return artist

def attach_path(axes,path,*,distance_scale=1.,width=500000.,color='#a576bf',**style):
    if not isinstance(path,LunarPath):raise TypeError('Require calculated LunarPath')
    if getattr(axes,'_terrain3d',False):
        if style:raise ValueError('3D trajectory supports color, distance_scale and metre width')
        if axes.layers and axes.local_frame!=EARTH_FIXED:raise ValueError('Trajectory requires Earth-fixed frame')
        if axes.vertical_exaggeration!=1:raise ValueError('Global trajectory requires vertical_exaggeration=1')
        artist=SurfaceArtist(path.mesh(distance_scale=distance_scale,width=width),color=color,shade=False,elevation_reference='Calculated Earth-fixed lunar trajectory, not an inertial orbit')
        axes._attach(artist);axes.local_frame=EARTH_FIXED;return artist
    if distance_scale!=1 or width!=500000:raise ValueError('3D trajectory scales do not apply to geographic groundtracks')
    return axes.geojson(FeatureCollection((Feature(path.groundtrack,{'frame':'earth-fixed','calculated':True}),)),color=color,fit=False,**style)

class LunarBinding:
    def __init__(self,series,artist,*,scale='global',norm=None):
        if scale!='global' or norm is not None:raise ValueError('Lunar states have no scalar normalization')
        if artist.axes is None:raise ValueError('Lunar binding requires an attached Artist')
        self.series,self.artist,self.index=series,artist,None
        for frame in series:
            artist._prepare_lunar(frame.data)
            if series.kind=='date' and isinstance(frame.data,MoonPosition) and frame.time!=frame.data.instant.utc:raise ValueError('Lunar frame date must match its instant')
    def apply(self,index):
        if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<len(self.series):raise IndexError('Invalid lunar frame index')
        if self.artist.axes is None:raise RuntimeError('Lunar Artist was removed')
        self.artist.set_position(self.series[index].data);self.index=index;return self.artist
