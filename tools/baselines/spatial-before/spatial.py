"""Own immutable bounding-box hierarchy; no external spatial engine.

Envelopes are conservative candidates, never exact topology intersections.
Projected preparation is separate from generic indexing and retains ambiguous
geometry. All queries return the original integer keys in ascending order.
"""
from collections import OrderedDict
from dataclasses import dataclass
import math
from numbers import Real
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


@dataclass(frozen=True)
class _Node:
    bounds: tuple
    children: tuple=()
    entries: tuple=()


def _build(entries,leaf_size):
    if not entries:return None
    bounds=(min(b[0] for _,b in entries),min(b[1] for _,b in entries),
            max(b[2] for _,b in entries),max(b[3] for _,b in entries))
    if len(entries)<=leaf_size:return _Node(bounds,entries=tuple(entries))
    axis=0 if bounds[2]-bounds[0]>=bounds[3]-bounds[1] else 1
    entries=sorted(entries,key=lambda entry:entry[1][axis]/2+entry[1][axis+2]/2)
    middle=len(entries)//2
    return _Node(bounds,children=(_build(entries[:middle],leaf_size),_build(entries[middle:],leaf_size)))


@dataclass(frozen=True,init=False)
class BoundsIndex:
    """Immutable median-split BVH of (integer key, bounds) pairs.

    Bounds use (west, south, east, north) in one common coordinate space.
    Touching/zero-area envelopes are included. query returns candidates, not
    geometric intersections. Construction owns and validates a frozen copy.
    """
    _root: _Node | None
    size: int

    def __init__(self,entries=(),*,leaf_size=12):
        if isinstance(leaf_size,bool) or not isinstance(leaf_size,int) or leaf_size<1:
            raise ValueError('leaf_size must be a positive integer')
        frozen=[];keys=set()
        for key,bounds in entries:
            if isinstance(key,bool) or not isinstance(key,int) or key in keys:
                raise ValueError('Index keys must be distinct integers')
            keys.add(key);frozen.append((key,_box(bounds)))
        object.__setattr__(self,'size',len(frozen))
        object.__setattr__(self,'_root',_build(frozen,leaf_size))

    @property
    def bounds(self):return self._root.bounds if self._root is not None else None

    def query(self,bounds):
        """Sorted keys of envelopes intersecting the closed query rectangle."""
        bounds=_box(bounds);result=[];stack=[self._root] if self._root is not None else []
        while stack:
            node=stack.pop()
            if not _intersects(node.bounds,bounds):continue
            if node.children:stack.extend(node.children)
            else:result.extend(key for key,box in node.entries if _intersects(box,bounds))
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
