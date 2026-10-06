"""Bounded reuse of immutable projected geometry, independent of screen/style.

Only exact built-in projections and Geometry are eligible. Entries weakly
reference their geographic source; projected float64 coordinates are packed
without quantization. This is a rendering cache, not simplification/topology.
"""
from collections import OrderedDict, namedtuple
from dataclasses import dataclass
from struct import Struct
import sys
from threading import RLock
import weakref

from .geometry import (Geometry, split_antimeridian, clip_polygon_antimeridian,
                       clip_orthographic_polygon, clip_orthographic_line)
from .viewport import _BUILTINS, densify


_PAIR=Struct('<2d')
CacheInfo=namedtuple('CacheInfo','hits misses entries payload_bytes max_bytes max_entries')


def _pack(points):
    data=bytearray()
    for point in points:data.extend(_PAIR.pack(*point))
    return bytes(data)


def _line_paths(coordinates,projection):
    if projection.name=='orthographic':return tuple(_pack(p) for p in clip_orthographic_line(coordinates,projection))
    groups=[]
    for part in split_antimeridian(coordinates,projection.central_longitude):
        current=[]
        for point in densify(part):
            p=projection.forward(*point)
            if p is None:
                if len(current)>1:groups.append(_pack(current))
                current=[]
            else:current.append(p)
        if len(current)>1:groups.append(_pack(current))
    return tuple(groups)


def _polygon_paths(rings,projection):
    if not rings:return ()
    if projection.name=='orthographic':
        return tuple(tuple(_pack(ring) for ring in polygon)
                     for polygon in clip_orthographic_polygon(rings,projection))
    from .render_map import _clip_latitude
    polygons=[]
    for polygon in clip_polygon_antimeridian(rings,projection.central_longitude):
        paths=[]
        for index,ring in enumerate(polygon):
            if projection.name=='mercator':
                ring=_clip_latitude(ring,-projection.max_latitude,projection.max_latitude)
            if not ring:
                if index==0:break
                continue
            points=[projection.forward(*p) for p in densify(ring)]
            if any(p is None for p in points):
                raise ValueError('Polygon crosses an unsupported projection singularity; use a regional extent/data subset')
            if len(points)>2:paths.append(_pack(points))
        else:
            if paths:polygons.append(tuple(paths))
    return tuple(polygons)


def _prepare(geometry,projection):
    kind=geometry.type;coordinates=geometry.coordinates
    if kind in ('LineString','MultiLineString'):
        return tuple(_line_paths(line,projection) for line in
                     ((coordinates,) if kind=='LineString' else coordinates))
    return tuple(_polygon_paths(polygon,projection) for polygon in
                 ((coordinates,) if kind=='Polygon' else coordinates))


def _payload_size(value):
    return sys.getsizeof(value)+(sum(_payload_size(child) for child in value)
                                 if isinstance(value,tuple) else 0)


def screen_points(packed,viewport):
    """Fresh display coordinates using the original float64 affine operations."""
    return [viewport.xy(x,y) for x,y in _PAIR.iter_unpack(packed)]


@dataclass(frozen=True,slots=True)
class _Entry:
    source: object
    paths: tuple
    weight: int


class _ProjectedPathCache:
    """LRU bounded by packed payload/tuple bytes and by number of entries.

    Limits apply to retained payload, not temporary preparation, total process
    memory, or metadata. Zero capacity disables preparation/cache entirely.
    """
    def __init__(self,*,max_bytes=16*1024*1024,max_entries=1024):
        if any(isinstance(v,bool) or not isinstance(v,int) or v<0 for v in (max_bytes,max_entries)):
            raise ValueError('Cache limits must be nonnegative integers')
        self.max_bytes=max_bytes;self.max_entries=max_entries
        self._entries=OrderedDict();self._bytes=0;self._hits=0;self._misses=0;self._lock=RLock()

    def clear(self):
        with self._lock:
            self._entries.clear();self._bytes=0;self._hits=0;self._misses=0

    def info(self):
        with self._lock:
            return CacheInfo(self._hits,self._misses,len(self._entries),self._bytes,self.max_bytes,self.max_entries)

    def _discard(self,key,source):
        with self._lock:
            entry=self._entries.get(key)
            if entry is not None and entry.source is source:
                self._entries.pop(key);self._bytes-=entry.weight

    def get(self,geometry,projection):
        if (not self.max_bytes or not self.max_entries or type(geometry) is not Geometry or
                type(projection) not in _BUILTINS or
                geometry.type not in ('LineString','MultiLineString','Polygon','MultiPolygon')):
            return None
        # Identity avoids hashing every source vertex and distinguishes replacements.
        key=(id(geometry),projection)
        with self._lock:
            entry=self._entries.get(key)
            if entry is not None and entry.source() is geometry:
                self._entries.move_to_end(key);self._hits+=1;return entry.paths
            self._misses+=1
        paths=_prepare(geometry,projection);weight=_payload_size(paths)
        if weight>self.max_bytes:return paths
        owner=weakref.ref(self)
        def released(source):
            cache=owner()
            if cache is not None:cache._discard(key,source)
        source=weakref.ref(geometry,released)
        with self._lock:
            previous=self._entries.pop(key,None)
            if previous is not None:self._bytes-=previous.weight
            self._entries[key]=_Entry(source,paths,weight);self._bytes+=weight
            while self._bytes>self.max_bytes or len(self._entries)>self.max_entries:
                _,old=self._entries.popitem(last=False);self._bytes-=old.weight
        return paths


_paths=_ProjectedPathCache()
