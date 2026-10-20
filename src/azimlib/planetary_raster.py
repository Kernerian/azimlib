"""Bounded immutable Body rasters; explicit local acquisition and inverse sampling."""
from dataclasses import dataclass,replace
from functools import cached_property
import math
from pathlib import Path
from .bodies import BodySource,UnsupportedBodyOperation
from .planetary import PlanetaryContext
from .geometry import _number,wrap_longitude
from .scientific import scalar,color_rows,is_color,interpolate
from .surfaces import BodySurface,SurfaceProjection
from .geodesy import METRE,Unit


@dataclass(frozen=True)
class RasterBudget:
    max_pixels:int=262144
    max_bytes:int=67108864
    def __post_init__(self):
        if type(self.max_pixels) is not int or not 1<=self.max_pixels<=4_000_000:raise ValueError('Raster pixel budget must be 1..4 million')
        if type(self.max_bytes) is not int or not 1024<=self.max_bytes<=1_073_741_824:raise ValueError('Invalid raster memory/input byte budget')
    def check(self,ny,nx):
        if type(ny) is not int or type(nx) is not int or min(ny,nx)<1 or ny*nx>self.max_pixels or ny*nx*160>self.max_bytes:
            raise ValueError('Raster exceeds declared allocation budget before materialization')


@dataclass(frozen=True)
class ElevationProfile:
    context:PlanetaryContext
    coordinates:tuple
    distance_m:tuple
    elevation_m:tuple
    projected_distance_m:tuple | None
    source:BodySource


@dataclass(frozen=True)
class PlanetaryRaster:
    """Corner affine in declared angular context or SurfaceProjection metres.

    Scalar DEM units are explicit length units; images use unit='rgba', scalar
    intensity uses unit='1'. Pixel order follows affine rows, masks are True
    for missing values. No geographic or vertical datum is inferred.
    """
    values:tuple
    affine:tuple
    context:PlanetaryContext
    source:BodySource
    license:str
    unit:object=METRE
    projection:SurfaceProjection | None=None
    nodata:float | None=None
    mask:object=None
    color_mode:str='auto'
    copyright:str=''
    budget:RasterBudget=RasterBudget()
    history:tuple=()
    provenance:tuple=()
    def __post_init__(self):
        if not isinstance(self.context,PlanetaryContext) or not isinstance(self.source,BodySource):raise TypeError('Raster requires coordinate context and factual source identity')
        BodySurface(self.context)
        if not isinstance(self.license,str) or not self.license.strip() or not isinstance(self.copyright,str):raise ValueError('Raster requires explicit license and copyright declaration')
        if not isinstance(self.budget,RasterBudget):raise TypeError('Require RasterBudget')
        self.budget.check(len(self.values),len(self.values[0]) if len(self.values) else 0)
        if any(len(row)!=len(self.values[0]) for row in self.values):raise ValueError('Raster requires rectangular rows')
        a=tuple(_number(v,'affine coefficient') for v in self.affine)
        if len(a)!=6 or a[0]*a[4]-a[1]*a[3]==0:raise ValueError('Raster affine must be invertible')
        if self.projection is not None and (not isinstance(self.projection,SurfaceProjection) or self.projection.context!=self.context):raise ValueError('Raster projection/context mismatch')
        if not isinstance(self.unit,Unit) and (not isinstance(self.unit,str) or not self.unit.strip()):raise ValueError('Declare raster measurement units')
        if self.color_mode not in ('auto','scalar','rgba'):raise ValueError('Unknown pixel mode')
        color=self.color_mode=='rgba' or self.color_mode=='auto' and is_color(self.values)
        nodata=None if self.nodata is None else float(self.nodata)
        if nodata is not None and not (math.isfinite(nodata) or math.isnan(nodata)):raise ValueError('Invalid NoData')
        if color and nodata is not None:raise ValueError('Color pixels use alpha/mask, not scalar NoData')
        mask=self.mask
        if mask is not None and (len(mask)!=len(self.values) or any(len(row)!=len(self.values[0]) for row in mask)):raise ValueError('Mask must match pixels')
        raw=tuple(tuple(None if mask is not None and mask[j][i] else v for i,v in enumerate(row)) for j,row in enumerate(self.values))
        rows=color_rows(raw) if color else tuple(tuple(None if (n:=scalar(v)) is None or nodata is not None and n==nodata else n for v in row) for row in raw)
        object.__setattr__(self,'values',rows);object.__setattr__(self,'affine',a);object.__setattr__(self,'color_mode','rgba' if color else 'scalar')
        object.__setattr__(self,'mask',tuple(tuple(v[3]==0 if color else v is None for v in row) for row in rows))
        object.__setattr__(self,'nodata',nodata)
        object.__setattr__(self,'history',tuple(str(v) for v in self.history))
        provenance=tuple(self.provenance) or ((self.source,self.license,self.copyright),)
        if any(len(p)!=3 or not isinstance(p[0],BodySource) or not all(isinstance(v,str) for v in p[1:]) for p in provenance):raise ValueError('Invalid source/license provenance')
        object.__setattr__(self,'provenance',provenance)
        if self.projection is None:
            for c,r in ((0,0),(self.shape[1],0),(0,self.shape[0]),(self.shape[1],self.shape[0])):self.context.canonical(*self.coordinate(c,r))
    @property
    def body(self):return self.context.body
    @property
    def shape(self):return len(self.values),len(self.values[0])
    @property
    def resolution(self):a,b,_,d,e,_=self.affine;return math.hypot(a,d),math.hypot(b,e)
    @property
    def bounds(self):
        ny,nx=self.shape;p=[self.coordinate(c,r) for c,r in ((0,0),(nx,0),(nx,ny),(0,ny))]
        return min(v[0] for v in p),max(v[0] for v in p),min(v[1] for v in p),max(v[1] for v in p)
    def coordinate(self,c,r,*,center=False):
        c,r=_number(c),_number(r)
        if center:c+=.5;r+=.5
        a,b,x,d,e,y=self.affine;return a*c+b*r+x,d*c+e*r+y
    def geographic(self,c,r,*,center=False):
        p=self.coordinate(c,r,center=center)
        return p if self.projection is None else self.projection.inverse(*p)
    def sample(self,lon,lat,*,method='nearest',missing='strict'):
        self.context.canonical(lon,lat)
        p=(lon,lat) if self.projection is None else self.projection.forward(lon,lat)
        if p is None:return (0.,0.,0.,0.) if self.color_mode=='rgba' else None
        a,b,x,d,e,y=self.affine;det=a*e-b*d;xx,yy=p
        return interpolate(self.values,(e*(xx-x)-b*(yy-y))/det,(-d*(xx-x)+a*(yy-y))/det,method,missing,color=self.color_mode=='rgba')
    def geographic_mesh(self):
        a,b,c,d,e,f=self.affine;ny,nx=self.shape
        if b or d or self.projection is not None and self.projection.method not in ('equirectangular','mercator'):
            raise UnsupportedBodyOperation('Plotting requires a separable geographic mesh; explicitly resample this raster to an angular grid first')
        qx=[self.geographic(i,0) for i in range(nx+1)];qy=[self.geographic(0,j) for j in range(ny+1)]
        if any(p is None for p in qx+qy):raise ValueError('Raster grid edges leave projection domain')
        x=tuple(p[0] for p in qx);y=tuple(p[1] for p in qy);rows=self.values
        if a<0:x=x[::-1];rows=tuple(row[::-1] for row in rows)
        if e<0:y=y[::-1];rows=rows[::-1]
        if any(u>=v for u,v in zip(x,x[1:])):raise UnsupportedBodyOperation('Split seam-crossing raster grids explicitly before plotting')
        return x,y,rows
    def resample(self,shape,*,extent,projection=None,method='nearest',missing='strict',budget=None):
        budget=self.budget if budget is None else budget;ny,nx=tuple(shape);budget.check(ny,nx)
        if projection is not None and (not isinstance(projection,SurfaceProjection) or projection.context!=self.context):raise ValueError('Target projection belongs to another Body/context')
        if method not in ('nearest','bilinear') or missing not in ('strict','renormalize'):raise ValueError('Invalid interpolation policy')
        w,e,s,n=map(_number,extent)
        if not w<e or not s<n:raise ValueError('Destination extent must increase')
        affine=((e-w)/nx,0,w,0,(s-n)/ny,n);rows=[]
        for j in range(ny):
            row=[]
            for i in range(nx):
                p=(w+(i+.5)*(e-w)/nx,n-(j+.5)*(n-s)/ny)
                q=p if projection is None else projection.inverse(*p)
                row.append(None if q is None else self.sample(*q,method=method,missing=missing))
            rows.append(row)
        return replace(self,values=rows,affine=affine,projection=projection,nodata=None,mask=None,budget=budget,
                       history=(*self.history,'inverse sampling '+method+'; missing='+missing))
    def crop(self,extent):
        a,b,c,d,e,f=self.affine
        if b or d:raise UnsupportedBodyOperation('Exact pixel window cropping requires an axis-aligned source')
        w,ee,s,n=map(_number,extent)
        if not w<ee or not s<n:raise ValueError('Crop extent must increase')
        cols=sorted(((w-c)/a,(ee-c)/a));rows=sorted(((s-f)/e,(n-f)/e))
        i0,i1=max(0,math.floor(cols[0])),min(self.shape[1],math.ceil(cols[1]));j0,j1=max(0,math.floor(rows[0])),min(self.shape[0],math.ceil(rows[1]))
        if i0>=i1 or j0>=j1:raise ValueError('Crop has no source coverage')
        return replace(self,values=tuple(row[i0:i1] for row in self.values[j0:j1]),affine=(a,0,c+a*i0,0,e,f+e*j0),mask=None,nodata=None,history=(*self.history,'pixel-window crop'))
    @classmethod
    def mosaic(cls,rasters,*,shape,extent,projection=None,overlap='first',budget=RasterBudget()):
        rasters=tuple(rasters)
        if not 1<=len(rasters)<=16 or overlap not in ('first','last','error'):raise ValueError('Mosaic requires 1..16 sources and explicit overlap policy')
        first=rasters[0]
        if any(not isinstance(r,cls) or r.context!=first.context or r.unit!=first.unit or r.color_mode!=first.color_mode for r in rasters):raise ValueError('Mosaic Body/context/unit/pixel mode mismatch')
        if any(r.license!=first.license for r in rasters):raise UnsupportedBodyOperation('Mixed-license mosaics require external license composition before use')
        ny,nx=tuple(shape);budget.check(ny,nx)
        if projection is not None and projection.context!=first.context:raise ValueError('Mosaic projection/context mismatch')
        w,e,s,n=map(_number,extent)
        if not w<e or not s<n:raise ValueError('Mosaic extent must increase')
        affine=((e-w)/nx,0,w,0,(s-n)/ny,n);rows=[]
        for j in range(ny):
            row=[]
            for i in range(nx):
                p=(w+(i+.5)*(e-w)/nx,n-(j+.5)*(n-s)/ny);q=p if projection is None else projection.inverse(*p)
                values=[] if q is None else [r.sample(*q) for r in rasters]
                valid=[v for v in values if v is not None and (first.color_mode!='rgba' or v[3]>0)]
                if overlap=='error' and len(valid)>1:raise ValueError('Mosaic contains overlapping valid pixels')
                row.append(None if not valid else valid[-1] if overlap=='last' else valid[0])
            rows.append(row)
        return replace(first,values=rows,affine=affine,projection=projection,mask=None,nodata=None,budget=budget,source=BodySource('derived:mosaic','1','Explicit inverse-sampled composite'),
                       provenance=tuple(p for r in rasters for p in r.provenance),history=(*first.history,'mosaic overlap='+overlap))
    @classmethod
    def from_image(cls,path,*,affine,context,source,license,unit='rgba',budget=RasterBudget(),**kwargs):
        import hashlib
        from .raster import _pixels
        path=Path(path)
        if path.stat().st_size>budget.max_bytes:raise ValueError('Image exceeds declared input byte budget')
        with path.open('rb') as stream:raw=stream.read(budget.max_bytes+1)
        if len(raw)>budget.max_bytes:raise ValueError('Image exceeds declared input byte budget')
        if source.sha256 and hashlib.sha256(raw).hexdigest()!=source.sha256:raise ValueError('Image source hash mismatch')
        rows,_=_pixels(raw,budget.max_pixels)
        return cls(rows,affine,context,source,license,unit=unit,budget=budget,**kwargs)
    def _height(self,v):
        if self.color_mode!='scalar' or not isinstance(self.unit,Unit) or self.unit.quantity!='length':raise ValueError('DEM requires declared length units')
        return None if v is None else self.unit.convert(v,METRE)
    def profile(self,start,end,*,samples=101,method='bilinear',missing='strict',projection=None):
        s=BodySurface(self.context);points=s.route(start,end,samples=samples);total=s.distance(start,end)
        if projection is not None and projection.context!=self.context:raise ValueError('Profile projection/context mismatch')
        projected=None
        if projection is not None:
            if any(abs(wrap_longitude(b[0],projection.central_longitude)-wrap_longitude(a[0],projection.central_longitude))>180 for a,b in zip(points,points[1:])):
                raise UnsupportedBodyOperation('Projected profile crosses the chart seam; select another central meridian or split the profile explicitly')
            projected=[0.];previous=projection.forward(*points[0])
            if previous is None:raise ValueError('Profile starts outside projection')
            for p in points[1:]:
                current=projection.forward(*p)
                if current is None:raise ValueError('Profile leaves projection domain')
                projected.append(projected[-1]+math.dist(current,previous));previous=current
        return ElevationProfile(self.context,points,tuple(total*i/(samples-1) for i in range(samples)),
                                tuple(self._height(self.sample(*p,method=method,missing=missing)) for p in points),
                                None if projected is None else tuple(projected),self.source)
    def hillshade(self,light,*,exaggeration=1):
        from .planetary_light import GeometricLight
        if not isinstance(light,GeometricLight) or light.context!=self.context:raise ValueError('Light and DEM must share Body/context')
        exaggeration=_number(exaggeration)
        if exaggeration<=0:raise ValueError('Visual exaggeration must be positive')
        def point(i,j):
            h=self._height(self.values[j][i]);geo=self.geographic(i,j,center=True)
            return None if h is None or geo is None else self.context.to_fixed(*geo,METRE.convert(h*exaggeration,self.context.height_unit)).xyz
        ny,nx=self.shape
        if min(ny,nx)<2:raise ValueError('Hillshade needs at least 2x2 samples')
        points=tuple(tuple(point(i,j) for i in range(nx)) for j in range(ny));out=[]
        for j in range(ny):
            row=[]
            for i in range(nx):
                p=points[j][i];a,b=points[j][max(0,i-1)],points[j][min(nx-1,i+1)];c,d=points[max(0,j-1)][i],points[min(ny-1,j+1)][i]
                if any(v is None for v in (p,a,b,c,d)):row.append(None);continue
                u=tuple(y-x for x,y in zip(a,b));v=tuple(y-x for x,y in zip(c,d));normal=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
                size=math.hypot(*normal)
                if not size:row.append(None);continue
                sign=1 if sum(n*x for n,x in zip(normal,p))>=0 else -1
                row.append(max(0,sum(sign*n/size*l for n,l in zip(normal,light.vector_at(p)))))
            out.append(row)
        return replace(self,values=out,mask=None,unit='1',nodata=None,history=(*self.history,'geometric hillshade; visual exaggeration='+str(exaggeration)))


@dataclass(frozen=True)
class SurfaceFrame:
    """Exact fixed-XYZ to ENU transform for a bounded regional terrain view."""
    context:PlanetaryContext
    lon:float
    lat:float
    def __post_init__(self):
        BodySurface(self.context);self.context.canonical(self.lon,self.lat)
    @cached_property
    def origin(self):return self.context.to_fixed(self.lon,self.lat).xyz
    @cached_property
    def basis(self):
        lon,lat=map(math.radians,BodySurface(self.context).geodetic(self.lon,self.lat))
        return ((-math.sin(lon),math.cos(lon),0),(-math.sin(lat)*math.cos(lon),-math.sin(lat)*math.sin(lon),math.cos(lat)),(math.cos(lat)*math.cos(lon),math.cos(lat)*math.sin(lon),math.sin(lat)))
    def vector(self,v):return tuple(sum(x*y for x,y in zip(row,v)) for row in self.basis)
    @cached_property
    def surface(self):return BodySurface(self.context)
    def position(self,lon,lat,height_m):
        if self.surface.distance((self.lon,self.lat),(lon,lat))>min(250000,.1*self.context.body.axes[0]):raise ValueError('Terrain exceeds declared local ENU radius')
        q=self.context.to_fixed(lon,lat,METRE.convert(height_m,self.context.height_unit)).xyz
        return self.vector(tuple(x-y for x,y in zip(q,self.origin)))
