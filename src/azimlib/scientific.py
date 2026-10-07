"""Original scalar/color raster kernels. No numerical/GIS dependency required."""
import math
from numbers import Integral, Real


def scalar(value):
    """Normalize missing/nonfinite/masked scalars without importing NumPy."""
    if value is None or bool(getattr(value, 'mask', False)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def color_rows(values):
    """Validate RGB/RGBA: integer channels 0..255, floating channels 0..1.

    Missing or masked pixels/channels become transparent black. Premultiplied
    interpolation avoids invisible RGB bleeding during bilinear resampling.
    """
    rows = []
    for row in values:
        output = []
        for pixel in row:
            mask = getattr(pixel, 'mask', False)
            masked = any(bool(v) for v in mask) if hasattr(mask, '__iter__') else bool(mask)
            if pixel is None or masked:
                output.append((0., 0., 0., 0.)); continue
            channels = tuple(pixel)
            if len(channels) not in (3, 4):
                raise ValueError('Color pixels require three or four channels')
            vals = tuple(scalar(v) for v in channels)
            if any(v is None for v in vals):
                output.append((0., 0., 0., 0.)); continue
            integer = all(isinstance(v, Integral) for v in channels)
            limit = 255 if integer else 1
            if any(not 0 <= v <= limit for v in vals):
                raise ValueError('Integer color channels require 0..255; floats require 0..1')
            vals = tuple(v / limit for v in vals)
            output.append((*vals[:3], vals[3] if len(vals) == 4 else 1.))
        rows.append(tuple(output))
    if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError('Color image requires a nonempty rectangular matrix')
    return tuple(rows)


def is_color(values):
    for row in values:
        for value in row:
            if value is not None and not isinstance(value, Real):
                try: return len(value) in (3, 4)
                except TypeError: return False
    return False


def color_hex(pixel):
    return '#' + ''.join(f'{round(max(0., min(1., v))*255):02x}' for v in pixel)


def interpolate(rows, column, row, method, missing='strict', *, color=False):
    """Sample pixel centres; reject outside pixel coverage. Edge taps clamp.

    strict masks a sample if any positive-weight tap is missing; renormalize
    uses valid taps only. Color alpha uses premultiplied interpolation.
    """
    if method not in ('nearest', 'bilinear'): raise ValueError('method must be nearest or bilinear')
    if missing not in ('strict', 'renormalize'): raise ValueError('missing must be strict or renormalize')
    ny, nx = len(rows), len(rows[0])
    if not 0 <= column < nx or not 0 <= row < ny: return (0., 0., 0., 0.) if color else None
    if method == 'nearest': return rows[math.floor(row)][math.floor(column)]
    x, y = column-.5, row-.5
    i, j = math.floor(x), math.floor(y); tx, ty = x-i, y-j
    taps = [(rows[min(ny-1, max(0, jj))][min(nx-1, max(0, ii))], weight)
            for ii, jj, weight in ((i,j,(1-tx)*(1-ty)),(i+1,j,tx*(1-ty)),
                                  (i,j+1,(1-tx)*ty),(i+1,j+1,tx*ty)) if weight > 0]
    if color:
        alpha = sum(p[3]*w for p,w in taps)
        return tuple(sum(p[k]*p[3]*w for p,w in taps)/alpha if alpha else 0. for k in range(3))+(alpha,)
    if missing == 'strict' and any(p is None for p,w in taps): return None
    taps = [(p,w) for p,w in taps if p is not None]
    total = sum(w for p,w in taps)
    return sum(p*w for p,w in taps)/total if total else None


def histogram(lon, lat, *, weights=None, bins=24, extent=None, smoothing=0,
              normalization='count'):
    """Weighted angular histogram with mass-preserving cell Gaussian spread.

    probability sums to one; density integrates to one in square degrees.
    These are not physical areal densities. Points outside extent are excluded.
    """
    from .field_artists import image_extent, image_edges
    x,y = tuple(lon),tuple(lat)
    if not x or len(x) != len(y): raise ValueError('Require nonempty equal-length lon/lat')
    points = tuple((float(a),float(b)) for a,b in zip(x,y))
    if any(not math.isfinite(a+b) or not -180<=a<=180 or not -90<=b<=90 for a,b in points):
        raise ValueError('Histogram coordinates must be finite geographic points')
    weights = (1.,)*len(x) if weights is None else tuple(float(v) for v in weights)
    if len(weights)!=len(x) or any(not math.isfinite(v) or v<0 for v in weights):
        raise ValueError('Weights must be finite nonnegative and match points')
    bins = (bins,bins) if isinstance(bins,Integral) else tuple(bins)
    if len(bins)!=2 or any(isinstance(b,bool) or not isinstance(b,Integral) or not 2<=b<=512 for b in bins):
        raise ValueError('bins requires integers (nx,ny) in [2,512]')
    nx,ny=bins
    if extent is None:
        w,e=min(x),max(x);s,n=min(y),max(y)
        dx,dy=max(.1,(e-w)*.08),max(.1,(n-s)*.08)
        extent=(max(-180,w-dx),min(180,e+dx),max(-90,s-dy),min(90,n+dy))
    w,e,s,n=image_extent(extent)
    if normalization not in ('count','probability','density'): raise ValueError('Unknown histogram normalization')
    smoothing=float(smoothing)
    if not math.isfinite(smoothing) or not 0<=smoothing<=5: raise ValueError('smoothing must be in [0,5] cells')
    grid=[[0.]*nx for _ in range(ny)]
    for (a,b),v in zip(points,weights):
        if w<=a<=e and s<=b<=n: grid[min(ny-1,int((b-s)*ny/(n-s)))][min(nx-1,int((a-w)*nx/(e-w)))]+=v
    if smoothing:
        radius=math.ceil(3*smoothing)
        for axis in (0,1):
            out=[[0.]*nx for _ in range(ny)]
            # Normalize each source footprint at the boundary to conserve mass.
            for j in range(ny):
                for i in range(nx):
                    if not grid[j][i]: continue
                    taps=[]
                    for k in range(-radius,radius+1):
                        a,b=(i+k,j) if axis==0 else (i,j+k)
                        if 0<=a<nx and 0<=b<ny: taps.append((a,b,math.exp(-k*k/(2*smoothing*smoothing))))
                    total=sum(t[2] for t in taps)
                    for a,b,v in taps: out[b][a]+=grid[j][i]*v/total
            grid=out
    total=sum(map(sum,grid))
    if normalization!='count':
        if total<=0: raise ValueError('Normalized histogram needs positive included weight')
        divisor=total if normalization=='probability' else total*(e-w)*(n-s)/(nx*ny)
        grid=[[v/divisor for v in row] for row in grid]
    xe,ye=image_edges((w,e,s,n),nx,ny)
    return xe,ye,tuple(tuple(r) for r in grid)


def filled_levels(valid, levels):
    if isinstance(levels,Integral):
        if isinstance(levels,bool) or levels<1: raise ValueError('levels requires positive intervals')
        low,high=min(valid),max(valid)
        if low==high: low-=.5;high+=.5
        levels=[low*(1-i/levels)+high*(i/levels) for i in range(levels+1)]
    levels=tuple(float(v) for v in levels)
    if len(levels)<2 or any(not math.isfinite(v) for v in levels) or any(a>=b for a,b in zip(levels,levels[1:])):
        raise ValueError('Filled contours require at least two increasing finite boundaries')
    return levels


def clip_band(points, low, high):
    """Clip a CCW linearly interpolated triangle to a scalar interval."""
    polygon=list(points)
    for bound,lower in ((low,True),(high,False)):
        output=[]
        for a,b in zip(polygon,polygon[1:]+polygon[:1]):
            inside_a=a[2]>=bound if lower else a[2]<=bound
            inside_b=b[2]>=bound if lower else b[2]<=bound
            if inside_a: output.append(a)
            if inside_a != inside_b:
                t=(bound-a[2])/(b[2]-a[2]);output.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),bound))
        polygon=output
        if not polygon: break
    ring=[tuple(round(v,12) for v in p[:2]) for p in polygon]
    ring=[p for i,p in enumerate(ring) if p!=ring[i-1]]
    if len(ring)<3 or abs(area(ring))<1e-22: return []
    return ring


def area(ring):
    return sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(ring,ring[1:]+ring[:1]))/2


def inside(point, ring):
    x,y=point;result=False
    for a,b in zip(ring,ring[1:]+ring[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]: result=not result
    return result


def band_polygons(triangles, low, high, *, include_upper=False):
    """Cancel opposite mesh edges, trace union boundaries, associate holes."""
    edges=set()
    for triangle in triangles:
        if any(p[2] is None for p in triangle): continue
        # Flat triangles on an interior upper boundary belong to the next band.
        if not include_upper and all(p[2]==high for p in triangle): continue
        ring=clip_band(triangle,low,high)
        for a,b in zip(ring,ring[1:]+ring[:1]):
            if (b,a) in edges: edges.remove((b,a))
            elif a!=b: edges.add((a,b))
    outgoing={}
    for a,b in edges: outgoing.setdefault(a,set()).add(b)
    rings=[]
    while edges:
        start,point=min(edges);previous=start;ring=[start]
        while True:
            edge=(previous,point)
            if edge not in edges: raise ValueError('Non-manifold filled contour boundary')
            edges.remove(edge);outgoing[previous].remove(point);ring.append(point)
            if point==start: break
            options=outgoing.get(point,set())
            if not options: raise ValueError('Unclosed filled contour boundary')
            dx,dy=point[0]-previous[0],point[1]-previous[1]
            next_point=max(options,key=lambda p:math.atan2(dx*(p[1]-point[1])-dy*(p[0]-point[0]),dx*(p[0]-point[0])+dy*(p[1]-point[1])))
            previous,point=point,next_point
        rings.append(ring)
    outers=[r for r in rings if area(r)>0];holes=[r for r in rings if area(r)<0]
    polygons=[[r] for r in outers]
    for hole in holes:
        candidates=[i for i,r in enumerate(outers) if inside(hole[0],r)]
        if not candidates: raise ValueError('Orphan contour hole')
        polygons[min(candidates,key=lambda i:abs(area(outers[i])))].append(hole)
    return polygons


def grid_triangles(x,y,z):
    triangles=[]
    for j in range(len(y)-1):
        for i in range(len(x)-1):
            points=((x[i],y[j],z[j][i]),(x[i+1],y[j],z[j][i+1]),
                    (x[i+1],y[j+1],z[j+1][i+1]),(x[i],y[j+1],z[j+1][i]))
            if any(p[2] is None for p in points): continue
            triangles.extend(((points[0],points[1],points[2]),(points[0],points[2],points[3])))
    return triangles
