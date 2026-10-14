"""NumPy accelerates our same bounded midpoint/Beer equations; not a renderer."""
import numpy as np
from .terrain3d import RasterResult


def sample(layer,p):
    f=layer.field;dims=np.array(f.shape[::-1]);q=(p-np.array(f.origin))/np.array(f.spacing)
    valid=np.all((q>=0)&(q<=dims-1),axis=-1);q=np.clip(q,0,dims-1);base=np.minimum(np.floor(q).astype(int),dims-2);t=q-base;out=np.zeros(q.shape[:-1])
    grid=np.frombuffer(f.values,dtype='<f4').reshape(f.shape)
    for dz in (0,1):
        for dy in (0,1):
            for dx in (0,1):
                weight=np.prod(np.where(np.array((dx,dy,dz)),t,1-t),axis=-1);v=grid[base[...,2]+dz,base[...,1]+dy,base[...,0]+dx]
                valid&=(weight==0)|np.isfinite(v);out+=np.where(np.isfinite(v),v,0)*weight
    return np.where(valid,out,np.nan)


def colors(layer,v):
    lo,hi=layer.limits;valid=np.isfinite(v)
    if layer.logarithmic:
        valid&=v>0;v=np.log(np.maximum(v,np.finfo(float).tiny));lo,hi=np.log(lo),np.log(hi)
    t=np.zeros_like(v) if hi==lo else np.clip((v-lo)/(hi-lo),0,1)*255
    t=np.where(valid,t,0);i=np.minimum(254,t.astype(int));u=t-i;lut=np.frombuffer(layer.table,dtype='<f4').reshape(256,4)
    out=lut[i]*(1-u[...,None])+lut[i+1]*u[...,None];out[...,3]=np.where(valid,out[...,3],0)
    return out


def slab(bounds,o,d,maximum):
    low=np.zeros(o.shape[:-1]);high=np.array(maximum,copy=True);valid=np.ones(low.shape,dtype=bool)
    for k in range(3):
        parallel=np.abs(d[...,k])<1e-15;valid&=~parallel|((o[...,k]>=bounds[2*k])&(o[...,k]<=bounds[2*k+1]))
        safe=np.where(parallel,1.,d[...,k]);a=(bounds[2*k]-o[...,k])/safe;b=(bounds[2*k+1]-o[...,k])/safe
        low=np.maximum(low,np.where(parallel,-np.inf,np.minimum(a,b)));high=np.minimum(high,np.where(parallel,np.inf,np.maximum(a,b)))
    return low,high,valid&(high>low)


def shade(layer,p):
    light=layer.light
    if light is None:return np.ones(p.shape[:-1])
    gradient=[]
    for k,s in enumerate(layer.field.spacing):
        offset=np.eye(3)[k]*s*.5;a=sample(layer,p-offset);b=sample(layer,p+offset)
        gradient.append(np.where(np.isfinite(a)&np.isfinite(b),-(b-a)/s,0))
    gradient=np.stack(gradient,axis=-1);size=np.linalg.norm(gradient,axis=-1);diff=np.maximum(0,np.sum(gradient*np.array(light.direction),axis=-1)/np.maximum(size,1e-12))
    value=light.ambient+light.diffuse*diff
    if light.shadow_steps:
        direction=np.broadcast_to(np.array(light.direction),p.shape);_,end,valid=slab(layer.field.bounds,p,direction,np.full(p.shape[:-1],np.inf));ds=np.where(valid,end/light.shadow_steps,0);tau=np.zeros(ds.shape)
        for i in range(light.shadow_steps):
            rgba=colors(layer,sample(layer,p+direction*((i+.5)*ds)[...,None]));tau+=-np.log(np.maximum(1e-12,1-rgba[...,3]))*ds/layer.reference_length*layer.density
        value=light.ambient+(value-light.ambient)*np.exp(-tau)
    return value


def compose(item,geometry,width,height,steps,check):
    layers=item.volumes;inv=np.array(layers[0].inverse).reshape(4,4);out=np.frombuffer(geometry.rgba,dtype=np.uint8).reshape(height,width,4).copy();depth=np.asarray(geometry.depth).reshape(height,width)
    step=min(v.step for v in layers)
    for row in range(0,height,16):
        if check:check()
        stop=min(height,row+16);xx,yy=np.meshgrid(2*(np.arange(width)+.5)/width-1,1-2*(np.arange(row,stop)+.5)/height)
        def world(z):
            q=np.stack((xx,yy,np.broadcast_to(z,xx.shape),np.ones(xx.shape)),axis=-1)@inv.T
            return q[...,:3]/q[...,3,None]
        origin=world(-1.);far=world(1.);direction=far-origin;length=np.linalg.norm(direction,axis=-1);direction/=length[...,None]
        geometry_z=depth[row:stop];hit=world(np.where(np.isfinite(geometry_z),geometry_z,1.));length=np.where(np.isfinite(geometry_z),np.sum((hit-origin)*direction,axis=-1),length)
        intervals=[slab(v.field.bounds,origin,direction,length) for v in layers]
        start=np.minimum.reduce([np.where(valid,a,np.inf) for a,b,valid in intervals]);end=np.maximum.reduce([np.where(valid,b,-np.inf) for a,b,valid in intervals]);active=np.isfinite(start)&(end>start);start=np.where(active,start,0)
        rgb=np.zeros((*xx.shape,3));alpha=np.zeros(xx.shape)
        for i in range(steps):
            ds=np.maximum(0,np.minimum(step,end-start-i*step));use=active&(ds>0)&(alpha<.999999)
            if not np.any(use):break
            t=start+i*step+ds/2;p=origin+direction*t[...,None];tau=np.zeros(xx.shape);color=np.zeros(rgb.shape)
            for layer,(a,b,valid) in zip(layers,intervals):
                rgba=colors(layer,sample(layer,p));amount=-np.log(np.maximum(1e-12,1-rgba[...,3]))*ds/layer.reference_length*layer.density
                amount=np.where(use&valid&(t>=a)&(t<=b),amount,0);tau+=amount;color+=rgba[...,:3]*(amount*shade(layer,p))[...,None]
            a=1-np.exp(-tau);rgb+=(1-alpha)[...,None]*a[...,None]*color/np.maximum(tau[...,None],1e-30);alpha+=(1-alpha)*a
        base=out[row:stop].astype(float)/255;outa=alpha+(1-alpha)*base[...,3];color=rgb+(1-alpha)[...,None]*base[...,:3]*base[...,3,None]
        out[row:stop,:,:3]=np.rint(np.clip(color/np.maximum(outa[...,None],1e-30),0,1)*255).astype(np.uint8);out[row:stop,:,3]=np.rint(outa*255).astype(np.uint8)
    return RasterResult(width,height,out.tobytes(),geometry.depth)
