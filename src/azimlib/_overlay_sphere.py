"""Own spherical arrangement of minor great-circle arcs on a unit sphere.

No map projection is used. Regions retain a reference point and its membership,
so empty/full spheres, poles and complements have unambiguous interiors.
"""
from dataclasses import dataclass
from itertools import product
from math import acos, atan2, cos, degrees, floor, fsum, pi, radians, sin, sqrt

from .geometry import Geometry, position, _number, EARTH_RADIUS
from .spatial import BoundsIndex
from ._overlay_planar import (Graph,Edge,TopologyError,TopologyPrecisionError,boolean,stitch)


def dot(a,b):return fsum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def mul(a,t):return tuple(x*t for x in a)
def norm(a):return sqrt(dot(a,a))
def unit(a):
    length=norm(a)
    if length<1e-15:raise TopologyPrecisionError('Undefined spherical direction')
    return mul(a,1/length)
def angle(a,b):return atan2(norm(cross(a,b)),dot(a,b))


def vector(p):
    p=position(p)
    if len(p)!=2:raise TopologyError('Spherical topology requires 2D lon/lat; no inferred elevation')
    lon,lat=radians(p[0]%360),radians(p[1])
    if abs(p[1])==90:return (0.,0.,1. if p[1]>0 else -1.)
    return unit((cos(lat)*cos(lon),cos(lat)*sin(lon),sin(lat)))


def coordinate(p):return degrees(atan2(p[1],p[0])),degrees(atan2(p[2],sqrt(p[0]**2+p[1]**2)))


def arc_valid(a,b,tol):
    length=angle(a,b)
    if length<32*tol:raise TopologyPrecisionError('Arc too short for the configured angular precision')
    if pi-length<32*tol:raise TopologyError('Antipodal/near-antipodal endpoints do not define a unique supported minor arc')


def on_arc(p,a,b,tol):
    if angle(p,a)<=tol or angle(p,b)<=tol:return True
    n=unit(cross(a,b))
    if abs(dot(p,n))>tol:return False
    return dot(cross(a,p),n)>=-tol and dot(cross(p,b),n)>=-tol


def arc_hits(a,b,c,d,tol):
    n,m=unit(cross(a,b)),unit(cross(c,d));axis=cross(n,m);length=norm(axis)
    if length<1e-14:
        found=[]
        for p in (a,b,c,d):
            if on_arc(p,a,b,tol) and on_arc(p,c,d,tol) and not any(angle(p,q)<=tol for q in found):found.append(p)
        return tuple(found)
    if length<32*tol:raise TopologyPrecisionError('Nearly coincident great-circle planes are unresolved at this precision')
    p=mul(axis,1/length)
    return tuple(q for q in (p,mul(p,-1)) if on_arc(q,a,b,tol) and on_arc(q,c,d,tol))


def arc_distance(p,a,b,tol):
    n=unit(cross(a,b));foot=add(p,mul(n,-dot(p,n)))
    if norm(foot)>1e-15:
        foot=unit(foot)
        if on_arc(foot,a,b,tol):return angle(p,foot)
    return min(angle(p,a),angle(p,b))


def arc_box(a,b,tol):
    candidates=[a,b];n=unit(cross(a,b))
    for axis in ((1.,0.,0.),(0.,1.,0.),(0.,0.,1.)):
        p=add(axis,mul(n,-dot(axis,n)))
        if norm(p)>1e-15:
            p=unit(p)
            candidates.extend(q for q in (p,mul(p,-1)) if on_arc(q,a,b,tol))
    return tuple(min(p[i] for p in candidates)-4*tol for i in range(3))+tuple(max(p[i] for p in candidates)+4*tol for i in range(3))


def candidates():
    yield (1.,0.,0.);yield (0.,1.,0.);yield (0.,0.,1.)
    for i in range(48):
        z=1-2*(i+.5)/48;lon=i*pi*(3-sqrt(5));r=sqrt(1-z*z)
        yield (r*cos(lon),r*sin(lon),z)


def ray_crossings(a,b,edges,tol):
    length=angle(a,b)
    if length<tol:return 0
    if pi-length<32*tol:return None
    count=0
    for c,d in edges:
        try:hits=arc_hits(a,b,c,d,tol)
        except TopologyPrecisionError:return None
        for p in hits:
            if min(angle(p,q) for q in (a,b,c,d))<32*tol:return None
            count+=1
    return count


def locate(p,rings,reference,reference_inside,tol):
    edges=tuple((a,b) for ring in rings for a,b in zip(ring,ring[1:]))
    if any(on_arc(p,a,b,tol) for a,b in edges):return 0
    if not edges:return 1 if reference_inside else -1
    direct=ray_crossings(reference,p,edges,tol)
    if direct is not None:return 1 if reference_inside^(direct%2==1) else -1
    for middle in candidates():
        first=ray_crossings(reference,middle,edges,tol)
        if first is None:continue
        second=ray_crossings(middle,p,edges,tol)
        if second is not None:return 1 if reference_inside^((first+second)%2==1) else -1
    raise TopologyPrecisionError('No unambiguous reference ray within the spherical classification budget')


def sides(a,b,other_edges,tol):
    m=unit(add(a,b));n=unit(cross(a,b));clearance=min((arc_distance(m,c,d,tol) for c,d in other_edges),default=pi)
    offset=min(.01,angle(a,b)/8,clearance/8)
    if offset<32*tol:raise TopologyPrecisionError('Boundary sides cannot be isolated at the configured angular precision')
    return m,unit(add(mul(m,cos(offset)),mul(n,sin(offset)))),unit(add(mul(m,cos(offset)),mul(n,-sin(offset))))


def left_area(ring):
    turns=[];vertices=ring[:-1]
    for i,b in enumerate(vertices):
        a,c=vertices[i-1],vertices[(i+1)%len(vertices)]
        incoming=unit(add(mul(b,dot(a,b)),mul(a,-1)))
        outgoing=unit(add(c,mul(b,-dot(b,c))))
        turns.append(atan2(dot(b,cross(incoming,outgoing)),dot(incoming,outgoing)))
    area=(2*pi-fsum(turns))%(4*pi)
    if min(area,4*pi-area)<1e-14:raise TopologyPrecisionError('Spherical ring area is unresolved')
    return area


def validate_rings(rings,tol):
    edges=[]
    for r,ring in enumerate(rings):
        if len(ring)<4 or angle(ring[0],ring[-1])>tol:raise TopologyError('Spherical rings require at least three vertices and closure')
        for s,(a,b) in enumerate(zip(ring,ring[1:])):
            arc_valid(a,b,tol);edges.append((a,b,r,s,len(ring)-1))
    for i,(a,b,r,s,n) in enumerate(edges):
        for c,d,q,t,_ in edges[:i]:
            hit=arc_hits(a,b,c,d,tol)
            adjacent=r==q and (abs(s-t)==1 or {s,t}=={0,n-1})
            shared_vertex=r!=q and len(hit)==1 and any(angle(hit[0],p)<=tol for p in (a,b)) and any(angle(hit[0],p)<=tol for p in (c,d))
            if hit and not shared_vertex and (not adjacent or len(hit)>1):raise TopologyError('Spherical boundaries cross, touch or retrace; node/dissolve explicitly')


@dataclass(frozen=True,init=False)
class SphericalRegion:
    """Oriented spherical boundaries plus explicit reference membership.

    Edges are minor great-circle arcs; filled area is to their left. Empty
    boundaries with reference_inside=True represent the full sphere. Ordinary
    GeoJSON alone cannot express that state or a general spherical complement.
    """
    rings: tuple
    reference: tuple
    reference_inside: bool
    tolerance: float

    def __init__(self,rings=(),*,reference=(17.123,23.456),reference_inside=False,tolerance=1e-10):
        tol=_number(tolerance,'angular tolerance')
        if not 1e-13<=tol<=1e-6:raise ValueError('Angular tolerance must be 1e-13..1e-6 radians')
        if not isinstance(reference_inside,bool):raise TypeError('reference_inside must be bool')
        frozen=tuple(tuple(vector(p) for p in ring) for ring in rings);ref=vector(reference)
        validate_rings(frozen,tol)
        if any(on_arc(ref,a,b,tol) for ring in frozen for a,b in zip(ring,ring[1:])):raise TopologyError('Reference point is on a boundary')
        object.__setattr__(self,'rings',frozen);object.__setattr__(self,'reference',ref)
        object.__setattr__(self,'reference_inside',reference_inside);object.__setattr__(self,'tolerance',tol)
        all_edges=tuple((a,b) for ring in frozen for a,b in zip(ring,ring[1:]))
        for ring in frozen:
            a,b=ring[:2];_,l,r=sides(a,b,tuple((c,d) for c,d in all_edges if not (c is a and d is b)),tol)
            if self._location(l)!=1 or self._location(r)!=-1:raise TopologyError('Boundary orientation disagrees with reference membership; filled side must be left')

    @classmethod
    def _from_vectors(cls,rings,reference,inside,tol):
        # Output is validated in 3D before this internal constructor is called.
        obj=object.__new__(cls)
        for name,value in (('rings',tuple(rings)),('reference',reference),('reference_inside',inside),('tolerance',tol)):object.__setattr__(obj,name,value)
        return obj

    @classmethod
    def from_geometry(cls,geometry,*,interior='small',tolerance=1e-10):
        if not isinstance(geometry,Geometry) or geometry.type not in ('Polygon','MultiPolygon'):raise TypeError('SphericalRegion.from_geometry requires Polygon/MultiPolygon')
        if interior not in ('small','left'):raise ValueError('interior must be small or left')
        tol=_number(tolerance)
        if not 1e-13<=tol<=1e-6:raise ValueError('Invalid angular tolerance')
        polys=(geometry.coordinates,) if geometry.type=='Polygon' and geometry.coordinates else geometry.coordinates if geometry.type=='MultiPolygon' else ()
        prepared=[];flat=[]
        for polygon in polys:
            rings=[]
            for i,ring in enumerate(polygon):
                vectors=tuple(map(vector,ring));validate_rings((vectors,),tol);area=left_area(vectors)
                # Shell normalization is explicit; holes always denote smaller
                # excluded regions and are then oriented with filled side left.
                if i and area<2*pi or not i and interior=='small' and area>2*pi:vectors=vectors[::-1]
                edges=tuple(zip(vectors,vectors[1:]));a,b=edges[0]
                _,seed,_=sides(a,b,edges[1:],tol)
                rings.append((vectors,seed))
            if rings:prepared.append(tuple(rings));flat.extend(r[0] for r in rings)
        validate_rings(tuple(flat),tol)
        def membership(p):
            for rings in prepared:
                shell=locate(p,(rings[0][0],),rings[0][1],True,tol)==1
                # A hole was oriented clockwise: its excluded small interior
                # is on its right, hence reference on left is outside the hole.
                holes=[locate(p,(r,),seed,False,tol)==1 for r,seed in rings[1:]]
                if shell and not any(holes):return True
            return False
        for rings in prepared:
            for hole,_ in rings[1:]:
                if locate(hole[0],(rings[0][0],),rings[0][1],True,tol)!=1:raise TopologyError('Spherical hole outside shell')
            for j,(hole,seed) in enumerate(rings[1:],1):
                for other,_ in rings[:j]:
                    if any(arc_hits(a,b,c,d,tol) for a,b in zip(hole,hole[1:]) for c,d in zip(other,other[1:])):raise TopologyError('Spherical hole boundaries touch or cross')
                for previous,other_seed in rings[1:j]:
                    if locate(hole[0],(previous,),other_seed,False,tol)==1 or locate(previous[0],(hole,),seed,False,tol)==1:raise TopologyError('Nested spherical holes')
        for i,rings in enumerate(prepared):
            for other in prepared[:i]:
                for poly,target in ((rings,other),(other,rings)):
                    for p in poly[0][0][:-1]:
                        if locate(p,(target[0][0],),target[0][1],True,tol)==1 and all(locate(p,(r,),seed,False,tol)==-1 for r,seed in target[1:]):raise TopologyError('Spherical multipolygon interiors overlap')
        edges=tuple((a,b) for ring in flat for a,b in zip(ring,ring[1:]))
        reference=next((p for p in candidates() if all(arc_distance(p,a,b,tol)>64*tol for a,b in edges)),None)
        if reference is None:raise TopologyPrecisionError('No safe spherical reference point')
        return cls._from_vectors(tuple(flat),reference,membership(reference),tol)

    @classmethod
    def hemisphere(cls,longitude,latitude,*,tolerance=1e-10):
        """Closed hemisphere centred at the given geographic unit normal."""
        n=vector((longitude,latitude));tol=_number(tolerance)
        if not 1e-13<=tol<=1e-6:raise ValueError('Invalid angular tolerance')
        u=unit(cross((0.,0.,1.) if abs(n[2])<.9 else (0.,1.,0.),n));v=unit(cross(n,u))
        return cls._from_vectors(((u,v,mul(u,-1),mul(v,-1),u),),n,True,tol)

    def to_dict(self):
        """Lossless interior metadata, intentionally not a GeoJSON polygon."""
        return dict(type='AzimlibSphericalRegion',schema_version=1,edges='minor-great-circle',
                    rings=[[coordinate(p) for p in ring] for ring in self.rings],
                    reference=coordinate(self.reference),reference_inside=self.reference_inside,tolerance=self.tolerance)

    @classmethod
    def from_dict(cls,data):
        if not isinstance(data,dict) or set(data)!={'type','schema_version','edges','rings','reference','reference_inside','tolerance'} or data['type']!='AzimlibSphericalRegion' or type(data['schema_version']) is not int or data['schema_version']!=1 or data['edges']!='minor-great-circle':raise ValueError('Invalid spherical region serialization')
        return cls(data['rings'],reference=data['reference'],reference_inside=data['reference_inside'],tolerance=data['tolerance'])

    def _location(self,p):return locate(p,self.rings,self.reference,self.reference_inside,self.tolerance)
    def location(self,longitude,latitude):return ('outside','boundary','inside')[self._location(vector((longitude,latitude)))+1]
    def covers(self,longitude,latitude):return self._location(vector((longitude,latitude)))>=0
    def complement(self):return self._from_vectors(tuple(r[::-1] for r in self.rings),self.reference,not self.reference_inside,self.tolerance)
    @property
    def is_empty(self):return not self.rings and not self.reference_inside
    @property
    def is_full(self):return not self.rings and self.reference_inside
    def area(self,*,radius=EARTH_RADIUS):
        radius=_number(radius,'radius')
        if radius<=0:raise ValueError('radius must be positive')
        area=4*pi if self.is_full else fsum(left_area(r) for r in self.rings)%(4*pi) if self.rings else 0.
        return area*radius**2
    def boundary(self,*,step=2.):
        step=_number(step,'step')
        if not .01<=step<=30:raise ValueError('step must be .01..30 degrees')
        from math import ceil
        lines=[]
        for ring in self.rings:
            line=[]
            for a,b in zip(ring,ring[1:]):
                theta=angle(a,b);n=max(1,ceil(degrees(theta)/step))
                for i in range(n):
                    t=i/n;p=unit(add(mul(a,sin((1-t)*theta)),mul(b,sin(t*theta))))
                    line.append(coordinate(p))
            line.append(line[0]);lines.append(tuple(line))
        return Geometry('MultiLineString',tuple(lines))


def node(regions,*,max_segments=20000,max_pairs=2000000,max_edges=100000):
    for value in (max_segments,max_pairs,max_edges):
        if isinstance(value,bool) or not isinstance(value,int) or value<1:raise ValueError('Topology budgets must be positive integers')
    tol=max(r.tolerance for r in regions);segments=[]
    for operand,region in enumerate(regions):
        for ring,coords in enumerate(region.rings):
            for segment,(a,b) in enumerate(zip(coords,coords[1:])):segments.append((a,b,(operand,'polygon',0,ring,segment)))
    if len(segments)>max_segments:raise TopologyError('Input segment budget exceeded')
    nodes=[];buckets={}
    def register(p):
        key=tuple(floor(x/tol) for x in p)
        for delta in product((-1,0,1),repeat=3):
            for i in buckets.get(tuple(x+y for x,y in zip(key,delta)),()):
                if angle(p,nodes[i])<=tol:return i
        i=len(nodes);nodes.append(p);buckets.setdefault(key,[]).append(i);return i
    splits=[{register(a),register(b)} for a,b,_ in segments]
    boxes=[arc_box(a,b,tol) for a,b,_ in segments]
    xy=[(b[0],b[1],b[3],b[4]) for b in boxes];index=BoundsIndex(enumerate(xy));pairs=0
    for i,(a,b,_) in enumerate(segments):
        for j in index.query(xy[i]):
            if j<=i or boxes[i][5]<boxes[j][2] or boxes[j][5]<boxes[i][2]:continue
            pairs+=1
            if pairs>max_pairs:raise TopologyError('Candidate pair budget exceeded')
            for p in arc_hits(a,b,*segments[j][:2],tol):
                k=register(p);splits[i].add(k);splits[j].add(k)
    grouped={}
    for (a,b,source),ids in zip(segments,splits):
        ordered=sorted(ids,key=lambda i:angle(a,nodes[i]))
        for u,v in zip(ordered,ordered[1:]):
            if angle(nodes[u],nodes[v])<32*tol:raise TopologyPrecisionError('Noded spherical edge below supported precision')
            key=tuple(sorted((u,v)));grouped.setdefault(key,[]).append(source+(1 if key==(u,v) else -1,))
            if len(grouped)>max_edges:raise TopologyError('Noded edge budget exceeded')
    return Graph('spherical',tuple(nodes),tuple(Edge(a,b,tuple(sorted(s))) for (a,b),s in sorted(grouped.items())),pairs,len(segments))


def compute(left,right,operation,**budgets):
    boolean(operation,False,False)
    if not isinstance(left,SphericalRegion) or not isinstance(right,SphericalRegion):raise TypeError('Spherical overlay requires explicit SphericalRegion operands')
    tol=max(left.tolerance,right.tolerance);graph=node((left,right),**budgets);directed=[]
    for edge in graph.edges:
        a,b=graph.nodes[edge.start],graph.nodes[edge.end]
        others=tuple((graph.nodes[e.start],graph.nodes[e.end]) for e in graph.edges if e is not edge)
        _,l,r=sides(a,b,others,tol)
        lv=boolean(operation,left._location(l)==1,right._location(l)==1)
        rv=boolean(operation,left._location(r)==1,right._location(r)==1)
        if lv!=rv:directed.append((edge.start,edge.end) if lv else (edge.end,edge.start))
    def turn(a,b,c):
        p=graph.nodes[b];u=unit(add(graph.nodes[a],mul(p,-dot(p,graph.nodes[a]))))
        v=unit(add(graph.nodes[c],mul(p,-dot(p,graph.nodes[c]))))
        return (-atan2(dot(p,cross(u,v)),dot(u,v)))%(2*pi)
    loops=stitch(graph,directed,sphere_turn=turn)
    edges=tuple((a,b) for ring in loops for a,b in zip(ring,ring[1:]))
    all_edges=tuple((graph.nodes[e.start],graph.nodes[e.end]) for e in graph.edges)
    reference=next((p for p in candidates() if all(arc_distance(p,a,b,tol)>64*tol for a,b in all_edges)),None)
    if reference is None:raise TopologyPrecisionError('No safe output reference')
    inside=boolean(operation,left._location(reference)==1,right._location(reference)==1)
    result=SphericalRegion._from_vectors(loops,reference,inside,tol)
    # Crossings/touching output components are already noded. Each retained
    # boundary must separate filled left from empty right at its midpoint.
    for ring in loops:
        a,b=ring[:2];_,l,r=sides(a,b,tuple((c,d) for c,d in edges if not (c is a and d is b)),tol)
        if result._location(l)!=1 or result._location(r)!=-1:raise TopologyPrecisionError('Output reference/orientation consistency failed')
    return result,graph
