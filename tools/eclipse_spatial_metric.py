"""Local geodesic distance to a smooth implicit terrestrial boundary.

No meridian distance or planar degree norm is used. A converged solution is a
feasible surface root with a local closest-point stationarity check. It is not
a global Hausdorff certificate for a disconnected curve; unresolved roots,
multiple branches and temporal endpoints must remain explicit failures.
"""
import math
from azimlib.geodesy import Geodesic


def boundary_distance(reference,margin,*,max_radius_m=300000,residual_tolerance=1e-9):
    """margin(lon,lat) must be signed and smooth near the chosen branch.

    Geodesic polar coordinates about the reference make hypot(east,north) the
    ellipsoidal distance exactly. Finite differences and constrained normal
    iteration enforce a root and radial/gradient alignment, independent of map
    orientation and of longitude seams. Failure never returns zero distance.
    """
    geo=Geodesic();origin=tuple(reference);x=y=0.;evaluations=0
    def point(e,n):
        q=geo.direct(*origin,math.degrees(math.atan2(e,n)),math.hypot(e,n))
        return q.longitude,q.latitude
    def value(e,n):
        nonlocal evaluations
        evaluations+=1;v=margin(*point(e,n))
        if not math.isfinite(v):raise ArithmeticError('Nonfinite spatial boundary margin')
        return v
    for iteration in range(1,25):
        f=value(x,y);step=100.
        gx=(value(x+step,y)-value(x-step,y))/(2*step)
        gy=(value(x,y+step)-value(x,y-step))/(2*step);norm2=gx*gx+gy*gy
        if norm2<1e-28:raise ArithmeticError('Degenerate spatial boundary gradient')
        tangent=abs(x*gy-y*gx)/math.sqrt(norm2)
        if abs(f)<=residual_tolerance and tangent<=.1:
            p=point(x,y);distance=geo.inverse(*origin,*p).distance
            return dict(distance_m=distance,point=p,residual=f,tangent_residual_m=tangent,
                        iterations=iteration,evaluations=evaluations,
                        metric='local constrained WGS84 geodesic surface distance',global_nearest_certified=False)
        multiplier=(gx*x+gy*y-f)/norm2
        dx,dy=multiplier*gx-x,multiplier*gy-y;size=math.hypot(dx,dy)
        if size>20000:dx*=20000/size;dy*=20000/size
        for power in range(14):
            fraction=2.**-power;nx,ny=x+fraction*dx,y+fraction*dy
            if math.hypot(nx,ny)>max_radius_m:continue
            nf=value(nx,ny)
            if abs(nf)<abs(f) or abs(nf)<=residual_tolerance:
                x,y=nx,ny;break
        else:raise ArithmeticError('Spatial boundary projection failed to descend')
    raise ArithmeticError('Spatial boundary projection did not converge')
