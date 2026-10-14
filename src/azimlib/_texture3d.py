"""Owned nearest-neighbour opaque/masked texture reference, perspective-correct UV."""
import math


def validate_texture(texture,uv,count):
    try:w,h,pixels=texture
    except (TypeError,ValueError):raise ValueError('Texture requires width, height and RGBA bytes') from None
    if any(isinstance(v,bool) or not isinstance(v,int) or v<=0 for v in (w,h)) or w*h>8000000:raise ValueError('Texture requires integer dimensions and <=8M pixels')
    if not isinstance(pixels,bytes) or len(pixels)!=w*h*4:raise ValueError('Texture requires immutable RGBA bytes with exact size')
    if any(a not in (0,255) for a in pixels[3::4]):raise ValueError('3D texture alpha must be opaque or fully masked')
    uv=tuple(tuple(tuple(float(v) for v in p) for p in face) for face in uv or ())
    if len(uv)!=count or any(len(face)!=3 or any(len(p)!=2 or not all(math.isfinite(v) and 0<=v<=1 for v in p) for p in face) for face in uv):raise ValueError('Each textured triangle needs three finite normalized UV pairs')
    return (w,h,pixels),uv


def clipped(vertices,uv):
    polygon=[tuple(p)+tuple(t) for p,t in zip(vertices,uv)]
    for axis,sign in ((0,1),(0,-1),(1,1),(1,-1),(2,1),(2,-1)):
        if not polygon:break
        output=[];a=polygon[-1];da=a[3]+sign*a[axis]
        for b in polygon:
            db=b[3]+sign*b[axis]
            if (da>=0)!=(db>=0):
                t=da/(da-db);output.append(tuple(x+t*(y-x) for x,y in zip(a,b)))
            if db>=0:output.append(b)
            a,da=b,db
        polygon=output
    return tuple((polygon[0],polygon[i],polygon[i+1]) for i in range(1,len(polygon)-1) if all(v[3]>1e-12 for v in (polygon[0],polygon[i],polygon[i+1])))


def atlas(groups):
    """One depth scene, deterministic non-overlapping textures plus a white texel."""
    textures={texture:None for texture,faces in groups if texture is not None}
    width=max((t[0] for t in textures),default=1);height=1+sum(t[1] for t in textures)
    if width*height>8000000:raise ValueError('3D texture atlas exceeds 8M pixels')
    data=bytearray(b'\xff'*(width*height*4));offset=1
    for texture in textures:
        w,h,pixels=texture;textures[texture]=offset
        for row in range(h):data[((offset+row)*width)*4:((offset+row)*width+w)*4]=pixels[row*w*4:(row+1)*w*4]
        offset+=h
    triangles=[];uvs=[]
    for texture,faces in groups:
        for points,color,uv in faces:
            triangles.append((points,color))
            if texture is None:uvs.append(((.5/width,.5/height),)*3)
            else:
                w,h,_=texture;offset=textures[texture]
                uvs.append(tuple((min(u,1-1e-7)*w/width,(offset+min(v,1-1e-7)*h)/height) for u,v in uv))
    return tuple(triangles),(width,height,bytes(data)),tuple(uvs)


def rasterize_textured(item,width,height,*,check=None):
    from array import array
    from .terrain3d import edge,top_left,RasterResult,clip_triangle
    if width*height>8000000:raise ValueError('Textured raster limited to 8M pixels')
    texture,uvs=validate_texture(item.texture,item.uv,len(item.triangles));tw,th,pixels=texture
    depth=array('d',[math.inf])*(width*height);rgba=bytearray(width*height*4);work=0
    if len(item.triangles)>20000:raise ValueError('Textured raster limited to 20000 triangles')
    for (vertices,color),uv in zip(item.triangles,uvs):
        if len(color)!=4 or any(isinstance(c,bool) or not isinstance(c,int) or not 0<=c<=255 for c in color) or color[3] not in (0,255):raise ValueError('Textured triangles require opaque or masked RGBA')
        clip_triangle(vertices)
        if not color[3]:continue
        for face in clipped(vertices,uv):
            p=[((v[0]/v[3]+1)*width/2,(1-v[1]/v[3])*height/2,v[2]/v[3]) for v in face]
            area=edge(p[0],p[1],*p[2][:2])
            if abs(area)<1e-12:continue
            if area<0:p[1],p[2]=p[2],p[1];face=(face[0],face[2],face[1]);area=-area
            x0=max(0,math.ceil(min(q[0] for q in p)-.5));x1=min(width,math.floor(max(q[0] for q in p)-.5)+1)
            y0=max(0,math.ceil(min(q[1] for q in p)-.5));y1=min(height,math.floor(max(q[1] for q in p)-.5)+1)
            work+=max(0,x1-x0)*max(0,y1-y0)
            if work>64000000:raise ValueError('Textured raster work budget exceeded')
            for y in range(y0,y1):
                if check and y%16==0:check()
                for x in range(x0,x1):
                    e=(edge(p[1],p[2],x+.5,y+.5),edge(p[2],p[0],x+.5,y+.5),edge(p[0],p[1],x+.5,y+.5))
                    if any(v<0 or v==0 and not top_left(a,b) for v,a,b in zip(e,(p[1],p[2],p[0]),(p[2],p[0],p[1]))):continue
                    z=sum(e[i]*p[i][2] for i in range(3))/area;index=y*width+x
                    if z>=depth[index]-1e-7:continue
                    weights=[e[i]/face[i][3] for i in range(3)];total=sum(weights)
                    u,v=(sum(weights[i]*face[i][k] for i in range(3))/total for k in (4,5))
                    tx=max(0,min(tw-1,math.floor(u*tw)));ty=max(0,min(th-1,math.floor(v*th)));offset=(ty*tw+tx)*4
                    sample=pixels[offset:offset+4]
                    if sample[3]==0:continue
                    rgba[index*4:index*4+4]=bytes(round(sample[k]*color[k]/255) for k in range(4));depth[index]=z
    return RasterResult(width,height,bytes(rgba),depth)
