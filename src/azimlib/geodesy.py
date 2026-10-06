"""Independent ellipsoid models and geodesics from published equations.

The usual inverse uses Vincenty's fixed point. Difficult inverse cases use an
own multi-start damped shooting solve of the direct equations, never a spherical
fallback. Models are static: no datum shifts, epochs or geoid grids are implied.
"""
from dataclasses import dataclass
from math import atan, atan2, cos, degrees, hypot, pi, radians, sin, sqrt, tan
from .geometry import _number, position, wrap_longitude, haversine


@dataclass(frozen=True)
class Unit:
    name: str
    symbol: str
    to_si: float
    quantity: str = 'length'

    def __post_init__(self):
        scale = _number(self.to_si, 'unit scale')
        if not isinstance(self.name,str) or not self.name or not isinstance(self.symbol,str) or not self.symbol or scale <= 0 or self.quantity not in ('length', 'angle'):
            raise ValueError('Unit requires name, symbol, positive scale and length/angle quantity')
        object.__setattr__(self, 'to_si', scale)

    def convert(self, value, target):
        if not isinstance(target, Unit) or self.quantity != target.quantity:
            raise ValueError('Units must describe the same quantity')
        return _number(value)*self.to_si/target.to_si


METRE = Unit('metre', 'm', 1)
KILOMETRE = Unit('kilometre', 'km', 1000)
RADIAN = Unit('radian', 'rad', 1, 'angle')
DEGREE = Unit('degree', 'deg', pi/180, 'angle')


@dataclass(frozen=True)
class Ellipsoid:
    semi_major_axis: float = 6378137.0
    inverse_flattening: float = 298.257223563
    name: str = 'WGS84'

    def __post_init__(self):
        a = _number(self.semi_major_axis, 'semi-major axis')
        rf = _number(self.inverse_flattening, 'inverse flattening')
        if a <= 0 or rf != 0 and rf < 150:
            raise ValueError('Ellipsoid requires a>0 and inverse_flattening=0 (sphere) or >=150')
        if not isinstance(self.name, str) or not self.name: raise ValueError('Ellipsoid requires a name')
        object.__setattr__(self, 'semi_major_axis', a)
        object.__setattr__(self, 'inverse_flattening', rf)

    @property
    def flattening(self): return 0.0 if self.inverse_flattening == 0 else 1/self.inverse_flattening
    @property
    def semi_minor_axis(self): return self.semi_major_axis*(1-self.flattening)
    @property
    def eccentricity_squared(self): return self.flattening*(2-self.flattening)


WGS84 = Ellipsoid()
GRS80 = Ellipsoid(6378137, 298.257222101, 'GRS80')


@dataclass(frozen=True)
class Datum:
    name: str = 'WGS84'
    ellipsoid: Ellipsoid = WGS84
    prime_meridian: float = 0

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name or not isinstance(self.ellipsoid, Ellipsoid):
            raise ValueError('Datum requires name and Ellipsoid')
        value=_number(self.prime_meridian,'prime meridian')
        if not -180<=value<=180:raise ValueError('Prime meridian must lie in [-180,180]')
        object.__setattr__(self, 'prime_meridian', value)


WGS84_DATUM = Datum()


@dataclass(frozen=True)
class GeodesicResult:
    longitude: float
    latitude: float
    distance: float
    azimuth1: float
    azimuth2: float
    iterations: int
    method: str


class Geodesic:
    """Ellipsoidal direct/inverse in metres, degrees and longitude/latitude order.

    Azimuth2 is the forward continuation at the endpoint (not back azimuth).
    Failure raises ArithmeticError; diagnostics expose the solver used. Distance
    is the shortest converged candidate in inverse; antipodes can have multiple
    equally short azimuths. Accuracy is tested, not guaranteed for every model.
    """
    def __init__(self, ellipsoid=WGS84):
        if not isinstance(ellipsoid, Ellipsoid): raise TypeError('ellipsoid must be Ellipsoid')
        self.ellipsoid = ellipsoid

    def _coefficients(self, cos2alpha):
        e = self.ellipsoid
        u2 = cos2alpha*(e.semi_major_axis**2-e.semi_minor_axis**2)/e.semi_minor_axis**2
        return 1+u2*(4096+u2*(-768+u2*(320-175*u2)))/16384, u2*(256+u2*(-128+u2*(74-47*u2)))/1024

    @staticmethod
    def _delta(sigma, midpoint, B):
        ss, cs, cm = sin(sigma), cos(sigma), cos(midpoint)
        return B*ss*(cm+B/4*(cs*(-1+2*cm*cm)-B/6*cm*(-3+4*ss*ss)*(-3+4*cm*cm)))

    def direct(self, longitude, latitude, azimuth, distance):
        lon, lat = position((longitude, latitude))
        if not -180 <= lon <= 180: raise ValueError('Geodesic longitude must lie in [-180,180]')
        distance, azimuth = _number(distance, 'distance'), _number(azimuth, 'azimuth') % 360
        if distance < 0: raise ValueError('Geodesic distance must be nonnegative')
        if distance == 0: return GeodesicResult(lon, lat, 0, azimuth, azimuth, 0, 'direct')
        e = self.ellipsoid; f = e.flattening; b = e.semi_minor_axis
        alpha = radians(azimuth); u = atan((1-f)*tan(radians(lat)))
        su, cu, sa, ca = sin(u), cos(u), sin(alpha), cos(alpha)
        sigma1 = atan2(tan(u), ca); sinalpha = cu*sa; cos2alpha = 1-sinalpha*sinalpha
        A, B = self._coefficients(cos2alpha); initial = distance/(b*A); sigma = initial
        for iteration in range(1, 101):
            new = initial+self._delta(sigma, 2*sigma1+sigma, B)
            if abs(new-sigma) < 2e-14: sigma = new; break
            sigma = new
        else: raise ArithmeticError('Direct ellipsoidal geodesic did not converge')
        ss, cs = sin(sigma), cos(sigma); t = su*ss-cu*cs*ca
        phi = atan2(su*cs+cu*ss*ca, (1-f)*hypot(sinalpha, t))
        lam = atan2(ss*sa, cu*cs-su*ss*ca)
        C = f*cos2alpha*(4+f*(4-3*cos2alpha))/16
        correction = (1-C)*f*sinalpha*(sigma+C*ss*(cos(2*sigma1+sigma)+C*cs*(-1+2*cos(2*sigma1+sigma)**2)))
        return GeodesicResult(wrap_longitude(lon+degrees(lam-correction)), degrees(phi), distance,
                              azimuth, degrees(atan2(sinalpha, -t)) % 360, iteration, 'direct')

    def inverse(self, longitude1, latitude1, longitude2, latitude2):
        lon1, lat1 = position((longitude1, latitude1)); lon2, lat2 = position((longitude2, latitude2))
        if not all(-180 <= lon <= 180 for lon in (lon1, lon2)): raise ValueError('Geodesic longitude must lie in [-180,180]')
        L = radians(wrap_longitude(lon2-lon1))
        if lat1 == lat2 and (L == 0 or abs(lat1) == 90):
            return GeodesicResult(lon2,lat2,0,0,0,0,'coincident')
        e = self.ellipsoid; f = e.flattening
        u1, u2 = atan((1-f)*tan(radians(lat1))), atan((1-f)*tan(radians(lat2)))
        s1,c1,s2,c2 = sin(u1),cos(u1),sin(u2),cos(u2)
        lam = L
        for iteration in range(1, 201):
            sl,cl = sin(lam),cos(lam)
            sine = hypot(c2*sl,c1*s2-s1*c2*cl); cosine = s1*s2+c1*c2*cl
            if sine < 1e-15: break
            sigma = atan2(sine,cosine); sa = c1*c2*sl/sine; ca2 = max(0,1-sa*sa)
            cm = 0 if ca2 < 1e-16 else cosine-2*s1*s2/ca2
            C=f*ca2*(4+f*(4-3*ca2))/16
            new=L+(1-C)*f*sa*(sigma+C*sine*(cm+C*cosine*(-1+2*cm*cm)))
            if abs(new-lam) < 2e-14:
                A,B=self._coefficients(ca2)
                distance=e.semi_minor_axis*A*(sigma-self._delta(sigma, atan2(sqrt(max(0,1-cm*cm)),cm), B))
                # _delta only uses cos(midpoint); the acos branch is immaterial.
                a1=degrees(atan2(c2*sl,c1*s2-s1*c2*cl)) % 360
                a2=degrees(atan2(c1*sl,-s1*c2+c1*s2*cl)) % 360
                return GeodesicResult(lon2,lat2,distance,a1,a2,iteration,'vincenty')
            lam=new
        return self._shoot(lon1,lat1,lon2,lat2)

    def _shoot(self, lon1, lat1, lon2, lat2):
        # Own finite-difference Newton shooting with line search and multiple
        # initial azimuths. Three-vector endpoint errors avoid longitude seams.
        def vector(lon,lat):
            l,p=radians(lon),radians(lat)
            return cos(p)*cos(l),cos(p)*sin(l),sin(p)
        target=vector(lon2,lat2); l,p=radians(lon2),radians(lat2)
        east=(-sin(l),cos(l),0); north=(-sin(p)*cos(l),-sin(p)*sin(l),cos(p))
        def error(az,s):
            r=self.direct(lon1,lat1,degrees(az),s); v=vector(r.longitude,r.latitude)
            diff=tuple(a-b for a,b in zip(v,target))
            return (sum(a*b for a,b in zip(diff,east)),sum(a*b for a,b in zip(diff,north))), sqrt(sum(x*x for x in diff)),r
        radius=(2*self.ellipsoid.semi_major_axis+self.ellipsoid.semi_minor_axis)/3
        initial=haversine((lon1,lat1),(lon2,lat2),radius)
        candidates=[]; limit=pi*self.ellipsoid.semi_major_axis*1.01
        for seed in range(0,360,15):
            az=radians(seed); s=initial
            for it in range(1,81):
                residual, norm, result=error(az,s)
                if norm < 2e-12:
                    candidates.append((s,result,it)); break
                h=1e-5; hs=10.0
                ea,_,_=error(az+h,s); eb,_,_=error(az-h,s)
                es,_,_=error(az,s+hs); et,_,_=error(az,max(0,s-hs))
                ja=tuple((a-b)/(2*h) for a,b in zip(ea,eb)); js=tuple((a-b)/(2*hs) for a,b in zip(es,et))
                determinant=ja[0]*js[1]-ja[1]*js[0]
                if abs(determinant)<1e-20: break
                da=(-residual[0]*js[1]+residual[1]*js[0])/determinant
                ds=(-ja[0]*residual[1]+ja[1]*residual[0])/determinant
                da=max(-.5,min(.5,da)); ds=max(-1e6,min(1e6,ds))
                for power in range(12):
                    fraction=2.**-power; na=az+da*fraction; ns=s+ds*fraction
                    if 0 <= ns <= limit and error(na,ns)[1] < norm:
                        az,s=na,ns; break
                else: break
        if not candidates: raise ArithmeticError('Ellipsoidal inverse shooting did not converge; no spherical fallback was used')
        distance,result,iterations=min(candidates,key=lambda item:item[0])
        return GeodesicResult(lon2,lat2,distance,result.azimuth1,result.azimuth2,iterations,'shooting')

    def line(self, start, end, *, steps=100):
        if isinstance(steps,bool) or not isinstance(steps,int) or steps<1: raise ValueError('steps must be a positive integer')
        start,end=position(start)[:2],position(end)[:2]
        inverse=self.inverse(*start,*end)
        points=[start]
        for i in range(1,steps):
            r=self.direct(*start,inverse.azimuth1,inverse.distance*i/steps)
            points.append((r.longitude,r.latitude))
        return tuple(points)+(end,)
