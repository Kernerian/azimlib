"""Own hatch geometry clipped by the even-odd rule, including holes."""
import math
from collections import Counter
from .scene import Path,Circle
from .typography import POINT

def add_hatches(scene,paths,style,clip=None):
    pattern=style.get('hatch')
    if not pattern:return
    points=[p for ring in paths for p in ring]
    if not points:return
    x0,y0,x1,y1=min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)
    if clip:x0,y0,x1,y1=max(x0,clip[0]),max(y0,clip[1]),min(x1,clip[0]+clip[2]),min(y1,clip[1]+clip[3])
    edges=[(a,b) for ring in paths for a,b in zip(ring,ring[1:]+ring[:1]) if a!=b]
    runs=[];dots=[];stars=[];spacing=style.get('hatch_spacing',12)*POINT
    dirs={'/':[(1,1)],'\\':[(1,-1)],'|':[(1,0)],'-':[(0,1)],'+':[(1,0),(0,1)],'x':[(1,1),(1,-1)]}
    for char,count in Counter(pattern).items():
        step=spacing/count
        for nx,ny in dirs.get(char,[]):
            length=math.hypot(nx,ny);nx/=length;ny/=length;vx,vy=-ny,nx
            values=[nx*x+ny*y for x,y in ((x0,y0),(x0,y1),(x1,y0),(x1,y1))]
            line_step=step/math.sqrt(2) if char in '/\\x' else step
            first,last=math.ceil(min(values)/line_step),math.floor(max(values)/line_step)
            if last-first>2000:raise ValueError('Hatch too dense; increase spacing')
            for index in range(first,last+1):
                c=index*line_step;hits=[]
                for a,b in edges:
                    ua,ub=nx*a[0]+ny*a[1],nx*b[0]+ny*b[1]
                    if (ua<=c<ub) or (ub<=c<ua):
                        t=(c-ua)/(ub-ua);hits.append(vx*(a[0]+t*(b[0]-a[0]))+vy*(a[1]+t*(b[1]-a[1])))
                hits.sort()
                runs.extend([[(nx*c+vx*a,ny*c+vy*a),(nx*c+vx*b,ny*c+vy*b)] for a,b in zip(hits[::2],hits[1::2])])
        if char in '.oO*':
            if (x1-x0)*(y1-y0)/step**2>10000:raise ValueError('Hatch too dense; increase spacing')
            for j in range(math.ceil(y0/step),math.floor(y1/step)+1):
                for i in range(math.ceil(x0/step),math.floor(x1/step)+1):
                    x,y=(i+.5*(j%2))*step,j*step
                    inside=sum((a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0] for a,b in edges)%2
                    r={'.':.1,'o':.2,'O':.35,'*':1/3}[char]*step
                    if not inside or min(_distance((x,y),a,b) for a,b in edges)<r*r:continue
                    if char=='.':dots.append((x,y,r))
                    elif char=='*':
                        stars.append([(x+(r if k%2==0 else r*.42)*math.cos(k*math.pi/5-math.pi/2),
                                       y+(r if k%2==0 else r*.42)*math.sin(k*math.pi/5-math.pi/2)) for k in range(10)])
                    else:runs.append([(x+r*math.cos(k*math.pi/8),y+r*math.sin(k*math.pi/8)) for k in range(17)])
    color=style.get('hatch_color',style.get('edgecolor',style.get('color','black')))
    if color in (None,'none'):color='black'
    if runs:scene.add(Path(runs,False,dict(stroke=color,stroke_width=style.get('hatch_linewidth',1)*POINT,opacity=style.get('alpha',1),linecap='butt',linejoin='round'),clip))
    for x,y,r in dots:scene.add(Circle(x,y,r,dict(fill=color,opacity=style.get('alpha',1)),clip))
    if stars:scene.add(Path(stars,True,dict(fill=color,opacity=style.get('alpha',1)),clip))

def _distance(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy))) if dx or dy else 0
    return (p[0]-a[0]-t*dx)**2+(p[1]-a[1]-t*dy)**2
