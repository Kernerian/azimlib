"""Bulk arithmetic for our round-join stroke polygons; NumPy is optional.

This emits the same quads and circle fans as StrokeMesh and the CPU stroke
constructor. It changes preparation cost, not width, tessellation or clipping.
"""
import math


def round_stroke(rings, width, cap, closed):
    try: import numpy as np
    except ImportError: return None
    from ._gpu_geometry import unit_circle
    if width <= 0: return np.empty((0,3))
    radius=width/2
    count=max(16,min(2048,math.ceil(math.pi*math.sqrt(radius*8))))
    unit=np.asarray(unit_circle(count))
    chunks=[];points=0;vertices=0
    def append_triangles(triangles):
        nonlocal vertices
        flat=triangles.reshape(-1,3,2)
        a=flat[:,1]-flat[:,0];b=flat[:,2]-flat[:,0]
        flat=flat[(a[:,0]*b[:,1]-a[:,1]*b[:,0])!=0].reshape(-1,2)
        vertices+=len(flat)
        if vertices>2000000: raise ValueError('GPU mesh exceeds two million vertices')
        out=np.ones((len(flat),3));out[:,:2]=flat;chunks.append(out)
    for ring in rings:
        p=np.asarray(ring,dtype='f8').reshape(-1,2)
        if len(p)<2: continue
        p=p[np.r_[True,np.any(p[1:]!=p[:-1],axis=1)]]
        if closed and len(p)>1 and np.array_equal(p[0],p[-1]): p=p[:-1]
        if len(p)<2: continue
        end=np.roll(p,-1,axis=0) if closed else p[1:]
        start=p if closed else p[:-1]
        delta=end-start
        length=np.hypot(delta[:,0],delta[:,1])
        directions=delta/length[:,None]
        normals=np.column_stack((-directions[:,1],directions[:,0]))*radius
        quads=np.stack((start+normals,end+normals,end-normals,start-normals),axis=1)
        points+=4*len(quads)
        centers=p if closed else p[1:-1]
        if not closed and cap=='round': centers=np.concatenate((centers,p[[0,-1]]))
        points+=count*len(centers)
        if not closed and cap=='square': points+=8
        if points>700000: raise ValueError('GPU stroke mesh budget exceeded')
        append_triangles(quads[:,[0,1,2,0,2,3]])
        if len(centers):
            circles=centers[:,None,:]+radius*unit[None,:,:]
            a=np.broadcast_to(circles[:,0:1,:],circles[:,1:-1,:].shape)
            append_triangles(np.stack((a,circles[:,1:-1,:],circles[:,2:,:]),axis=2))
        if not closed and cap=='square':
            for i,sign in ((0,-1),(-1,1)):
                v=p[i];n=normals[i];extension=directions[i]*radius*sign
                q=np.asarray((v+n,v+n+extension,v-n+extension,v-n))
                append_triangles(q[[0,1,2,0,2,3]])
    return np.concatenate(chunks) if chunks else np.empty((0,3))
