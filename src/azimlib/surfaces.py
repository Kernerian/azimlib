"""Own static sphere/oblate cartography. No ephemerides or spherical fallback."""
from dataclasses import dataclass,replace
from functools import cached_property,lru_cache
import math
from .bodies import Body,EARTH,UnsupportedBodyOperation
from .planetary import PlanetaryContext,axis_context
from .geodesy import Geodesic,METRE,DEGREE
from .geometry import _number,wrap_longitude
from .projections import Projection,get_projection,Orthographic


def _unit(v):
    v=tuple(_number(x) for x in v)
    if len(v)!=3 or math.hypot(*v)==0:raise ValueError('Require a nonzero finite XYZ vector')
    scale=max(abs(x) for x in v);v=tuple(x/scale for x in v)
    size=math.hypot(*v);return tuple(x/size for x in v)


@lru_cache(maxsize=1)
def _gauss():
    # Roots/weights of P16, derived by Newton iteration, not a copied table.
    result=[];n=16
    for k in range(1,n+1):
        x=math.cos(math.pi*(k-.25)/(n+.5))
        for _ in range(20):
            p,q=1.,x
            for j in range(2,n+1):p,q=q,((2*j-1)*x*q-(j-1)*p)/j
            derivative=n*(x*q-p)/(x*x-1);step=q/derivative;x-=step
            if abs(step)<1e-15:break
        result.append((x,2/((1-x*x)*derivative*derivative)))
    return tuple(result)


def _integrate(f,a,b):
    middle=(a+b)/2;half=(b-a)/2
    return half*sum(w*f(middle+half*x) for x,w in _gauss())


@dataclass(frozen=True)
class BodySurface:
    """Static ideal reference surface, with explicitly tagged angular inputs."""
    context: PlanetaryContext

    def __post_init__(self):
        if isinstance(self.context,Body):object.__setattr__(self,'context',axis_context(self.context))
        if not isinstance(self.context,PlanetaryContext):raise TypeError('Require Body or PlanetaryContext')
        if self.body.shape not in ('sphere','ellipsoid'):
            raise UnsupportedBodyOperation('Surface cartography/geodesy requires a demonstrated sphere or oblate ellipsoid')
        self.body.ellipsoid  # Also checks the existing solver flattening domain.

    @property
    def body(self):return self.context.body
    @cached_property
    def ellipsoid(self):return self.body.ellipsoid
    @cached_property
    def geodesic(self):return Geodesic(self.ellipsoid)
    @property
    def a(self):return self.body.axes[0]
    @property
    def c(self):return self.body.axes[2]
    @property
    def e2(self):return self.ellipsoid.eccentricity_squared

    def geodetic(self,lon,lat):
        lon,lat=self.context.canonical(lon,lat)
        if self.context.latitude_type=='planetocentric':lat=math.degrees(math.atan2(self.a*self.a*math.sin(math.radians(lat)),self.c*self.c*math.cos(math.radians(lat))))
        return lon,lat

    def angular(self,lon,lat):
        if self.context.latitude_type=='planetocentric':lat=math.degrees(math.atan2(self.c*self.c*math.sin(math.radians(lat)),self.a*self.a*math.cos(math.radians(lat))))
        return (DEGREE.convert(self.context.longitude.from_east(lon,self.context.prime_meridian),self.context.angle_unit),
                DEGREE.convert(lat,self.context.angle_unit))

    def inverse(self,start,end):
        r=self.geodesic.inverse(*self.geodetic(*start),*self.geodetic(*end))
        lon,lat=self.angular(r.longitude,r.latitude)
        return replace(r,longitude=lon,latitude=lat)
    def distance(self,start,end,*,unit=METRE):return METRE.convert(self.inverse(start,end).distance,unit)
    def chord(self,start,end,*,unit=METRE):
        return METRE.convert(math.dist(self.context.to_fixed(*start).xyz,self.context.to_fixed(*end).xyz),unit)
    def route(self,start,end,*,samples=101):
        if type(samples) is not int or not 2<=samples<=10001:raise ValueError('Route samples require 2..10001')
        return tuple(self.angular(*p) for p in self.geodesic.line(self.geodetic(*start),self.geodetic(*end),steps=samples-1))
    def direct(self,start,azimuth,distance,*,unit=METRE):
        r=self.geodesic.direct(*self.geodetic(*start),azimuth,unit.convert(distance,METRE))
        return self.angular(r.longitude,r.latitude)
    def length(self,points,*,unit=METRE):
        points=tuple(points)
        if not 2<=len(points)<=10001:raise ValueError('Length requires 2..10001 vertices')
        return METRE.convert(sum(self.inverse(a,b).distance for a,b in zip(points,points[1:])),unit)

    def area_primitive(self,phi):
        u=math.sin(phi);e=math.sqrt(self.e2)
        return self.a*self.a*u if not e else self.a*self.a*(1-self.e2)/2*(u/(1-self.e2*u*u)+math.atanh(e*u)/e)

    def rectangle_area(self,bounds):
        """m² of parallels/meridians in context units; not geodesic edges."""
        w,e,s,n=map(_number,bounds)
        span=self.context.angle_unit.convert(e-w,DEGREE)
        if not 0<span<=360 or not s<n:raise ValueError('Require increasing angular bounds with longitude span <=360 degrees')
        self.context.canonical(e,n)
        south=self.geodetic(w,s)[1];north=self.geodetic(w,n)[1]
        return math.radians(span)*(self.area_primitive(math.radians(north))-self.area_primitive(math.radians(south)))

    def polygon_area(self,vertices):
        """Smaller geodesic polygon area in m²; oblate polar-winding rings refused.

        Oblate integration follows Q(phi) d(lambda) along each direct geodesic.
        Nonpolar rings must be simple and lie in |geodetic latitude|<=80 degrees.
        """
        points=tuple(self.geodetic(*p) for p in vertices)
        if points and points[0]==points[-1]:points=points[:-1]
        if not 3<=len(points)<=256:raise ValueError('Require 3..256 simple polygon vertices')
        if self.body.shape=='sphere':
            from ._overlay_sphere import validate_rings,vector
            ring=tuple(vector(p) for p in points)
            validate_rings(((*ring,ring[0]),),1e-12)
            def vec(p):l,f=map(math.radians,p);return math.cos(f)*math.cos(l),math.cos(f)*math.sin(l),math.sin(f)
            v=tuple(map(vec,points));anchor=v[0];area=0.
            for b,c in zip(v[1:],v[2:]):
                cross=(b[1]*c[2]-b[2]*c[1],b[2]*c[0]-b[0]*c[2],b[0]*c[1]-b[1]*c[0])
                area+=2*math.atan2(sum(x*y for x,y in zip(anchor,cross)),1+sum(x*y for x,y in zip(anchor,b))+sum(x*y for x,y in zip(b,c))+sum(x*y for x,y in zip(c,anchor)))
            return abs((area+2*math.pi)%(4*math.pi)-2*math.pi)*self.a*self.a
        if any(abs(p[1])>80 for p in points):raise UnsupportedBodyOperation('Oblate geodesic polygon area currently excludes polar rings; use rectangle_area for polar parallels')
        if abs(sum(wrap_longitude(b[0]-a[0]) for a,b in zip(points,points[1:]+points[:1])))>180:
            raise UnsupportedBodyOperation('Oblate polar winding is not implemented')
        from .topology import validate_ring
        validate_ring((*points,points[0])).raise_if_invalid()
        total=0.
        for start,end in zip(points,points[1:]+points[:1]):
            r=self.geodesic.inverse(*start,*end)
            def f(s):
                p=self.geodesic.direct(*start,r.azimuth1,s);phi=math.radians(p.latitude)
                if abs(p.latitude)>85:raise UnsupportedBodyOperation('Geodesic edge enters unsupported polar area domain')
                N=self.a/math.sqrt(1-self.e2*math.sin(phi)**2)
                return self.area_primitive(phi)*math.sin(math.radians(p.azimuth2))/(N*math.cos(phi))
            def integrate(a,b,depth=0):
                whole=_integrate(f,a,b);m=(a+b)/2;split=_integrate(f,a,m)+_integrate(f,m,b)
                if abs(split-whole)<=max(.001,abs(split)*1e-11):return split
                if depth>=10:raise ArithmeticError('Polygon area quadrature did not converge')
                return integrate(a,m,depth+1)+integrate(m,b,depth+1)
            total+=integrate(0,r.distance)
        if abs(total)>2*math.pi*self.a*self.a:raise UnsupportedBodyOperation('Polygon area exceeds the declared smaller-interior domain')
        return abs(total)

    @lru_cache(maxsize=2048)
    def meridian(self,phi):return _integrate(lambda p:self.a*(1-self.e2*math.sin(p)**2)**-1.5*(1-self.e2),0,phi)
    def inverse_meridian(self,value):
        limit=self.meridian(math.pi/2)
        if abs(value)>limit+1e-7:return None
        phi=value/self.a
        for _ in range(10):
            d=(self.meridian(phi)-value)/(self.a*(1-self.e2)/(1-self.e2*math.sin(phi)**2)**1.5);phi-=d
            if abs(d)<1e-14:return max(-math.pi/2,min(math.pi/2,phi))
        raise ArithmeticError('Meridional inverse did not converge')

    def projection(self,method='equirectangular',**parameters):
        return SurfaceProjection(context=self.context,method=method,radius=self.a,**parameters)


@dataclass(frozen=True)
class SurfaceProjection(Projection):
    """Body-bound metric projection. All input coordinates use context conventions."""
    context: PlanetaryContext | None = None
    method: str = 'equirectangular'
    standard_parallel: float = 0
    scale_factor: float = 1
    max_latitude: float = 85.0511287798066
    @property
    def name(self):return self.method
    @cached_property
    def surface(self):return BodySurface(self.context)
    def __post_init__(self):
        super().__post_init__();s=self.surface
        from .bodies import LongitudeConvention
        if (self.context.angle_unit!=DEGREE or self.context.longitude!=LongitudeConvention() or
                self.context.prime_meridian!=0):
            raise UnsupportedBodyOperation('Projection inputs require canonical east-positive degrees and zero prime-meridian offset; convert coordinates explicitly')
        if self.radius!=s.a:raise ValueError('Projection radius must match the declared Body; no replacement sphere')
        aliases={'platecarree':'equirectangular','ortho':'orthographic','stereo':'stereographic','tmerc':'transverse_mercator','laea':'lambert_azimuthal_equal_area','aeqd':'azimuthal_equidistant'}
        object.__setattr__(self,'method',aliases.get(self.method,self.method))
        allowed=('equirectangular','mercator','orthographic','stereographic','transverse_mercator','equalearth','azimuthal_equidistant','lambert_azimuthal_equal_area')
        if self.method not in allowed:raise UnsupportedBodyOperation('Planetary projection not implemented: '+str(self.method))
        if s.body.shape!='sphere' and self.method in ('equalearth','azimuthal_equidistant','lambert_azimuthal_equal_area'):
            raise UnsupportedBodyOperation('No spherical substitution for this oblate projection')
        for n in ('standard_parallel','scale_factor','max_latitude'):object.__setattr__(self,n,_number(getattr(self,n),n))
        if abs(self.standard_parallel)>=90 or self.scale_factor<=0 or not 0<self.max_latitude<90:raise ValueError('Invalid projection scale/parallel/domain')
        if s.body.shape!='sphere' and self.method=='stereographic' and abs(self.central_latitude)!=90:
            raise UnsupportedBodyOperation('Oblate stereographic is polar only')
        if self.method=='mercator' and abs(self.central_latitude)>=90:raise ValueError('Mercator origin cannot be a pole')
        self.base
    @cached_property
    def base(self):
        params=dict(central_longitude=self.center[0],central_latitude=self.center[1],radius=self.radius)
        if self.method=='equirectangular':params['standard_parallel']=self.standard_parallel
        if self.method=='mercator':params['max_latitude']=self.max_latitude
        if self.method=='transverse_mercator':params.update(ellipsoid=self.surface.body.ellipsoid,scale_factor=self.scale_factor)
        return get_projection(self.method,**params)
    @cached_property
    def center(self):return self.surface.geodetic(self.central_longitude,self.central_latitude)
    @property
    def latitude_limits(self):return tuple(self.surface.angular(0,v)[1] for v in (-self.max_latitude,self.max_latitude))
    def _psi(self,phi):
        e=math.sqrt(self.surface.e2)
        return math.asinh(math.tan(phi))-e*math.atanh(e*math.sin(phi))
    def _inverse_psi(self,value):
        if abs(value)>40:return None
        phi=math.atan(math.sinh(value))
        for _ in range(12):
            d=(self._psi(phi)-value)*math.cos(phi)*(1-self.surface.e2*math.sin(phi)**2)/(1-self.surface.e2);phi-=d
            if abs(d)<1e-14:return phi
        raise ArithmeticError('Conformal latitude inverse did not converge')
    @cached_property
    def auxiliary(self):
        g=math.radians(self.center[1]);a,c=self.surface.a,self.surface.c
        beta=math.atan2(a*math.sin(g),c*math.cos(g));b=math.hypot(a*math.sin(g),c*math.cos(g))
        N=a/math.sqrt(1-self.surface.e2*math.sin(g)**2);offset=-N*self.surface.e2*math.sin(g)*math.cos(g)
        return Orthographic(self.center[0],math.degrees(beta),1),b,offset
    def _reduced(self,lon,lat):
        lon=wrap_longitude(_number(lon),self.central_longitude)
        g=self.surface.geodetic(0,lat)[1];p=math.radians(g)
        return lon,math.degrees(math.atan2(self.surface.c*math.sin(p),self.surface.a*math.cos(p)))
    def visibility(self,lon,lat):return self.auxiliary[0].visibility(*self._reduced(lon,lat))
    def clip_polygon(self,rings,*,step=2):
        from .geometry import clip_orthographic_polygon
        aux,b,offset=self.auxiliary
        polygons=clip_orthographic_polygon(tuple(tuple(self._reduced(*p[:2]) for p in ring) for ring in rings),aux,step=step)
        return tuple(tuple(tuple((self.radius*x,b*y-offset) for x,y in ring) for ring in polygon) for polygon in polygons)
    def forward(self,lon,lat):
        s=self.surface;lon=wrap_longitude(_number(lon),self.central_longitude);g=s.geodetic(0,lat)[1];p=math.radians(g);p0=math.radians(self.center[1]);dl=math.radians(wrap_longitude(lon-self.center[0]))
        if self.method=='orthographic':
            aux,b,offset=self.auxiliary;q=aux.forward(lon,math.degrees(math.atan2(s.c*math.sin(p),s.a*math.cos(p))))
            return None if q is None else (s.a*q[0],b*q[1]-offset)
        if self.method=='transverse_mercator':
            if abs(math.degrees(dl))>3+1e-10:return None
            return self.base.forward(lon,g)
        if s.body.shape=='sphere':return self.base.forward(lon,g)
        if self.method=='equirectangular':
            t=math.radians(self.standard_parallel);k=s.a*math.cos(t)/math.sqrt(1-s.e2*math.sin(t)**2)
            return k*dl,s.meridian(p)-s.meridian(p0)
        if self.method=='mercator':
            if abs(g)>self.max_latitude:return None
            return s.a*dl,s.a*(self._psi(p)-self._psi(p0))
        sign=1 if self.central_latitude>0 else -1
        if g*sign<=-89.999999:return None
        rho=2*s.a*self.scale_factor*math.exp(-self._psi(sign*p))/math.sqrt((1+math.sqrt(s.e2))**(1+math.sqrt(s.e2))*(1-math.sqrt(s.e2))**(1-math.sqrt(s.e2))) if abs(g)<90 else 0
        return rho*math.sin(dl),-sign*rho*math.cos(dl)
    def inverse(self,x,y):
        x,y=_number(x),_number(y);s=self.surface;p0=math.radians(self.center[1])
        if self.method=='orthographic':
            aux,b,offset=self.auxiliary;q=aux.inverse(x/s.a,(y+offset)/b)
            if q is None:return None
            lon,beta=q;p=math.radians(beta);g=math.degrees(math.atan2(s.a*math.sin(p),s.c*math.cos(p)))
            return s.angular(lon,g)
        if self.method=='transverse_mercator':
            q=self.base.inverse(x,y)
            return None if q is None or abs(wrap_longitude(q[0]-self.center[0]))>3+1e-8 else s.angular(*q)
        if s.body.shape=='sphere':
            q=self.base.inverse(x,y);return None if q is None else s.angular(*q)
        if self.method=='equirectangular':
            t=math.radians(self.standard_parallel);k=s.a*math.cos(t)/math.sqrt(1-s.e2*math.sin(t)**2);dl=x/k;p=s.inverse_meridian(y+s.meridian(p0))
        elif self.method=='mercator':
            dl=x/s.a;p=self._inverse_psi(y/s.a+self._psi(p0))
            if p is not None and abs(math.degrees(p))>self.max_latitude+1e-9:return None
        else:
            sign=1 if self.central_latitude>0 else -1;rho=math.hypot(x,y)
            if rho==0:return s.angular(self.center[0],sign*90)
            e=math.sqrt(s.e2);k=math.sqrt((1+e)**(1+e)*(1-e)**(1-e));p=self._inverse_psi(-math.log(rho*k/(2*s.a*self.scale_factor)))
            p=None if p is None else sign*p;dl=math.atan2(x,-sign*y)
        if p is None or abs(dl)>math.pi+1e-10:return None
        return s.angular(wrap_longitude(self.center[0]+math.degrees(dl)),math.degrees(p))
