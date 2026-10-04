"""Own immutable bounding-box hierarchy; no external spatial engine.

Envelopes are conservative candidates, never exact topology intersections.
Projected preparation is separate from generic indexing and retains ambiguous
geometry. All queries return the original integer keys in ascending order.
"""
from collections import OrderedDict
from dataclasses import dataclass, field
import math
from numbers import Real
from struct import Struct
from threading import RLock


def _box(bounds):
    bounds=tuple(bounds)
    if len(bounds)!=4 or any(isinstance(v,bool) or not isinstance(v,Real) or not math.isfinite(v) for v in bounds):
        raise ValueError('Bounds must contain four finite numbers')
    if bounds[0]>bounds[2] or bounds[1]>bounds[3]:
        raise ValueError('Bounds require west <= east and south <= north')
    return tuple(float(v) for v in bounds)


def _intersects(a,b):
    return not (a[2]<b[0] or a[0]>b[2] or a[3]<b[1] or a[1]>b[3])


def _contains(outer,inner):
    return (outer[0]<=inner[0] and outer[1]<=inner[1] and
            outer[2]>=inner[2] and outer[3]>=inner[3])


_PACKED_BOX = Struct('<4d')


@dataclass(frozen=True, slots=True)
class _Node:
    bounds: tuple
    children: tuple=()
    start: int=0
    count: int=0


def _envelope(boxes):
    return (min(b[0] for b in boxes),min(b[1] for b in boxes),
            max(b[2] for b in boxes),max(b[3] for b in boxes))


def _tiles(items,capacity,boxof):
    """Sort-tile-recursive bulk loading, with group-aligned vertical strips."""
    groups=(len(items)+capacity-1)//capacity
    slices=math.isqrt(groups)
    if slices*slices<groups:slices+=1
    strip_capacity=slices*capacity
    strip_size=((len(items)+strip_capacity-1)//strip_capacity)*capacity
    items.sort(key=lambda item:boxof(item)[0]/2+boxof(item)[2]/2)
    for start in range(0,len(items),strip_size):
        strip=items[start:start+strip_size]
        strip.sort(key=lambda item:boxof(item)[1]/2+boxof(item)[3]/2)
        for offset in range(0,len(strip),capacity):
            yield strip[offset:offset+capacity]


def _build(entries,leaf_size):
    if not entries:return None,b'',()
    storage=bytearray();keys=[];nodes=[]
    for group in _tiles(entries,leaf_size,lambda entry:entry[1]):
        start=len(keys)
        for key,box in group:
            keys.append(key);storage.extend(_PACKED_BOX.pack(*box))
        nodes.append(_Node(_envelope([box for _,box in group]),start=start,count=len(group)))
    # Entries are an owned temporary copy. Release it before parent packing.
    entries.clear()
    # A capacity of one is valid for leaves, but parents must reduce the level.
    fanout=max(2,leaf_size)
    while len(nodes)>1:
        nodes=[_Node(_envelope([node.bounds for node in group]),children=tuple(group))
               for group in _tiles(nodes,fanout,lambda node:node.bounds)]
    return nodes[0],bytes(storage),tuple(keys)


@dataclass(frozen=True,init=False)
class BoundsIndex:
    """Immutable STR hierarchy of (integer key, bounds) pairs.

    Bounds use (west, south, east, north) in one common coordinate space.
    Touching/zero-area envelopes are included. query returns candidates, not
    geometric intersections. Construction owns and validates a frozen copy;
    envelopes retain full float64 precision in compact immutable storage.
    """
    _root: _Node | None=field(repr=False)
    _boxes: bytes=field(repr=False)
    _keys: tuple=field(repr=False)
    size: int

    def __init__(self,entries=(),*,leaf_size=12):
        if isinstance(leaf_size,bool) or not isinstance(leaf_size,int) or leaf_size<1:
            raise ValueError('leaf_size must be a positive integer')
        frozen=[];keys=set()
        for key,bounds in entries:
            if isinstance(key,bool) or not isinstance(key,int) or key in keys:
                raise ValueError('Index keys must be distinct integers')
            keys.add(key);frozen.append((key,_box(bounds)))
        size=len(frozen);del keys
        root,boxes,ordered_keys=_build(frozen,leaf_size)
        object.__setattr__(self,'size',size)
        object.__setattr__(self,'_root',root)
        object.__setattr__(self,'_boxes',boxes)
        object.__setattr__(self,'_keys',ordered_keys)

    @property
    def bounds(self):return self._root.bounds if self._root is not None else None

    def query(self,bounds):
        """Sorted keys of envelopes intersecting the closed query rectangle."""
        bounds=_box(bounds);result=[];stack=[self._root] if self._root is not None else []
        if self._root is not None and _contains(bounds,self._root.bounds):
            return tuple(sorted(self._keys))
        unpack=_PACKED_BOX.unpack_from;storage=self._boxes;keys=self._keys
        while stack:
            node=stack.pop()
            if not _intersects(node.bounds,bounds):continue
            if node.children:stack.extend(node.children)
            elif _contains(bounds,node.bounds):result.extend(keys[node.start:node.start+node.count])
            else:
                for i in range(node.start,node.start+node.count):
                    box=unpack(storage,i*32)
                    if _intersects(box,bounds):result.append(keys[i])
        return tuple(sorted(result))


@dataclass(frozen=True)
class _PreparedCollection:
    index: BoundsIndex
    always: tuple

    def query(self,bounds,extra=()):
        return tuple(sorted(set(self.index.query(bounds)).union(self.always,extra)))


class _ViewportIndexCache:
    """Four prepared projection envelopes per immutable collection, lazy/LRU."""
    def __init__(self):self._entries=OrderedDict();self._lock=RLock()

    def get(self,collection,projection):
        from .viewport import _geometry_projected_bounds
        with self._lock:
            prepared=self._entries.get(projection)
            if prepared is not None:
                self._entries.move_to_end(projection);return prepared
            entries=[];always=[]
            for i,feature in enumerate(collection):
                geometry=feature.geometry
                if geometry is None:continue
                if geometry.type not in ('LineString','MultiLineString','Polygon','MultiPolygon'):
                    always.append(i);continue
                bounds=_geometry_projected_bounds(projection,geometry.bounds)
                if bounds is None:always.append(i)
                else:entries.append((i,bounds))
            prepared=_PreparedCollection(BoundsIndex(entries),tuple(always))
            self._entries[projection]=prepared
            if len(self._entries)>4:self._entries.popitem(last=False)
            return prepared
