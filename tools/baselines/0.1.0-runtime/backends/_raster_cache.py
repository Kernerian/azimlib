"""Bounded owned RGBA frames for the desktop viewer; never used by savefig.

Keys cover validated drawing primitives, dimensions/background and bundled
font file revisions. Geographic metadata is recomposed on every draw. There is
no coordinate quantization or approximate image rescaling on a cache hit.
"""
from collections import OrderedDict
import hashlib
from numbers import Integral
from ..scene import Text,Path,Circle
from ..renderers._common import validate
from ..typography import font_path


def scene_key(scene):
    validate(scene)
    digest=hashlib.sha256()
    def add(value):digest.update(repr(value).encode('utf-8'));digest.update(b'\x00')
    add((scene.width,scene.height,scene.background));fonts=set()
    for item in scene.items:
        add(type(item).__name__);add(tuple(sorted(item.style.items())));add(item.clip)
        if isinstance(item,Path):
            add(item.closed)
            for part in item.paths:add(tuple(tuple(p) for p in part))
            add('end-path')
        elif isinstance(item,Text):
            add((item.x,item.y,item.text))
            path=font_path(item.style)
            if path is not None:fonts.add(path)
        elif isinstance(item,Circle):add((item.x,item.y,item.r))
        else:add((item.x,item.y,item.width,item.height))
    for path in sorted(fonts):
        add(str(path))
        add(hashlib.sha256(path.read_bytes()).digest() if path.exists() else None)
    return digest.digest()


class RasterCache:
    """LRU of at most four frames / 16 MiB cached RGBA pixel storage.

    Does not count active image, Tk PhotoImage, composition, Python objects or
    temporary copies in that bound. Cached images never escape: hits are copies.
    """
    def __init__(self,*,max_entries=4,max_bytes=16*1024*1024):
        for value in (max_entries,max_bytes):
            if isinstance(value,bool) or not isinstance(value,Integral) or value<0:
                raise ValueError('Cache limits must be non-negative integers')
        self.max_entries=max_entries;self.max_bytes=max_bytes
        self._images=OrderedDict();self.bytes=0;self.hits=0;self.misses=0

    def lookup(self,scene):
        key=scene_key(scene)
        if key not in self._images:self.misses+=1;return key,None
        self.hits+=1;image=self._images.pop(key);self._images[key]=image
        return key,image.copy()

    def store(self,key,image):
        if image.mode!='RGBA':raise ValueError('Cache stores RGBA images only')
        size=image.width*image.height*4
        if not self.max_entries or size>self.max_bytes:return
        # Allocate before evicting so failed copies leave prior entries intact.
        owned=image.copy()
        previous=self._images.pop(key,None)
        if previous is not None:self.bytes-=previous.width*previous.height*4;previous.close()
        while self._images and (len(self._images)>=self.max_entries or self.bytes+size>self.max_bytes):
            _,old=self._images.popitem(last=False);self.bytes-=old.width*old.height*4;old.close()
        self._images[key]=owned;self.bytes+=size

    def clear(self):
        for image in self._images.values():image.close()
        self._images.clear();self.bytes=0
