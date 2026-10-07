"""Owned primitive tiles for navigation, never a transformed canvas screenshot."""
from collections import OrderedDict
from copy import deepcopy
from dataclasses import replace
from threading import RLock
from ..scene import Path,Text,Circle
from ..typography import font_path
try:
    import numpy as np
except ImportError:np=None


def _anchor(item):
    if isinstance(item,Path):
        return next((part[0] for part in item.paths if part),None)
    return item.x,item.y


def _signature(item,factor):
    point=_anchor(item)
    if point is None:return None
    x,y=point
    if isinstance(item,Path):
        shape=(item.closed,tuple((len(p),tuple(round(v,3) for i in (0,len(p)//2,-1)
                    for v in (p[i][0]-x,p[i][1]-y))) for p in item.paths if p))
    elif isinstance(item,Text):
        font=font_path(item.style)
        revision=font.stat() if font is not None else None
        phase=(round(item.x*3)%3,round(item.y*3)%3) if factor==1 else None
        shape=(item.text, (revision.st_mtime_ns,revision.st_size) if revision else None,phase)
    elif isinstance(item,Circle):shape=(round(item.r,3),round(item.x*factor*16)%16,round(item.y*factor*16)%16)
    else:shape=round(item.width,3),round(item.height,3)
    return type(item),factor,repr(sorted(item.style.items())),shape


class TileCache:
    """128 entries / 16 MiB retained pixel/array payload; RGBA tile <= 8 MiB.

    Shapes are reused only at integer supersample translations after checking
    every vertex. Tiles are unclipped; clipping, ticks, labels and composition
    always use the new Scene. Text glyph tiles have fresh rounded positions.
    Prepared vertex arrays are separately bounded to 8 MiB per frame. Python
    object overhead is not included in either payload budget.
    """
    max_item_bytes=8*1024*1024
    def __init__(self,*,max_entries=128):
        if isinstance(max_entries,bool) or not isinstance(max_entries,int) or max_entries<1:raise ValueError('Positive integer tile entry capacity required')
        self.max_entries=max_entries
        self.entries=OrderedDict();self.bytes=0;self.hits=self.misses=0
        self._lock=RLock();self.closed=False
        self._prepared={};self._prepared_bytes=0

    def begin_frame(self):
        with self._lock:self._prepared.clear();self._prepared_bytes=0

    def validate_points(self,item):
        import math
        arrays=[];weight=0
        for part in item.paths:
            if np is not None and len(part)>=64:
                try:values=np.asarray(part,dtype=float)
                except (ValueError,TypeError):raise ValueError('Path coordinates must be finite (x, y) pairs') from None
                if values.ndim!=2 or values.shape[1]!=2 or not np.isfinite(values).all():
                    raise ValueError('Path coordinates must be finite (x, y) pairs')
                arrays.append(values);weight+=values.nbytes
            else:
                if any(len(p)!=2 or not all(math.isfinite(v) for v in p) for p in part):
                    raise ValueError('Path coordinates must be finite (x, y) pairs')
                arrays.append(None)
        with self._lock:
            if not self.closed and self._prepared_bytes+weight<=8*1024*1024:
                self._prepared[id(item)]=arrays;self._prepared_bytes+=weight

    def _same_points(self,item,old,old_arrays,dx,dy):
        if len(item.paths)!=len(old.paths):return False
        current=self._prepared.get(id(item))
        for i,(p,q) in enumerate(zip(item.paths,old.paths)):
            if len(p)!=len(q):return False
            if current is not None and old_arrays is not None and current[i] is not None and old_arrays[i] is not None:
                if not (np.abs(current[i]-old_arrays[i]-(dx,dy))<1e-8).all():return False
            elif not all(abs(a-c-dx)<1e-8 and abs(b-d-dy)<1e-8 for (a,b),(c,d) in zip(p,q)):return False
        return True

    def lookup(self,item,factor):
        key=_signature(item,factor)
        with self._lock:
            entry=self.entries.get(key)
            if entry is not None:
                old,image,origin,offset,weight,old_arrays=entry
                if isinstance(item,Text):
                    if offset is None:
                        position=(origin[0]+(round(item.x*3)-round(old.x*3))//3,
                                  origin[1]+(round(item.y*3)-round(old.y*3))//3)
                    else:position=(round(item.x*factor+offset[0]),round(item.y*factor+offset[1]))
                    valid=True
                else:
                    x,y=_anchor(item);ox,oy=_anchor(old);dx,dy=x-ox,y-oy
                    ix,iy=round(dx*factor),round(dy*factor)
                    valid=abs(dx*factor-ix)<1e-7 and abs(dy*factor-iy)<1e-7
                    if valid and isinstance(item,Path):
                        valid=self._same_points(item,old,old_arrays,dx,dy)
                    elif valid and isinstance(item,Circle):valid=abs(item.r-old.r)<1e-8
                    elif valid:valid=abs(item.width-old.width)<1e-8 and abs(item.height-old.height)<1e-8
                    position=origin[0]+ix,origin[1]+iy
                if valid:
                    self.hits+=1;self.entries.move_to_end(key)
                    return image.copy(),position
            self.misses+=1
        return None

    def store(self,item,factor,image,origin,text_offset=None):
        size=image.width*image.height*4;key=_signature(item,factor)
        if key is None or size>self.max_item_bytes:return
        options={'style':deepcopy(dict(item.style))}
        if isinstance(item,Path):options['paths']=tuple(tuple(tuple(p) for p in ring) for ring in item.paths)
        snapshot=replace(item,**options)
        with self._lock:
            if self.closed:return
            arrays=self._prepared.get(id(item)) if isinstance(item,Path) else None
            if arrays is not None:
                arrays=[a.copy() if a is not None else None for a in arrays]
                for a in arrays:
                    if a is not None:a.flags.writeable=False
                size+=sum(a.nbytes for a in arrays if a is not None)
            if size>16*1024*1024:return
            previous=self.entries.pop(key,None)
            if previous is not None:self.bytes-=previous[4];previous[1].close()
            while self.entries and (len(self.entries)>=self.max_entries or self.bytes+size>16*1024*1024):
                _,entry=self.entries.popitem(last=False);self.bytes-=entry[4];entry[1].close()
            self.entries[key]=(snapshot,image.copy(),origin,text_offset,size,arrays);self.bytes+=size

    def close(self):
        with self._lock:
            self.closed=True
            for entry in self.entries.values():entry[1].close()
            self.entries.clear();self.bytes=0
            self._prepared.clear();self._prepared_bytes=0
