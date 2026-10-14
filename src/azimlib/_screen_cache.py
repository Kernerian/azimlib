"""Bounded exact display centerlines, separate from triangulated GPU meshes.

Keys contain the unquantized projected bytes and all affine operands. Public
callers receive fresh mutable lists; modifying one invalidates its optional
compiled local coordinates. No viewport ranges or approximate scale keys.
"""
from collections import OrderedDict
from array import array
from threading import RLock
import hashlib
import sys


class ScreenPoints(list):
    def __init__(self, points, compiled):
        super().__init__(points)
        self._compiled = compiled

    def _mutate(name):
        def call(self, *args, **kwargs):
            self._compiled = None
            return getattr(super(ScreenPoints, self), name)(*args, **kwargs)
        return call

    for _name in ('__setitem__', '__delitem__', '__iadd__', '__imul__', 'append',
                  'extend', 'insert', 'pop', 'remove', 'clear', 'reverse', 'sort'):
        locals()[_name] = _mutate(_name)
    del _name, _mutate


class ScreenCache:
    def __init__(self, limit=16*1024*1024, max_entries=512):
        self.limit, self.max_entries = limit, max_entries
        self.entries = OrderedDict()
        self.bytes = self.hits = self.misses = 0
        self.lock = RLock()

    def clear(self):
        with self.lock:
            self.entries.clear()
            self.bytes = self.hits = self.misses = 0

    def get(self, packed, viewport, prepare):
        key = (packed, viewport.ox, viewport.oy, viewport.scale,
               viewport.bearing, viewport._cos, viewport._sin)
        with self.lock:
            found = self.entries.get(key)
            if found is not None:
                self.entries.move_to_end(key)
                self.hits += 1
                points, compiled, _ = found
                return ScreenPoints(points, compiled)
            self.misses += 1
        points = tuple(prepare())
        x, y = points[0] if points else (0., 0.)
        local = tuple((a-x, b-y) for a, b in points)
        digest = hashlib.sha256(array('d', (v for p in local for v in p)).tobytes()).digest()
        compiled = (local, digest)
        # Include Python containers/float objects as well as retained source
        # bytes, rather than calling packed payload size a process RAM bound.
        # The owned affine transform emits float64 pairs as Python float
        # tuples. Their object sizes are constant; accounting must not walk
        # every coordinate again or allocate a combined staging tuple.
        pair_bytes=sys.getsizeof((0.,0.))+2*sys.getsizeof(0.)
        weight = (sys.getsizeof(key)+sys.getsizeof(packed)+sys.getsizeof(points)+
                  sys.getsizeof(local)+(len(points)+len(local))*pair_bytes+512)
        with self.lock:
            if weight <= self.limit and self.max_entries:
                previous = self.entries.pop(key, None)
                if previous is not None:self.bytes -= previous[2]
                while self.entries and (self.bytes+weight > self.limit or
                                        len(self.entries) >= self.max_entries):
                    _, old = self.entries.popitem(last=False)
                    self.bytes -= old[2]
                self.entries[key] = points, compiled, weight
                self.bytes += weight
        return ScreenPoints(points, compiled)


screen_cache = ScreenCache()
