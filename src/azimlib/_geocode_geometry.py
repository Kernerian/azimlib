"""Own representatives, spherical nearest points and conservative search boxes."""
from math import asin, cos, degrees, floor, pi, radians, sin

from .geometry import Geometry, position, EARTH_RADIUS
from . import _overlay_sphere as sphere
from . import _overlay_planar as plane


def coordinate(value):
    p = position(value)
    if len(p) != 2 or not -180 <= p[0] <= 180:
        raise ValueError('Geocoding requires 2D WGS84 longitude [-180,180], latitude [-90,90]')
    return p


def lines(geometry):
    if geometry.type == 'LineString': return (geometry.coordinates,)
    if geometry.type == 'MultiLineString': return geometry.coordinates
    if geometry.type == 'Polygon': return geometry.coordinates
    if geometry.type == 'MultiPolygon': return tuple(r for p in geometry.coordinates for r in p)
    return ()


def at_fraction(line, fraction):
    lengths = [sphere.angle(sphere.vector(a), sphere.vector(b)) for a,b in zip(line,line[1:])]
    total = sum(lengths)
    if not total: return line[0]
    wanted = fraction*total
    for (a,b), length in zip(zip(line,line[1:]), lengths):
        if wanted <= length and length:
            a,b = sphere.vector(a),sphere.vector(b)
            t = max(0., min(1., wanted/length))
            return sphere.coordinate(sphere.unit(sphere.add(sphere.mul(a,sin((1-t)*length)),
                                                            sphere.mul(b,sin(t*length)))))
        wanted -= length
    return line[-1]


def representative(geometry):
    positions = tuple(geometry.iter_positions())
    if not positions: raise ValueError('Empty geocoding geometry')
    for p in positions: coordinate(p)
    if geometry.type == 'Point': return geometry.coordinates, 'source_point'
    if geometry.type in ('LineString','MultiLineString'):
        paths = lines(geometry)
        for line in paths:
            for a,b in zip(line,line[1:]):
                if sphere.angle(sphere.vector(a),sphere.vector(b)) > pi-1e-8:
                    raise ValueError('Antipodal street segment has no unique minor arc')
        longest = max(paths,key=lambda l:sum(sphere.angle(sphere.vector(a),sphere.vector(b)) for a,b in zip(l,l[1:])))
        return at_fraction(longest,.5), 'centerline_representative'
    if geometry.type not in ('Polygon','MultiPolygon'):
        raise ValueError('Geocoding supports points, lines and regional polygons')
    if geometry.bounds[2]-geometry.bounds[0] >= 180:
        raise ValueError('Administrative/address polygons require a regional lon/lat domain below 180 degrees')
    # Exact planar validation and scanline interior; never place a marker in a hole.
    from .topology import validate_geometry
    if not validate_geometry(geometry).valid: raise ValueError('Invalid geocoding polygon')
    shape = plane.prepare(geometry,validate=False)
    levels = sorted({plane.point(p)[1] for p in positions})
    best = None
    for low,high in zip(levels,levels[1:]):
        y = (low+high)/2; hits = []
        for ring in lines(geometry):
            for p,q in zip(ring,ring[1:]):
                a,b = plane.point(p),plane.point(q)
                if min(a[1],b[1]) < y < max(a[1],b[1]):
                    hits.append(a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]))
        hits = sorted(set(hits))
        for left,right in zip(hits,hits[1:]):
            point = ((left+right)/2,y)
            if shape.location(point) == 1 and (best is None or right-left > best[0]):
                best = (right-left,point)
    if best is None: raise ValueError('Polygon has no resolved interior representative')
    return tuple(map(float,best[1])), 'boundary_representative'


def nearest(geometry, query):
    query = coordinate(query); p = sphere.vector(query)
    if geometry.type == 'Point':
        return geometry.coordinates, EARTH_RADIUS*sphere.angle(p,sphere.vector(geometry.coordinates)),False
    if geometry.type in ('Polygon','MultiPolygon') and plane.prepare(geometry,validate=False).location(plane.point(query)) >= 0:
        return query,0.,True
    candidates = []
    for line in lines(geometry):
        for start,end in zip(line,line[1:]):
            a,b = sphere.vector(start),sphere.vector(end)
            candidates.extend((a,b))
            if sphere.angle(a,b) < 1e-14: continue
            n = sphere.unit(sphere.cross(a,b))
            foot = sphere.add(p,sphere.mul(n,-sphere.dot(p,n)))
            if sphere.norm(foot) > 1e-14:
                foot = sphere.unit(foot)
                if sphere.on_arc(foot,a,b,1e-10): candidates.append(foot)
    found = min(candidates,key=lambda v:sphere.angle(p,v))
    return sphere.coordinate(found), EARTH_RADIUS*sphere.angle(p,found),False


def bounds(geometry):
    west,south,east,north = geometry.bounds
    if geometry.type in ('LineString','MultiLineString','Polygon','MultiPolygon'):
        for line in lines(geometry):
            for a,b in zip(line,line[1:]):
                va,vb = sphere.vector(a),sphere.vector(b)
                if sphere.angle(va,vb) < 1e-14: continue
                box = sphere.arc_box(va,vb,1e-10)
                south = min(south,degrees(asin(max(-1.,box[2]))))
                north = max(north,degrees(asin(min(1.,box[5]))))
                if abs(a[0]-b[0]) > 180: west,east = -180.,180.
    return west,max(-90.,south),east,min(90.,north)


def cap_boxes(query, metres):
    lon,lat = coordinate(query); angle = metres/EARTH_RADIUS
    south,north = max(-90.,lat-degrees(angle)),min(90.,lat+degrees(angle))
    if south == -90 or north == 90 or angle >= pi/2: return ((-180.,south,180.,north),)
    width = degrees(asin(min(1.,sin(angle)/cos(radians(lat)))))
    west,east = lon-width,lon+width
    if width==0 and abs(lon)==180:
        return ((-180.,south,-180.,north),(180.,south,180.,north))
    if west < -180: return ((-180.,south,east,north),(west+360,south,180.,north))
    if east > 180: return ((west,south,180.,north),(-180.,south,east-360,north))
    return ((west,south,east,north),)


def cells(box, level):
    n = 2**level; west,south,east,north = box
    x0 = min(n-1,max(0,floor((west+180)/360*n)))
    x1 = min(n-1,max(0,floor((east+180)/360*n)))
    y0 = min(n-1,max(0,floor((south+90)/180*n)))
    y1 = min(n-1,max(0,floor((north+90)/180*n)))
    return x0,y0,x1,y1


def postings(geometry):
    box = bounds(geometry)
    for level in range(12,-1,-1):
        x0,y0,x1,y1 = cells(box,level)
        if (x1-x0+1)*(y1-y0+1) <= 16:
            return tuple((level,x,y) for x in range(x0,x1+1) for y in range(y0,y1+1))
