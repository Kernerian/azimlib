"""Geographic extent → projected meters → screen pixels, preserving aspect."""
from __future__ import annotations
import math


class Viewport:
    def __init__(self, projection, extent, box):
        self.projection, self.extent, self.box = projection, extent, box
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
        self.projected_bounds = (x0, y0, x1, y1)
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
