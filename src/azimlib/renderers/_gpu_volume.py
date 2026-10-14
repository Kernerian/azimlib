"""Original bounded GLSL midpoint ray marcher; same physical model as CPU."""
import hashlib
import math
from array import array


_FRAGMENT='''#version 330
uniform mat4 inverse_camera;
uniform vec4 viewport;
uniform int count;
uniform int max_steps;
uniform float step_length;
uniform vec3 lower[4];
uniform vec3 upper[4];
uniform vec3 spacing[4];
uniform ivec3 dimensions[4];
uniform vec4 parameters[4]; // scalar limits, reference metres, density
uniform int logarithmic[4];
uniform vec4 lighting[4]; // direction toward light, ambient
uniform float diffuse[4];
uniform int shadow_steps[4];
uniform sampler3D field0;
uniform sampler3D field1;
uniform sampler3D field2;
uniform sampler3D field3;
uniform sampler2D table0;
uniform sampler2D table1;
uniform sampler2D table2;
uniform sampler2D table3;
uniform sampler2D geometry_depth;
out vec4 pixel;
float missing(){return uintBitsToFloat(0x7fc00000u);}
vec3 world(vec3 p){vec4 q=inverse_camera*vec4(p,1.0);return q.xyz/q.w;}
bool slab(int n,vec3 o,vec3 d,float maximum,out float entry,out float exit){
    entry=0.0;exit=maximum;
    for(int k=0;k<3;k++){
        if(abs(d[k])<1e-15){if(o[k]<lower[n][k]||o[k]>upper[n][k])return false;}
        else{float a=(lower[n][k]-o[k])/d[k];float b=(upper[n][k]-o[k])/d[k];entry=max(entry,min(a,b));exit=min(exit,max(a,b));}
    }return exit>entry;
}
float node(int n,ivec3 p){if(n==0)return texelFetch(field0,p,0).r;if(n==1)return texelFetch(field1,p,0).r;if(n==2)return texelFetch(field2,p,0).r;return texelFetch(field3,p,0).r;}
float sample_field(int n,vec3 p){
    vec3 q=(p-lower[n])/spacing[n];vec3 last=vec3(dimensions[n]-1);
    if(any(lessThan(q,vec3(0)))||any(greaterThan(q,last)))return missing();
    ivec3 base=min(ivec3(floor(q)),dimensions[n]-2);vec3 t=q-vec3(base);float value=0.0;
    for(int z=0;z<2;z++)for(int y=0;y<2;y++)for(int x=0;x<2;x++){
        float w=(x==1?t.x:1.0-t.x)*(y==1?t.y:1.0-t.y)*(z==1?t.z:1.0-t.z);
        if(w==0.0)continue;float v=node(n,base+ivec3(x,y,z));if(isnan(v)||isinf(v))return missing();value+=w*v;
    }return value;
}
vec4 rgba(int n,float v){
    if(isnan(v)||isinf(v)||(logarithmic[n]!=0&&v<=0.0))return vec4(0);
    float lo=parameters[n].x,hi=parameters[n].y;if(logarithmic[n]!=0){lo=log(lo);hi=log(hi);v=log(v);}
    float t=hi==lo?0.0:clamp((v-lo)/(hi-lo),0.0,1.0);vec2 uv=vec2((t*255.0+0.5)/256.0,0.5);
    if(n==0)return texture(table0,uv);if(n==1)return texture(table1,uv);if(n==2)return texture(table2,uv);return texture(table3,uv);
}
float extinction(float a){return -log(max(1e-12,1.0-a));}
float shade(int n,vec3 p){
    if(diffuse[n]<0.0)return 1.0;
    vec3 g=vec3(0);for(int k=0;k<3;k++){vec3 offset=vec3(0);offset[k]=spacing[n][k]*0.5;float a=sample_field(n,p-offset),b=sample_field(n,p+offset);if(!isnan(a)&&!isnan(b))g[k]=-(b-a)/spacing[n][k];}
    float size=length(g);float amount=size>1e-12?max(0.0,dot(g/size,lighting[n].xyz)):0.0;
    float value=lighting[n].w+diffuse[n]*amount;
    if(shadow_steps[n]>0){float a,b;if(slab(n,p,lighting[n].xyz,1e30,a,b)){
        float ds=b/float(shadow_steps[n]),tau=0.0;
        for(int j=0;j<32;j++){if(j>=shadow_steps[n])break;float alpha=rgba(n,sample_field(n,p+lighting[n].xyz*(float(j)+0.5)*ds)).a;tau+=extinction(alpha)*ds/parameters[n].z*parameters[n].w;}
        value=lighting[n].w+(value-lighting[n].w)*exp(-tau);
    }}return value;
}
void main(){
    vec2 ndc=2.0*(gl_FragCoord.xy-viewport.xy)/viewport.zw-1.0;vec3 origin=world(vec3(ndc,-1)),far=world(vec3(ndc,1));vec3 d=normalize(far-origin);float maximum=length(far-origin);
    float depth=texelFetch(geometry_depth,ivec2(gl_FragCoord.xy)*3+ivec2(1),0).r;
    if(depth<1.0)maximum=min(maximum,dot(world(vec3(ndc,depth*2.0-1.0))-origin,d));
    float starts[4],ends[4];bool hits[4];float start=1e30,end=-1e30;
    for(int n=0;n<4;n++){hits[n]=false;if(n>=count)continue;hits[n]=slab(n,origin,d,maximum,starts[n],ends[n]);if(hits[n]){start=min(start,starts[n]);end=max(end,ends[n]);}}
    vec3 color=vec3(0);float alpha=0.0;
    if(end>start)for(int i=0;i<512;i++){
        if(i>=max_steps||start+float(i)*step_length>=end||alpha>=0.999999)break;
        float ds=min(step_length,end-start-float(i)*step_length);float t=start+float(i)*step_length+ds*0.5;vec3 p=origin+d*t;float tau=0.0;vec3 mixture=vec3(0);
        for(int n=0;n<4;n++){
            if(n>=count||!hits[n]||t<starts[n]||t>ends[n])continue;
            vec4 c=rgba(n,sample_field(n,p));float amount=extinction(c.a)*ds/parameters[n].z*parameters[n].w;
            if(amount>0.0){tau+=amount;mixture+=amount*c.rgb*shade(n,p);}
        }
        if(tau>0.0){float a=1.0-exp(-tau);color+=(1.0-alpha)*a*mixture/tau;alpha+=(1.0-alpha)*a;}
    }
    pixel=vec4(color,alpha);
}
'''

_COMPOSITE='''#version 330
uniform sampler2D volume_image;
out vec4 pixel;
void main(){pixel=texelFetch(volume_image,ivec2(gl_FragCoord.xy)/3,0);}
'''


class VolumePainter:
    def __init__(self,renderer):
        from .gpu import _QUAD_VERTEX
        r=renderer;self.r=r
        self.program=r._own(r.ctx.program(vertex_shader=_QUAD_VERTEX,fragment_shader=_FRAGMENT));self.composite=r._own(r.ctx.program(vertex_shader=_QUAD_VERTEX,fragment_shader=_COMPOSITE))
        quad=r._own(r.ctx.buffer(array('f',(-1,-1,1,-1,1,1,-1,-1,1,1,-1,1)).tobytes()))
        self.quad=r._own(r.ctx.vertex_array(self.program,[(quad,'2f','corner')]));self.overlay=r._own(r.ctx.vertex_array(self.composite,[(quad,'2f','corner')]))
        for i in range(4):self.program[f'field{i}'].value=2+i;self.program[f'table{i}'].value=6+i
        self.program['geometry_depth'].value=10;self.composite['volume_image'].value=0
    def texture(self,key,size,components,data,dimension,unit,linear=False):
        from .gpu import GpuResourceError
        r=self.r
        if key not in r._textures:
            while r._textures and (r._texture_bytes+len(data)>r.config.max_cache_bytes or len(r._textures)>=64):
                _,(texture,old)=r._textures.popitem(last=False);texture.release();r._texture_bytes-=old
            if len(data)>r.config.max_cache_bytes:raise GpuResourceError('Volume texture exceeds GPU cache budget')
            texture=r.ctx.texture3d(size,components,data,dtype='f4',alignment=1) if dimension==3 else r.ctx.texture(size,components,data,dtype='f4',alignment=1)
            texture.filter=(r.gl.LINEAR,r.gl.LINEAR) if linear else (r.gl.NEAREST,r.gl.NEAREST);texture.repeat_x=texture.repeat_y=False
            if dimension==3:texture.repeat_z=False
            r._textures[key]=(texture,len(data));r._texture_bytes+=len(data);r.stats['volume_texture_uploads']=r.stats.get('volume_texture_uploads',0)+1
        texture,length=r._textures.pop(key);r._textures[key]=(texture,length);texture.use(unit)
    def draw(self,item,scale):
        from .gpu import GpuResourceError
        r=self.r;layers=item.volumes;w,h=r._size
        width,height=max(1,round(item.width*scale)),max(1,round(item.height*scale))
        diagonal=math.sqrt(sum((max(v.field.bounds[2*k+1] for v in layers)-min(v.field.bounds[2*k] for v in layers))**2 for k in range(3)));step=min(v.step for v in layers);steps=math.ceil(diagonal/step)
        cost=sum(1+(6+v.light.shadow_steps if v.light is not None else 0) for v in layers)
        if width*height>min(v.field.budget.max_pixels for v in layers) or steps>min(v.field.budget.max_steps for v in layers) or width*height*steps*cost>min(v.field.budget.max_samples for v in layers):raise GpuResourceError('Volume pixel/step/sample budget exceeded before drawing')
        if sum(len(v.field.values)+len(v.table) for v in layers)>r.config.max_cache_bytes:raise GpuResourceError('Combined volume textures exceed GPU cache budget')
        for i,v in enumerate(layers):
            self.texture(('volume',v.field.shape,hashlib.sha256(v.field.values).digest()),v.field.shape[::-1],1,v.field.values,3,2+i)
            self.texture(('transfer',hashlib.sha256(v.table).digest()),(256,1),4,v.table,2,6+i,True)
        # Unused sampler slots still bind valid resources of their declared type.
        for i in range(len(layers),4):
            v=layers[-1];self.texture(('volume',v.field.shape,hashlib.sha256(v.field.values).digest()),v.field.shape[::-1],1,v.field.values,3,2+i);self.texture(('transfer',hashlib.sha256(v.table).digest()),(256,1),4,v.table,2,6+i,True)
        slots=list(layers)+[layers[-1]]*(4-len(layers));p=self.program
        shift=tuple(sum(v.field.bounds[2*k]+v.field.bounds[2*k+1] for v in layers)/(2*len(layers)) for k in range(3))
        source=layers[0].inverse;inverse=tuple(source[i*4+j]-(shift[i]*source[12+j] if i<3 else 0) for i in range(4) for j in range(4))
        p['inverse_camera'].write(array('f',(inverse[j*4+i] for i in range(4) for j in range(4))).tobytes())
        x,y,bw,bh=item.x*scale,h-(item.y+item.height)*scale,item.width*scale,item.height*scale
        p['viewport'].value=(x,y,bw,bh);p['count'].value=len(layers);p['max_steps'].value=steps;p['step_length'].value=step
        p['lower'].value=tuple(tuple(v.field.bounds[2*k]-shift[k] for k in range(3)) for v in slots);p['upper'].value=tuple(tuple(v.field.bounds[2*k+1]-shift[k] for k in range(3)) for v in slots)
        p['spacing'].value=tuple(v.field.spacing for v in slots);p['dimensions'].value=tuple(v.field.shape[::-1] for v in slots)
        p['parameters'].value=tuple((*v.limits,v.reference_length,v.density) for v in slots);p['logarithmic'].value=tuple(int(v.logarithmic) for v in slots)
        p['lighting'].value=tuple((*v.light.direction,v.light.ambient) if v.light else (0,0,1,1) for v in slots);p['diffuse'].value=tuple(v.light.diffuse if v.light else -1 for v in slots);p['shadow_steps'].value=tuple(v.light.shadow_steps if v.light else 0 for v in slots)
        r.ctx.enable_only(0);r.ctx.scissor=None;r.volume_low.use();r.volume_low.clear(0,0,0,0);r.ctx.viewport=(0,0,w,h);r.depth.use(10)
        clip=r._scissor((item.x,item.y,item.x+item.width,item.y+item.height),item.clip,scale)
        if clip is not None:
            cx,cy,cw,ch=clip;r.ctx.scissor=(cx//3,cy//3,math.ceil(cw/3),math.ceil(ch/3));self.quad.render(r.gl.TRIANGLES)
        r.ctx.scissor=clip;r.main.use();r.ctx.viewport=(0,0,w*3,h*3);r.volume_color.use(0);r.ctx.enable_only(r.gl.BLEND);r.ctx.blend_func=(r.gl.ONE,r.gl.ONE_MINUS_SRC_ALPHA)
        if clip is not None:self.overlay.render(r.gl.TRIANGLES)
        r.stats['volume_frames']=r.stats.get('volume_frames',0)+1;r.stats['volume_steps_bound']=steps
