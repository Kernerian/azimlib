"""Own bounded physical surface illumination and opaque triangle shadows.

Physical metres before camera exaggeration. Shared CPU/GPU scene preparation;
finite-disk directions are deterministic quadrature, not Monte Carlo transport.
"""
from dataclasses import dataclass
import math
from .solar import SunPosition,SunDirection,SolarModel,_unit,_cross
from .terrain3d import LocalFrame,dot,finite
from ._frames import Observer
from .artist import Artist,artist_mutation

def _sub(a,b):return tuple(x-y for x,y in zip(a,b))
def _center(points):return tuple(sum(p[k] for p in points)/len(points) for k in range(3))

@dataclass(frozen=True)
class ShadowBudget:
    max_triangles:int=20000
    max_rays:int=500000
    max_triangle_tests:int=4000000
    def __post_init__(self):
        for key,maximum in (('max_triangles',20000),('max_rays',2000000),('max_triangle_tests',16000000)):
            v=getattr(self,key)
            if isinstance(v,bool) or not isinstance(v,int) or not 1<=v<=maximum:raise ValueError('Invalid bounded shadow budget '+key)

class ShadowIndex:
    """Independent median BVH, slab intervals and double-sided ray triangles."""
    def __init__(self,triangles,budget,bias):
        if len(triangles)>budget.max_triangles:raise ValueError('Shadow triangle budget exceeded')
        self.triangles=tuple(triangles);self.budget=budget;self.bias=bias;self.rays=0;self.tests=0
        def build(ids):
            box=tuple(v for k in range(3) for v in (min(p[k] for i in ids for p in self.triangles[i][1]),max(p[k] for i in ids for p in self.triangles[i][1])))
            if len(ids)<=8:return box,ids,None,None
            axis=max(range(3),key=lambda k:box[2*k+1]-box[2*k]);ids=tuple(sorted(ids,key=lambda i:_center(self.triangles[i][1])[axis]));mid=len(ids)//2
            return box,(),build(ids[:mid]),build(ids[mid:])
        self.tree=build(tuple(range(len(triangles)))) if triangles else None
    def reset(self):self.rays=self.tests=0
    def blocked(self,origin,direction,maximum=math.inf,ignore=None):
        self.rays+=1
        if self.rays>self.budget.max_rays:raise ValueError('Shadow ray budget exceeded; coarsen scene/sampling explicitly')
        def intersects(box):
            lo,hi=self.bias,maximum
            for k in range(3):
                if abs(direction[k])<1e-15:
                    if not box[k*2]-self.bias<=origin[k]<=box[k*2+1]+self.bias:return False
                else:
                    a=(box[k*2]-origin[k])/direction[k];b=(box[k*2+1]-origin[k])/direction[k]
                    lo=max(lo,min(a,b));hi=min(hi,max(a,b))
            return hi>=lo
        stack=[] if self.tree is None else [self.tree]
        while stack:
            box,ids,left,right=stack.pop()
            if not intersects(box):continue
            if left is not None:stack.extend((left,right));continue
            for i in ids:
                identity,points=self.triangles[i]
                if identity==ignore:continue
                self.tests+=1
                if self.tests>self.budget.max_triangle_tests:raise ValueError('Shadow intersection budget exceeded')
                a,b,c=points;e1,e2=_sub(b,a),_sub(c,a);p=_cross(direction,e2);det=dot(e1,p)
                # Scale-aware angular threshold, separate from metre bias.
                if abs(det)<=1e-12*math.sqrt(dot(e1,e1)*dot(e2,e2)):continue
                tvec=_sub(origin,a);u=dot(tvec,p)/det
                if not -1e-12<=u<=1+1e-12:continue
                q=_cross(tvec,e1);v=dot(direction,q)/det
                if v< -1e-12 or u+v>1+1e-12:continue
                t=dot(e2,q)/det
                if self.bias<t<maximum-self.bias:return True
        return False

def subdivide(points,max_edge,depth=0):
    if max_edge is None or max(math.dist(a,b) for a,b in zip(points,points[1:]+points[:1]))<=max_edge:return (points,)
    if depth>=12:raise ValueError('Shadow refinement exceeds twelve levels')
    a,b,c=points;ab,bc,ca=(_center(p) for p in ((a,b),(b,c),(c,a)))
    return tuple(t for p in ((a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)) for t in subdivide(p,max_edge,depth+1))

class SolarLighting(Artist):
    """Optional editable light for one explicit metre ENU frame."""
    _lighting_artist=True
    def __init__(self,axes,value,*,frame,model=None,offsets=None,ambient=.25,diffuse=.75,shadows=True,samples=1,angular_radius=None,bias_m=.001,max_edge_m=None,budget=None):
        super().__init__(axes);self._axes=axes;self.frame=frame;self.model=model if model is not None else self._default_model();self.offsets=offsets
        self._validate_frame(frame)
        self.ambient,self.diffuse=finite(ambient),finite(diffuse)
        if not 0<=self.ambient<=1 or not 0<=self.diffuse<=1 or self.ambient+self.diffuse>1:raise ValueError('Ambient/diffuse require nonnegative total <=1')
        if isinstance(samples,bool) or not isinstance(samples,int) or not 1<=samples<=64:raise ValueError('Solar disk samples must be 1..64')
        self.shadows=bool(shadows);self.samples=samples;self.angular_radius=None if angular_radius is None else finite(angular_radius)
        if self.angular_radius is not None and not 0<=self.angular_radius<=2:raise ValueError('Solar angular radius must be 0..2 degrees')
        self.bias_m=finite(bias_m);self.max_edge_m=None if max_edge_m is None else finite(max_edge_m)
        if self.bias_m<=0 or self.max_edge_m is not None and self.max_edge_m<=self.bias_m:raise ValueError('Require positive metre bias and larger refinement edge')
        self.budget=budget or ShadowBudget()
        if not isinstance(self.budget,ShadowBudget):raise TypeError('Require ShadowBudget')
        self.visible=True;self._key=None;self._pieces={};self._factors={};self._index=None;self._volumes=[];self.geometry_builds=0;self.lighting_builds=0
        self.state=self._prepare_lighting(value);self._state_key=None
    def _default_model(self):return SolarModel()
    def _validate_frame(self,frame):
        if not isinstance(frame,LocalFrame):raise TypeError("Surface solar lighting requires an explicit LocalFrame")
    @property
    def axes(self):return self._axes
    def _prepare_lighting(self,value):
        if not isinstance(value,(SunPosition,SunDirection)):raise TypeError('Require calculated SunPosition or manual SunDirection')
        if value.observer is not None and (value.observer.longitude,value.observer.latitude)!=(self.frame.lon,self.frame.lat):raise ValueError('Light observer and ENU frame origins differ')
        if isinstance(value,SunDirection) and self.angular_radius is None:raise ValueError('Manual direction requires explicit angular_radius, including zero')
        return value
    def get_position(self):return self.state
    @artist_mutation
    def set_position(self,value):
        value=self._prepare_lighting(value);self.state=value;self._state_key=None
        for artist,steps,previous in self._volumes:
            if artist.axes is self.axes:artist.set_light(self.volume_light(shadow_steps=steps) if self.visible else previous)
    def set_time(self,instant,*,offsets=None):return self.set_position(self.model.position(instant,Observer(self.frame.lon,self.frame.lat),offsets=self.offsets if offsets is None else offsets))
    def get_visible(self):return self.visible
    @artist_mutation
    def set_visible(self,value):
        self.visible=bool(value)
        for artist,steps,previous in self._volumes:
            if artist.axes is self.axes:artist.set_light(self.volume_light(shadow_steps=steps) if self.visible else previous)
    def remove(self):
        for artist,steps,previous in self._volumes:
            if artist.axes is self.axes:artist.set_light(previous)
        if self.axes is not None:self.axes._solar_lighting=None;self.axes._changed()
        self._axes=None;self._bind_parent(None)
    @property
    def direction(self):
        if isinstance(self.state,SunDirection):return self.state.lighting_direction
        return _unit(Observer(self.frame.lon,self.frame.lat).to_local.apply(self.state.fixed).xyz)
    @property
    def semidiameter(self):return self.angular_radius if self.angular_radius is not None else self.state.semidiameter_degrees
    def volume_light(self,*,shadow_steps=0):
        from .volume_render import VolumeLight
        return VolumeLight(self.direction,self.ambient,self.diffuse,shadow_steps)
    def bind_volume(self,artist,*,shadow_steps=0):
        from .volume_artist import VolumeArtist
        if not isinstance(artist,VolumeArtist) or artist.axes is not self.axes or artist.field.frame!=self.frame:raise ValueError('Volume light target must share axes and explicit ENU frame')
        if any(a is artist for a,_,_ in self._volumes):raise ValueError('Volume already bound to this light')
        light=self.volume_light(shadow_steps=shadow_steps);previous=artist.light;artist.set_light(light if self.visible else previous);self._volumes.append((artist,shadow_steps,previous));return artist
    def _directions(self):
        n=self.direction
        if self.samples==1 or self.semidiameter==0:return (n,)
        a=_unit(_cross(n,(0,0,1) if abs(n[2])<.9 else (1,0,0)));b=_cross(n,a);radius=math.tan(math.radians(self.semidiameter))
        return tuple(_unit(tuple(n[k]+radius*math.sqrt((i+.5)/self.samples)*(a[k]*math.cos(i*math.pi*(3-math.sqrt(5)))+b[k]*math.sin(i*math.pi*(3-math.sqrt(5)))) for k in range(3))) for i in range(self.samples))
    def prepare(self,artists):
        from .terrain_axes import SurfaceArtist
        if any(type(a) is not SurfaceArtist for a in artists):raise ValueError('ENU surface light cannot illuminate global/sky body Artists')
        if self.shadows and any(a.get_texture() is not None for a in artists):raise ValueError('Masked textured shadow occluders are not supported; disable shadows explicitly')
        from .colors import to_rgba
        materials={}
        for a in artists:
            colors=[]
            for face in a.mesh.triangles:
                v=[a._array[i] for i in face]
                colors.append(a.color if a.color is not None else None if any(x is None for x in v) else to_rgba(a.to_color(sum(v)/3)))
            materials[id(a)]=tuple(colors)
        key=(self.shadows,self.max_edge_m,self.bias_m,self.budget,tuple((id(a),id(a.mesh),a.shade,materials[id(a)]) for a in artists))
        if key!=self._key:
            triangles=[];pieces={};count=0
            for artist in artists:
                result=[]
                for j,face in enumerate(artist.mesh.triangles):
                    color=materials[id(artist)][j]
                    if color is None:continue
                    if not color[3]:continue
                    if color[3]!=1:raise ValueError('Solar shadows require opaque or hidden surfaces')
                    points=tuple(artist.mesh.vertices[i] for i in face);normal=_cross(_sub(points[1],points[0]),_sub(points[2],points[0]))
                    if not any(normal):continue
                    normal=_unit(normal)
                    edge=self.max_edge_m if self.shadows and artist.shade else None
                    if edge is not None:
                        longest=max(math.dist(a,b) for a,b in zip(points,points[1:]+points[:1]))
                        levels=max(0,math.ceil(math.log2(longest/edge))) if longest else 0
                        if levels>12 or count+4**levels>self.budget.max_triangles:raise ValueError('Shadow refinement exceeds budget before allocation; increase edge length')
                    subfaces=subdivide(points,edge)
                    count+=len(subfaces)
                    if count>self.budget.max_triangles:raise ValueError('Refined shadow mesh exceeds triangle budget; increase edge length explicitly')
                    for k,p in enumerate(subfaces):
                        identity=(id(artist),j,k);result.append((j,p,normal,identity));triangles.append((identity,p))
                pieces[id(artist)]=tuple(result)
            self._index=ShadowIndex(triangles,self.budget,self.bias_m);self._pieces=pieces;self._key=key;self._state_key=None;self.geometry_builds+=1
        statekey=(self.state,self.shadows,self.samples,self.semidiameter,self.ambient,self.diffuse,tuple((id(a),a.shade) for a in artists))
        if statekey!=self._state_key:
            self._index.reset();directions=self._directions();factors={}
            for artist in artists:
                result=[]
                for j,points,normal,identity in self._pieces[id(artist)]:
                    amount=0.;center=_center(points)
                    for direction in directions:
                        incidence=max(0,dot(normal,direction))
                        if incidence and self.shadows:
                            origin=tuple(center[k]+normal[k]*self.bias_m for k in range(3))
                            if self._index.blocked(origin,direction,ignore=identity):incidence=0.
                        amount+=incidence/len(directions)
                    result.append(1. if not artist.shade else self.ambient+self.diffuse*amount)
                factors[id(artist)]=tuple(result)
            self._factors=factors;self._state_key=statekey;self.lighting_builds+=1
        return self
    def faces(self,artist,camera,bounds,aspect,exaggeration,*,with_uv=False):
        from .terrain3d import transform_point
        from .colors import to_rgba
        matrix=camera.matrix(bounds,aspect,exaggeration);output=[]
        for (j,points,normal,identity),factor in zip(self._pieces[id(artist)],self._factors[id(artist)]):
            values=[artist._array[i] for i in artist.mesh.triangles[j]];c=artist.color if artist.color is not None else to_rgba(artist.to_color(sum(values)/3))
            rgba=tuple(round(v*factor*255) for v in c[:3])+(255,)
            result=(tuple(transform_point(matrix,p) for p in points),rgba)
            if with_uv:
                if artist.get_texture() is not None and self.max_edge_m is not None:raise ValueError('Refined textured faces require explicit UV subdivision, unsupported')
                uv=None if artist.get_texture_uv() is None else tuple(artist.get_texture_uv()[i] for i in artist.mesh.triangles[j]);result=(*result,uv)
            output.append(result)
        return output

def attach_light(axes,value,*,frame=None,**options):
    if not getattr(axes,'_terrain3d',False):raise ValueError('solar_light requires 3D axes')
    if getattr(axes,'_solar_lighting',None) is not None:raise ValueError('Remove the existing solar light before attaching another')
    frame=axes.local_frame if frame is None else frame
    if axes.local_frame is not None and axes.local_frame!=frame:raise ValueError('Solar light cannot silently change the axes frame')
    light=SolarLighting(axes,value,frame=frame,**options);axes.local_frame=frame;axes._solar_lighting=light;axes._changed();return light

class LightingBinding:
    def __init__(self,series,artist,*,scale='global',norm=None):
        if scale!='global' or norm is not None or artist.axes is None:raise ValueError('Light binding requires an attached handle and no scalar norm')
        self.series,self.artist,self.index=series,artist,None
        for frame in series:
            artist._prepare_lighting(frame.data)
            if series.kind=='date' and isinstance(frame.data,SunPosition) and frame.time!=frame.data.instant.utc:raise ValueError('Light frame date must match solar instant')
    def apply(self,index):
        if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<len(self.series):raise IndexError('Invalid lighting frame index')
        if self.artist.axes is None:raise RuntimeError('Light was removed')
        self.artist.set_position(self.series[index].data);self.index=index;return self.artist
