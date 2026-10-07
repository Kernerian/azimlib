"""Opt-in polyline error bounds and exact shared-edge regional polygon thinning.

No quantization, automatic topology repair, external geometry engine or mutation.
Only exactly matching input edges are shared; unmatched vertexization is rejected
as an implicit assumption, not snapped. Closed rings are validated before reuse.
"""
from collections import OrderedDict,defaultdict
from threading import RLock
import math,sys
from .picking import segment_distance
from .geometry import Geometry,Feature,FeatureCollection

def _tolerance(value):
    value=float(value)
    if not math.isfinite(value) or value<0:raise ValueError('Tolerance must be finite nonnegative pixels')
    return value

def simplify_indices(points,tolerance):
    """Iterative Douglas-Peucker; bounds each input vertex against its kept chord."""
    tolerance=_tolerance(tolerance);points=list(points)
    if any(len(p)!=2 or not all(math.isfinite(float(v)) for v in p) for p in points):raise ValueError('Require finite XY pairs')
    if len(points)<3 or not tolerance:return tuple(range(len(points)))
    kept={0,len(points)-1};stack=[(0,len(points)-1)]
    while stack:
        a,b=stack.pop();distance,index=max(((segment_distance(points[i],points[a],points[b]),i) for i in range(a+1,b)),default=(0,a))
        if distance>tolerance:kept.add(index);stack.extend(((a,index),(index,b)))
    return tuple(sorted(kept))

def simplify_path(points,tolerance):
    points=list(points);return tuple(points[i] for i in simplify_indices(points,tolerance))

class SimplificationCache:
    """Translation-independent bounded packed-path index LRU; scale changes invalidate."""
    def __init__(self,max_bytes=4*1024*1024):
        if isinstance(max_bytes,bool) or not isinstance(max_bytes,int) or max_bytes<0:raise ValueError('Nonnegative integer cache capacity required')
        self.max_bytes=max_bytes;self._entries=OrderedDict();self.bytes=0;self.hits=self.misses=0;self._lock=RLock()
    def clear(self):
        with self._lock:self._entries.clear();self.bytes=self.hits=self.misses=0
    def indices(self,packed,scale,tolerance):
        tolerance=_tolerance(tolerance);scale=float(scale)
        if not math.isfinite(scale) or scale<=0:raise ValueError('Finite positive projected scale required')
        key=(id(packed),scale,tolerance)
        with self._lock:
            row=self._entries.get(key)
            if row is not None and row[0] is packed:self._entries.move_to_end(key);self.hits+=1;return row[1]
            self.misses+=1
        from struct import iter_unpack
        points=[(x*scale,y*scale) for x,y in iter_unpack('<2d',packed)];indices=simplify_indices(points,tolerance)
        reduced=b''.join(packed[i*16:(i+1)*16] for i in indices)
        weight=sys.getsizeof(packed)+sys.getsizeof(indices)+sum(sys.getsizeof(i) for i in indices)+sys.getsizeof(reduced)
        if weight<=self.max_bytes:
            with self._lock:
                previous=self._entries.pop(key,None)
                if previous:self.bytes-=previous[2]
                self._entries[key]=(packed,indices,weight,reduced);self.bytes+=weight
                while self.bytes>self.max_bytes:_,old=self._entries.popitem(last=False);self.bytes-=old[2]
        return indices
    def path(self,packed,scale,tolerance):
        indices=self.indices(packed,scale,tolerance);key=(id(packed),float(scale),float(tolerance))
        with self._lock:
            row=self._entries.get(key)
            if row is not None and row[0] is packed:return row[3]
        return b''.join(packed[i*16:(i+1)*16] for i in indices)
    def info(self):
        with self._lock:return dict(hits=self.hits,misses=self.misses,entries=len(self._entries),payload_bytes=self.bytes,max_bytes=self.max_bytes)

_simplified=SimplificationCache()

def simplify_boundaries(data,transform,tolerance):
    """Simplify exact shared chains once; preserve IDs/properties/ring direction.

    transform is an Azimlib Transform to physical display pixels. Polygon-only,
    regional lon/lat planar topology is required. Invalid inputs fail; a proposed
    invalid simplification conservatively returns the original whole collection.
    """
    from .transforms import Transform
    from .topology import validate_geometry,ring_orientation
    tolerance=_tolerance(tolerance)
    if not isinstance(data,FeatureCollection) or not isinstance(transform,Transform):raise TypeError('FeatureCollection and Azimlib Transform required')
    if not tolerance:return data
    count=sum(len(r) for f in data if f.geometry and f.geometry.type in ('Polygon','MultiPolygon') for polygon in ((f.geometry.coordinates,) if f.geometry.type=='Polygon' else f.geometry.coordinates) for r in polygon)
    if count>10000:raise ValueError('Boundary simplification budget is 10000 input vertices')
    rings=[];owners=defaultdict(set)
    for feature in data:
        if feature.geometry is None:continue
        if feature.geometry.type not in ('Polygon','MultiPolygon'):raise ValueError('Polygon-only regional collection required')
        if not validate_geometry(feature.geometry).valid:raise ValueError('Invalid input polygon topology')
        polygons=(feature.geometry.coordinates,) if feature.geometry.type=='Polygon' else feature.geometry.coordinates
        for polygon in polygons:
            for ring in polygon:
                if any(len(p)!=2 for p in ring) or max(p[0] for p in ring)-min(p[0] for p in ring)>=180:raise ValueError('Regional 2D rings required')
                rid=len(rings);rings.append(ring)
                for a,b in zip(ring,ring[1:]):
                    if a==b:raise ValueError('Duplicate ring vertices')
                    owners[tuple(sorted((a,b)))].add(rid)
    from .spatial import BoundsIndex
    from .topology import segment_intersection
    def crossings(edges):
        edges=list(edges);boxes=[(min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])) for a,b in edges]
        index=BoundsIndex(enumerate(boxes))
        for i,(a,b) in enumerate(edges):
            for j in index.query(boxes[i]):
                if j<=i:continue
                c,d=edges[j];hit=segment_intersection(a,b,c,d)
                if hit.kind=='overlap' or hit.kind=='point' and any(p not in (a,b) or p not in (c,d) for p in hit.points):return True
        return False
    if crossings(owners):raise ValueError('Crossing or differently vertexized boundaries require explicit preprocessing')
    groups=defaultdict(set)
    for edge,rids in owners.items():groups[tuple(sorted(rids))].add(edge)
    keep=set()
    for edges in groups.values():
        graph=defaultdict(set)
        for a,b in edges:graph[a].add(b);graph[b].add(a)
        remaining=set(edges)
        def walk(start,neighbor):
            chain=[start];a,b=start,neighbor
            while tuple(sorted((a,b))) in remaining:
                remaining.remove(tuple(sorted((a,b))));chain.append(b)
                if len(graph[b])!=2 or b==start:break
                nxt=next(v for v in graph[b] if v!=a);a,b=b,nxt
            projected=[transform.transform_point(p) for p in chain]
            if any(p is None for p in projected):keep.update(chain);return
            indices=simplify_indices(projected,tolerance)
            if chain[0]==chain[-1] and len(indices)<4:keep.update(chain)
            else:keep.update(chain[i] for i in indices)
        for vertex in sorted(graph):
            if len(graph[vertex])!=2:
                for neighbor in sorted(graph[vertex]):
                    if tuple(sorted((vertex,neighbor))) in remaining:walk(vertex,neighbor)
        while remaining:a,b=min(remaining);walk(a,b)
    output=[]
    for feature in data:
        geometry=feature.geometry
        if geometry is not None:
            polygons=(geometry.coordinates,) if geometry.type=='Polygon' else geometry.coordinates;replacement=[]
            for polygon in polygons:
                result=[]
                for ring in polygon:
                    reduced=[p for p in ring[:-1] if p in keep]
                    if len(reduced)<3:return data
                    reduced.append(reduced[0])
                    if ring_orientation(reduced)!=ring_orientation(ring):return data
                    result.append(reduced)
                replacement.append(result)
            geometry=Geometry(geometry.type,replacement[0] if geometry.type=='Polygon' else replacement)
            if not validate_geometry(geometry).valid:return data
        output.append(Feature(geometry,feature.properties,feature.id))
    edges={tuple(sorted((a,b))) for f in output if f.geometry for polygon in ((f.geometry.coordinates,) if f.geometry.type=='Polygon' else f.geometry.coordinates) for ring in polygon for a,b in zip(ring,ring[1:])}
    if crossings(edges):return data
    return FeatureCollection(output)
