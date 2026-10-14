"""Indexed form of the owned stroke triangles, retaining exact vertex arithmetic.

Index order and degenerate filtering are identical to expanded triangles.
Shared vertices reduce CPU packing/transfer; no analytic stroke approximation,
quantization, altered circle resolution or geographic transformation is used.
"""
import math


def indexed_stroke(rings,width,cap,closed):
    try:import numpy as np
    except ImportError:return None
    from ._gpu_geometry import PackedMesh,PackedBytes,unit_circle
    if width<=0:return PackedMesh(PackedBytes(b''),(0.,0.),(0.,0.,0.,0.),0,PackedBytes(b''))
    radius=width/2;count=max(16,min(2048,math.ceil(math.pi*math.sqrt(radius*8))))
    unit=np.asarray(unit_circle(count));vertices=[];indices=[];offset=0;budget=0
    # Minimal nonzero fan area before placement. A conservative ulp bound
    # below proves translated vertices cannot produce a zero-area triangle.
    ua=unit[1:-1]-unit[0];ub=unit[2:]-unit[0]
    fan_area=float(np.min(np.abs(ua[:,0]*ub[:,1]-ua[:,1]*ub[:,0])))*radius*radius
    def add(points,topology,*,nondegenerate=False):
        nonlocal offset
        v=points.reshape(-1,2);idx=topology.reshape(-1,3)
        if not nondegenerate:
            tri=v[idx];a=tri[:,1]-tri[:,0];b=tri[:,2]-tri[:,0]
            valid=(a[:,0]*b[:,1]-a[:,1]*b[:,0])!=0;idx=idx[valid]
        indices.append((idx+offset).reshape(-1));vertices.append(v);offset+=len(v)
    for ring in rings:
        p=np.asarray(ring,dtype='f8').reshape(-1,2)
        if len(p)<2:continue
        p=p[np.r_[True,np.any(p[1:]!=p[:-1],axis=1)]]
        if closed and len(p)>1 and np.array_equal(p[0],p[-1]):p=p[:-1]
        if len(p)<2:continue
        end=np.roll(p,-1,axis=0) if closed else p[1:];start=p if closed else p[:-1]
        delta=end-start;length=np.hypot(delta[:,0],delta[:,1]);direction=delta/length[:,None]
        normals=np.column_stack((-direction[:,1],direction[:,0]))*radius
        quads=np.stack((start+normals,end+normals,end-normals,start-normals),axis=1)
        centers=p if closed else p[1:-1]
        if not closed and cap=='round':centers=np.concatenate((centers,p[[0,-1]]))
        budget+=4*len(quads)+count*len(centers)+(8 if not closed and cap=='square' else 0)
        if budget>700000:raise ValueError('GPU stroke mesh budget exceeded')
        add(quads,(np.arange(len(quads))[:,None]*4+np.array((0,1,2,0,2,3))).reshape(-1,3))
        if len(centers):
            circles=centers[:,None,:]+radius*unit[None,:,:]
            fan=np.column_stack((np.zeros(count-2,dtype='i8'),np.arange(1,count-1),np.arange(2,count)))
            magnitude=float(np.max(np.abs(centers)))+radius
            ulp=math.ulp(magnitude)
            # Coordinates incur multiplication/addition rounding, then two
            # differences and cross products. 256 ulps is conservative versus
            # their summed error bound; borderline/overflow cases use exactly
            # the previous per-triangle predicate. No screen quantization.
            proven=math.isfinite(fan_area) and fan_area>256*ulp*(radius+ulp)
            add(circles,(np.arange(len(centers))[:,None,None]*count+fan).reshape(-1,3),nondegenerate=proven)
        if not closed and cap=='square':
            for i,sign in ((0,-1),(-1,1)):
                v=p[i];n=normals[i];extension=direction[i]*radius*sign
                add(np.asarray((v+n,v+n+extension,v-n+extension,v-n)),np.array(((0,1,2),(0,2,3))))
    if not vertices:return PackedMesh(PackedBytes(b''),(0.,0.),(0.,0.,0.,0.),0,PackedBytes(b''))
    points=np.concatenate(vertices);idx=np.concatenate(indices)
    if len(idx)>2000000:raise ValueError('GPU mesh exceeds two million vertices')
    if not len(idx):return PackedMesh(PackedBytes(b''),(0.,0.),(0.,0.,0.,0.),0,PackedBytes(b''))
    origin=tuple(map(float,points[idx[0]]));used=np.zeros(len(points),dtype=bool);used[idx]=True;referenced=points[used]
    bounds=tuple(map(float,(referenced[:,0].min(),referenced[:,1].min(),referenced[:,0].max(),referenced[:,1].max())))
    out=np.empty((len(points),3),dtype='f4')
    np.subtract(points[:,0],origin[0],out=out[:,0]);np.subtract(points[:,1],origin[1],out=out[:,1]);out[:,2]=1.
    if not np.all(np.isfinite(out)):raise ValueError('GPU vertices exceed finite float32 domain')
    return PackedMesh(PackedBytes(out.tobytes()),origin,bounds,len(idx),PackedBytes(idx.astype('<u4').tobytes()))
