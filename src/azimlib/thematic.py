"""Context-bound thematic definitions and owned Artists over existing Layers."""
from dataclasses import dataclass,replace,field
from functools import cached_property
import math
from .geometry import Geometry,Feature,FeatureCollection,_number,wrap_longitude
from .planetary import PlanetaryContext
from .bodies import EARTH,LongitudeConvention,UnsupportedBodyOperation
from .geodesy import DEGREE,METRE
from .layers import Layer
from .artist import artist_mutation
from .styles import style_dict
from .thematic_assets import SymbolDefinition,SymbolPart,AssetSource,get_symbol,symbol_catalog


def _context(c):
    if not isinstance(c,PlanetaryContext):raise TypeError('Require explicit PlanetaryContext')
    if c.angle_unit!=DEGREE or c.longitude!=LongitudeConvention() or c.prime_meridian!=0:raise UnsupportedBodyOperation('Thematic plotting requires explicit east-positive signed degrees and zero meridian offset')
    return c

def _points(values,context,limit=4097,*,allow_unwrapped=False):
    _context(context)
    if not hasattr(values,'__len__') or not 1<=len(values)<=limit:raise ValueError('Position resource budget exceeded')
    result=[]
    for p in values:
        if len(p)!=2:raise ValueError('Require longitude/latitude pairs')
        lon,lat=map(_number,p);context.canonical(wrap_longitude(lon) if allow_unwrapped else lon,lat);result.append((lon,lat))
    return tuple(result)

def _unwrap(points):
    out=[points[0]]
    for lon,lat in points[1:]:out.append((out[-1][0]+wrap_longitude(lon-out[-1][0]),lat))
    if max(x for x,y in out)-min(x for x,y in out)>360:raise UnsupportedBodyOperation('Multi-turn angular paths need explicit splitting')
    return tuple(out)

def _semantic(value):
    if value not in ('decorative','quantitative','uncertainty'):raise ValueError('Declare decorative, quantitative or uncertainty semantics')
    return value

@dataclass(frozen=True)
class RegionDefinition:
    geometry:Geometry
    context:PlanetaryContext
    category:str=''
    semantics:str='decorative'
    meaning:str=''
    def __post_init__(self):
        _context(self.context);_semantic(self.semantics)
        if not isinstance(self.geometry,Geometry) or self.geometry.type not in ('Polygon','MultiPolygon'):raise TypeError('Thematic regions require Polygon/MultiPolygon')
        if any(not isinstance(v,str) for v in (self.category,self.meaning)):raise TypeError('Category/meaning must be strings')
        if self.semantics!='decorative' and not self.meaning.strip():raise ValueError('Quantitative/uncertainty regions require author meaning')
        points=tuple(self.geometry.iter_positions())
        if any(len(p)!=2 for p in points):raise ValueError('Thematic areas use 2D angular coordinates, not implicit altitude')
        if len(points)>2048:raise ValueError('Region topology budget: at most 2048 vertices')
        from .topology import validate_geometry,_unwrap
        polygons=(self.geometry.coordinates,) if self.geometry.type=='Polygon' else self.geometry.coordinates
        for rings in polygons:
            if not rings:continue
            outer=_unwrap(rings[0]);width=max(p[0] for p in outer)-min(p[0] for p in outer)
            if width>=180 or any(abs(p[1])>=90 for r in rings for p in r):raise UnsupportedBodyOperation('Regional angular interiors only: split >=180 degree/pole-touching regions explicitly')
        validate_geometry(self.geometry).raise_if_invalid()
    @classmethod
    def polygon(cls,shell,*,context,holes=(),**metadata):
        def close(r):
            r=tuple(tuple(p) for p in r);return r if not r or r[0]==r[-1] else (*r,r[0])
        return cls(Geometry('Polygon',(close(shell),*(close(r) for r in holes))),context,**metadata)
    def _planar(self):
        from .topology import _unwrap
        polys=(self.geometry.coordinates,) if self.geometry.type=='Polygon' else self.geometry.coordinates
        prepared=[];center=None
        for rings in polys:
            if not rings:continue
            shell=_unwrap(rings[0],center);center=shell[0][0] if center is None else center
            prepared.append((shell,*( _unwrap(r,shell[0][0]) for r in rings[1:])))
        return Geometry('MultiPolygon',tuple(prepared))
    def masked(self,mask):
        if not isinstance(mask,RegionDefinition) or mask.context!=self.context:raise ValueError('Region mask context mismatch')
        a=self._planar();b=mask._planar()
        if not a.coordinates or not b.coordinates:return replace(self,geometry=Geometry('Polygon'))
        center=a.coordinates[0][0][0][0];offset=360*round((center-b.coordinates[0][0][0][0])/360)
        b=Geometry('MultiPolygon',tuple(tuple(tuple((x+offset,y) for x,y in r) for r in p) for p in b.coordinates))
        from .overlay import intersection
        result=intersection(a,b,max_segments=4096,max_pairs=200000,max_edges=16384).geometry
        return replace(self,geometry=_areas(result))

def _areas(g):
    if g.type in ('Polygon','MultiPolygon'):return g
    result=[]
    if g.type=='GeometryCollection':
        for child in g.geometries:
            a=_areas(child)
            if a.type=='Polygon' and a.coordinates:result.append(a.coordinates)
            elif a.type=='MultiPolygon':result.extend(a.coordinates)
    return Geometry('MultiPolygon',tuple(result))

@dataclass(frozen=True)
class LinearGradient:
    start:tuple
    end:tuple
    colors:tuple
    semantics:str
    steps:int=32
    values:tuple | None=None
    unit:str | None=None
    meaning:str=''
    def __post_init__(self):
        _semantic(self.semantics)
        for k in ('start','end'):
            p=tuple(_number(v) for v in getattr(self,k))
            if len(p)!=2:raise ValueError('Gradient coordinates require pairs')
            object.__setattr__(self,k,p)
        if self.start==self.end:raise ValueError('Gradient axis must be nonzero')
        from .colors import to_rgba
        colors=tuple(tuple(to_rgba(c)) for c in self.colors)
        if len(colors)!=2:raise ValueError('LinearGradient requires two endpoint colors')
        object.__setattr__(self,'colors',colors)
        if type(self.steps) is not int or not 2<=self.steps<=128:raise ValueError('Gradient display steps must be 2..128')
        if self.semantics!='decorative':
            if self.values is None or len(self.values)!=2 or not isinstance(self.unit,str) or not self.unit.strip() or not self.meaning.strip():raise ValueError('Declare quantitative/uncertainty endpoints, unit and meaning')
            object.__setattr__(self,'values',tuple(_number(v) for v in self.values))
        elif self.values is not None or self.unit is not None:raise ValueError('Decorative gradient has no scientific values/unit')
    def fraction(self,point):
        dx,dy=(b-a for a,b in zip(self.start,self.end));return max(0.,min(1.,sum((p-a)*v for p,a,v in zip(point,self.start,(dx,dy)))/(dx*dx+dy*dy)))
    def color(self,t):
        t=max(0,min(1,_number(t)));return '#'+''.join(f'{round(255*(a*(1-t)+b*t)):02x}' for a,b in zip(*self.colors))
    def slices(self,region):
        if self.semantics!=region.semantics:raise ValueError('Gradient and region semantics differ')
        g=region._planar();points=tuple(g.iter_positions())
        if not points:return ()
        if max(p[0] for p in points)-min(p[0] for p in points)>=180:raise UnsupportedBodyOperation('A gradient needs one regional angular chart')
        dx,dy=(b-a for a,b in zip(self.start,self.end));length=math.hypot(dx,dy);u=(dx/length,dy/length);v=(-u[1],u[0])
        a=[sum(p*q for p,q in zip(t,u)) for t in points];b=[sum(p*q for p,q in zip(t,v)) for t in points];lo,hi=min(a),max(a);bl,bh=min(b)-1,max(b)+1
        base=sum(p*q for p,q in zip(self.start,u));cuts=sorted(set([lo,hi]+[base+length*i/self.steps for i in range(self.steps+1) if lo<base+length*i/self.steps<hi]))
        from .overlay import intersection
        out=[]
        for low,high in zip(cuts,cuts[1:]):
            ring=tuple((s*u[0]+t*v[0],s*u[1]+t*v[1]) for s,t in ((low,bl),(high,bl),(high,bh),(low,bh),(low,bl)))
            # Clip to a valid angular latitude strip before exact planar overlay.
            from .render_map import _clip_latitude
            ring=_clip_latitude(ring,-89.999999999,89.999999999)
            part=_areas(intersection(g,Geometry('Polygon',(ring,)),max_segments=4096,max_pairs=200000,max_edges=16384).geometry)
            if part.coordinates:out.append((part,self.color((low+high)/2/length-base/length)))
        if sum(len(tuple(g.iter_positions())) for g,c in out)>32768:raise ValueError('Gradient output geometry budget exceeded')
        return tuple(out)

_ROUTE_PROOF=object()

@dataclass(frozen=True)
class CartographicPath:
    points:tuple
    context:PlanetaryContext
    kind:str='editorial'
    interpolation:str='geographic-polyline'
    controls:tuple=()
    physical_length_m:float | None=None
    _proof:object=field(default=None,repr=False,compare=False)
    def __post_init__(self):
        points=_points(self.points,self.context,allow_unwrapped=True)
        if len(points)<2:raise ValueError('Path needs at least two positions')
        if self.kind not in ('editorial','geodesic','network'):raise UnsupportedBodyOperation('Physical/orbital trajectories are reserved to 0.6')
        if self.kind!='editorial' and self._proof is not _ROUTE_PROOF:raise ValueError('Use geodesic/network factories for computed scientific contracts')
        if self.kind=='editorial' and self.physical_length_m is not None:raise ValueError('Editorial geometry is not a physical trajectory')
        if self.physical_length_m is not None and _number(self.physical_length_m)<0:raise ValueError('Invalid physical path length')
        object.__setattr__(self,'points',points);object.__setattr__(self,'controls',tuple(tuple(p) for p in self.controls))
    @classmethod
    def polyline(cls,points,*,context):return cls(_unwrap(_points(points,context)),context)
    @classmethod
    def bezier(cls,controls,*,context,samples=97):
        controls=_unwrap(_points(controls,context))
        if len(controls)!=4:raise ValueError('Cubic Bezier requires four controls')
        _samples(samples);out=[]
        for i in range(samples):
            t=i/(samples-1);q=list(controls)
            while len(q)>1:q=[tuple(a*(1-t)+b*t for a,b in zip(p,r)) for p,r in zip(q,q[1:])]
            out.append(q[0])
        return cls(tuple(out),context,controls=controls,interpolation='geographic-cubic-bezier')
    @classmethod
    def spline(cls,waypoints,*,context,samples_per_segment=25):
        points=_unwrap(_points(waypoints,context,limit=128));_samples(samples_per_segment)
        if len(points)<2 or (len(points)-1)*(samples_per_segment-1)+1>4097:raise ValueError('Spline sample budget exceeded')
        tangents=[tuple((points[min(i+1,len(points)-1)][k]-points[max(0,i-1)][k])/(1 if i in (0,len(points)-1) else 2) for k in (0,1)) for i in range(len(points))];out=[]
        for i,(a,b) in enumerate(zip(points,points[1:])):
            for j in range(samples_per_segment-1):
                t=j/(samples_per_segment-1);h=(2*t**3-3*t*t+1,t**3-2*t*t+t,-2*t**3+3*t*t,t**3-t*t)
                out.append(tuple(h[0]*a[k]+h[1]*tangents[i][k]+h[2]*b[k]+h[3]*tangents[i+1][k] for k in (0,1)))
        out.append(points[-1]);return cls(tuple(out),context,controls=points,interpolation='geographic-cardinal-hermite')
    @classmethod
    def geodesic(cls,waypoints,*,context,samples_per_segment=49):
        from .surfaces import BodySurface
        points=_points(waypoints,context,limit=128);_samples(samples_per_segment);surface=BodySurface(context);out=[];length=0
        if len(points)<2 or (len(points)-1)*(samples_per_segment-1)+1>4097:raise ValueError('Geodesic sample budget exceeded')
        for a,b in zip(points,points[1:]):
            length+=surface.distance(a,b);part=surface.route(a,b,samples=samples_per_segment);out.extend(part[:-1])
        out.append(points[-1]);return cls(tuple(out),context,'geodesic','surface-geodesic',points,length,_ROUTE_PROOF)
    @classmethod
    def network(cls,route,*,context):
        from .routing import RoadRoute
        if context.body!=EARTH or not isinstance(route,RoadRoute):raise UnsupportedBodyOperation('Network adapter requires existing terrestrial RoadRoute, not invented planetary graph metrics')
        if route.geometry.type!='LineString':raise ValueError('Network route needs at least two positions')
        return cls(route.geometry.coordinates,context,'network','network-edge-geometry',(),route.distance_m,_ROUTE_PROOF)
    @cached_property
    def geometry(self):return Geometry('LineString',self.points)
    def surface_length(self,*,unit=METRE):
        if self.physical_length_m is None:raise UnsupportedBodyOperation('Editorial path has no implicit physical length; request sampled_surface_length explicitly')
        return METRE.convert(self.physical_length_m,unit)
    def sampled_surface_length(self,*,unit=METRE):
        from .surfaces import BodySurface
        return METRE.convert(BodySurface(self.context).length(tuple((wrap_longitude(x),y) for x,y in self.points)),unit)

def _samples(n):
    if type(n) is not int or not 3<=n<=4097:raise ValueError('Sample count must be 3..4097')

def _attach(axes,artist):
    from .axes import MapAxes
    if not isinstance(axes,MapAxes) or getattr(axes,'_terrain3d',False) or axes.figure is None or axes._colorbar_artist is not None:raise TypeError('Thematic Artists require a live 2D MapAxes')
    if artist.axes is not None or artist.get_context()!=axes.get_context():raise ValueError('Thematic Artist ownership/Body mismatch')
    artist._axes=axes;artist._bind_parent(axes)
    from .groups import _GroupStyle
    artist._theme_aware=True;artist.style=_GroupStyle(artist,artist.style)
    axes.layers.append(artist);axes._changed();return artist

class ThematicArtist(Layer):
    def labels_for(self,text,**options):
        from .editorial_labels import associated_labels
        return associated_labels(self,text,**options)
    def set_array(self,value):raise TypeError('Thematic styles are explicit; scalar fields use separate numeric Artists')
    def set_norm(self,value):raise TypeError('No implicit scalar normalizer for thematic geometry')
    def set_cmap(self,value):raise TypeError('Set an explicit LinearGradient or visual styles')
    def set_clim(self,*args,**kwargs):raise TypeError('No implicit numeric color limits')
    def _prepare_set(self,kwargs,**options):
        if set(kwargs)&{'array','norm','cmap','clim','vmin','vmax'}:raise TypeError('No implicit scalar mapping on thematic Artists')
        if 'transform' in kwargs:raise UnsupportedBodyOperation('Thematic data stay in their declared Body context; use symbol rotation/offset for presentation')
        return super()._prepare_set(kwargs,**options)
    def set_transform(self,transform):raise UnsupportedBodyOperation('Arbitrary transforms of thematic scientific coordinates are not supported')
    def get_legend_entries(self):
        group=getattr(self,'_group',None)
        if group is not None and not group.get_legend_visible():return []
        label=self.style.get('label') or self.options.get('category','')
        if not label or str(label).startswith('_'):return []
        if self.kind=='thematic_symbols':return [(str(label),dict(self.style,_symbol=self.symbol),'cartographic_symbol')]
        return [(str(label),dict(self.style),'polygon' if self.kind=='thematic_region' else 'line')]

class SymbolArtist(ThematicArtist):
    def __init__(self,points,symbol,context,*,size=12,size_unit='pt',anchor='center',offset=(0,0),labels=None,category='',priorities=None,stroke_width=None,halo=None,shadow=None,scale=1,**style):
        if stroke_width is not None:style['icon_stroke_width']=stroke_width
        if halo is not None:style['icon_halo']=halo
        if shadow is not None:style['icon_shadow']=shadow
        if scale!=1:style['icon_scale']=scale
        super().__init__('thematic_symbols',_points(points,context,limit=2048),style_dict(style),dict(category=str(category)))
        self._body_context=context;self.symbol=get_symbol(symbol)
        self._size=self._validate_size(size,size_unit);self.size_unit=size_unit
        anchors={'center':(.5,.5),'bottom':(.5,1),'top':(.5,0),'left':(0,.5),'right':(1,.5)}
        anchor=anchors.get(anchor,anchor) if isinstance(anchor,str) else anchor
        self.anchor=tuple(_number(v) for v in anchor);self.offset=tuple(_number(v) for v in offset)
        if len(self.anchor)!=2 or len(self.offset)!=2 or any(not 0<=v<=1 for v in self.anchor):raise ValueError('Invalid symbol anchor/offset')
        self.labels=tuple(str(v) for v in labels) if labels is not None else ('',)*len(self.data)
        self.priorities=tuple(_number(v) for v in priorities) if priorities is not None else (0.,)*len(self.data)
        if len(self.labels)!=len(self.data) or len(self.priorities)!=len(self.data):raise ValueError('Labels/priorities must match positions')
        if len(self.data)*sum(len(r) for p in self.symbol.parts for r in p.paths)>262144:raise ValueError('Symbol batch vertex budget exceeded')
    @staticmethod
    def _validate_size(size,unit):
        if unit not in ('pt','m'):raise ValueError('Symbol size unit must be pt or m')
        size=_number(size)
        if not 0<size<=(256 if unit=='pt' else 500000):raise ValueError('Symbol size out of bounded range')
        return size
    @artist_mutation
    def set_halo(self,value):self.style.update(style_dict(icon_halo=value));return self
    @artist_mutation
    def set_shadow(self,value):self.style.update(style_dict(icon_shadow=value));return self
    @artist_mutation
    def set_stroke_width(self,value):self.style.update(style_dict(icon_stroke_width=value));return self
    @artist_mutation
    def set_size(self,value):self._size=self._validate_size(value,self.size_unit);return self
    @artist_mutation
    def set_labels(self,labels):
        labels=tuple(str(v) for v in labels)
        if len(labels)!=len(self.data):raise ValueError('Labels must match positions')
        self.labels=labels;return self
    @artist_mutation
    def set_symbol(self,value):
        value=get_symbol(value)
        if len(self.data)*sum(len(r) for p in value.parts for r in p.paths)>262144:raise ValueError('Symbol batch vertex budget exceeded')
        self.symbol=value;return self
    @artist_mutation
    def set_positions(self,points):
        points=_points(points,self.get_context(),limit=2048)
        if len(points)!=len(self.data):raise ValueError('Preserve batch cardinality or instantiate another Artist')
        self.data=points;return self
    def instantiate(self,axes):
        if axes.get_context()!=self.get_context():raise ValueError('Explicitly recreate positions for a different Body')
        return _clone_state(self,_attach(axes,SymbolArtist(self.data,self.symbol,self.get_context(),size=self._size,size_unit=self.size_unit,anchor=self.anchor,offset=self.offset,labels=self.labels,category=self.options['category'],priorities=self.priorities,**_local_style(self))))

class RegionArtist(ThematicArtist):
    def __init__(self,region,*,gradient=None,mask=None,**style):
        if not isinstance(region,RegionDefinition):raise TypeError('Require RegionDefinition')
        if mask is not None:region=region.masked(mask)
        if gradient is not None and not isinstance(gradient,LinearGradient):raise TypeError('Require LinearGradient')
        super().__init__('thematic_region',region.geometry,style_dict(style),dict(category=region.category))
        self.definition=region;self.gradient=gradient;self._body_context=region.context
        self.slices=gradient.slices(region) if gradient else ()
    @artist_mutation
    def set_gradient(self,gradient):
        if gradient is not None and not isinstance(gradient,LinearGradient):raise TypeError('Require LinearGradient')
        slices=gradient.slices(self.definition) if gradient else ();self.gradient=gradient;self.slices=slices;return self
    def instantiate(self,axes):
        if axes.get_context()!=self.get_context():raise ValueError('Region Body/context mismatch')
        return _clone_state(self,_attach(axes,RegionArtist(self.definition,gradient=self.gradient,**_local_style(self))))

class CartographicPathArtist(ThematicArtist):
    def __init__(self,path,*,path_symbol=None,spacing=30,symbol_size=8,**style):
        if not isinstance(path,CartographicPath):raise TypeError('Require CartographicPath')
        super().__init__('thematic_path',path.geometry,style_dict(style),dict(category=''))
        self.definition=path;self._body_context=path.context;self.path_symbol=None if path_symbol is None else get_symbol(path_symbol)
        self.spacing=_number(spacing);self.symbol_size=_number(symbol_size)
        if not 4<=self.spacing<=10000 or not 0<self.symbol_size<=128:raise ValueError('Invalid path-symbol spacing/size (points)')
    def get_length(self,*,space='surface',unit=METRE):
        if space=='surface':return self.definition.surface_length(unit=unit)
        if space=='sampled_surface':return self.definition.sampled_surface_length(unit=unit)
        if space=='visual':
            if self.axes is None:raise ValueError('Detached path has no viewport')
            scene=self.figure.to_scene();from .scene import Path as ScenePath
            return sum(math.dist(a,b) for owner,_,start,end in scene._pick_records if owner is self for item in scene.items[start:end] if isinstance(item,ScenePath) and not item.closed for r in item.paths for a,b in zip(r,r[1:]))*self.figure.dpi/100
        raise ValueError('Choose surface, sampled_surface or visual (output pixels)')
    @artist_mutation
    def set_definition(self,path):
        if not isinstance(path,CartographicPath) or path.context!=self.get_context():raise ValueError('Path context mismatch')
        self.definition=path;self.data=path.geometry;return self
    def instantiate(self,axes):
        if axes.get_context()!=self.get_context():raise ValueError('Path Body/context mismatch')
        return _clone_state(self,_attach(axes,CartographicPathArtist(self.definition,path_symbol=self.path_symbol,spacing=self.spacing,symbol_size=self.symbol_size,**_local_style(self))))

def _local_style(artist):
    from .groups import _GroupStyle
    return dict(artist.style.local) if isinstance(artist.style,_GroupStyle) else dict(artist.style)


def _clone_state(source,target):
    target.set_visible(source.get_local_visible());target.set_clip_on(getattr(source,'_clip_on',True));target.set_pickradius(source.get_pickradius())
    if not callable(source.get_picker()):target.set_picker(source.get_picker())
    return target
