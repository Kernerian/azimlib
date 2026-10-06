"""Opt-in regional planar topology, not spherical overlay or automatic repair.

Longitude seams are unwrapped before polygon checks. Tests refer to straight
lon/lat segments in this branch, not great-circle intersections. Cost is O(n²).
"""
from dataclasses import dataclass
from fractions import Fraction
from math import fsum
from .geometry import position, wrap_longitude, Geometry, _number


def _point(value): return position(value)[:2]


def orientation(a,b,c):
    """Exact sign of the binary-float 2D determinant: -1, 0 or 1."""
    a,b,c=map(_point,(a,b,c));x=(b[0]-a[0])*(c[1]-a[1]);y=(b[1]-a[1])*(c[0]-a[0]);d=x-y
    if abs(d)>8e-16*(abs(x)+abs(y)):return 1 if d>0 else -1
    ax,ay,bx,by,cx,cy=map(Fraction,(*a,*b,*c));d=(bx-ax)*(cy-ay)-(by-ay)*(cx-ax)
    return (d>0)-(d<0)


@dataclass(frozen=True)
class Intersection:
    kind: str
    points: tuple = ()


def segment_intersection(a,b,c,d):
    """Return none, point or overlap, including endpoints and zero-length edges."""
    a,b,c,d=map(_point,(a,b,c,d))
    def on(p,u,v):return orientation(u,v,p)==0 and all(min(u[i],v[i])<=p[i]<=max(u[i],v[i]) for i in (0,1))
    hits=sorted(set(p for p in (a,b,c,d) if on(p,a,b) and on(p,c,d)))
    if hits:return Intersection('point' if len(hits)==1 else 'overlap',tuple((hits[0],) if len(hits)==1 else (hits[0],hits[-1])))
    o1,o2,o3,o4=orientation(a,b,c),orientation(a,b,d),orientation(c,d,a),orientation(c,d,b)
    if o1*o2<0 and o3*o4<0:
        # Exact rational location avoids cancellation near parallel edges.
        ax,ay,bx,by,cx,cy,dx,dy=map(Fraction,(*a,*b,*c,*d))
        t=((cx-ax)*(dy-cy)-(cy-ay)*(dx-cx))/((bx-ax)*(dy-cy)-(by-ay)*(dx-cx))
        return Intersection('point',((float(ax+t*(bx-ax)),float(ay+t*(by-ay))),))
    return Intersection('none')


def _unwrap(ring,center=None):
    points=tuple(map(_point,ring))
    if not points:return points
    first=points[0][0] if center is None else wrap_longitude(points[0][0],center)
    output=[(first,points[0][1])]
    for p in points[1:]:output.append((output[-1][0]+wrap_longitude(p[0]-output[-1][0]),p[1]))
    return tuple(output)


def ring_orientation(ring):
    points=_unwrap(ring)
    if len(points)<3:return 'degenerate'
    origin=points[0];area=fsum((a[0]-origin[0])*(b[1]-origin[1])-(b[0]-origin[0])*(a[1]-origin[1]) for a,b in zip(points,points[1:]+points[:1]))
    return 'counterclockwise' if area>0 else 'clockwise' if area<0 else 'degenerate'


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: tuple
    message: str


@dataclass(frozen=True)
class TopologyReport:
    issues: tuple
    @property
    def valid(self):return not self.issues
    def raise_if_invalid(self):
        if self.issues:raise ValueError('; '.join(f'{i.code} at {i.path}: {i.message}' for i in self.issues))
        return self


def validate_ring(ring,*,winding=None):
    if winding not in (None,'clockwise','counterclockwise'):raise ValueError('Invalid winding')
    points=_unwrap(ring);issues=[]
    def issue(code,path,message):issues.append(ValidationIssue(code,path,message))
    if len(points)<4:issue('too_short',(),'A closed ring needs at least four positions')
    if points and points[0]!=points[-1]:issue('not_closed',(),'Ring is not closed in the regional longitude branch')
    orient=ring_orientation(points)
    if orient=='degenerate':issue('zero_area',(),'Ring has zero signed area')
    elif winding and orient!=winding:issue('winding',(),f'Expected {winding}')
    edges=list(zip(points,points[1:]))
    for i,(a,b) in enumerate(edges):
        if a==b:issue('zero_edge',(i,),'Consecutive positions coincide')
        for j,(c,d) in enumerate(edges[i+1:],i+1):
            adjacent=j==i+1 or i==0 and j==len(edges)-1
            hit=segment_intersection(a,b,c,d)
            if hit.kind!='none' and (not adjacent or hit.kind=='overlap'):
                issue('self_intersection',(i,j),'Ring edges intersect or overlap')
    return TopologyReport(tuple(issues))


def _inside(point,ring):
    x,y=point;inside=False
    for a,b in zip(ring,ring[1:]):
        if segment_intersection(point,point,a,b).kind!='none':return 'boundary'
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return 'inside' if inside else 'outside'


def validate_geometry(geometry,*,require_winding=False):
    """Check rings/holes and multipolygon interiors in a regional lon/lat plane.

    Does not repair input, verify a global land tessellation or reject all
    spherical polar ambiguities. Geometry construction remains permissive.
    """
    if not isinstance(geometry,Geometry):raise TypeError('geometry must be Geometry')
    if geometry.type=='GeometryCollection':
        return TopologyReport(tuple(ValidationIssue(i.code,(j,)+i.path,i.message) for j,g in enumerate(geometry.geometries) for i in validate_geometry(g,require_winding=require_winding).issues))
    if geometry.type not in ('Polygon','MultiPolygon'):return TopologyReport(())
    polygons=(geometry.coordinates,) if geometry.type=='Polygon' else geometry.coordinates
    issues=[];prepared=[]
    for p,rings in enumerate(polygons):
        center=rings[0][0][0] if rings and rings[0] else 0
        aligned=[_unwrap(r,center) for r in rings];prepared.append(aligned)
        for j,ring in enumerate(aligned):
            winding=('counterclockwise' if j==0 else 'clockwise') if require_winding else None
            issues.extend(ValidationIssue(i.code,(p,j)+i.path,i.message) for i in validate_ring(ring,winding=winding).issues)
            if j and ring and _inside(ring[0],aligned[0])!='inside':issues.append(ValidationIssue('hole_outside',(p,j),'Hole must be strictly inside its shell'))
            for k,other in enumerate(aligned[:j]):
                if any(segment_intersection(a,b,c,d).kind!='none' for a,b in zip(ring,ring[1:]) for c,d in zip(other,other[1:])):
                    issues.append(ValidationIssue('boundary_intersection',(p,k,j),'Ring boundaries cross or touch'))
                if k>0 and ring and other and (_inside(ring[0],other)=='inside' or _inside(other[0],ring)=='inside'):
                    issues.append(ValidationIssue('nested_holes',(p,k,j),'Holes overlap or contain each other'))
    for p,rings in enumerate(prepared):
        if not rings:continue
        for q,others in enumerate(prepared[:p]):
            if not others:continue
            # Shift the other polygon to the same longitude branch.
            shifted=[_unwrap(r,rings[0][0][0]) for r in others]
            crossing=any(segment_intersection(a,b,c,d).kind=='overlap' or (orientation(a,b,c)*orientation(a,b,d)<0 and orientation(c,d,a)*orientation(c,d,b)<0) for r in rings for o in shifted for a,b in zip(r,r[1:]) for c,d in zip(o,o[1:]))
            def interior(point,poly):return _inside(point,poly[0])=='inside' and not any(_inside(point,h)!='outside' for h in poly[1:])
            containment=any(interior(v,shifted) for v in rings[0][:-1]) or any(interior(v,rings) for v in shifted[0][:-1])
            if crossing or containment:issues.append(ValidationIssue('polygon_overlap',(q,p),'Multipolygon interiors/boundaries overlap'))
    return TopologyReport(tuple(issues))
