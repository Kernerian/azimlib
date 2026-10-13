"""Original OpenGL scene painter. ModernGL supplies bindings/context, never cartography.

Threefold supersampling, premultiplied composition, floating winding masks and
homogeneous depth triangles. Explicit selection only; no context at import.
"""
from collections import OrderedDict
from dataclasses import dataclass
import hashlib
import math
import threading
import time
import warnings


class GpuError(RuntimeError):pass
class GpuUnavailableError(GpuError):pass
class GpuResourceError(GpuError):pass
class GpuCancelled(GpuError):pass


@dataclass(frozen=True)
class GpuConfig:
    context_backend: str | None = None
    max_surface_bytes: int = 256*1024**2
    max_cache_bytes: int = 32*1024**2
    max_vertices: int = 2000000
    def __post_init__(self):
        if self.context_backend not in (None,'egl'):raise ValueError('GPU context backend must be platform default or explicit egl')
        for value,upper in ((self.max_surface_bytes,512*1024**2),(self.max_cache_bytes,128*1024**2),(self.max_vertices,2000000)):
            if isinstance(value,bool) or not isinstance(value,int) or not 0<value<=upper:raise ValueError('GPU resource limits must be positive bounded integers')


_MASK_VERTEX='''#version 330
in vec3 point;
uniform vec2 size;
uniform vec2 origin;
flat out float weight;
void main(){vec2 p=point.xy+origin;gl_Position=vec4(2.0*p.x/size.x-1.0,1.0-2.0*p.y/size.y,0.0,1.0);weight=point.z;}
'''
_MASK_FRAGMENT='''#version 330
flat in float weight;
out float coverage;
void main(){coverage=weight;}
'''
_QUAD_VERTEX='''#version 330
in vec2 corner;
void main(){gl_Position=vec4(corner,0.0,1.0);}
'''
_PAINT_FRAGMENT='''#version 330
uniform sampler2D mask_image;
uniform vec4 color;
uniform int rule;
out vec4 pixel;
void main(){float n=abs(texelFetch(mask_image,ivec2(gl_FragCoord.xy),0).r);bool on=rule==1?mod(floor(n+0.5),2.0)>0.5:n>0.5;if(!on)discard;pixel=vec4(color.rgb*color.a,color.a);}
'''
_RESOLVE_FRAGMENT='''#version 330
uniform sampler2D source_image;
out vec4 pixel;
void main(){ivec2 p=ivec2(gl_FragCoord.xy)*3;vec4 sum=vec4(0.0);for(int y=0;y<3;y++)for(int x=0;x<3;x++)sum+=texelFetch(source_image,p+ivec2(x,y),0);sum/=9.0;pixel=vec4(sum.a>0.0?sum.rgb/sum.a:vec3(0.0),sum.a);}
'''
_DEPTH_VERTEX='''#version 330
in vec4 position;
in vec4 face_color;
in vec2 texture_uv;
flat out vec4 color;
out vec2 uv;
void main(){gl_Position=position;color=face_color;uv=texture_uv;}
'''
_DEPTH_FRAGMENT='''#version 330
flat in vec4 color;
in vec2 uv;
uniform sampler2D surface_texture;
uniform bool textured;
out vec4 pixel;
void main(){vec4 sample_color=textured?texture(surface_texture,uv):vec4(1.0);if(color.a*sample_color.a==0.0)discard;pixel=color*sample_color;}
'''


class GpuRenderer:
    """Thread-owned context; close on owner thread. Recreate explicitly after loss."""
    def __init__(self,config=None):
        self.config=config or GpuConfig()
        if not isinstance(self.config,GpuConfig):raise TypeError('config must be GpuConfig')
        self.owner=threading.get_ident();self.closed=False;self.lost=False
        self._objects=[];self._surfaces=[];self._cache=OrderedDict();self._cache_bytes=0;self._size=None
        self._textures=OrderedDict();self._texture_bytes=0
        from ._gpu_geometry import PreparationCache
        self.prepared=PreparationCache(self.config.max_cache_bytes)
        self._generation=-1;self.stats=dict(frames=0,uploads=0,cache_hits=0,uploaded_bytes=0,surface_bytes=0,cache_bytes=0)
        try:
            import moderngl
        except ImportError as exc:raise GpuUnavailableError('GPU needs azimlib[gpu]; CPU remains available') from exc
        self.gl=moderngl
        try:
            options=dict(require=330)
            if self.config.context_backend:options['backend']=self.config.context_backend
            self.ctx=moderngl.create_standalone_context(**options)
            self.info={k:self.ctx.info.get(k) for k in ('GL_VENDOR','GL_RENDERER','GL_VERSION','GL_MAX_TEXTURE_SIZE')}
            self.mask_program=self._own(self.ctx.program(vertex_shader=_MASK_VERTEX,fragment_shader=_MASK_FRAGMENT))
            self.paint_program=self._own(self.ctx.program(vertex_shader=_QUAD_VERTEX,fragment_shader=_PAINT_FRAGMENT))
            self.resolve_program=self._own(self.ctx.program(vertex_shader=_QUAD_VERTEX,fragment_shader=_RESOLVE_FRAGMENT))
            self.depth_program=self._own(self.ctx.program(vertex_shader=_DEPTH_VERTEX,fragment_shader=_DEPTH_FRAGMENT))
            from array import array
            quad=self._own(self.ctx.buffer(array('f',(-1,-1,1,-1,1,1,-1,-1,1,1,-1,1)).tobytes()))
            self.paint_quad=self._own(self.ctx.vertex_array(self.paint_program,[(quad,'2f','corner')]))
            self.resolve_quad=self._own(self.ctx.vertex_array(self.resolve_program,[(quad,'2f','corner')]))
            self.mask_program['size'].value=(1.,1.)
            self.paint_program['mask_image'].value=0;self.resolve_program['source_image'].value=0
            self.depth_program['surface_texture'].value=1
        except Exception as exc:
            self._dispose();raise GpuUnavailableError('Cannot initialize OpenGL 3.3; select an explicit supported context or CPU fallback') from exc
    def _own(self,obj):self._objects.append(obj);return obj
    def _check(self):
        if threading.get_ident()!=self.owner:raise GpuError('GPU context belongs to its creating thread')
        if self.closed:raise GpuError('GPU renderer is closed')
        if self.lost:raise GpuError('GPU context lost; close and explicitly recreate the renderer')
    def _dispose(self):
        for _,objects,size in self._cache.values():
            for obj in reversed(objects):obj.release()
        self._cache.clear();self._cache_bytes=0
        for texture,size in self._textures.values():texture.release()
        self._textures.clear();self._texture_bytes=0
        self.prepared.clear()
        for obj in reversed(self._surfaces+self._objects):
            try:obj.release()
            except Exception:pass
        self._surfaces=[];self._objects=[]
        if hasattr(self,'ctx'):
            try:self.ctx.release()
            except Exception:pass
    def close(self):
        if threading.get_ident()!=self.owner:raise GpuError('Close GPU renderer on its owner thread')
        if self.closed:return
        self._dispose();self.closed=True
    def __enter__(self):self._check();return self
    def __exit__(self,*args):self.close()
    def _resize(self,w,h):
        if self._size==(w,h):return
        size=w*h*(9*16+12)
        if size>self.config.max_surface_bytes:raise GpuResourceError('GPU surface budget exceeded before allocation')
        if max(w,h)*3>self.info['GL_MAX_TEXTURE_SIZE']:raise GpuResourceError('GPU texture dimensions exceed driver limits')
        for obj in reversed(self._surfaces):obj.release()
        self._surfaces=[];self._size=None
        def own(obj):self._surfaces.append(obj);return obj
        self.color=own(self.ctx.texture((w*3,h*3),4,dtype='f2'))
        self.mask=own(self.ctx.texture((w*3,h*3),1,dtype='f4'))
        self.depth=own(self.ctx.depth_texture((w*3,h*3)));self.depth.compare_func=''
        self.output=own(self.ctx.texture((w,h),4,dtype='f1'))
        self.main=own(self.ctx.framebuffer([self.color],self.depth))
        self.mask_fbo=own(self.ctx.framebuffer([self.mask]))
        self.depth_fbo=own(self.ctx.framebuffer(depth_attachment=self.depth))
        self.result=own(self.ctx.framebuffer([self.output]));self._size=(w,h)
        self.volume_color=own(self.ctx.texture((w,h),4,dtype='f2'))
        self.volume_low=own(self.ctx.framebuffer([self.volume_color]))
        self.stats['surface_bytes']=size
    def _buffer(self,data,program,layout,attrs):
        # bytes caches its own hash; equality still compares the full payload,
        # so hash collisions never reuse a different mesh. Include the shader
        # and attribute layout because a VAO belongs to that exact program.
        key=(program.glo,layout,tuple(attrs),data)
        if key in self._cache:
            entry=self._cache[key];self._cache.move_to_end(key);self.stats['cache_hits']+=1;return entry[0]
        # Evict before upload; retained GPU buffer payload has a separate budget.
        if len(data)>self.config.max_cache_bytes:raise GpuResourceError('GPU mesh exceeds the buffer budget')
        while self._cache and (self._cache_bytes+len(data)>self.config.max_cache_bytes or len(self._cache)>=2048):
            _,(_,objects,size)=self._cache.popitem(last=False)
            for obj in reversed(objects):obj.release()
            self._cache_bytes-=size
        buffer=self.ctx.buffer(data)
        try:vao=self.ctx.vertex_array(program,[(buffer,layout,*attrs)])
        except BaseException:buffer.release();raise
        self._cache[key]=(vao,(buffer,vao),len(data));self._cache_bytes+=len(data)
        self.stats['uploads']+=1;self.stats['uploaded_bytes']+=len(data);self.stats['cache_bytes']=self._cache_bytes
        return vao
    def _scissor(self,bounds,clip,scale):
        w,h=self._size;x,y,r,b=bounds
        if clip:
            a,c,cw,ch=clip;x=max(x,a);y=max(y,c);r=min(r,a+cw);b=min(b,c+ch)
        x=max(0,math.floor(x*scale*3));y=max(0,math.floor(y*scale*3))
        r=min(w*3,math.ceil(r*scale*3));b=min(h*3,math.ceil(b*scale*3))
        if r<=x or b<=y:return None
        return x,h*3-b,r-x,b-y
    def _draw(self,draw,scene,scale,anchor,clip):
        data,origin,bounds,color,rule,count=draw
        ax,ay=anchor;origin=(origin[0]+ax,origin[1]+ay)
        bounds=(bounds[0]+ax,bounds[1]+ay,bounds[2]+ax,bounds[3]+ay)
        scissor=self._scissor(bounds,clip,scale)
        if scissor is None:return
        vao=self._buffer(data,self.mask_program,'3f',('point',))
        self.mask_fbo.use();self.ctx.scissor=scissor
        self.mask_fbo.clear(0.,viewport=scissor)
        if not self._two_dimensional:
            self.ctx.enable_only(self.gl.BLEND);self.mask.use(0)
            self._two_dimensional=True
        self.ctx.blend_func=(self.gl.ONE,self.gl.ONE)
        self._mask_origin.value=origin
        vao.render(self.gl.TRIANGLES)
        self.main.use();self.ctx.scissor=scissor
        self.ctx.blend_func=(self.gl.ONE,self.gl.ONE_MINUS_SRC_ALPHA)
        if self._paint_color_value!=color:
            self._paint_color.value=color;self._paint_color_value=color
        if self._paint_rule_value!=rule:
            self._paint_rule.value=rule;self._paint_rule_value=rule
        self.paint_quad.render(self.gl.TRIANGLES)
    def _terrain(self,item,scale):
        from array import array
        from ..terrain3d import clip_triangle
        if len(item.triangles)>20000:raise GpuResourceError('GPU terrain limited to 20000 triangles')
        self.ctx.scissor=None;self.depth_fbo.use();self.depth_fbo.clear(depth=1.)
        values=array('f')
        if item.texture is not None:
            from .._texture3d import validate_texture
            validate_texture(item.texture,item.uv,len(item.triangles))
            tw,th,rgba=item.texture;key=(tw,th,hashlib.sha256(rgba).digest())
            if len(rgba)>self.config.max_cache_bytes:raise GpuResourceError('GPU texture cache budget exceeded')
            if key not in self._textures:
                while self._textures and (self._texture_bytes+len(rgba)>self.config.max_cache_bytes or len(self._textures)>=64):
                    _,(texture,size)=self._textures.popitem(last=False);texture.release();self._texture_bytes-=size
                texture=self.ctx.texture((tw,th),4,rgba,alignment=1);texture.filter=(self.gl.NEAREST,self.gl.NEAREST);texture.repeat_x=texture.repeat_y=False
                self._textures[key]=(texture,len(rgba));self._texture_bytes+=len(rgba)
                self.stats['texture_uploads']=self.stats.get('texture_uploads',0)+1
            texture,size=self._textures.pop(key);self._textures[key]=(texture,size);texture.use(1)
        self.depth_program['textured'].value=item.texture is not None
        for index,(vertices,color) in enumerate(item.triangles):
            if len(color)!=4 or any(isinstance(c,bool) or not isinstance(c,int) or not 0<=c<=255 for c in color) or color[3] not in (0,255):raise ValueError('GPU terrain accepts opaque or fully masked faces only')
            if not color[3]:continue
            # Shared owned validation; OpenGL performs the homogeneous clipping.
            clip_triangle(vertices)
            for k,vertex in enumerate(vertices):values.extend((*vertex,*(c/255 for c in color),*(item.uv[index][k] if item.uv is not None else (0,0))))
        if not values:return
        vao=self._buffer(values.tobytes(),self.depth_program,'4f 4f 2f',('position','face_color','texture_uv'))
        self.ctx.scissor=None;self.depth_fbo.use();self.depth_fbo.clear(depth=1.)
        self.main.use();self.ctx.enable_only(self.gl.DEPTH_TEST);self.ctx.depth_func='<'
        w,h=self._size
        viewport=(round(item.x*scale*3),round(h*3-(item.y+item.height)*scale*3),max(1,round(item.width*scale*3)),max(1,round(item.height*scale*3)))
        self.ctx.viewport=viewport
        self.ctx.scissor=self._scissor((item.x,item.y,item.x+item.width,item.y+item.height),item.clip,scale)
        if self.ctx.scissor is not None:vao.render(self.gl.TRIANGLES)
        self.ctx.viewport=(0,0,w*3,h*3)
    def render(self,scene,scale=1,*,cancel=None,generation=None):
        self._check()
        if generation is not None:
            if isinstance(generation,bool) or not isinstance(generation,int) or generation<self._generation:raise GpuCancelled('Stale GPU frame generation')
            self._generation=generation
        from ._common import validate
        from ..scene import Raster3D
        from ..colors import to_rgba
        from PIL import Image
        validate(scene)
        if not math.isfinite(scale) or scale<=0:raise ValueError('GPU scale must be finite and positive')
        if len(scene.items)>50000:raise GpuResourceError('GPU scene limited to 50000 primitives')
        w,h=max(1,round(scene.width*scale)),max(1,round(scene.height*scale))
        start=time.perf_counter();count=0
        try:
            self._resize(w,h);self.main.use();self.ctx.scissor=None
            self._two_dimensional=False;self._paint_color_value=None;self._paint_rule_value=None
            self._mask_origin=self.mask_program['origin'];self._paint_color=self.paint_program['color'];self._paint_rule=self.paint_program['rule']
            self.mask_program['size'].value=(scene.width,scene.height)
            r,g,b,a=to_rgba(scene.background or 'none');self.main.clear(r*a,g*a,b*a,a,depth=1.)
            for item in scene.items:
                if cancel is not None and (cancel.is_set() if hasattr(cancel,'is_set') else cancel()):raise GpuCancelled('GPU frame cancelled')
                draws,anchor=self.prepared.get(item)
                for draw in draws:
                    if not isinstance(draw,Raster3D):
                        count+=draw[-1]
                        if count>self.config.max_vertices:raise GpuResourceError('GPU frame vertex budget exceeded')
                        self._draw(draw,scene,scale,anchor,item.clip)
                    else:
                        self._two_dimensional=False;self._paint_color_value=None;self._paint_rule_value=None
                        self._terrain(draw,scale)
                        if draw.volumes:
                            if not hasattr(self,'volume_painter'):
                                from ._gpu_volume import VolumePainter
                                self.volume_painter=VolumePainter(self)
                            self.volume_painter.draw(draw,scale)
            self.ctx.enable_only(0);self.ctx.scissor=None;self.result.use();self.color.use(0)
            self.resolve_quad.render(self.gl.TRIANGLES)
            raw=self.result.read(components=4,alignment=1)
            if cancel is not None and (cancel.is_set() if hasattr(cancel,'is_set') else cancel()):raise GpuCancelled('GPU frame cancelled before presentation')
            image=Image.frombytes('RGBA',(w,h),raw).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            self.stats.update(frames=self.stats['frames']+1,last_vertices=count,last_seconds=time.perf_counter()-start,
                              prepared_hits=self.prepared.hits,prepared_misses=self.prepared.misses,prepared_bytes=self.prepared.bytes,texture_bytes=self._texture_bytes)
            return image
        except (GpuError,ValueError,ImportError):raise
        except Exception as exc:
            self.lost=True;raise GpuError('GPU drawing failed; context marked lost, explicit recreation or CPU fallback required') from exc


def render_gpu_image(scene,scale=1,*,fallback='raise',config=None,cancel=None):
    if fallback not in ('raise','cpu'):raise ValueError('GPU fallback must be explicitly raise or cpu')
    try:
        with GpuRenderer(config) as renderer:return renderer.render(scene,scale,cancel=cancel)
    except GpuCancelled:raise
    except (GpuError,ImportError):
        if fallback!='cpu':raise
        warnings.warn('GPU unavailable/failed; explicitly requested CPU fallback is in use',RuntimeWarning,stacklevel=2)
        from .pillow import render_image
        return render_image(scene,scale,_cancel=cancel)


def render_gpu_png(scene,path_or_stream,scale=1,*,fallback='raise',config=None):
    from ..text_engine import with_text_notices
    from PIL.PngImagePlugin import PngInfo
    import json
    scene=with_text_notices(scene);image=render_gpu_image(scene,scale,fallback=fallback,config=config)
    info=PngInfo()
    if scene._material_notices:info.add_itxt('Azimlib material provenance',json.dumps(scene._material_notices,ensure_ascii=True,sort_keys=True))
    try:image.save(path_or_stream,format='PNG',pnginfo=info)
    finally:image.close()
