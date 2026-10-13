"""Experimental own reductions from explicit SPK states to Earth-fixed disks.

Internal until the scientific gate establishes a quantitative accuracy bound.
The short nutation reduction, spherical limbs and absent polar motion must not
be represented as a precision-certified IAU/IERS transformation engine.
"""
from dataclasses import dataclass
import math
from ._timescales import JulianCoordinate
from ._spk import SpkKernel
from ._frames import Coordinates,EARTH_FIXED,Observer,GEODETIC
from .eclipse import ShadowSphere,ShadowCone,occultation,SUN_RADIUS_M,_norm,_sub,_dot
from .lunar import MOON_RADIUS_M

C=299792458.
ARCSEC=math.pi/(180*3600)


class EclipseDomainError(ValueError):
    """Explicit experimental-domain rejection; never an extrapolated forecast."""
    def __init__(self,message,quantity,value):
        super().__init__(message);self.quantity=quantity;self.value=value
        self.scientific_prediction_valid=False


def _rotate(v,axis,angle):
    c,s=math.cos(angle),math.sin(angle);x,y,z=v
    if axis==0:return x,c*y-s*z,s*y+c*z
    if axis==1:return c*x+s*z,y,-s*x+c*z
    return c*x-s*y,s*x+c*y,z


def _j2000_seconds(coordinate,scale):
    if not isinstance(coordinate,JulianCoordinate) or coordinate.scale!=scale:
        raise ValueError('Require explicit '+scale+' JulianCoordinate')
    return (coordinate.day-2451545)*86400+coordinate.seconds


@dataclass(frozen=True)
class EclipseState:
    sun: ShadowSphere
    moon: ShadowSphere
    tt: JulianCoordinate
    ut1: JulianCoordinate
    kernel_sha256: str
    accuracy_validated: bool = False

    def solar(self,observer,*,lunar_limb='physical-mean',solar_limb='state'):
        """Finite disks with an explicit lunar limb convention.

        NASA bulletin k values are dimensionless equatorial-Earth-radius
        ratios: 0.272281 internal, 0.2725076 external. They do not change the
        state, Sun radius, terrestrial geometry, clock or ephemeris accuracy.
        Selecting a lunar convention alone does not reproduce all catalog
        conventions. Source: eclipse.gsfc.nasa.gov/SEmono/reference/radius.html
        """
        if not isinstance(observer,Observer) or observer.geodetic.fixed!=EARTH_FIXED:
            raise ValueError('Require terrestrial geodetic observer')
        if solar_limb=='state':sun=self.sun
        elif solar_limb=='usno-696000km':
            # Explicit published Solar Eclipse Computer convention. Independent
            # contact comparisons must select it, not fit a radius to residuals.
            # Source: https://aa.usno.navy.mil/data/SolarEclipses (Notes).
            sun=ShadowSphere(self.sun.center,696000000.)
        else:raise ValueError('Unknown explicit solar limb convention')
        if lunar_limb=='physical-mean':moon=self.moon
        elif lunar_limb in ('nasa-bulletin-internal','nasa-bulletin-external','nasa-canon-external'):
            # Distinct published constants: do not silently equate a Canon
            # k1=0.272488 table with the bulletin/IAU external mean radius.
            k={'nasa-bulletin-internal':.272281,'nasa-bulletin-external':.2725076,
               'nasa-canon-external':.272488}[lunar_limb]
            moon=ShadowSphere(self.moon.center,6378137.*k)
        else:raise ValueError('Unknown explicit lunar limb convention')
        return occultation(observer.fixed_position,sun,moon)

    def central_point(self):
        """Near-side shadow-axis intersection with WGS84; None if axis misses."""
        moon=self.moon.center.xyz;sun=self.sun.center.xyz
        direction=_sub(moon,sun);length=_norm(direction);d=tuple(v/length for v in direction)
        e=GEODETIC.fixed.body.ellipsoid;a=e.semi_major_axis;b=e.semi_minor_axis
        weighted=lambda v,w:(v[0]*w[0]+v[1]*w[1])/(a*a)+v[2]*w[2]/(b*b)
        A=weighted(d,d);B=2*weighted(moon,d);D=weighted(moon,moon)-1
        disc=B*B-4*A*D
        if disc<0:return None
        distance=(-B-math.sqrt(disc))/(2*A)
        if distance<0:return None
        point=tuple(v+distance*q for v,q in zip(moon,d))
        return GEODETIC.from_fixed(Coordinates(point,EARTH_FIXED))[:2]

    def lunar_margins(self,*,shadow_convention):
        """Signed metre margins for penumbral, partial and total lunar contacts.

        Danjon-mean is explicitly the NASA catalog's effective spherical
        atmosphere/mean-oblateness convention, not a physical atmosphere or an
        exact projection of the terrestrial ellipsoid. Negative means contact
        has occurred. This does not compute lunar surface brightness.
        """
        if shadow_convention not in ('airless-mean','danjon-mean'):
            raise ValueError('Choose an explicit lunar shadow convention')
        radius=6378137.*(1.01 if shadow_convention=='danjon-mean' else 1-1/594)
        earth=ShadowSphere.from_xyz((0.,0.,0.),radius_m=radius)
        cone=ShadowCone(self.sun,earth);axis=cone.axis;moon=self.moon.center.xyz
        distance=_dot(moon,axis)
        if distance<0:return (float('inf'),)*3
        perpendicular=_norm(tuple(v-distance*d for v,d in zip(moon,axis)))
        umbra,penumbra=cone.radii(distance);r=self.moon.radius_m
        return perpendicular-penumbra-r,perpendicular-umbra-r,perpendicular-umbra+r


def contact_roots(function,start,end,*,step=60.,tolerance=.01,critical_points=()):
    """Bracketed sign-change contacts; grazing/double roots remain unsupported.

    Bounded interval/iterations with no implicit time-scale conversion. A
    numerical root is not an independently validated eclipse prediction.
    """
    if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (start,end,step,tolerance)) or not start<end or not 0<tolerance<=step or math.ceil((end-start)/step)>3000:
        raise ValueError('Invalid/beyond-budget contact search')
    # A short negative interval can lie wholly between coarse samples. Explicit
    # independently computed extrema split that interval, without substituting
    # reference contact times or changing the bisection accuracy.
    critical_points=tuple(critical_points)
    if len(critical_points)>3000 or any(not isinstance(t,(int,float)) or not math.isfinite(t) or not start<=t<=end for t in critical_points):
        raise ValueError('Invalid/beyond-budget critical points')
    grid=sorted({start,end,*critical_points,*(min(start+i*step,end) for i in range(1,math.ceil((end-start)/step)))})
    roots=[];a=start;fa=function(a)
    for b in grid[1:]:
        fb=function(b)
        if not math.isfinite(fa) or not math.isfinite(fb):raise ValueError('Contact function must be finite')
        if fa==0 and (not roots or a-roots[-1]>tolerance):roots.append(a)
        if fa*fb<0:
            lo,hi=a,b;flo=fa
            for _ in range(64):
                if hi-lo<=tolerance:break
                mid=(lo+hi)/2;fm=function(mid)
                if not math.isfinite(fm):raise ValueError('Nonfinite contact bisection')
                if flo*fm<=0:hi=mid
                else:lo=mid;flo=fm
            else:raise ArithmeticError('Contact root did not converge')
            roots.append((lo+hi)/2)
        a,fa=b,fb
    if fa==0 and (not roots or end-roots[-1]>tolerance):roots.append(end)
    return tuple(roots)


class EclipseEphemeris:
    """External local kernel only; no downloads, inherited accuracy or fallback."""
    def __init__(self,kernel):
        if not isinstance(kernel,SpkKernel):raise TypeError('Require our bounded SpkKernel')
        self.kernel=kernel

    @staticmethod
    def domain_contract():
        """Development bounds are not a certified scientific accuracy interval.

        Expansion requires independently validated reductions, EOP/UT1 and
        explicit time uncertainty, kernel coverage and a complete error budget.
        No certified interval is claimed while the global gate remains open.
        """
        return dict(experimental_tt_dates=('1972-01-01','2101-01-01'),
                    experimental_tt_minus_ut1_s=(0,200),
                    certified_accuracy_interval=None,accuracy_validated=False,
                    outside_domain='raise EclipseDomainError; no extrapolation')

    def at(self,tt,ut1):
        seconds=_j2000_seconds(tt,'TT');rotation_seconds=_j2000_seconds(ut1,'UT1')
        if not (2441317-2451545)*86400+43200<=seconds<(2488434-2451545)*86400+43200:
            raise EclipseDomainError('Reduction development domain is 1972-2100; no certified scientific accuracy interval', 'TT',seconds)
        if not 0<=seconds-rotation_seconds<=200:
            raise EclipseDomainError('Explicit TT-UT1 must lie in 0..200 seconds; no extrapolated scientific prediction', 'TT-UT1',seconds-rotation_seconds)
        T=seconds/(86400*36525)
        # Leading periodic TT-to-TDB correction; this is not a relativistic
        # ephemeris time transformation with a certified uncertainty bound.
        g=math.radians(357.5277233+35999.05034*T)
        tdb=seconds+.001657*math.sin(g)+.000022*math.sin(2*g)
        earth=self.kernel.state(399,tdb)
        beta=tuple(v/C for v in earth.velocity_m_s);beta2=_dot(beta,beta)
        gamma=1/math.sqrt(1-beta2)
        def apparent(target):
            delay=0.
            for _ in range(8):
                state=self.kernel.state(target,tdb-delay)
                relative=_sub(state.position_m,earth.position_m);distance=_norm(relative)
                nextdelay=distance/C
                if abs(nextdelay-delay)<1e-9:break
                delay=nextdelay
            else:raise ArithmeticError('Light time failed to converge')
            n=tuple(v/distance for v in relative);dot=_dot(n,beta)
            # Lorentz aberration for the geocentric observer velocity.
            direction=tuple((n[i]/gamma+beta[i]+gamma/(1+gamma)*dot*beta[i])/(1+dot) for i in range(3))
            return tuple(v*distance for v in direction)
        # Independent IAU-1976 precession angles and dominant nutation terms.
        zeta=(2306.2181*T+.30188*T*T+.017998*T**3)*ARCSEC
        z=(2306.2181*T+1.09468*T*T+.018203*T**3)*ARCSEC
        theta=(2004.3109*T-.42665*T*T-.041833*T**3)*ARCSEC
        omega=math.radians(125.04452-1934.136261*T)
        L=math.radians(280.4665+36000.7698*T)
        moonL=math.radians(218.3165+481267.8813*T)
        dpsi=(-17.20*math.sin(omega)-1.32*math.sin(2*L)-.23*math.sin(2*moonL)+.21*math.sin(2*omega))*ARCSEC
        deps=(9.20*math.cos(omega)+.57*math.cos(2*L)+.10*math.cos(2*moonL)-.09*math.cos(2*omega))*ARCSEC
        eps=(84381.448-46.815*T-.00059*T*T+.001813*T**3)*ARCSEC
        days=rotation_seconds/86400;Tu=days/36525
        gmst=math.radians((280.46061837+360.98564736629*days+.000387933*Tu*Tu-Tu**3/38710000)%360)
        gast=gmst+dpsi*math.cos(eps+deps)
        def fixed(v):
            v=_rotate(_rotate(_rotate(v,2,zeta),1,-theta),2,z)
            v=_rotate(_rotate(_rotate(v,0,-eps),2,dpsi),0,eps+deps)
            return _rotate(v,2,-gast)
        return EclipseState(ShadowSphere.from_xyz(fixed(apparent(10)),radius_m=SUN_RADIUS_M),
                            ShadowSphere.from_xyz(fixed(apparent(301)),radius_m=MOON_RADIUS_M),
                            tt,ut1,self.kernel.sha256)
