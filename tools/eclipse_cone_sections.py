"""Seed-independent sections of a fixed smooth double cone and an ellipsoid.

The cone ray discriminant is a trigonometric polynomial of degree two. A
tangent-half-angle substitution gives degree <=4. Exact rational Sturm counts
isolate every real root of the represented coefficients, including repeated
roots. This is a fixed-epoch component audit, NOT a certificate of a whole
event's envelope, floating-point model error, visibility or interpolation.
"""
from fractions import Fraction as F
from functools import reduce
import math


def _trim(p):
    p=list(p)
    while len(p)>1 and p[-1]==0:p.pop()
    return p

def _primitive(p):
    p=_trim(p);den=math.lcm(*(v.denominator for v in p));ints=[int(v*den) for v in p]
    gcd=reduce(math.gcd,(abs(v) for v in ints)) or 1
    return [F(v//gcd) for v in ints]

def _divide(a,b):
    a=_trim(a);b=_trim(b)
    if b==[0]:raise ZeroDivisionError('Zero polynomial')
    q=[F(0)]*max(1,len(a)-len(b)+1)
    while len(a)>=len(b) and a!=[0]:
        i=len(a)-len(b);v=a[-1]/b[-1];q[i]+=v
        for j,x in enumerate(b):a[i+j]-=v*x
        a=_trim(a)
    return _trim(q),a

def _sturm(p):
    p=_primitive(p);sequence=[p,_primitive([i*p[i] for i in range(1,len(p))])]
    while sequence[-1]!=[0]:
        _,r=_divide(sequence[-2],sequence[-1])
        if r==[0]:break
        sequence.append(_primitive([-v for v in r]))
    return sequence

def _value(p,x):
    result=F(0)
    for coefficient in reversed(p):result=result*x+coefficient
    return result

def isolate_real_roots(coefficients,*,angular_tolerance=1e-11):
    """Exact counts, rational brackets; angular tolerance in 2*atan(t)."""
    p=_primitive([F(v) for v in coefficients])
    if p==[0]:return dict(status='identically_zero',brackets=[],repeated=True)
    if len(p)==1:return dict(status='constant_nonzero',brackets=[],repeated=False)
    chain=_sturm(p);repeated=len(chain[-1])>1
    if repeated:p,_=_divide(p,chain[-1]);p=_primitive(p);chain=_sturm(p)
    def variations(x):
        signs=[1 if v>0 else -1 for poly in chain if (v:=_value(poly,x))!=0]
        return sum(a!=b for a,b in zip(signs,signs[1:]))
    bound=F(math.ceil(1+max(abs(x/p[-1]) for x in p[:-1])))
    pending=[(-bound,bound,variations(-bound)-variations(bound))];brackets=[];iterations=0
    while pending:
        lo,hi,count=pending.pop();iterations+=1
        if iterations>20000:raise ArithmeticError('Sturm isolation budget exceeded')
        if not count:continue
        if count==1 and 2*abs(math.atan(float(hi))-math.atan(float(lo)))<=angular_tolerance:
            brackets.append((lo,hi));continue
        mid=(lo+hi)/2;left=variations(lo)-variations(mid)
        pending.append((mid,hi,count-left));pending.append((lo,mid,left))
    brackets.sort()
    return dict(status='isolated',brackets=brackets,repeated=repeated)


class ConeSections:
    """Parametric fixed cone sections, independent of geographic seeds/labels.

    apex is in metres; slope=tan(half_angle); axes are ellipsoid semi-axes.
    Both cone nappes and both ellipsoid intersections are retained. Physical
    occluder ordering, daylight and event-envelope reduction are separate.
    """
    def __init__(self,apex,axis,slope,axes=(6378137.,6378137.,6356752.314245179)):
        self.apex=tuple(map(float,apex));axis=tuple(map(float,axis));self.axes=tuple(map(float,axes));self.slope=float(slope)
        if len(self.apex)!=3 or len(axis)!=3 or len(self.axes)!=3 or not all(math.isfinite(v) for v in (*self.apex,*axis,*self.axes,self.slope)) or min(self.axes)<=0 or self.slope<=0:
            raise ValueError('Require finite cone/ellipsoid data, positive axes and slope')
        length=math.sqrt(sum(v*v for v in axis))
        if not length:raise ValueError('Nonzero cone axis required')
        self.axis=tuple(v/length for v in axis)
        k=min(range(3),key=lambda i:abs(self.axis[i]));basis=[float(i==k) for i in range(3)]
        dot=sum(a*b for a,b in zip(self.axis,basis));basis=[b-dot*a for a,b in zip(self.axis,basis)];length=math.sqrt(sum(v*v for v in basis));self.e=tuple(v/length for v in basis)
        a,b=self.axis,self.e;self.f=(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
        # Exact arithmetic starts from the represented basis/slope/axes, with
        # no cancellation-prone floating discriminant coefficient subtraction.
        A=[F(v)/F(r) for v,r in zip(self.apex,self.axes)];C=sum(v*v for v in A)-1
        d=[[F(self.axis[i])+F(self.slope)*F(self.e[i]),2*F(self.slope)*F(self.f[i]),F(self.axis[i])-F(self.slope)*F(self.e[i])] for i in range(3)]
        n=[[d[i][j]/F(self.axes[i]) for i in range(3)] for j in range(3)]
        v=[sum(a*b for a,b in zip(A,part)) for part in n];p=[F(0)]*5
        for i in range(3):
            for j in range(3):p[i+j]+=v[i]*v[j]-C*sum(a*b for a,b in zip(n[i],n[j]))
        self.polynomial=_primitive(p);isolated=isolate_real_roots(self.polynomial);self.isolation=isolated
        angles=[]
        for lo,hi in isolated['brackets']:
            angle=(2*math.atan(float((lo+hi)/2)))%(2*math.pi)
            if angle<1e-10 or 2*math.pi-angle<1e-10:angle=0.
            angles.append(angle)
        # Infinity of the rational parameter is phi=pi, retained explicitly.
        if len(_trim(p))<5:angles.append(math.pi)
        self.tangencies=sorted(set(angles));cuts=sorted({0.,2*math.pi,*self.tangencies});arcs=[]
        for lo,hi in zip(cuts,cuts[1:]):
            mid=(lo+hi)/2;t=F(math.tan(mid/2));sign=_value(self.polynomial,t)
            if sign>0:arcs.append((lo,hi))
        if len(arcs)>1 and arcs[0][0]==0 and arcs[-1][1]==2*math.pi:
            arcs=[(arcs[-1][0],arcs[0][1]+2*math.pi),*arcs[1:-1]]
        self.arcs=tuple(arcs)
        self.identically_tangent=isolated['status']=='identically_zero'

    def isolated_tangencies(self):
        """Retain zero-dimensional components instead of reporting absence."""
        output=[]
        if self.identically_tangent:return ()
        for angle in self.tangencies:
            other=[abs(math.remainder(angle-b,2*math.pi)) for b in self.tangencies if b!=angle]
            step=min([.001,*[v/4 for v in other]])
            signs=[_value(self.polynomial,F(math.tan((angle+d)/2))) for d in (-step,step)]
            if all(v<0 for v in signs):output.append(self.intersections(angle)[0])
        return tuple(output)

    def intersections(self,phi):
        d=tuple(a+self.slope*(b*math.cos(phi)+c*math.sin(phi)) for a,b,c in zip(self.axis,self.e,self.f))
        u=tuple(a/r for a,r in zip(self.apex,self.axes));v=tuple(a/r for a,r in zip(d,self.axes))
        A=sum(x*x for x in v);B=2*sum(x*y for x,y in zip(u,v));C=sum(x*x for x in u)-1
        disc=B*B-4*A*C;allowance=64*math.ulp(max(abs(B*B),abs(4*A*C)))
        if disc < -allowance:raise ArithmeticError('Ray has no certified represented ellipsoid intersection')
        root=math.sqrt(max(0.,disc));q=-.5*(B+math.copysign(root,B))
        values=sorted((q/A,C/q)) if q else (0.,0.)
        return tuple(tuple(a+s*b for a,b in zip(self.apex,d)) for s in values)

    def components(self,samples=129):
        if not isinstance(samples,int) or samples<3 or samples>10000:raise ValueError('Require 3..10000 samples')
        if self.identically_tangent:
            return (tuple(self.intersections(i*2*math.pi/(samples-1))[0] for i in range(samples)),)
        output=[]
        for lo,hi in self.arcs:
            pairs=[self.intersections(lo+(hi-lo)*i/(samples-1)) for i in range(samples)]
            if hi-lo>=2*math.pi-1e-10:
                output.extend(tuple(pair[side] for pair in pairs) for side in (0,1))
            else:output.append(tuple([p[0] for p in pairs]+[p[1] for p in reversed(pairs)]))
        output.extend((point,) for point in self.isolated_tangencies())
        return tuple(output)

    def contract(self):
        return dict(discriminant_degree=len(self.polynomial)-1,finite_tangency_roots=len(self.isolation['brackets']),repeated_roots=self.isolation['repeated'],ray_parameter_arcs=self.arcs,all_represented_polynomial_roots_isolated=not self.identically_tangent,identically_tangent=self.identically_tangent,geographic_seed_used=False,north_south_selected_by_latitude=False,
            singular_topology=self.isolation['repeated'],event_envelope_complete=False,
            fixed_coefficient_scope='Complete root counts for exact rational represented cone/ellipsoid discriminant',
            limitations=['Floating basis/model roundoff not bounded by this root certificate','Sampling points does not certify curve interpolation','Both nappes/ellipsoid faces retained; daylight and occluder-order filters not certified','Fixed epoch sections are not the temporal eclipse envelope','Repeated roots require singular-graph topology classification'])
