"""Own exact-rational planar arrangement; no coordinate wrapping or snapping.

Constructions retain Fraction coordinates until explicit GeoJSON conversion.
The STR index only eliminates impossible pairs; predicates remain exact.
"""
from dataclasses import dataclass
from fractions import Fraction as Q
from functools import cmp_to_key
from math import inf, nextafter

from .geometry import Geometry
from .spatial import BoundsIndex


class TopologyError(ValueError):
    """Input topology or an operation contract is invalid."""


class TopologyPrecisionError(TopologyError):
    """The requested output cannot preserve the topology at its precision."""


def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def mul(a,t):return tuple(x*t for x in a)
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def orient(a,b,c):return cross(sub(b,a),sub(c,a))
def on(p,a,b):return orient(a,b,p)==0 and all(min(a[i],b[i])<=p[i]<=max(a[i],b[i]) for i in (0,1))


def hits(a,b,c,d):
    found=tuple(sorted({p for p in (a,b,c,d) if on(p,a,b) and on(p,c,d)}))
    if found:return found[:1] if len(found)==1 else (found[0],found[-1])
    ab,cd=sub(b,a),sub(d,c);den=cross(ab,cd)
    if not den:return ()
    t=cross(sub(c,a),cd)/den;u=cross(sub(c,a),ab)/den
    return (add(a,mul(ab,t)),) if 0<t<1 and 0<u<1 else ()


def point(value):
    if len(value)!=2:raise TopologyError('Overlay requires explicit 2D coordinates; elevation is not inferred')
    return tuple(Q(v) for v in value)


def signed_area(ring):return sum(cross(a,b) for a,b in zip(ring,ring[1:]))/2


def ring_location(p,ring):
    inside=False
    for a,b in zip(ring,ring[1:]):
        if on(p,a,b):return 0
        if (a[1]>p[1])!=(b[1]>p[1]):
            x=a[0]+(p[1]-a[1])*(b[0]-a[0])/(b[1]-a[1])
            if x>p[0]:inside=not inside
    return 1 if inside else -1


@dataclass(frozen=True)
class Shape:
    polygons: tuple=()
    lines: tuple=()
    points: tuple=()

    def location(self,p):
        boundary=False
        for rings in self.polygons:
            outer=ring_location(p,rings[0])
            holes=[ring_location(p,r) for r in rings[1:]]
            boundary |= outer==0 or outer==1 and 0 in holes
            if outer==1 and all(v==-1 for v in holes):return 1
        return 0 if boundary else -1

    def contains(self,p):
        return self.location(p)>=0 or p in self.points or any(on(p,a,b) for line in self.lines for a,b in zip(line,line[1:]))

    def segments(self,operand):
        for part,rings in enumerate(self.polygons):
            for ring,coords in enumerate(rings):
                for segment,(a,b) in enumerate(zip(coords,coords[1:])):
                    yield a,b,(operand,'polygon',part,ring,segment)
        for part,line in enumerate(self.lines):
            for segment,(a,b) in enumerate(zip(line,line[1:])):
                yield a,b,(operand,'line',part,0,segment)


def prepare(geometry,*,validate=True):
    if not isinstance(geometry,Geometry):raise TypeError('Expected Geometry')
    kind=geometry.type;c=geometry.coordinates
    if kind=='GeometryCollection':
        members=tuple(prepare(g,validate=False) for g in geometry.geometries)
        shape=Shape(tuple(p for g in members for p in g.polygons),tuple(l for g in members for l in g.lines),tuple(p for g in members for p in g.points))
    elif kind in ('Polygon','MultiPolygon'):
        polys=(c,) if kind=='Polygon' and c else c if kind=='MultiPolygon' else ()
        shape=Shape(tuple(tuple(tuple(map(point,ring)) for ring in rings) for rings in polys if rings))
    elif kind in ('LineString','MultiLineString'):
        lines=(c,) if kind=='LineString' and c else c if kind=='MultiLineString' else ()
        shape=Shape(lines=tuple(tuple(map(point,line)) for line in lines if line))
    else:shape=Shape(points=tuple(map(point,(c,) if kind=='Point' and c else c if kind=='MultiPoint' else ())))
    if validate:validate_shape(shape)
    return shape


def validate_shape(shape):
    for line in shape.lines:
        if any(a==b for a,b in zip(line,line[1:])):raise TopologyError('Consecutive duplicate line positions; repair explicitly')
    for rings in shape.polygons:
        for ring in rings:
            if len(ring)<4 or ring[0]!=ring[-1] or signed_area(ring)==0:raise TopologyError('Closed nonzero-area rings required')
            edges=tuple(zip(ring,ring[1:]))
            for i,(a,b) in enumerate(edges):
                if a==b:raise TopologyError('Consecutive duplicate ring positions')
                for j in range(i+1,len(edges)):
                    h=hits(a,b,*edges[j]);adjacent=j==i+1 or i==0 and j==len(edges)-1
                    if h and (not adjacent or len(h)>1):raise TopologyError('Ring self-intersection or retracing')
        for j,ring in enumerate(rings[1:],1):
            if ring_location(ring[0],rings[0])!=1:raise TopologyError('Hole must be strictly inside shell')
            for k,other in enumerate(rings[:j]):
                if any(hits(a,b,c,d) for a,b in zip(ring,ring[1:]) for c,d in zip(other,other[1:])):
                    raise TopologyError('Ring boundaries cross or touch')
                if k and (ring_location(ring[0],other)==1 or ring_location(other[0],ring)==1):
                    raise TopologyError('Holes overlap or nest')
    for j,rings in enumerate(shape.polygons):
        for other in shape.polygons[:j]:
            for ring in rings:
                for previous in other:
                    for a,b in zip(ring,ring[1:]):
                        for c,d in zip(previous,previous[1:]):
                            h=hits(a,b,c,d)
                            if len(h)>1 or h and orient(a,b,c)*orient(a,b,d)<0 and orient(c,d,a)*orient(c,d,b)<0:
                                raise TopologyError('Multipolygon boundaries cross or share an edge; dissolve explicitly')
            for poly,other_poly in ((rings,other),(other,rings)):
                if any(Shape((other_poly,)).location(p)==1 for p in poly[0][:-1]):raise TopologyError('Multipolygon interiors overlap')


def box(a,b):
    return (nextafter(float(min(a[0],b[0])),-inf),nextafter(float(min(a[1],b[1])),-inf),
            nextafter(float(max(a[0],b[0])),inf),nextafter(float(max(a[1],b[1])),inf))


@dataclass(frozen=True)
class Edge:
    start: int
    end: int
    sources: tuple


@dataclass(frozen=True)
class Graph:
    domain: str
    nodes: tuple
    edges: tuple
    candidate_pairs: int
    input_segments: int

    @property
    def shared_edges(self):
        return tuple(e for e in self.edges if len({s[0] for s in e.sources})>1)


def node(shapes,*,max_segments=20000,max_pairs=2000000,max_edges=100000):
    for value in (max_segments,max_pairs,max_edges):
        if isinstance(value,bool) or not isinstance(value,int) or value<1:raise ValueError('Topology budgets must be positive integers')
    segments=tuple(s for operand,shape in enumerate(shapes) for s in shape.segments(operand))
    if len(segments)>max_segments:raise TopologyError('Input segment budget exceeded')
    splits=[{a,b} for a,b,_ in segments];boxes=[box(a,b) for a,b,_ in segments]
    index=BoundsIndex(enumerate(boxes));pairs=0
    for i,(a,b,_) in enumerate(segments):
        for j in index.query(boxes[i]):
            if j<=i:continue
            pairs+=1
            if pairs>max_pairs:raise TopologyError('Candidate pair budget exceeded')
            h=hits(a,b,*segments[j][:2]);splits[i].update(h);splits[j].update(h)
    for shape in shapes:
        for p in shape.points:
            for i in index.query(box(p,p)):
                if on(p,*segments[i][:2]):splits[i].add(p)
    grouped={}
    for (a,b,source),points in zip(segments,splits):
        v=sub(b,a);axis=0 if abs(v[0])>=abs(v[1]) else 1
        ordered=sorted(points,key=lambda p:(p[axis]-a[axis])/v[axis])
        for u,v in zip(ordered,ordered[1:]):
            key=tuple(sorted((u,v)));direction=1 if key==(u,v) else -1
            grouped.setdefault(key,[]).append(source+(direction,))
            if len(grouped)>max_edges:raise TopologyError('Noded edge budget exceeded')
    nodes=tuple(sorted({p for pair in grouped for p in pair}|{p for s in shapes for p in s.points}))
    ids={p:i for i,p in enumerate(nodes)}
    return Graph('planar',nodes,tuple(Edge(ids[a],ids[b],tuple(sorted(sources))) for (a,b),sources in sorted(grouped.items())),pairs,len(segments))


def probes(graph,edge):
    a,b=(graph.nodes[i] for i in (edge.start,edge.end));m=mul(add(a,b),Q(1,2));v=sub(b,a)
    normal=(-v[1],v[0]);normal=mul(normal,1/max(abs(x) for x in normal));step=Q(1,2)
    for _ in range(256):
        left=add(m,mul(normal,step));right=add(m,mul(normal,-step))
        safe=True
        for other in graph.edges:
            if other is edge:continue
            c,d=graph.nodes[other.start],graph.nodes[other.end]
            if hits(m,left,c,d) or hits(m,right,c,d):safe=False;break
        if safe:return m,left,right
        step/=2
    raise TopologyPrecisionError('Could not isolate the two sides of an edge within the probe budget')


def _angle_cmp(a,b):
    def half(p):return 0 if p[1]>0 or p[1]==0 and p[0]>=0 else 1
    ha,hb=half(a),half(b)
    if ha!=hb:return -1 if ha<hb else 1
    c=cross(a,b)
    return -1 if c>0 else 1 if c<0 else 0


def stitch(graph,directed,*,sphere_turn=None):
    outgoing={}
    for a,b in directed:outgoing.setdefault(a,[]).append(b)
    remaining=set(directed);loops=[]
    def following(a,b):
        options=outgoing.get(b,())
        if not options:raise TopologyError('Open area boundary in arrangement')
        if sphere_turn is not None:return min(options,key=lambda c:sphere_turn(a,b,c))
        base=sub(graph.nodes[a],graph.nodes[b])
        def angle(c):
            v=sub(graph.nodes[c],graph.nodes[b]);return dot(base,v),-cross(base,v)
        return sorted(options,key=cmp_to_key(lambda c,d:_angle_cmp(angle(c),angle(d))))[0]
    successors={(a,b):(b,following(a,b)) for a,b in directed}
    if len(set(successors.values()))!=len(successors):raise TopologyPrecisionError('Area boundary does not have bijective half-edge successors')
    while remaining:
        first=min(remaining);edge=first;loop=[]
        while True:
            if edge not in remaining:raise TopologyError('Boundary cycle joins another cycle')
            remaining.remove(edge);loop.append(edge[0]);edge=successors[edge]
            if edge==first:break
        if len(loop)<3:raise TopologyError('Degenerate area boundary')
        loops.append(tuple(graph.nodes[i] for i in loop+(loop[:1])))
    return tuple(loops)


def polygons(loops):
    shells=[];holes=[]
    for ring in loops:
        area=signed_area(ring)
        if not area:raise TopologyError('Zero-area output ring')
        (shells if area>0 else holes).append(ring)
    result=[[shell] for shell in shells]
    for hole in holes:
        candidates=[i for i,shell in enumerate(shells) if any(ring_location(p,shell)==1 for p in hole[:-1])]
        if not candidates:raise TopologyError('Output hole has no enclosing shell')
        owner=min(candidates,key=lambda i:abs(signed_area(shells[i])));result[owner].append(hole)
    return tuple(tuple(rings) for rings in result)


def geometry(polys=(),lines=(),points=()):
    coordinates={p for rings in polys for ring in rings for p in ring}|{p for line in lines for p in line}|set(points)
    rounded={p:tuple(map(float,p)) for p in coordinates}
    if len(set(rounded.values()))!=len(rounded):raise TopologyPrecisionError('Distinct rational nodes collapse when converted to float64 GeoJSON')
    def ring(r):return tuple(rounded[p] for p in r)
    parts=[]
    if polys:
        c=tuple(tuple(ring(r) for r in rings) for rings in polys)
        parts.append(Geometry('Polygon',c[0]) if len(c)==1 else Geometry('MultiPolygon',c))
    if lines:
        c=tuple(ring(line) for line in lines);parts.append(Geometry('LineString',c[0]) if len(c)==1 else Geometry('MultiLineString',c))
    if points:
        c=tuple(sorted(rounded[p] for p in points));parts.append(Geometry('Point',c[0]) if len(c)==1 else Geometry('MultiPoint',c))
    return parts[0] if len(parts)==1 else Geometry('GeometryCollection',geometries=tuple(parts))


def boolean(operation,a,b):
    if operation=='intersection':return a and b
    if operation=='union':return a or b
    if operation=='difference':return a and not b
    if operation=='symmetric_difference':return a!=b
    raise ValueError('Operation must be intersection, union, difference or symmetric_difference')


def compute(left,right,operation,*,_validate=True,**budgets):
    boolean(operation,False,False)
    shapes=(prepare(left,validate=False),prepare(right,validate=False))
    limit=budgets.get('max_segments',20000)
    if isinstance(limit,bool) or not isinstance(limit,int) or limit<1:raise ValueError('max_segments must be a positive integer')
    if sum(1 for i,s in enumerate(shapes) for _ in s.segments(i))>limit:raise TopologyError('Input segment budget exceeded')
    if _validate:
        for shape in shapes:validate_shape(shape)
    graph=node(shapes,**budgets);directed=[];wire=[]
    for edge in graph.edges:
        m,l,r=probes(graph,edge)
        lv=boolean(operation,*(s.location(l)==1 for s in shapes));rv=boolean(operation,*(s.location(r)==1 for s in shapes))
        if lv!=rv:directed.append((edge.start,edge.end) if lv else (edge.end,edge.start))
        elif not lv and boolean(operation,*(s.contains(m) for s in shapes)):wire.append((graph.nodes[edge.start],graph.nodes[edge.end]))
    polys=polygons(stitch(graph,directed));area_shape=Shape(polys)
    isolated=[]
    for p in graph.nodes:
        if boolean(operation,*(s.contains(p) for s in shapes)) and area_shape.location(p)<0 and not any(on(p,a,b) for a,b in wire):isolated.append(p)
    result=geometry(polys,tuple(wire),tuple(isolated))
    # Float conversion may introduce a crossing even without merging nodes.
    if result.type!='GeometryCollection':prepare(result)
    else:
        for member in result.geometries:prepare(member)
    return result,graph
