"""Own periodic line patterns; tiles carry explicit provenance."""
from dataclasses import dataclass
import math
@dataclass(frozen=True)
class Provenance:
    source: str
    license: str
    copyright: str
    attribution: str=''
    sha256: str=''
    license_text: str=''
    def __post_init__(self):
        if any(not isinstance(v,str) for v in (self.attribution,self.sha256,self.license_text)):raise TypeError('Provenance notices and hash must be strings')
        if any(not isinstance(v,str) or not v.strip() for v in (self.source,self.license,self.copyright)):
            raise ValueError('Require source, license and copyright (or explicit public-domain statement)')
        if self.sha256 and (len(self.sha256)!=64 or any(c not in '0123456789abcdef' for c in self.sha256)):raise ValueError('Invalid SHA-256')

@dataclass(frozen=True)
class HatchPattern:
    paths: tuple
    provenance: Provenance
    def __post_init__(self):
        paths=tuple(tuple(tuple(float(v) for v in p) for p in part) for part in self.paths)
        if not isinstance(self.provenance,Provenance):raise TypeError('Require explicit Provenance')
        if not paths or sum(len(p) for p in paths)>1024 or any(len(p)<2 for p in paths):raise ValueError('Require 1..1024 tile vertices, at least two per path')
        if any(len(p)!=2 or any(not math.isfinite(v) or not 0<=v<=1 for v in p) for part in paths for p in part):raise ValueError('Tile coordinates must lie in [0,1]')
        object.__setattr__(self,'paths',paths)

def register_notice(scene,provenance):
    from dataclasses import asdict
    if provenance is not None:
        notice=asdict(provenance)
        if notice not in scene._material_notices:scene._material_notices.append(notice)

def add_pattern(scene,rings,style,clip):
    from .scene import Path
    from .typography import POINT
    from .line_labels import clip_segment
    from .render_map import _inside_ring
    pattern=style['hatch'];register_notice(scene,pattern.provenance);step=style.get('hatch_spacing',12)*POINT
    points=[p for ring in rings for p in ring]
    if not points:return
    x0,x1=min(p[0] for p in points),max(p[0] for p in points);y0,y1=min(p[1] for p in points),max(p[1] for p in points)
    if clip:x0=max(x0,clip[0]);x1=min(x1,clip[0]+clip[2]);y0=max(y0,clip[1]);y1=min(y1,clip[1]+clip[3])
    if x0>=x1 or y0>=y1:return
    sx,sy=(x1-x0)/step,(y1-y0)/step
    if not math.isfinite(sx*sy) or sx*sy>20000:raise ValueError('Custom hatch too dense; increase spacing')
    nx,ny=math.ceil(sx)+2,math.ceil(sy)+2
    if nx*ny*sum(len(p)-1 for p in pattern.paths)>20000:raise ValueError('Custom hatch too dense; increase spacing')
    edges=[(a,b) for ring in rings for a,b in zip(ring,ring[1:]+ring[:1])];out=[]
    for i in range(math.floor(x0/step),math.ceil(x1/step)):
        for j in range(math.floor(y0/step),math.ceil(y1/step)):
            for part in pattern.paths:
                tile=[((i+p[0])*step,(j+p[1])*step) for p in part]
                for a,b in zip(tile,tile[1:]):
                    clipped=clip_segment(a,b,(x0,y0,x1-x0,y1-y0))
                    if clipped is None:continue
                    a,b=clipped;dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
                    if not den:continue
                    hits=[0.,1.]
                    for u,v in edges:
                        # Generic line intersection parameters, including holes.
                        ex,ey=v[0]-u[0],v[1]-u[1];det=dx*ey-dy*ex
                        if abs(det)<1e-12:continue
                        t=((u[0]-a[0])*ey-(u[1]-a[1])*ex)/det;q=((u[0]-a[0])*dy-(u[1]-a[1])*dx)/det
                        if 0<t<1 and 0<=q<=1:hits.append(t)
                    hits=sorted(set(hits))
                    for lo,hi in zip(hits,hits[1:]):
                        p=(a[0]+dx*(lo+hi)/2,a[1]+dy*(lo+hi)/2)
                        if sum(_inside_ring(p,ring if ring[0]==ring[-1] else [*ring,ring[0]]) for ring in rings)%2:
                            out.append([(a[0]+dx*lo,a[1]+dy*lo),(a[0]+dx*hi,a[1]+dy*hi)])
    color=style.get('hatch_color',style.get('edgecolor',style.get('color','black'))) or 'black'
    if out:scene.add(Path(out,False,dict(stroke=color,stroke_width=style.get('hatch_linewidth',1)*POINT,opacity=style.get('alpha',1),linecap='butt'),clip))
