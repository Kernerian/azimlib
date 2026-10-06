"""Own regional ellipsoidal Transverse Mercator series (Snyder, USGS 1395).

The bounded series is intended for UTM/regional maps: latitude [-80,84],
longitude within six degrees of the central meridian. Not a global TM solver.
"""
from math import sin, cos, tan, sqrt, radians, degrees, pi
from .geometry import position, wrap_longitude, _number
from .geodesy import WGS84, Ellipsoid


def utm_zone(longitude, latitude):
    lon,lat=position((longitude,latitude))
    if not -180<=lon<=180 or not -80<=lat<=84: raise ValueError('UTM requires lon [-180,180], lat [-80,84]')
    zone=min(60,int((lon+180)//6)+1)
    if 56<=lat<64 and 3<=lon<12: zone=32
    if 72<=lat<=84 and 0<=lon<42:
        zone=31 if lon<9 else 33 if lon<21 else 35 if lon<33 else 37
    return zone


def utm_crs(longitude,latitude):
    from .crs import CRS
    zone=utm_zone(longitude,latitude)
    return CRS((32600 if latitude>=0 else 32700)+zone)


def _arc(phi,e,a):
    return a*((1-e/4-3*e**2/64-5*e**3/256)*phi
        -(3*e/8+3*e**2/32+45*e**3/1024)*sin(2*phi)
        +(15*e**2/256+45*e**3/1024)*sin(4*phi)-35*e**3/3072*sin(6*phi))


def tm_forward(lon,lat,*,central_longitude=0,central_latitude=0,scale_factor=.9996,
               false_easting=0,false_northing=0,ellipsoid=WGS84):
    lon,lat=position((lon,lat));dl=wrap_longitude(lon-central_longitude)
    if abs(dl)>6+1e-10 or not -80<=lat<=84: raise ValueError('Regional TM domain: lat [-80,84], longitude within 6 degrees of central meridian')
    p=radians(lat);e=ellipsoid.eccentricity_squared;a=ellipsoid.semi_major_axis
    ep=e/(1-e);t=tan(p)**2;c=ep*cos(p)**2;A=cos(p)*radians(dl);N=a/sqrt(1-e*sin(p)**2)
    x=N*(A+(1-t+c)*A**3/6+(5-18*t+t*t+72*c-58*ep)*A**5/120)
    y=_arc(p,e,a)-_arc(radians(central_latitude),e,a)+N*tan(p)*(A*A/2+(5-t+9*c+4*c*c)*A**4/24+(61-58*t+t*t+600*c-330*ep)*A**6/720)
    return false_easting+scale_factor*x,false_northing+scale_factor*y


def tm_inverse(x,y,*,central_longitude=0,central_latitude=0,scale_factor=.9996,
               false_easting=0,false_northing=0,ellipsoid=WGS84):
    x,y=_number(x),_number(y);a=ellipsoid.semi_major_axis;e=ellipsoid.eccentricity_squared
    M=(y-false_northing)/scale_factor+_arc(radians(central_latitude),e,a)
    mu=M/(a*(1-e/4-3*e*e/64-5*e**3/256));e1=(1-sqrt(1-e))/(1+sqrt(1-e))
    p=mu+(3*e1/2-27*e1**3/32)*sin(2*mu)+(21*e1*e1/16-55*e1**4/32)*sin(4*mu)+151*e1**3/96*sin(6*mu)+1097*e1**4/512*sin(8*mu)
    if abs(p)>pi/2 or abs(cos(p))<1e-12: raise ValueError('Coordinate outside regional TM domain')
    ep=e/(1-e);t=tan(p)**2;c=ep*cos(p)**2;N=a/sqrt(1-e*sin(p)**2);R=a*(1-e)/(1-e*sin(p)**2)**1.5;D=(x-false_easting)/(scale_factor*N)
    lat=degrees(p-N*tan(p)/R*(D*D/2-(5+3*t+10*c-4*c*c-9*ep)*D**4/24+(61+90*t+298*c+45*t*t-252*ep-3*c*c)*D**6/720))
    lon=central_longitude+degrees((D-(1+2*t+c)*D**3/6+(5-2*c+28*t-3*c*c+8*ep+24*t*t)*D**5/120)/cos(p))
    # Refine the inverse against our same forward series, not an external solver.
    parameters=dict(central_longitude=central_longitude,central_latitude=central_latitude,scale_factor=scale_factor,false_easting=false_easting,false_northing=false_northing,ellipsoid=ellipsoid)
    if not -80-1e-6<=lat<=84+1e-6 or abs(lon-central_longitude)>6+1e-5: raise ValueError('Coordinate outside regional TM domain')
    lat=max(-80,min(84,lat));lon=max(central_longitude-6,min(central_longitude+6,lon))
    for _ in range(4):
        fx,fy=tm_forward(lon,lat,**parameters);rx,ry=x-fx,y-fy
        if max(abs(rx),abs(ry))<1e-7: break
        h=1e-5
        # Use inward differences so exact domain edges remain legal.
        hl=-h if lon-central_longitude>5.99 else h;hp=-h if lat>83.99 else h
        lx,ly=tm_forward(lon+hl,lat,**parameters);px,py=tm_forward(lon,lat+hp,**parameters)
        j0,j1,j2,j3=(lx-fx)/hl,(px-fx)/hp,(ly-fy)/hl,(py-fy)/hp;det=j0*j3-j1*j2
        if abs(det)<1e-12: raise ArithmeticError('Singular regional TM inverse')
        lon+=(rx*j3-ry*j1)/det;lat+=(ry*j0-rx*j2)/det
        if not -80-1e-9<=lat<=84+1e-9 or abs(lon-central_longitude)>6+1e-9: raise ValueError('Coordinate outside regional TM domain')
        lat=max(-80,min(84,lat));lon=max(central_longitude-6,min(central_longitude+6,lon))
    fx,fy=tm_forward(lon,lat,**parameters)
    if max(abs(fx-x),abs(fy-y))>1e-4: raise ArithmeticError('Regional TM inverse did not converge')
    return wrap_longitude(lon),lat
