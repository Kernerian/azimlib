"""Validated scalar grids, own marching squares and terrain illumination."""
import math

def contour_levels(valid,levels):
    """Validate explicit levels; deduplicate float rounding in automatic levels.

    A constant field still owns an editable empty ContourSet. Automatic levels
    are evenly spaced (our existing policy), not Matplotlib's MaxNLocator.
    """
    if isinstance(levels,int):
        if levels<1:raise ValueError('levels must be positive')
        lo,hi=min(valid),max(valid)
        span=hi-lo
        if lo==hi:levels=(lo,)
        else:
            values=[]
            for i in range(1,levels+1):
                # Preserve existing arithmetic unless subtraction overflows.
                value=lo+span*i/(levels+1)
                if not math.isfinite(value):
                    fraction=i/(levels+1)
                    value=lo*(1-fraction)+hi*fraction
                if not values or value!=values[-1]:values.append(value)
            levels=values
    levels=tuple(float(v) for v in levels)
    if not levels or any(not math.isfinite(v) for v in levels) or any(a>=b for a,b in zip(levels,levels[1:])):
        raise ValueError('Levels must be finite and increasing')
    return levels

def grid_data(x,y,z):
    x,y=tuple(float(v) for v in x),tuple(float(v) for v in y)
    from .scientific import scalar
    values=tuple(tuple(scalar(v) for v in row) for row in z)
    if len(x)<2 or len(y)<2 or len(values)!=len(y) or any(len(row)!=len(x) for row in values):raise ValueError('Z must have shape (len(y), len(x)); at least 2 by 2')
    if any(not math.isfinite(v) for v in x+y) or any(a>=b for a,b in zip(x,x[1:])) or any(a>=b for a,b in zip(y,y[1:])):raise ValueError('x/y must be finite and strictly increasing')
    if y[0]<-90 or y[-1]>90:raise ValueError('Latitude must be in [-90,90]')
    return x,y,values

def contour_segments(x,y,z,level):
    segments=[]
    for j in range(len(y)-1):
        for i in range(len(x)-1):
            points=((x[i],y[j]),(x[i+1],y[j]),(x[i+1],y[j+1]),(x[i],y[j+1]))
            values=(z[j][i],z[j][i+1],z[j+1][i+1],z[j+1][i])
            if any(v is None for v in values):continue
            hits=[]
            for k in range(4):
                a,b=values[k],values[(k+1)%4]
                if (a<=level<b) or (b<=level<a):
                    t=(level-a)/(b-a);p,q=points[k],points[(k+1)%4]
                    hits.append((k,(p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1]))))
            if len(hits)==2:segments.append((hits[0][1],hits[1][1]))
            elif len(hits)==4:
                # Bilinear asymptotic decider resolves saddle connectivity.
                determinant=(values[0]-level)*(values[2]-level)-(values[1]-level)*(values[3]-level)
                pairs=((0,1),(2,3)) if determinant>=0 else ((0,3),(1,2))
                segments.extend((hits[a][1],hits[b][1]) for a,b in pairs)
    return _stitch(segments)

def _stitch(segments):
    nodes={};edges={}
    for i,(a,b) in enumerate(segments):
        aa,bb=tuple(round(v,12) for v in a),tuple(round(v,12) for v in b)
        if aa==bb:continue
        nodes.setdefault(aa,[]).append(i);nodes.setdefault(bb,[]).append(i);edges[i]=(aa,bb)
    used=set();lines=[]
    starts=sorted(nodes,key=lambda p:len(nodes[p])!=1)
    for start in starts:
        for edge in nodes[start]:
            if edge in used:continue
            line=[start];point=start
            while edge not in used:
                used.add(edge);a,b=edges[edge];point=b if point==a else a;line.append(point)
                nxt=next((i for i in nodes[point] if i not in used),None)
                if nxt is None:break
                edge=nxt
            if len(line)>1:lines.append(line)
    return lines

def hillshade(z,*,dx=1,dy=1,azdeg=315,altdeg=45,vert_exag=1):
    """Lambertian illumination; dx/dy and elevation use consistent units."""
    from .scientific import scalar
    z=[[scalar(v) for v in row] for row in z]
    if len(z)<2 or len(z[0])<2 or any(len(row)!=len(z[0]) for row in z):raise ValueError('Rectangular terrain grid required')
    if dx<=0 or dy<=0 or not all(math.isfinite(v) for v in (dx,dy,azdeg,altdeg,vert_exag)):raise ValueError('Invalid terrain spacing/light')
    if not 0<=altdeg<=90:raise ValueError('altdeg must be in [0,90]')
    az,alt=math.radians(azdeg),math.radians(altdeg)
    light=(math.sin(az)*math.cos(alt),math.cos(az)*math.cos(alt),math.sin(alt));out=[]
    for j,row in enumerate(z):
        result=[]
        for i,value in enumerate(row):
            left,right=max(0,i-1),min(len(row)-1,i+1);bottom,top=max(0,j-1),min(len(z)-1,j+1)
            neighbors=(z[j][left],z[j][right],z[bottom][i],z[top][i])
            if value is None or any(v is None for v in neighbors):result.append(None);continue
            gx=(neighbors[1]-neighbors[0])/((right-left)*dx)*vert_exag
            gy=(neighbors[3]-neighbors[2])/((top-bottom)*dy)*vert_exag
            result.append(max(0,(-gx*light[0]-gy*light[1]+light[2])/math.sqrt(gx*gx+gy*gy+1)))
        out.append(result)
    return out
