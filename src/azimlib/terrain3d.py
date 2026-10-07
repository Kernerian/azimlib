"""Experimental own metric terrain, homogeneous camera and triangle depth raster.

No globe/volume backend, GIS engine, implicit geoid conversion or transparent
surface sorting. Numeric operations are own code; NumPy is an optional array
accelerator. Coordinates and elevations remain physical metres before display.
"""
from dataclasses import dataclass,replace
from array import array
import math
from .geodesy import Unit,METRE,WGS84

def finite(value):
    value=float(value)
    if not math.isfinite(value):raise ValueError('3D values must be finite')
    return value
def length_unit(unit):
    if isinstance(unit,str):
        try:unit={'m':METRE,'km':Unit('kilometre','km',1000),'ft':Unit('foot','ft',.3048)}[unit]
        except KeyError:raise ValueError('Length unit must be m, km, ft or a Unit') from None
    if not isinstance(unit,Unit) or unit.quantity!='length':raise ValueError('3D coordinates require a length unit')
    return unit
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def normalized(a):
    size=math.sqrt(dot(a,a))
    if size<=1e-14:raise ValueError('Degenerate 3D direction')
    return tuple(v/size for v in a)
def matmul(a,b):return tuple(sum(a[i*4+k]*b[k*4+j] for k in range(4)) for i in range(4) for j in range(4))
def transform_point(matrix,point):
    p=tuple(point)+(1,) if len(point)==3 else tuple(point)
    if len(matrix)!=16 or len(p)!=4:raise ValueError('Require a 4x4 row-major matrix and XYZ/XYZW')
    return tuple(sum(matrix[i*4+j]*p[j] for j in range(4)) for i in range(4))

@dataclass(frozen=True)
class LocalFrame:
    """WGS84 zero-height tangent-plane horizontal metres, source height kept separately.

    East/north are ECEF-derived local coordinates of the zero-height ellipsoid.
    Z is supplied elevation, not an inferred geoid/ellipsoid/vertical datum shift.
    Regional use is limited to 250 km ground distance from the explicit origin.
    """
    lon:float
    lat:float
    def __post_init__(self):
        lon,lat=finite(self.lon),finite(self.lat)
        if not -180<=lon<=180 or not -89<=lat<=89:raise ValueError('LocalFrame origin requires lon [-180,180], lat [-89,89]')
        object.__setattr__(self,'lon',lon);object.__setattr__(self,'lat',lat)
    def horizontal(self,lon,lat):
        lon,lat=finite(lon),finite(lat)
        if not -180<=lon<=180 or not -90<=lat<=90:raise ValueError('Geographic coordinates outside domain')
        lam,phi=map(math.radians,(self.lon,self.lat));l,p=map(math.radians,(lon,lat));a=WGS84.semi_major_axis;e=WGS84.eccentricity_squared
        def ecef(l,p):
            n=a/math.sqrt(1-e*math.sin(p)**2)
            return n*math.cos(p)*math.cos(l),n*math.cos(p)*math.sin(l),n*(1-e)*math.sin(p)
        source=ecef(l,p);origin=ecef(lam,phi);delta=tuple(s-o for s,o in zip(source,origin))
        angular=math.acos(max(-1,min(1,math.sin(phi)*math.sin(p)+math.cos(phi)*math.cos(p)*math.cos(l-lam))))
        if a*angular>250000:raise ValueError('Local terrain must remain within 250 km of its origin')
        return dot(delta,(-math.sin(lam),math.cos(lam),0)),dot(delta,(-math.sin(phi)*math.cos(lam),-math.sin(phi)*math.sin(lam),math.cos(phi)))

@dataclass(frozen=True)
class Camera:
    """Own camera angles in degrees and magnification, orthographic or perspective."""
    elev:float=35
    azim:float=-60
    roll:float=0
    projection:str='persp'
    zoom:float=1
    fov:float=35
    near:float=.1
    far:float=100
    def __post_init__(self):
        for name in ('elev','azim','roll','zoom','fov','near','far'):object.__setattr__(self,name,finite(getattr(self,name)))
        if not -89<=self.elev<=89 or not .1<=self.zoom<=5 or not 5<=self.fov<=100 or not 0<self.near<4<self.far:raise ValueError('Invalid camera elevation/zoom/FOV/clipping planes')
        if self.projection not in ('ortho','persp'):raise ValueError('Camera projection must be ortho or persp')
    def matrix(self,bounds,aspect=1,vertical_exaggeration=1):
        bounds=tuple(finite(v) for v in bounds);aspect=finite(aspect);ex=finite(vertical_exaggeration)
        if len(bounds)!=6 or aspect<=0 or ex<=0 or any(bounds[2*i]>=bounds[2*i+1] for i in range(3)):raise ValueError('Require positive aspect/exaggeration and increasing XYZ limits')
        centers=[(bounds[2*i]+bounds[2*i+1])/2 for i in range(3)]
        size=max(bounds[1]-bounds[0],bounds[3]-bounds[2],(bounds[5]-bounds[4])*ex);s=1.6/size
        model=(s,0,0,-s*centers[0],0,s,0,-s*centers[1],0,0,s*ex,-s*ex*centers[2],0,0,0,1)
        az,el,roll=map(math.radians,(self.azim,self.elev,self.roll));eye=(4*math.cos(el)*math.cos(az),4*math.cos(el)*math.sin(az),4*math.sin(el))
        forward=normalized(tuple(-v for v in eye));right=normalized(cross(forward,(0,0,1)));up=cross(right,forward)
        right,up=tuple(a*math.cos(roll)+b*math.sin(roll) for a,b in zip(right,up)),tuple(-a*math.sin(roll)+b*math.cos(roll) for a,b in zip(right,up))
        view=(*right,-dot(right,eye),*up,-dot(up,eye),*(-v for v in forward),dot(forward,eye),0,0,0,1)
        if self.projection=='persp':
            k=self.zoom/math.tan(math.radians(self.fov)/2);a=-(self.far+self.near)/(self.far-self.near);b=-2*self.far*self.near/(self.far-self.near)
            projection=(k/aspect,0,0,0,0,k,0,0,0,0,a,b,0,0,-1,0)
        else:
            k=self.zoom/1.2;projection=(k/aspect,0,0,0,0,k,0,0,0,0,-2/(self.far-self.near),-(self.far+self.near)/(self.far-self.near),0,0,0,1)
        return matmul(projection,matmul(view,model))

@dataclass(frozen=True)
class Mesh:
    vertices:tuple
    triangles:tuple
    def __post_init__(self):
        vertices=tuple(tuple(finite(v) for v in p) for p in self.vertices);triangles=tuple(tuple(p) for p in self.triangles)
        if not vertices or any(len(p)!=3 for p in vertices) or len(vertices)>50000 or not triangles or len(triangles)>20000:raise ValueError('Mesh requires XYZ vertices and 1..20000 triangles (<=50000 vertices)')
        for face in triangles:
            if len(face)!=3 or any(isinstance(i,bool) or not isinstance(i,int) or not 0<=i<len(vertices) for i in face):raise ValueError('Invalid triangle indices')
        object.__setattr__(self,'vertices',vertices);object.__setattr__(self,'triangles',triangles)
    @property
    def bounds(self):
        used={i for t in self.triangles for i in t};values=[self.vertices[i] for i in used]
        return tuple(v for k in range(3) for v in (min(p[k] for p in values),max(p[k] for p in values)))

def clip_triangle(points):
    """Six homogeneous clip halfspaces before perspective divide; immutable input."""
    polygon=[tuple(finite(v) for v in p) for p in points]
    if len(polygon)!=3 or any(len(p)!=4 for p in polygon):raise ValueError('Three XYZW vertices required')
    for axis,sign in ((0,1),(0,-1),(1,1),(1,-1),(2,1),(2,-1)):
        result=[]
        if not polygon:break
        a=polygon[-1];da=a[3]+sign*a[axis]
        for b in polygon:
            db=b[3]+sign*b[axis]
            if (da>=0)!=(db>=0):
                t=da/(da-db);result.append(tuple(x+t*(y-x) for x,y in zip(a,b)))
            if db>=0:result.append(b)
            a,da=b,db
        polygon=result
    return tuple((polygon[0],polygon[i],polygon[i+1]) for i in range(1,len(polygon)-1) if all(p[3]>1e-12 for p in (polygon[0],polygon[i],polygon[i+1])))

def edge(a,b,x,y):return (b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])
def top_left(a,b):return b[1]<a[1] or b[1]==a[1] and b[0]>a[0]

@dataclass
class RasterResult:
    width:int
    height:int
    rgba:bytes
    depth:object

def rasterize(triangles,width,height,*,accelerate=True,check=None):
    """Flat RGBA triangle colors, top-left coverage and screen-linear NDC depth.

    8M pixels / 64M bounding-box tests maximum. Opaque fragments only; alpha zero
    skips coverage/depth. Coincident depth within 1e-7 keeps the first fragment.
    NumPy vectorizes our same edge equations; it is not a raster/3D backend.
    """
    if any(isinstance(v,bool) or not isinstance(v,int) or v<=0 for v in (width,height)) or width*height>8000000:raise ValueError('3D raster requires positive integer dimensions and <=8M pixels')
    triangles=tuple(triangles)
    for _,color in triangles:
        if len(color)!=4 or any(isinstance(v,bool) or not isinstance(v,int) or not 0<=v<=255 for v in color):raise ValueError('Triangle colors require integer RGBA channels in 0..255')
    if len(triangles)>20000:raise ValueError('Raster input limited to 20000 triangles')
    prepared=[];work=0
    for clip,color in triangles:
        color=tuple(color)
        if len(color)!=4 or any(isinstance(c,bool) or not isinstance(c,int) or not 0<=c<=255 for c in color) or color[3] not in (0,255):raise ValueError('Experimental 3D supports only opaque or fully masked faces')
        if color[3]==0:continue
        for face in clip_triangle(clip):
            p=[((v[0]/v[3]+1)*width/2,(1-v[1]/v[3])*height/2,v[2]/v[3]) for v in face]
            area=edge(p[0],p[1],*p[2][:2])
            if abs(area)<1e-12:continue
            if area<0:p[1],p[2]=p[2],p[1];area=-area
            x0=max(0,math.ceil(min(q[0] for q in p)-.5));x1=min(width,math.floor(max(q[0] for q in p)-.5)+1)
            y0=max(0,math.ceil(min(q[1] for q in p)-.5));y1=min(height,math.floor(max(q[1] for q in p)-.5)+1)
            if x0>=x1 or y0>=y1:continue
            work+=(x1-x0)*(y1-y0)
            if work>64000000:raise ValueError('3D projected work budget exceeded; reduce resolution/mesh density')
            prepared.append((p,area,(x0,y0,x1,y1),color))
    np=None
    if accelerate:
        try:import numpy as np
        except ImportError:pass
    if np is not None:
        depth=np.full((height,width),np.inf,dtype=np.float64);rgba=np.zeros((height,width,4),dtype=np.uint8)
        for p,area,(x0,y0,x1,y1),color in prepared:
            if check:check()
            # Bounded row bands; no full-frame array per triangle.
            for start in range(y0,y1,32):
                end=min(y1,start+32);xx=np.arange(x0,x1,dtype=np.float64)[None,:]+.5;yy=np.arange(start,end,dtype=np.float64)[:,None]+.5
                e0=edge(p[1],p[2],xx,yy);e1=edge(p[2],p[0],xx,yy);e2=edge(p[0],p[1],xx,yy)
                cover=((e0>0)|((e0==0)&top_left(p[1],p[2])))&((e1>0)|((e1==0)&top_left(p[2],p[0])))&((e2>0)|((e2==0)&top_left(p[0],p[1])))
                z=(e0*p[0][2]+e1*p[1][2]+e2*p[2][2])/area;target=depth[start:end,x0:x1];mask=cover&(z<target-1e-7)
                target[mask]=z[mask];rgba[start:end,x0:x1][mask]=color
        return RasterResult(width,height,rgba.tobytes(),depth)
    depth=array('d',[math.inf])*(width*height);rgba=bytearray(width*height*4)
    for p,area,(x0,y0,x1,y1),color in prepared:
        for y in range(y0,y1):
            if check and y%32==0:check()
            for x in range(x0,x1):
                e0=edge(p[1],p[2],x+.5,y+.5);e1=edge(p[2],p[0],x+.5,y+.5);e2=edge(p[0],p[1],x+.5,y+.5)
                if any(e<0 or e==0 and not top_left(a,b) for e,a,b in ((e0,p[1],p[2]),(e1,p[2],p[0]),(e2,p[0],p[1]))):continue
                z=(e0*p[0][2]+e1*p[1][2]+e2*p[2][2])/area;index=y*width+x
                if z<depth[index]-1e-7:depth[index]=z;rgba[index*4:index*4+4]=bytes(color)
    return RasterResult(width,height,bytes(rgba),depth)

class TerrainViewport:
    def __init__(self,box):self.box=tuple(box)
    def inverse(self,x,y):return None

def camera_drag(ax,state,start,end,box,mode='pan',button=1):
    dx,dy=end[0]-start[0],end[1]-start[1];w,h=box[2:]
    if mode=='pan' and button==1:camera=replace(state,azim=state.azim+dx/w*180,elev=max(-89,min(89,state.elev+dy/h*180)))
    else:camera=replace(state,zoom=max(.1,min(5,state.zoom*math.exp(max(-4,min(4,-dy/h*3))))))
    ax.set_camera(camera)

def camera_zoom(ax,factor):ax.set_camera(replace(ax.camera,zoom=max(.1,min(5,ax.camera.zoom*factor))))

def png_bytes(item):
    """PNG embedded by SVG; Pillow encodes pixels, not the 3D geometry."""
    try:from PIL import Image
    except ImportError as exc:raise ImportError('3D SVG export requires azimlib[png] for image encoding') from exc
    from io import BytesIO
    w,h=max(1,round(item.width)),max(1,round(item.height))
    pixels=rasterize(item.triangles,w,h);out=BytesIO()
    with Image.frombytes('RGBA',(w,h),pixels.rgba) as image:image.save(out,format='PNG')
    return out.getvalue()
