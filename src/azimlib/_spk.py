"""Owned, bounded DAF/SPK type 2/3 evaluator from NAIF format specifications.

No SPICE code is incorporated. Kernels are external numerical data, supplied
explicitly with a SHA-256 and provenance; never downloaded or redistributed.
States are geometric ICRF/J2000 barycentric metres and metres/second at TDB
seconds from J2000. Light time, aberration and Earth orientation are separate.
"""
from dataclasses import dataclass
import hashlib
import math
from pathlib import Path
import re
import struct


@dataclass(frozen=True)
class State:
    position_m: tuple
    velocity_m_s: tuple
    tdb_seconds: float
    frame: str = 'ICRF/J2000'
    center: int = 0


@dataclass(frozen=True)
class Segment:
    start: float
    end: float
    target: int
    center: int
    frame: int
    kind: int
    first: int
    last: int
    initial: float
    interval: float
    record_size: int
    records: int


def chebyshev(coefficients, x):
    """Polynomial and derivative using the defining Chebyshev recurrence."""
    p, derivative = coefficients[0], 0.
    a, b, da, db = 1., x, 0., 1.
    for i, coefficient in enumerate(coefficients[1:], 1):
        p += coefficient*b; derivative += coefficient*db
        a, b, da, db = b, 2*x*b-a, db, 2*b+2*x*db-da
    return p, derivative


class SpkKernel:
    MAX_BYTES = 64*1024**2
    def __init__(self, path, *, sha256, source):
        if not isinstance(sha256,str) or not re.fullmatch('[0-9a-f]{64}',sha256):
            raise ValueError('Kernel requires a lowercase SHA-256')
        if not isinstance(source,str) or not source.strip():raise ValueError('Kernel provenance required')
        with Path(path).open('rb') as stream:
            data=stream.read(self.MAX_BYTES+1)
        if len(data)>self.MAX_BYTES:raise ValueError('SPK exceeds 64 MiB input bound')
        if hashlib.sha256(data).hexdigest()!=sha256:raise ValueError('SPK SHA-256 mismatch')
        if len(data)<3072 or len(data)%1024 or data[:8]!=b'DAF/SPK ':raise ValueError('Unsupported DAF/SPK header')
        self.endian={b'LTL-IEEE':'<',b'BIG-IEEE':'>'}.get(data[88:96])
        if self.endian is None:raise ValueError('SPK requires IEEE double representation')
        self._data=data;self.sha256=sha256;self.source=source
        nd,ni=struct.unpack_from(self.endian+'2i',data,8)
        if (nd,ni)!=(2,6):raise ValueError('SPK descriptor must have ND=2, NI=6')
        forward,backward,free=struct.unpack_from(self.endian+'3i',data,76)
        if not 1<=free<=len(data)//8+1:raise ValueError('Invalid SPK free address')
        seen=set();segments=[];record=forward;previous=0
        while record:
            if record in seen or len(seen)>=256 or not 2<=record<=len(data)//1024:
                raise ValueError('Invalid/cyclic SPK summary chain')
            seen.add(record);offset=(record-1)*1024
            nxt,prev,count=struct.unpack_from(self.endian+'3d',data,offset)
            if not all(math.isfinite(v) and v==int(v) for v in (nxt,prev,count)) or prev!=previous or not 0<=count<=25:
                raise ValueError('Invalid SPK summary control')
            for i in range(int(count)):
                start,end,*ints=struct.unpack_from(self.endian+'2d6i',data,offset+24+i*40)
                target,center,frame,kind,first,last=ints
                if not math.isfinite(start) or not math.isfinite(end) or start>end or not 129<=first<=last<free:
                    raise ValueError('Invalid SPK descriptor range')
                if frame!=1 or kind not in (2,3):raise ValueError('Only J2000 SPK type 2/3 is supported')
                if last-first<5:raise ValueError('Truncated SPK segment')
                initial,interval,size,n=struct.unpack_from(self.endian+'4d',data,(last-4)*8)
                if not all(math.isfinite(v) for v in (initial,interval,size,n)) or interval<=0 or size!=int(size) or n!=int(n):
                    raise ValueError('Invalid SPK segment directory')
                components=3 if kind==2 else 6;size=int(size);n=int(n)
                if not 1<=n<=1000000 or not components+2<=size<=components*65+2 or (size-2)%components or n*size+4!=last-first+1:
                    raise ValueError('Invalid SPK polynomial layout')
                if start<initial-1e-6 or end>initial+n*interval+1e-6:
                    raise ValueError('SPK summary exceeds record coverage')
                segments.append(Segment(start,end,target,center,frame,kind,first,last,initial,interval,size,n))
                if len(segments)>4096:raise ValueError('SPK segment count bound exceeded')
            previous=record;record=int(nxt)
        if previous!=backward or not segments:raise ValueError('Invalid final SPK summary')
        self.segments=tuple(segments)

    def _relative(self, segment, epoch):
        index=min(segment.records-1,math.floor((epoch-segment.initial)/segment.interval))
        if not 0<=index<segment.records:raise ValueError('Epoch outside SPK records')
        offset=(segment.first-1+index*segment.record_size)*8
        values=struct.unpack_from(self.endian+str(segment.record_size)+'d',self._data,offset)
        midpoint,radius=values[:2]
        if not all(math.isfinite(v) for v in values) or radius<=0 or abs(epoch-midpoint)>radius+1e-6:
            raise ValueError('Invalid SPK polynomial record')
        x=(epoch-midpoint)/radius;components=3 if segment.kind==2 else 6
        length=(segment.record_size-2)//components
        evaluated=[chebyshev(values[2+i*length:2+(i+1)*length],x) for i in range(components)]
        position=tuple(p*1000 for p,d in evaluated[:3])
        velocity=tuple((d/radius if segment.kind==2 else evaluated[i+3][0])*1000 for i,(p,d) in enumerate(evaluated[:3]))
        if not all(math.isfinite(v) for v in (*position,*velocity)):raise ValueError('Nonfinite SPK evaluation')
        return position,velocity

    def state(self, target, tdb_seconds):
        if isinstance(target,bool) or not isinstance(target,int):raise ValueError('NAIF target must be an integer')
        if isinstance(tdb_seconds,bool) or not isinstance(tdb_seconds,(int,float)) or not math.isfinite(tdb_seconds):
            raise ValueError('Epoch requires finite TDB seconds since J2000')
        def solve(body,chain):
            if body==0:return (0.,0.,0.),(0.,0.,0.)
            if body in chain or len(chain)>=16:raise ValueError('Cyclic/overlong SPK center graph')
            segment=next((s for s in reversed(self.segments) if s.target==body and s.start<=tdb_seconds<=s.end),None)
            if segment is None:raise ValueError('Target/epoch outside SPK coverage')
            position,velocity=self._relative(segment,tdb_seconds)
            base,basevelocity=solve(segment.center,(*chain,body))
            return tuple(a+b for a,b in zip(position,base)),tuple(a+b for a,b in zip(velocity,basevelocity))
        p,v=solve(target,())
        return State(p,v,float(tdb_seconds))
