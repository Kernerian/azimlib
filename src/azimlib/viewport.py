"""Geographic extent → projected meters → screen pixels, preserving aspect."""
from __future__ import annotations
import math
from functools import lru_cache
from .projections import (Equirectangular, Mercator, EqualEarth, Orthographic,
                          LambertConformalConic, AlbersEqualArea, TransverseMercator, Stereographic, AzimuthalEquidistant)
from .geometry import wrap_longitude


_BUILTINS = (Equirectangular, Mercator, EqualEarth, Orthographic,
             LambertConformalConic, AlbersEqualArea, TransverseMercator, Stereographic, AzimuthalEquidistant)


def _projected_bounds(projection, extent):
    west, south, east, north = extent
    points = []
    for i in range(49):
        lon = west + (east-west)*i/48
        for j in range(25):
            lat = south + (north-south)*j/24
            p = projection.forward(lon, lat)
            if p is not None and all(math.isfinite(v) for v in p):
                points.append(p)
    if not points:
        raise ValueError("Extent is entirely outside the projection's visible domain")
    x0, x1 = min(p[0] for p in points), max(p[0] for p in points)
    y0, y1 = min(p[1] for p in points), max(p[1] for p in points)
    if x1-x0 < 1e-8 or y1-y0 < 1e-8:
        raise ValueError("Extent has zero projected area")
    return x0, y0, x1, y1


# Only exact, immutable built-in classes are eligible. Custom subclasses can
# depend on mutable resources or override forward; never cache them implicitly.
_cached_bounds = lru_cache(maxsize=128)(_projected_bounds)


def _geometry_projected_bounds(projection, bounds):
    """A monotonic cylindrical envelope, or None if it needs the full path."""
    if bounds is None or type(projection) not in (Equirectangular, Mercator):
        return None
    west,south,east,north = bounds
    if east-west >= 180:
        return None
    center = projection.central_longitude
    low,high = wrap_longitude(west,center),wrap_longitude(east,center)
    if low > high or abs((high-low)-(east-west)) > 1e-8:
        return None
    if type(projection) is Mercator:
        limit = projection.max_latitude
        if north < -limit or south > limit:
            return None
        south,north = max(south,-limit),min(north,limit)
    a,b = projection.forward(low,south),projection.forward(high,north)
    if a is None or b is None or not all(math.isfinite(v) for point in (a,b) for v in point):
        return None
    return min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])


class Viewport:
    def __init__(self, projection, extent, box):
        self.projection, self.extent, self.box = projection, extent, box
        bounds = _cached_bounds if type(projection) in _BUILTINS else _projected_bounds
        self.projected_bounds = bounds(projection, tuple(extent))
        x0,y0,x1,y1 = self.projected_bounds
        bx, by, bw, bh = box
        self.scale = min(bw/(x1-x0), bh/(y1-y0))
        self.ox = bx + (bw-(x1-x0)*self.scale)/2 - x0*self.scale
        self.oy = by + (bh-(y1-y0)*self.scale)/2 + y1*self.scale

    def xy(self, x, y):
        return self.ox+x*self.scale, self.oy-y*self.scale

    def project(self, lon, lat):
        point = self.projection.forward(lon, lat)
        return self.xy(*point) if point is not None else None

    def inverse(self, px, py):
        return self.projection.inverse((px-self.ox)/self.scale, (self.oy-py)/self.scale)

    def inside(self, point):
        x, y, w, h = self.box
        return point is not None and x <= point[0] <= x+w and y <= point[1] <= y+h

    def may_intersect(self, bounds, padding=0):
        """Conservative cylindrical bounds test in display units.

        Seam-spanning, wide and unsupported-projection geometries are retained.
        The projected rectangle (including overscan), not the geographic input
        extent, defines visibility. An enclosing polygon must remain visible.
        """
        envelope = _geometry_projected_bounds(self.projection,bounds)
        if envelope is None:
            return True
        west,south,east,north = envelope
        a,b = self.xy(west,south),self.xy(east,north)
        x,y,w,h = self.box
        return not (max(a[0],b[0])+padding < x or min(a[0],b[0])-padding > x+w or
                    max(a[1],b[1])+padding < y or min(a[1],b[1])-padding > y+h)

    def _query_bounds(self,padding):
        """Projected query envelope with roundoff overscan for an index."""
        x,y,w,h = self.box
        bounds=((x-padding-self.ox)/self.scale,(self.oy-y-h-padding)/self.scale,
                (x+w+padding-self.ox)/self.scale,(self.oy-y+padding)/self.scale)
        epsilon=max(1e-9,1e-12*max(abs(v) for v in bounds))
        return bounds[0]-epsilon,bounds[1]-epsilon,bounds[2]+epsilon,bounds[3]+epsilon


def densify(points, step=2.):
    if not points:
        return []
    result = [points[0][:2]]
    for a, b in zip(points, points[1:]):
        count = max(1, math.ceil(max(abs(b[0]-a[0]), abs(b[1]-a[1]))/step))
        for i in range(1, count+1):
            t = i/count
            result.append((a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t))
    return result
