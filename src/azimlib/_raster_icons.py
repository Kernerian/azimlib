"""Bounded premultiplied sprite sampling and own standard PNG byte encoder."""
from functools import lru_cache
import math,struct,zlib

@lru_cache(maxsize=8)
def rotated(texture,size,rotation):
    from PIL import Image
    w,h,raw=texture
    factor=2;long=max(1,math.ceil(size*factor));rw=max(1,round(w/max(w,h)*long));rh=max(1,round(h/max(w,h)*long))
    if max(rw,rh)>1024:raise ValueError('Icon sample budget exceeded')
    with Image.frombytes('RGBA',(w,h),raw) as source:
        with source.convert('RGBa') as pre:
            with pre.resize((rw,rh),Image.Resampling.BICUBIC) as resized:
                with resized.rotate(rotation,resample=Image.Resampling.BICUBIC,expand=True) as tilted:
                    if tilted.width*tilted.height>1048576:raise ValueError('Rotated icon sample budget exceeded')
                    with tilted.convert('RGBA') as result:return result.width,result.height,result.tobytes(),size/long

def png_bytes(item):
    w,h=item.pixel_width,item.pixel_height
    def chunk(name,data):return struct.pack('>I',len(data))+name+data+struct.pack('>I',zlib.crc32(name+data)&0xffffffff)
    data=b''.join(b'\0'+item.rgba[j*w*4:(j+1)*w*4] for j in range(h))
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(data))+chunk(b'IEND',b'')
