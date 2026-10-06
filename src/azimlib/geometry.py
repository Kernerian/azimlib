"""Immutable geographic primitives and small, independently implemented algorithms.

Positions use longitude, latitude in degrees, optionally followed by elevation.
Distances are spherical metres. No topology or ellipsoidal accuracy is implied.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from math import asin, atan2, ceil, cos, degrees, floor, hypot, isfinite, pi, radians, sin, sqrt
from numbers import Real
from types import MappingProxyType
from collections.abc import Mapping

EARTH_RADIUS = 6_371_008.8


def _number(value, name="coordinate"):
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value):
        raise ValueError(f"{name} must be a finite number, got {value!r}")
    return float(value)


def position(value):
    """Validate and freeze a two- or three-dimensional geographic position."""
    if isinstance(value, (str, bytes, Mapping)):
        raise ValueError("a position must contain longitude, latitude[, elevation]")
    try:
        values = tuple(value)
    except TypeError as exc:
        raise ValueError("a position must be a sequence") from exc
    if len(values) not in (2, 3):
        raise ValueError("a position must contain longitude, latitude[, elevation]")
    values = tuple(_number(v) for v in values)
    if not -90 <= values[1] <= 90:
        raise ValueError("latitude must lie between -90 and 90 degrees")
    return values


def _sequence(value):
    if isinstance(value, (str, bytes, Mapping)):
        raise ValueError("coordinates must be sequences")
    try:
        return tuple(value)
    except TypeError as exc:
        raise ValueError("coordinates must be sequences") from exc


def _line(value, ring=False):
    coords = tuple(position(p) for p in _sequence(value))
    minimum = 4 if ring else 2
    if coords and len(coords) < minimum:
        raise ValueError(f"{'ring' if ring else 'line'} needs at least {minimum} positions")
    if ring and coords and coords[0] != coords[-1]:
        raise ValueError("polygon rings must be explicitly closed")
    return coords


def _polygon(value):
    rings = tuple(_line(r, ring=True) for r in _sequence(value))
    if rings and any(not ring for ring in rings):
        raise ValueError("polygon rings cannot be empty")
    return rings


def _freeze_json(value):
    if isinstance(value, Mapping):
        if any(not isinstance(k, str) for k in value):
            raise ValueError("property object keys must be strings")
        return MappingProxyType({k: _freeze_json(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(v) for v in value)
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, Real):
        _number(value, "property number")
        return value
    raise ValueError(f"property value {value!r} is not JSON serializable")


def _thaw_json(value):
    if isinstance(value, Mapping):
        return {k: _thaw_json(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(v) for v in value]
    return value


def _bounds(positions):
    iterator = iter(positions)
    first = next(iterator, None)
    if first is None:
        return None
    west = east = first[0]
    south = north = first[1]
    for point in iterator:
        west, east = min(west, point[0]), max(east, point[0])
        south, north = min(south, point[1]), max(north, point[1])
    return west, south, east, north


@dataclass(frozen=True)
class Geometry:
    """A GeoJSON geometry with immutable coordinate tuples.

    Empty coordinates are retained as empty geometries; nonempty rings must be
    closed. Longitude may be unwrapped, but latitude must be within +/-90°.
    """

    type: str
    coordinates: tuple = ()
    geometries: tuple = ()

    def __post_init__(self):
        kinds = {"Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon", "GeometryCollection"}
        if self.type not in kinds:
            raise ValueError(f"unknown geometry type {self.type!r}")
        coords = _sequence(self.coordinates)
        geometries = _sequence(self.geometries)
        if self.type == "GeometryCollection":
            if coords or any(not isinstance(g, Geometry) for g in geometries):
                raise ValueError("GeometryCollection requires Geometry objects and no coordinates")
        else:
            if geometries:
                raise ValueError("only GeometryCollection may have geometries")
            if self.type == "Point":
                coords = position(coords) if coords else ()
            elif self.type == "MultiPoint":
                coords = tuple(position(p) for p in coords)
            elif self.type == "LineString":
                coords = _line(coords)
            elif self.type == "MultiLineString":
                coords = tuple(_line(line) for line in coords)
            elif self.type == "Polygon":
                coords = _polygon(coords)
            elif self.type == "MultiPolygon":
                coords = tuple(_polygon(polygon) for polygon in coords)
        object.__setattr__(self, "coordinates", coords)
        object.__setattr__(self, "geometries", geometries)

    def iter_positions(self):
        if self.type == "GeometryCollection":
            for geometry in self.geometries:
                yield from geometry.iter_positions()
            return
        def descend(values):
            if values and isinstance(values[0], Real):
                yield values
            else:
                for child in values:
                    yield from descend(child)
        yield from descend(self.coordinates)

    @cached_property
    def bounds(self):
        """Unwrapped (west, south, east, north), or None for an empty geometry."""
        return _bounds(self.iter_positions())

    def to_geojson(self):
        if self.type == "GeometryCollection":
            return {"type": self.type, "geometries": [g.to_geojson() for g in self.geometries]}
        return {"type": self.type, "coordinates": _thaw_json(self.coordinates)}

    @property
    def __geo_interface__(self):
        return self.to_geojson()


@dataclass(frozen=True)
class Feature:
    geometry: Geometry | None
    properties: Mapping = field(default_factory=dict)
    id: str | int | float | None = None

    def __post_init__(self):
        if self.geometry is not None and not isinstance(self.geometry, Geometry):
            raise TypeError("feature geometry must be a Geometry or None")
        if self.properties is not None and not isinstance(self.properties, Mapping):
            raise ValueError("feature properties must be an object or null")
        if self.id is not None:
            if isinstance(self.id, bool) or not isinstance(self.id, (str, Real)):
                raise ValueError("feature id must be a string or finite number")
            if isinstance(self.id, Real):
                _number(self.id, "feature id")
        object.__setattr__(self, "properties", _freeze_json(self.properties or {}))

    @property
    def bounds(self):
        return self.geometry.bounds if self.geometry is not None else None

    def to_geojson(self):
        result = {"type": "Feature", "geometry": self.geometry.to_geojson() if self.geometry is not None else None,
                  "properties": _thaw_json(self.properties)}
        if self.id is not None:
            result["id"] = self.id
        return result

    @property
    def __geo_interface__(self):
        return self.to_geojson()


@dataclass(frozen=True)
class FeatureCollection:
    features: tuple = ()

    def __post_init__(self):
        features = tuple(self.features)
        if any(not isinstance(f, Feature) for f in features):
            raise TypeError("FeatureCollection accepts Feature objects")
        object.__setattr__(self, "features", features)

    def __iter__(self):
        return iter(self.features)

    def __len__(self):
        return len(self.features)

    def __getitem__(self, index):
        return self.features[index]

    def select(self, where=None, *, predicate=None, geometry_types=None):
        """Return a new collection, preserving feature objects, IDs and order.

        ``where`` maps property names to exact values. Missing keys do not
        match explicit None. All filters are combined with AND; a predicate
        receives a Feature. Geometry types match top-level types, not members
        of GeometryCollection. With no geometry filter, null geometries stay.
        This selects attributes; it does not perform a spatial intersection.
        """
        if where is None:
            where = {}
        if not isinstance(where, Mapping) or any(not isinstance(key, str) for key in where):
            raise TypeError("where must be a mapping with string property names")
        where = _freeze_json(where)
        if predicate is not None and not callable(predicate):
            raise TypeError("predicate must be callable or None")
        allowed = None
        if geometry_types is not None:
            known = {"Point", "MultiPoint", "LineString", "MultiLineString",
                     "Polygon", "MultiPolygon", "GeometryCollection"}
            try:
                allowed = frozenset((geometry_types,) if isinstance(geometry_types, str)
                                    else geometry_types)
            except TypeError as exc:
                raise TypeError("geometry_types must be a type name or iterable of names") from exc
            if not allowed <= known:
                raise ValueError("geometry_types contains an unsupported GeoJSON type")
        def matches(feature):
            if allowed is not None and (feature.geometry is None or feature.geometry.type not in allowed):
                return False
            if any(key not in feature.properties or feature.properties[key] != value
                   for key, value in where.items()):
                return False
            return predicate is None or bool(predicate(feature))
        return FeatureCollection(tuple(feature for feature in self.features if matches(feature)))

    @cached_property
    def bounds(self):
        boxes = [f.bounds for f in self.features if f.bounds is not None]
        return _bounds(p for west,south,east,north in boxes for p in ((west,south),(east,north)))

    @cached_property
    def _viewport_indexes(self):
        from .spatial import _ViewportIndexCache
        return _ViewportIndexCache()

    def to_geojson(self):
        return {"type": "FeatureCollection", "features": [f.to_geojson() for f in self.features]}

    @property
    def __geo_interface__(self):
        return self.to_geojson()


def wrap_longitude(longitude, central_longitude=0.0):
    """Wrap longitude into the central meridian's closed +/-180° interval."""
    delta = _number(longitude) - _number(central_longitude)
    wrapped = (delta + 180.0) % 360.0 - 180.0
    if wrapped == -180.0 and delta > 0:
        wrapped = 180.0
    return wrapped + central_longitude


def haversine(start, end, radius=EARTH_RADIUS):
    """Great-circle distance in metres on a sphere."""
    lon1, lat1 = position(start)[:2]
    lon2, lat2 = position(end)[:2]
    radius = _number(radius, "radius")
    if radius <= 0:
        raise ValueError("radius must be positive")
    phi1, phi2 = radians(lat1), radians(lat2)
    a = sin((phi2 - phi1) / 2) ** 2 + cos(phi1) * cos(phi2) * sin(radians(lon2 - lon1) / 2) ** 2
    return 2 * radius * asin(sqrt(min(1.0, max(0.0, a))))


def destination(lon, lat, bearing, distance, radius=EARTH_RADIUS):
    """Destination at a bearing clockwise from true north and metres of travel."""
    lon, lat = position((lon, lat))
    radius = _number(radius, "radius")
    if radius <= 0:
        raise ValueError("radius must be positive")
    delta, theta = _number(distance, "distance") / radius, radians(_number(bearing, "bearing"))
    phi, lam = radians(lat), radians(lon)
    phi2 = asin(max(-1, min(1, sin(phi) * cos(delta) + cos(phi) * sin(delta) * cos(theta))))
    lam2 = lam + atan2(sin(theta) * sin(delta) * cos(phi), cos(delta) - sin(phi) * sin(phi2))
    return wrap_longitude(degrees(lam2)), degrees(phi2)


def great_circle(start, end, steps=100):
    """Sample the shorter spherical arc; return steps+1 positions.

    Antipodal endpoints have no unique shortest arc and raise ValueError.
    """
    start, end = position(start)[:2], position(end)[:2]
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
        raise ValueError("steps must be a positive integer")
    def vector(point):
        lon, lat = map(radians, point)
        return cos(lat) * cos(lon), cos(lat) * sin(lon), sin(lat)
    a, b = vector(start), vector(end)
    cross = (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
    sine = sqrt(sum(v*v for v in cross))
    dot = sum(x*y for x, y in zip(a, b))
    angle = atan2(sine, dot)
    if pi - angle < 1e-12:
        raise ValueError("antipodal endpoints do not define a unique great circle")
    if angle < 1e-12:
        return tuple(start for _ in range(steps)) + (end,)
    result = [start]
    for i in range(1, steps):
        fraction = i / steps
        wa, wb = sin((1-fraction)*angle)/sine, sin(fraction*angle)/sine
        x, y, z = (wa*v + wb*w for v, w in zip(a, b))
        result.append((degrees(atan2(y, x)), degrees(atan2(z, hypot(x, y)))))
    result.append(end)
    return tuple(result)


def split_antimeridian(coordinates, central_longitude=0.0):
    """Split linear geographic segments at the projection's longitude seam.

    Intersections are linear in lon/lat (GeoJSON segment semantics). Densify
    great-circle routes with great_circle before calling this function.
    """
    coords = tuple(position(p)[:2] for p in coordinates)
    if not coords:
        return ()
    center = _number(central_longitude)
    west, east = center - 180, center + 180
    previous = (wrap_longitude(coords[0][0], center), coords[0][1])
    parts, current = [], [previous]
    for lon, lat in coords[1:]:
        point = (wrap_longitude(lon, center), lat)
        delta = point[0] - previous[0]
        if abs(delta) > 180:
            adjusted = point[0] - (360 if delta > 0 else -360)
            edge = west if delta > 0 else east
            t = (edge - previous[0]) / (adjusted - previous[0])
            crossing_lat = previous[1] + t * (lat - previous[1])
            current.append((edge, crossing_lat))
            parts.append(tuple(current))
            current = [(east if delta > 0 else west, crossing_lat), point]
        else:
            current.append(point)
        previous = point
    parts.append(tuple(current))
    return tuple(parts)


def clip_polygon_antimeridian(rings, central_longitude=0.0):
    """Clip polygon rings into longitude slabs for even-odd rendering.

    Returns a tuple of polygons, each a tuple of closed rings. Holes are
    retained in their exterior's longitude branch. This is a rendering clip,
    not a topological overlay: concave clipped rings can contain zero-width
    connecting edges. Polar caps already cut at a meridian and explicitly
    closed along a pole are supported. Uncut polar-enclosing polygons need a
    dedicated spherical polygon engine and are not supported here.
    """
    rings = _polygon(rings)
    if not rings:
        return ()
    center = _number(central_longitude)
    def unwrap(ring, reference=None):
        result = [(wrap_longitude(ring[0][0], center), ring[0][1])]
        for index, (lon, lat, *_) in enumerate(ring[1:], start=1):
            previous_original = ring[index-1]
            # RFC 7946 datasets often explicitly cut a polar cap using an
            # edge from +180 to -180 along the pole. That edge represents a
            # complete longitude span, not the zero-length shortest arc.
            pole_edge = abs(lat) == 90 and lat == previous_original[1] and abs(lon-previous_original[0]) > 180
            if pole_edge:
                lon = result[-1][0]+lon-previous_original[0]
            else:
                lon = wrap_longitude(lon, center)
                while lon - result[-1][0] > 180:
                    lon -= 360
                while lon - result[-1][0] < -180:
                    lon += 360
            result.append((lon, lat))
        if abs(result[-1][0] - result[0][0]) > 1e-8:
            raise ValueError("polar-enclosing rings are not supported by longitude clipping")
        if reference is not None:
            mean = sum(p[0] for p in result[:-1]) / (len(result)-1)
            shift = 360 * round((reference - mean) / 360)
            result = [(x+shift, y) for x, y in result]
        return result
    outer = unwrap(rings[0])
    reference = sum(p[0] for p in outer[:-1]) / (len(outer)-1)
    unwrapped = [outer] + [unwrap(r, reference) for r in rings[1:]]
    def clip(ring, boundary, keep_greater):
        result = []
        vertices = ring[:-1] if ring and ring[0] == ring[-1] else ring
        if not vertices:
            return []
        a = vertices[-1]
        a_inside = a[0] >= boundary if keep_greater else a[0] <= boundary
        for b in vertices:
            b_inside = b[0] >= boundary if keep_greater else b[0] <= boundary
            if a_inside != b_inside:
                t = (boundary-a[0])/(b[0]-a[0])
                result.append((boundary, a[1]+t*(b[1]-a[1])))
            if b_inside:
                result.append(b)
            a, a_inside = b, b_inside
        if result:
            result.append(result[0])
        return result
    xmin, xmax = min(p[0] for p in outer), max(p[0] for p in outer)
    first, last = floor((xmin-center+180)/360), floor((xmax-center+180)/360)
    polygons = []
    for slab in range(first, last+1):
        west, east = center-180+360*slab, center+180+360*slab
        result = []
        for index, ring in enumerate(unwrapped):
            clipped = clip(clip(ring, west, True), east, False)
            area = abs(sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(clipped, clipped[1:])))
            if len(clipped) >= 4 and area > 1e-12:
                result.append(tuple((x-360*slab, y) for x, y in clipped))
            elif index == 0:
                break
        else:
            if result:
                polygons.append(tuple(result))
    return tuple(polygons)


def clip_orthographic_polygon(rings, projection, *, step=2.0):
    """Clip small spherical polygons to an Orthographic view, including its limb.

    Return a tuple of polygons, each a tuple of closed projected-metre rings,
    suitable for an even-odd path. Disconnected pieces of one input polygon
    share a compound path, preserving the clipping of its holes.
    Edges are first sampled linearly in geographic coordinates at at most
    ``step`` degrees, then intersected with the visible hemisphere. Horizon
    arcs are stitched by testing their midpoint against the spherical ring.
    Each ring denotes its smaller spherical interior (less than a hemisphere).
    Self-intersections and polygons intentionally covering most of Earth are
    unsupported; this is a rendering clip, not a general topology operation.
    """
    rings = _polygon(rings)
    step = _number(step, "step")
    if not 0 < step <= 10:
        raise ValueError("step must be greater than zero and at most ten degrees")
    if getattr(projection, "name", None) != "orthographic":
        raise TypeError("clip_orthographic_polygon requires an Orthographic projection")
    phi0 = radians(projection.central_latitude)
    def vector(point):
        lam, phi = radians(point[0]-projection.central_longitude), radians(point[1])
        return (cos(phi)*sin(lam), cos(phi0)*sin(phi)-sin(phi0)*cos(phi)*cos(lam),
                sin(phi0)*sin(phi)+cos(phi0)*cos(phi)*cos(lam))
    def dot(a, b):
        return sum(v*w for v, w in zip(a, b))
    def cross(a, b):
        return a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]
    output = []
    for ring in rings:
        sampled = []
        for a, b in zip(ring, ring[1:]):
            delta = wrap_longitude(b[0]-a[0])
            count = max(1, ceil(max(abs(delta), abs(b[1]-a[1]))/step))
            for i in range(count):
                fraction = i/count
                point = vector((a[0]+delta*fraction, a[1]+(b[1]-a[1])*fraction))
                if not sampled or sum((x-y)**2 for x, y in zip(sampled[-1], point)) > 1e-24:
                    sampled.append(point)
        if len(sampled) < 3:
            continue
        sampled.append(sampled[0])
        # Triangle solid angles establish which winding sign denotes the
        # smaller spherical interior, even if input ring winding is reversed.
        anchor = sampled[0]
        signed_area = sum(2*atan2(dot(anchor, cross(a, b)), 1+dot(anchor, a)+dot(a, b)+dot(b, anchor))
                          for a, b in zip(sampled[1:], sampled[2:]))
        signed_area = (signed_area+2*pi) % (4*pi)-2*pi
        if abs(signed_area) < 1e-14:
            continue
        def inside(point):
            total = 0.0
            for a, b in zip(sampled, sampled[1:]):
                total += atan2(dot(point, cross(a, b)), dot(a, b)-dot(point, a)*dot(point, b))
            return abs(total) > pi and total*signed_area > 0
        nodes, adjacency, edges, crossings = {}, {}, [], []
        def node(point):
            key = (round(point[0], 11), round(point[1], 11))
            nodes[key] = point[:2]
            return key
        def edge(a, b):
            ka, kb = node(a), node(b)
            if ka == kb:
                return
            index = len(edges)
            edges.append((ka, kb))
            adjacency.setdefault(ka, []).append(index)
            adjacency.setdefault(kb, []).append(index)
        def horizon_intersection(a, b):
            fraction = a[2]/(a[2]-b[2])
            x, y = a[0]+fraction*(b[0]-a[0]), a[1]+fraction*(b[1]-a[1])
            length = hypot(x, y)
            if length < 1e-14:
                raise ValueError("antipodal polygon segment cannot be clipped uniquely")
            return x/length, y/length, 0.0
        for a, b in zip(sampled, sampled[1:]):
            front_a, front_b = a[2] >= 0, b[2] >= 0
            if front_a and front_b:
                edge(a, b)
            elif front_a != front_b:
                crossing = horizon_intersection(a, b)
                crossings.append(crossing)
                edge(a, crossing) if front_a else edge(crossing, b)
        unique = {node(p): p for p in crossings}
        ordered = sorted(unique.values(), key=lambda p: atan2(p[1], p[0]) % (2*pi))
        if len(ordered) > 1:
            for index, a in enumerate(ordered):
                b = ordered[(index+1) % len(ordered)]
                start = atan2(a[1], a[0]) % (2*pi)
                finish = atan2(b[1], b[0]) % (2*pi)
                if finish <= start:
                    finish += 2*pi
                middle = (start+finish)/2
                # Slightly inside the visible hemisphere avoids ambiguous
                # winding exactly on a coincident polygon/horizon boundary.
                epsilon = 1e-7
                test = (cos(middle)*cos(epsilon), sin(middle)*cos(epsilon), sin(epsilon))
                if inside(test):
                    count = max(1, ceil(degrees(finish-start)/step))
                    previous = a
                    for j in range(1, count+1):
                        angle = start+(finish-start)*j/count
                        current = b if j == count else (cos(angle), sin(angle), 0)
                        edge(previous, current)
                        previous = current
        # Pre-cut polar caps contain a retraced meridian from coastline to
        # pole and back. It is a planar GeoJSON closure, not a spherical
        # boundary; coincident opposite edges cancel under even-odd filling.
        parity = {}
        for ka, kb in edges:
            key = tuple(sorted((ka, kb)))
            if key in parity:
                del parity[key]
            else:
                parity[key] = (ka, kb)
        edges = list(parity.values())
        adjacency = {}
        for index, (ka, kb) in enumerate(edges):
            adjacency.setdefault(ka, []).append(index)
            adjacency.setdefault(kb, []).append(index)
        if not edges:
            continue
        if any(len(links) != 2 for links in adjacency.values()):
            raise ValueError("polygon horizon clipping encountered unsupported degenerate topology")
        visited = set()
        for index, (start, _) in enumerate(edges):
            if index in visited:
                continue
            vertices, current, next_edge = [nodes[start]], start, index
            while next_edge not in visited:
                visited.add(next_edge)
                ka, kb = edges[next_edge]
                current = kb if current == ka else ka
                vertices.append(nodes[current])
                next_edge = next(i for i in adjacency[current] if i != next_edge)
            if current != start:
                raise ValueError("polygon horizon clipping did not produce a closed ring")
            if len(vertices) >= 4:
                output.append(tuple((x*projection.radius, y*projection.radius) for x, y in vertices))
    return (tuple(output),) if output else ()


def longitude_bounds(longitudes):
    """Shortest circular interval, returned increasing, possibly east>180.

    For point samples, not polygon interiors spanning most of Earth. Equal
    largest gaps are resolved deterministically. Empty input is invalid.
    """
    values=sorted(set(_number(lon)%360 for lon in longitudes))
    if not values:raise ValueError('longitude_bounds requires points')
    if len(values)==1:
        lon=wrap_longitude(values[0]);return lon,lon
    gaps=[((values[(i+1)%len(values)]-v)%360,i) for i,v in enumerate(values)]
    gap,index=max(gaps,key=lambda item:(item[0],-item[1]))
    west=wrap_longitude(values[(index+1)%len(values)]);return west,west+360-gap


def clip_orthographic_line(coordinates,projection,*,step=2.0):
    """Projected-metre line parts ending exactly on the visible horizon.

    GeoJSON edges interpolate lon/lat in the shorter longitude branch, sampled
    at most step degrees. Visibility crossings are bisected on that edge.
    This is a bounded rendering approximation, not great-circle topology.
    """
    points=tuple(position(p)[:2] for p in coordinates);step=_number(step,'step')
    if not 0<step<=10:raise ValueError('step must be greater than zero and at most ten degrees')
    if getattr(projection,'name',None)!='orthographic':raise TypeError('Requires Orthographic projection')
    if len(points)<2:return ()
    sampled=[points[0]]
    for a,b in zip(points,points[1:]):
        delta=wrap_longitude(b[0]-a[0]);count=max(1,ceil(max(abs(delta),abs(b[1]-a[1]))/step))
        sampled.extend((a[0]+delta*i/count,a[1]+(b[1]-a[1])*i/count) for i in range(1,count+1))
    groups=[];current=[]
    def project(point):
        # Snap roundoff at the limb through the front-side limit.
        p=projection.forward(*point)
        if p is None:return None
        return p
    def append(point):
        p=project(point)
        if p is not None and (not current or hypot(p[0]-current[-1][0],p[1]-current[-1][1])>1e-8):current.append(p)
    def flush():
        if len(current)>1:groups.append(tuple(current))
        current.clear()
    for a,b in zip(sampled,sampled[1:]):
        va,vb=projection.visibility(*a),projection.visibility(*b);fa,fb=va>=0,vb>=0
        if fa:append(a)
        if fa!=fb:
            lo,hi=0.,1.
            for _ in range(48):
                mid=(lo+hi)/2;v=projection.visibility(a[0]+(b[0]-a[0])*mid,a[1]+(b[1]-a[1])*mid)
                if (v>=0)==fa:lo=mid
                else:hi=mid
            t=lo if fa else hi
            append((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t))
            if not fb:flush()
        if fb:append(b)
        else:flush()
    flush();return tuple(groups)
