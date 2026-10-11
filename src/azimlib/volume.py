"""Original regular metric nodal fields and hash-checked streaming AZV bricks.

Arrays are Z/Y/X[/component], world coordinates are X/Y/Z metres. Missing
nodes are NaN; no projection, vertical datum or geographic axis is inferred.
"""
from dataclasses import dataclass
from functools import cached_property
from collections import OrderedDict
from array import array
from pathlib import Path
import hashlib
import json
import math
import os
import struct
import tempfile
from .terrain3d import finite,length_unit,LocalFrame


@dataclass(frozen=True)
class VolumeBudget:
    max_dense_bytes:int=32*1024**2
    max_cache_bytes:int=16*1024**2
    max_file_bytes:int=20_000_000_000
    max_samples:int=64_000_000
    max_steps:int=512
    max_pixels:int=1_000_000
    def __post_init__(self):
        for name,maximum in (('max_dense_bytes',128*1024**2),('max_cache_bytes',128*1024**2),('max_file_bytes',20_000_000_000),('max_samples',128_000_000),('max_steps',512),('max_pixels',1_000_000)):
            v=getattr(self,name)
            if isinstance(v,bool) or not isinstance(v,int) or not 0<v<=maximum:raise ValueError('Volume budget requires bounded positive integers')


def _shape(shape):
    shape=tuple(shape)
    if len(shape)!=3 or any(isinstance(n,bool) or not isinstance(n,int) or not 2<=n<=65536 for n in shape):raise ValueError('Volume shape requires Z,Y,X dimensions in 2..65536')
    return shape


def _packed(values):
    a=array('f',values)
    if os.sys.byteorder!='little':a.byteswap()
    return a.tobytes()


@dataclass(frozen=True)
class VolumeField:
    shape:tuple
    values:bytes|None
    origin:tuple=(0.,0.,0.)
    spacing:tuple=(1.,1.,1.)
    components:int=1
    value_unit:str='1'
    frame:LocalFrame|None=None
    store:object=None
    budget:VolumeBudget=VolumeBudget()
    def __post_init__(self):
        object.__setattr__(self,'shape',_shape(self.shape))
        for name in ('origin','spacing'):
            v=tuple(finite(x) for x in getattr(self,name))
            if len(v)!=3 or name=='spacing' and any(x<=0 for x in v):raise ValueError('Volume origin/positive spacing require three finite metric values')
            object.__setattr__(self,name,v)
        if not isinstance(self.components,int) or self.components not in (1,3) or isinstance(self.components,bool):raise ValueError('Volume fields have one scalar or three vector components')
        if not isinstance(self.budget,VolumeBudget):raise TypeError('Require VolumeBudget')
        if not isinstance(self.value_unit,str) or not self.value_unit.strip() or len(self.value_unit)>128:raise ValueError('Volume value_unit must be explicit nonempty text')
        if self.frame is not None and not isinstance(self.frame,LocalFrame):raise TypeError('Volume frame is an explicit terrain LocalFrame or None for Cartesian metres')
        size=math.prod(self.shape)*self.components*4
        if self.values is not None:
            if self.store is not None or not isinstance(self.values,bytes) or len(self.values)!=size or size>self.budget.max_dense_bytes:raise ValueError('Dense volume bytes/shape or memory budget mismatch')
            if any(math.isinf(v[0]) for v in struct.iter_unpack('<f',self.values)):raise ValueError('Volume samples must be finite or NaN')
        elif not isinstance(self.store,BrickStore):raise ValueError('A volume requires dense bytes or a verified AZV brick store')
        elif self.store.shape!=self.shape or self.store.components!=self.components:raise ValueError('Volume metadata must match its verified brick layout')
    @classmethod
    def from_array(cls,values,*,origin=(0,0,0),spacing=(1,1,1),unit='m',value_unit='1',frame=None,nodata=None,components=1,budget=None):
        from .scientific import scalar
        budget=budget or VolumeBudget();data=array('f');ny=nx=None;nz=0
        if not isinstance(components,int) or components not in (1,3) or isinstance(components,bool):raise ValueError('Require one or three components')
        for plane in values:
            rows=0
            for row in plane:
                cols=0
                for node in row:
                    if (len(data)+components)*4>budget.max_dense_bytes:raise ValueError('Dense volume memory budget exceeded before accumulation')
                    parts=(node,) if components==1 else (None,)*3 if node is None else tuple(node)
                    if len(parts)!=components:raise ValueError('Vector nodes require three components')
                    for part in parts:
                        v=scalar(part)
                        if v is None or nodata is not None and v==nodata:v=math.nan
                        if math.isfinite(v) and abs(v)>3.4028234663852886e38:raise ValueError('Volume float32 range exceeded')
                        data.append(v)
                    cols+=1
                if nx is None:nx=cols
                if cols!=nx:raise ValueError('Volume arrays must be rectangular Z/Y/X')
                rows+=1
            if ny is None:ny=rows
            if rows!=ny:raise ValueError('Volume arrays must be rectangular Z/Y/X')
            nz+=1
        shape=_shape((nz,ny or 0,nx or 0));scale=length_unit(unit).to_si
        if os.sys.byteorder!='little':data.byteswap()
        return cls(shape,data.tobytes(),tuple(finite(v)*scale for v in origin),tuple(finite(v)*scale for v in spacing),components,value_unit,frame,budget=budget)
    @property
    def bounds(self):return tuple(v for k,n in enumerate(reversed(self.shape)) for v in (self.origin[k],self.origin[k]+self.spacing[k]*(n-1)))
    def sampler(self):return VolumeSampler(self)
    def sample(self,x,y,z,*,method='linear'):return self.sampler().sample((x,y,z),method)
    @cached_property
    def summary(self):
        if self.store is not None:return self.store.summary
        low=[math.inf]*self.components;high=[-math.inf]*self.components;count=0
        for node in struct.iter_unpack('<'+'f'*self.components,self.values):
            if all(math.isfinite(v) for v in node):
                count+=1
                for k,v in enumerate(node):low[k]=min(low[k],v);high[k]=max(high[k],v)
        return dict(valid_nodes=count,minimum=tuple(None if v==math.inf else v for v in low),maximum=tuple(None if v==-math.inf else v for v in high))
    def select(self,bounds):
        """Copy a bounded nodal ROI, including interpolation support at its edges."""
        bounds=tuple(finite(v) for v in bounds)
        if len(bounds)!=6 or any(bounds[2*k]>=bounds[2*k+1] for k in range(3)):raise ValueError('Selection requires increasing XYZ endpoints')
        ranges=[]
        for k,n in enumerate(reversed(self.shape)):
            lo=max(0,math.floor((bounds[2*k]-self.origin[k])/self.spacing[k]));hi=min(n-1,math.ceil((bounds[2*k+1]-self.origin[k])/self.spacing[k]))
            if lo>=hi:raise ValueError('Selection must intersect at least one volume cell on every axis')
            ranges.append((lo,hi+1))
        shape=tuple(b-a for a,b in reversed(ranges))
        if math.prod(shape)*self.components*4>self.budget.max_dense_bytes:raise ValueError('Selected volume exceeds dense memory budget; select a smaller region')
        s=self.sampler();data=array('f')
        for z in range(*ranges[2]):
            for y in range(*ranges[1]):
                for x in range(*ranges[0]):data.extend(s.node(x,y,z))
        return VolumeField(shape,_packed(data),tuple(self.origin[k]+ranges[k][0]*self.spacing[k] for k in range(3)),self.spacing,self.components,self.value_unit,self.frame,budget=self.budget)
    def component(self,component):
        if self.components!=3:raise ValueError('Component extraction requires a vector field')
        if component not in (0,1,2,'magnitude') or isinstance(component,bool):raise ValueError('Component must be 0,1,2 or magnitude')
        if math.prod(self.shape)*4>self.budget.max_dense_bytes:raise ValueError('Select a region before dense component extraction')
        s=self.sampler();data=array('f');nz,ny,nx=self.shape
        for z in range(nz):
            for y in range(ny):
                for x in range(nx):
                    p=s.node(x,y,z);data.append(math.sqrt(sum(v*v for v in p)) if component=='magnitude' else p[component])
        return VolumeField(self.shape,_packed(data),self.origin,self.spacing,1,self.value_unit,self.frame,budget=self.budget)
    def iter_bricks(self,*,brick_size=16):
        if isinstance(brick_size,bool) or not isinstance(brick_size,int) or not 2<=brick_size<=64:raise ValueError('Brick size must be 2..64')
        s=self.sampler();nz,ny,nx=self.shape;b=brick_size
        if b**3*self.components*4>self.budget.max_cache_bytes:raise ValueError('One brick exceeds cache budget')
        for bz in range(math.ceil(nz/b)):
            for by in range(math.ceil(ny/b)):
                for bx in range(math.ceil(nx/b)):
                    data=array('f')
                    for z in range(bz*b,(bz+1)*b):
                        for y in range(by*b,(by+1)*b):
                            for x in range(bx*b,(bx+1)*b):data.extend(s.node(x,y,z) if x<nx and y<ny and z<nz else (math.nan,)*self.components)
                    yield (bx,by,bz),_packed(data)


class VolumeSampler:
    def __init__(self,field):self.field=field;self.cache=OrderedDict();self.cache_bytes=0;self.bricks_read=0
    def node(self,x,y,z):
        f=self.field;nz,ny,nx=f.shape
        if not 0<=x<nx or not 0<=y<ny or not 0<=z<nz:return (math.nan,)*f.components
        if f.values is not None:data=f.values;index=(z*ny+y)*nx+x
        else:
            b=f.store.brick_size;key=(x//b,y//b,z//b)
            if key in self.cache:data=self.cache.pop(key);self.cache[key]=data
            else:
                size=b**3*f.components*4
                while self.cache and self.cache_bytes+size>f.budget.max_cache_bytes:_,old=self.cache.popitem(last=False);self.cache_bytes-=len(old)
                if size>f.budget.max_cache_bytes:raise ValueError('Volume brick exceeds cache budget')
                data=f.store.brick(key);self.bricks_read+=1;self.cache[key]=data;self.cache_bytes+=len(data)
            index=((z%b)*b+y%b)*b+x%b
        return struct.unpack_from('<'+'f'*f.components,data,index*f.components*4)
    def sample(self,p,method='linear'):
        p=tuple(p)
        if len(p)!=3:raise ValueError('Volume samples require XYZ')
        f=self.field;q=tuple((finite(v)-a)/s for v,a,s in zip(p,f.origin,f.spacing))
        if any(v<0 or v>n-1 for v,n in zip(q,reversed(f.shape))):return None
        if method=='nearest':result=self.node(*(math.floor(v+.5) for v in q))
        elif method=='linear':
            base=tuple(min(n-2,math.floor(v)) for v,n in zip(q,reversed(f.shape)));t=tuple(v-i for v,i in zip(q,base));result=[0.]*f.components
            for dz in (0,1):
                for dy in (0,1):
                    for dx in (0,1):
                        weight=math.prod(t[k] if bit else 1-t[k] for k,bit in enumerate((dx,dy,dz)))
                        if not weight:continue
                        node=self.node(base[0]+dx,base[1]+dy,base[2]+dz)
                        if not all(math.isfinite(v) for v in node):return None
                        for k,v in enumerate(node):result[k]+=weight*v
        else:raise ValueError('Volume sampling must be nearest or linear')
        if not all(math.isfinite(v) for v in result):return None
        return result[0] if f.components==1 else tuple(result)


_MAGIC=b'AZIMVOL1\n'


@dataclass(frozen=True)
class BrickStore:
    path:Path
    shape:tuple
    components:int
    brick_size:int
    header_bytes:int
    signature:tuple
    sha256:str
    summary:dict
    def brick(self,index):
        stat=self.path.stat()
        if (stat.st_size,stat.st_mtime_ns)!=self.signature:raise ValueError('Volume source changed after verification')
        b=self.brick_size;nx,ny,nz=(math.ceil(n/b) for n in reversed(self.shape));x,y,z=index
        if not 0<=x<nx or not 0<=y<ny or not 0<=z<nz:raise ValueError('Brick index outside volume')
        size=b**3*self.components*4;offset=self.header_bytes+((z*ny+y)*nx+x)*(size+32)
        with self.path.open('rb') as stream:stream.seek(offset);digest=stream.read(32);data=stream.read(size)
        if len(data)!=size or hashlib.sha256(data).digest()!=digest:raise ValueError('Corrupt or truncated AZV brick')
        return data


def write_volume(path,field=None,*,shape=None,bricks=None,brick_size=16,origin=(0,0,0),spacing=(1,1,1),components=1,value_unit='1',frame=None,budget=None):
    """Write atomic AZV1; a streaming producer yields ordered (XYZ brick, LE f32)."""
    budget=budget or (field.budget if field is not None else VolumeBudget())
    if isinstance(brick_size,bool) or not isinstance(brick_size,int) or not 2<=brick_size<=64:raise ValueError('Brick size must be 2..64')
    if field is not None:
        if not isinstance(field,VolumeField) or bricks is not None or shape is not None:raise ValueError('Provide either a field or shape plus streaming bricks')
        shape,origin,spacing,components,value_unit,frame=field.shape,field.origin,field.spacing,field.components,field.value_unit,field.frame
        bricks=field.iter_bricks(brick_size=brick_size)
    shape=_shape(shape)
    if not isinstance(components,int) or components not in (1,3) or isinstance(components,bool):raise ValueError('AZV requires one or three components')
    # Validate metadata through a tiny field with the same metric contract.
    VolumeField((2,2,2),_packed([0.]*(8*components)),origin,spacing,components,value_unit,frame,budget=budget)
    meta=dict(shape=shape,origin=origin,spacing=spacing,components=components,value_unit=value_unit,frame=None if frame is None else (frame.lon,frame.lat),brick_size=brick_size)
    header=json.dumps(meta,sort_keys=True,separators=(',',':')).encode();prefix=_MAGIC+struct.pack('<I',len(header))+header
    b=brick_size;size=b**3*components*4;count=math.prod(math.ceil(n/b) for n in shape)
    if size>budget.max_cache_bytes or len(prefix)+count*(size+32)>budget.max_file_bytes:raise ValueError('AZV file or brick budget exceeded before writing')
    path=Path(path)
    if path.exists():raise FileExistsError('Volume destination already exists')
    path.parent.mkdir(parents=True,exist_ok=True);temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.azv-',delete=False) as output:
            temporary=Path(output.name);output.write(prefix);source=iter(bricks)
            nz,ny,nx=(math.ceil(n/b) for n in shape)
            for z in range(nz):
                for y in range(ny):
                    for x in range(nx):
                        try:index,data=next(source)
                        except StopIteration:raise ValueError('Missing AZV bricks') from None
                        if tuple(index)!=(x,y,z) or not isinstance(data,bytes) or len(data)!=size:raise ValueError('AZV bricks require exact ordered XYZ indices and immutable padded float32 bytes')
                        if any(math.isinf(v[0]) for v in struct.iter_unpack('<f',data)):raise ValueError('AZV values must be finite or NaN')
                        output.write(hashlib.sha256(data).digest());output.write(data)
            if next(source,None) is not None:raise ValueError('Extra AZV bricks')
        if path.exists():raise FileExistsError('Volume destination appeared during writing')
        os.replace(temporary,path);temporary=None
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
    return path


def read_volume(path,*,budget=None,sha256=None):
    """Verify every AZV brick in bounded memory; retain only its file descriptor."""
    budget=budget or VolumeBudget();path=Path(path).resolve();stat=path.stat()
    if stat.st_size>budget.max_file_bytes:raise ValueError('AZV file exceeds storage budget')
    with path.open('rb') as stream:
        if stream.read(len(_MAGIC))!=_MAGIC:raise ValueError('Not an AZV1 volume')
        raw=stream.read(4)
        if len(raw)!=4:raise ValueError('Truncated AZV header')
        size=struct.unpack('<I',raw)[0]
        if not 0<size<=65536:raise ValueError('AZV header budget exceeded')
        raw=stream.read(size)
        if len(raw)!=size:raise ValueError('Truncated AZV metadata')
        meta=json.loads(raw);header_bytes=stream.tell()
        if set(meta)!={'shape','origin','spacing','components','value_unit','frame','brick_size'}:raise ValueError('Unknown AZV metadata schema')
        shape=_shape(meta['shape']);c=meta['components'];b=meta['brick_size'];frame=None if meta['frame'] is None else LocalFrame(*meta['frame'])
        if not isinstance(c,int) or c not in (1,3) or isinstance(c,bool):raise ValueError('AZV requires one or three components')
        VolumeField((2,2,2),_packed([0.]*(8*c)),meta['origin'],meta['spacing'],c,meta['value_unit'],frame,budget=budget)
        if isinstance(b,bool) or not isinstance(b,int) or not 2<=b<=64:raise ValueError('Invalid AZV brick size')
        block=b**3*c*4
        if block>budget.max_cache_bytes:raise ValueError('AZV brick exceeds memory budget')
        nx,ny,nz=(math.ceil(n/b) for n in reversed(shape));count=nx*ny*nz
        if header_bytes+count*(32+block)!=stat.st_size:raise ValueError('AZV length, missing bricks or trailing data mismatch')
        digest=hashlib.sha256(_MAGIC+struct.pack('<I',size)+raw);low=[math.inf]*c;high=[-math.inf]*c;valid=0
        for index in range(count):
            checksum=stream.read(32);data=stream.read(block)
            if hashlib.sha256(data).digest()!=checksum:raise ValueError('Corrupt AZV brick')
            digest.update(checksum);digest.update(data);bx=index%nx;by=index//nx%ny;bz=index//(nx*ny)
            for i,node in enumerate(struct.iter_unpack('<'+'f'*c,data)):
                if any(math.isinf(v) for v in node):raise ValueError('Invalid infinite AZV sample')
                if bx*b+i%b>=shape[2] or by*b+i//b%b>=shape[1] or bz*b+i//(b*b)>=shape[0]:continue
                if all(math.isfinite(v) for v in node):
                    valid+=1
                    for k,v in enumerate(node):low[k]=min(low[k],v);high[k]=max(high[k],v)
        identity=digest.hexdigest()
    if sha256 is not None and identity!=sha256:raise ValueError('AZV SHA-256 does not match expected source')
    end=path.stat()
    if (end.st_size,end.st_mtime_ns)!=(stat.st_size,stat.st_mtime_ns):raise ValueError('AZV changed during verification')
    summary=dict(valid_nodes=valid,minimum=tuple(None if x==math.inf else x for x in low),maximum=tuple(None if x==-math.inf else x for x in high))
    store=BrickStore(path,shape,c,b,header_bytes,(stat.st_size,stat.st_mtime_ns),identity,summary)
    return VolumeField(shape,None,tuple(meta['origin']),tuple(meta['spacing']),c,meta['value_unit'],frame,store,budget)
