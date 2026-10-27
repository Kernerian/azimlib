"""Optional physical icon effects, independent of source strokes and coordinates."""
from dataclasses import dataclass,replace
import math,hashlib
from collections import OrderedDict
from threading import RLock
_MASK_CACHE=OrderedDict()
_MASK_CACHE_ENTRIES=256
_MASK_CACHE_BYTES=8*1024*1024
_MASK_LOCK=RLock()

def _mask_key(items,padding):
 from .scene import Path
 digest=hashlib.sha256(repr(padding).encode())
 for item in items:
  if isinstance(item,Path):value=(item.paths,item.closed,dict(item.style))
  else:
   value=(item.x,item.y,item.width,item.height,item.pixel_width,item.pixel_height,dict(item.style));digest.update(item.rgba)
  digest.update(repr(value).encode())
 return digest.digest()

def _clear_mask_cache():
 with _MASK_LOCK:_MASK_CACHE.clear()
from .geometry import _number
@dataclass(frozen=True)
class IconHalo:
 color:str='white'
 width:float=1.
 alpha:float=1.
 def __post_init__(self):
  from .colors import to_rgba
  to_rgba(self.color)
  if not 0<=_number(self.width)<=8 or not 0<=_number(self.alpha)<=1:raise ValueError('Icon halo requires width0..8pt, alpha0..1')
@dataclass(frozen=True)
class IconShadow:
 color:str='#142733'
 alpha:float=.25
 offset:tuple=(1.,1.)
 blur:float=0.
 def __post_init__(self):
  from .colors import to_rgba
  to_rgba(self.color);v=tuple(_number(x) for x in self.offset)
  if len(v)!=2 or max(map(abs,v))>16 or not 0<=_number(self.alpha)<=1 or not 0<=_number(self.blur)<=8:raise ValueError('Bounded shadow: offset<=16pt, blur<=8pt, alpha0..1')
  object.__setattr__(self,'offset',v)

def add_effects(items,scene,halo=None,shadow=None):
 """Draw effects behind the unchanged icon. Soft shadow is a local RGBA tile."""
 from .scene import Path,RasterIcon,Scene
 from .typography import POINT
 if not items:return
 if shadow and shadow.alpha:
  if shadow.blur>0 or any(isinstance(i,RasterIcon) for i in items):
   _soft_shadow(items,scene,shadow)
  else:
   dx,dy=(x*POINT for x in shadow.offset)
   for item in items:
    style=dict(item.style,fill=shadow.color if item.style.get('fill','none')!='none' else 'none',stroke=shadow.color if item.style.get('stroke','none')!='none' else 'none',opacity=item.style.get('opacity',1)*shadow.alpha,_icon_effect=True)
    scene.add(replace(item,paths=tuple(tuple((x+dx,y+dy) for x,y in p) for p in item.paths),style=style))
 if halo and halo.width and halo.alpha:
  if any(isinstance(i,RasterIcon) for i in items):_png_halo(items,scene,halo)
  else:
   for item in items:
    style=dict(item.style,fill='none',stroke=halo.color,stroke_width=item.style.get('stroke_width',0)+2*halo.width*POINT,opacity=item.style.get('opacity',1)*halo.alpha,linecap='round',linejoin='round',_icon_effect=True)
    scene.add(replace(item,style=style))

def _mask_tile(items,padding):
 from .scene import Path,RasterIcon,Scene
 from .renderers.pillow import render_image
 from PIL import Image
 key=_mask_key(items,padding)
 with _MASK_LOCK:
  cached=_MASK_CACHE.get(key)
  if cached is not None:
   _MASK_CACHE.move_to_end(key);x,y,w,h,data=cached
   return x,y,w,h,Image.frombytes('L',(w,h),data)
 from .layout_engine import primitive_bounds
 boxes=[primitive_bounds(replace(i,clip=None)) for i in items];x=math.floor(min(b[0] for b in boxes)-padding);y=math.floor(min(b[1] for b in boxes)-padding)
 right=math.ceil(max(b[0]+b[2] for b in boxes)+padding);bottom=math.ceil(max(b[1]+b[3] for b in boxes)+padding);w,h=max(1,right-x),max(1,bottom-y)
 if w*h>1000000:raise ValueError('Icon effect tile exceeds1Mpx')
 tile=Scene(w,h,background=None)
 for item in items:
  if isinstance(item,Path):tile.add(replace(item,paths=tuple(tuple((a-x,b-y) for a,b in p) for p in item.paths),clip=None))
  else:tile.add(replace(item,x=item.x-x,y=item.y-y,clip=None))
 with render_image(tile) as image:mask=image.getchannel('A')
 data=mask.tobytes()
 with _MASK_LOCK:
  _MASK_CACHE[key]=(x,y,w,h,data);_MASK_CACHE.move_to_end(key)
  while len(_MASK_CACHE)>_MASK_CACHE_ENTRIES or sum(len(v[4]) for v in _MASK_CACHE.values())>_MASK_CACHE_BYTES:_MASK_CACHE.popitem(last=False)
 return x,y,w,h,mask

def _colored_tile(mask,color,alpha):
 from .colors import to_rgba
 from PIL import Image
 rgba=to_rgba(color);mask=mask.point([round(i*alpha*rgba[3]) for i in range(256)]);im=Image.new('RGBA',mask.size,tuple(round(c*255) for c in rgba[:3])+(255,));im.putalpha(mask);mask.close();data=im.tobytes();im.close();return data

def _soft_shadow(items,scene,shadow):
 from PIL import ImageFilter
 from .typography import POINT
 from .scene import RasterIcon
 x,y,w,h,mask=_mask_tile(items,3*shadow.blur*POINT+2)
 try:
  softened=mask.filter(ImageFilter.GaussianBlur(shadow.blur*POINT)) if shadow.blur else mask.copy()
  try:data=_colored_tile(softened,shadow.color,shadow.alpha)
  finally:softened.close()
 finally:mask.close()
 dx,dy=(v*POINT for v in shadow.offset)
 scene.add(RasterIcon(x+dx,y+dy,w,h,w,h,data,{'_icon_effect':True},items[0].clip))

def _png_halo(items,scene,halo):
 from PIL import ImageFilter
 from .typography import POINT
 from .scene import RasterIcon
 radius=math.ceil(halo.width*POINT);x,y,w,h,mask=_mask_tile(items,radius+1)
 try:
  dilated=mask.filter(ImageFilter.MaxFilter(2*radius+1))
  try:data=_colored_tile(dilated,halo.color,halo.alpha)
  finally:dilated.close()
 finally:mask.close()
 scene.add(RasterIcon(x,y,w,h,w,h,data,{'_icon_effect':True},items[0].clip))
