"""Exact, per-layout spatial candidates for legend collision scoring.

The grid only removes impossible candidates. Inclusive vertex tests and the
original segment clip still determine scores; no simplification is performed.
"""
import math
from .scene import Path, Circle, Rect


class LegendIndex:
    def __init__(self, items, cell=64.):
        from .label_layout import text_box
        self.cell = cell
        self.points = []; self.segments = []; self.boxes = []
        self.point_cells = {}; self.segment_cells = {}; self.long_segments = []
        try: import numpy as np
        except ImportError: np = None
        self.np = np
        for item in items:
            if isinstance(item, Path):
                for part in item.paths:
                    for p in part:
                        if np is None:
                            key = self._cell(*p)
                            self.point_cells.setdefault(key, []).append(len(self.points))
                        self.points.append(p)
                    for a, b in zip(part, part[1:]):
                        index = len(self.segments); self.segments.append((a, b))
                        if np is not None: continue
                        keys = self._range((min(a[0], b[0]), min(a[1], b[1]),
                                            abs(b[0]-a[0]), abs(b[1]-a[1])))
                        if keys is None: self.long_segments.append(index)
                        else:
                            for key in keys: self.segment_cells.setdefault(key, []).append(index)
            else:
                box = ((item.x-item.r, item.y-item.r, 2*item.r, 2*item.r)
                       if isinstance(item, Circle) else
                       (item.x, item.y, item.width, item.height)
                       if isinstance(item, Rect) else text_box(item.x, item.y, item.text, item.style))
                self.boxes.append(box)
        if np is not None:
            self.points = np.asarray(self.points, dtype='f8').reshape(-1, 2)
            self.segments = np.asarray(self.segments, dtype='f8').reshape(-1, 2, 2)

    def _cell(self, x, y):
        return math.floor(x/self.cell), math.floor(y/self.cell)

    def _range(self, box):
        x, y, w, h = box
        a, b = self._cell(x, y); c, d = self._cell(x+w, y+h)
        if (c-a+1)*(d-b+1) > 256: return None
        return [(i, j) for i in range(a, c+1) for j in range(b, d+1)]

    def score(self, box):
        from .render_map import _overlap
        x, y, w, h = box; right = x+w; bottom = y+h
        if self.np is not None:
            np = self.np; points = self.points; a = self.segments[:,0]; b = self.segments[:,1]
            result = int(np.count_nonzero((x <= points[:,0]) & (points[:,0] <= right) &
                                         (y <= points[:,1]) & (points[:,1] <= bottom)))
            dx, dy = b[:,0]-a[:,0], b[:,1]-a[:,1]
            t0 = np.zeros(len(a)); t1 = np.ones(len(a)); valid = np.ones(len(a),dtype=bool)
            for p, q in ((-dx, a[:,0]-x), (dx, right-a[:,0]), (-dy, a[:,1]-y), (dy, bottom-a[:,1])):
                valid &= ~((p == 0) & (q < 0))
                ratio = np.divide(q, p, out=np.zeros(len(p)), where=p!=0)
                t0 = np.maximum(t0, np.where(p < 0, ratio, t0))
                t1 = np.minimum(t1, np.where(p > 0, ratio, t1))
            return result + int(np.count_nonzero(valid & (t0 <= t1))) + 10*sum(_overlap(box,b) for b in self.boxes)
        keys = self._range(box)
        if keys is None:
            points = range(len(self.points)); segments = range(len(self.segments))
        else:
            points = (i for key in keys for i in self.point_cells.get(key, ()))
            segments = set(self.long_segments)
            for key in keys: segments.update(self.segment_cells.get(key, ()))
        result = sum(x <= self.points[i][0] <= right and y <= self.points[i][1] <= bottom for i in points)
        for i in segments:
            a, b = self.segments[i]; t0, t1 = 0., 1.
            dx, dy = b[0]-a[0], b[1]-a[1]
            for p, q in ((-dx, a[0]-x), (dx, right-a[0]), (-dy, a[1]-y), (dy, bottom-a[1])):
                if p == 0:
                    if q < 0: t0, t1 = 1, 0; break
                elif p < 0: t0 = max(t0, q/p)
                else: t1 = min(t1, q/p)
            if t0 <= t1: result += 1
        return result + 10*sum(_overlap(box, b) for b in self.boxes)
