"""Exact temporal exclusions for polynomial audit models, not sampled astronomy.

An interval is regular only when ALL declared critical polynomials exclude a
zero. Bernstein bounds prove exclusions; exact Sturm counts isolate even roots
and arbitrarily short-lived branches. Unresolved boxes remain unresolved.

The cone adapter derives critical polynomials from the ray discriminant: its
resultant with the angular derivative, plus the infinity-chart coefficient.
This certifies regular intervals of the represented fixed-axis polynomial cone
model. It does not certify ephemeris approximation, physical visibility, curve
interpolation or the whole eclipse envelope. Those require separate bounds.
"""
from dataclasses import dataclass
from fractions import Fraction as F
from math import comb

from eclipse_cone_sections import _trim, _value, _divide, _sturm, _primitive, ConeSections


def add(a,b):
    return _trim([(a[i] if i<len(a) else F(0))+(b[i] if i<len(b) else F(0))
                  for i in range(max(len(a),len(b)))])


def mul(a,b):
    out=[F(0)]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):out[i+j]+=x*y
    return _trim(out)


def scale(p,k):return _trim([x*k for x in p])
def derivative(p):return [i*p[i] for i in range(1,len(p))] or [F(0)]


def bernstein_bounds(p,a,b):
    """Inclusive rational range enclosure, no floating interval endpoints."""
    a,b=F(a),F(b)
    if a>b:raise ValueError('Ordered interval required')
    p=_trim(list(map(F,p)));n=len(p)-1
    power=[sum(p[k]*comb(k,j)*a**(k-j)*(b-a)**j for k in range(j,n+1))
           for j in range(n+1)]
    coefficients=[sum(power[j]*F(comb(i,j),comb(n,j)) for j in range(i+1))
                  for i in range(n+1)]
    return min(coefficients),max(coefficients)


def _variations(chain,x):
    signs=[1 if value>0 else -1 for p in chain if (value:=_value(p,x))]
    return sum(a!=b for a,b in zip(signs,signs[1:]))


def roots_in_interval(p,a,b,*,time_tolerance=F(1,10**10),max_nodes=200000):
    """Disjoint rational root boxes, including endpoint and even-order roots.

    Counts use (left,right]; a left endpoint root is retained explicitly.
    Repeated roots are square-freed ONLY for counting, never discarded.
    """
    a,b,tol=F(a),F(b),F(time_tolerance)
    if a>=b or tol<=0:raise ValueError('Positive interval/tolerance required')
    p=_primitive(list(map(F,p)))
    if p==[0]:return dict(status='persistent_critical',roots=[],nodes=0,complete=False)
    if len(p)==1:return dict(status='no_roots',roots=[],nodes=1,complete=True)
    chain=_sturm(p);repeated=len(chain[-1])>1
    if repeated:p,_=_divide(p,chain[-1]);chain=_sturm(p)
    boxes=[(a,a)] if not _value(p,a) else []
    pending=[(a,b,_variations(chain,a)-_variations(chain,b))];nodes=0
    while pending:
        lo,hi,count=pending.pop();nodes+=1
        if nodes>max_nodes:
            return dict(status='budget_exhausted',roots=sorted(boxes),nodes=nodes,complete=False)
        low,high=bernstein_bounds(p,lo,hi)
        if low>0 or high<0:
            if count:raise ArithmeticError('Bernstein/Sturm disagreement')
            continue
        if count==0:continue
        if count==1 and hi-lo<=tol:boxes.append((lo,hi));continue
        mid=(lo+hi)/2;left=_variations(chain,lo)-_variations(chain,mid)
        pending.extend(((mid,hi,count-left),(lo,mid,left)))
    return dict(status='isolated',roots=sorted(boxes),nodes=nodes,complete=True,repeated=repeated)


@dataclass(frozen=True)
class CriticalPolynomial:
    name:str
    category:str
    coefficients:tuple


def temporal_partition(events,start,end,*,time_tolerance=F(1,10**10),max_nodes=200000):
    """Adaptive partition with explicit unresolved critical boxes.

    The finite event list must itself have a derivation. A successful scalar
    partition cannot assert that an unspecified physical component is absent.
    """
    start,end=F(start),F(end);events=tuple(events)
    if not events:raise ValueError('Require derived critical predicates')
    if len({e.name for e in events})!=len(events):raise ValueError('Unique critical names required')
    isolated=[];failures=[];nodes=0
    for event in events:
        result=roots_in_interval(event.coefficients,start,end,time_tolerance=time_tolerance,max_nodes=max_nodes)
        nodes+=result['nodes']
        if not result['complete']:failures.append((event.name,result['status']))
        isolated.extend((lo,hi,event.name,event.category) for lo,hi in result['roots'])
    boxes=[]
    for lo,hi,name,category in sorted(isolated):
        if boxes and lo<=boxes[-1]['end']:
            boxes[-1]['end']=max(hi,boxes[-1]['end']);boxes[-1]['events'].append((name,category))
        else:boxes.append(dict(start=lo,end=hi,events=[(name,category)]))
    regular=[];left=start
    for box in boxes:
        if box['start']>left:regular.append((left,box['start']))
        left=max(left,box['end'])
    if left<end:regular.append((left,end))
    return dict(critical_boxes=boxes,regular_open_intervals=[] if failures else regular,failures=failures,
                unresolved_intervals=[(start,end)] if failures else [(b["start"],b["end"]) for b in boxes],
                scalar_event_discovery_complete=not failures,nodes=nodes,
                physical_event_envelope_complete=False)


def verify_sampling_coverage(plan,times):
    """Reject a sampled representation missing a certified interval/event box.

    Passing is necessary, not sufficient: samples do not certify singular
    topology, visibility or interpolation. Critical boxes require further
    singular analysis even when a sample lies inside them.
    """
    times=tuple(map(F,times));missing=[]
    for a,b in plan['regular_open_intervals']:
        if not any(a<t<b for t in times):missing.append(('regular_interval',a,b))
    for box in plan['critical_boxes']:
        if not any(box['start']<=t<=box['end'] for t in times):
            missing.append(('critical_box',box['start'],box['end']))
    return dict(coverage_passed=plan['scalar_event_discovery_complete'] and not missing,
                missing=missing,physical_event_envelope_complete=False)


def interpolation_bound(coordinates,start,end):
    """Conservative Euclidean linear-interpolation error (L1 upper bound).

    Coordinates must be exact polynomials of time for ONE material point or
    a proven uniform bound over a complete parameterized component. Applying
    this to isolated samples does not certify the curve between them.
    """
    a,b=F(start),F(end)
    if a>b:raise ValueError('Ordered interval required')
    maximum=F(0)
    for p in coordinates:
        lo,hi=bernstein_bounds(derivative(derivative(p)),a,b)
        maximum+=max(abs(lo),abs(hi))
    return maximum*(b-a)**2/8


def adaptive_interpolation(coordinates,start,end,error,*,max_nodes=200000):
    error=F(error)
    if error<=0:raise ValueError('Positive spatial error required')
    pending=[(F(start),F(end))];accepted=[];nodes=0
    if pending[0][0]>=pending[0][1]:raise ValueError('Positive interval required')
    while pending:
        a,b=pending.pop();nodes+=1
        if nodes>max_nodes:return dict(complete=False,intervals=accepted,reason='budget_exhausted')
        bound=interpolation_bound(coordinates,a,b)
        if bound<=error:accepted.append((a,b,bound))
        else:
            mid=(a+b)/2;pending.extend(((mid,b),(a,mid)))
    return dict(complete=True,intervals=sorted(accepted),reason=None)


def polynomial_resultant(p,q):
    """Fraction-free Sylvester determinant over Q[time], independently written."""
    while len(p)>1 and p[-1]==[0]:p=p[:-1]
    while len(q)>1 and q[-1]==[0]:q=q[:-1]
    n,m=len(p)-1,len(q)-1
    if not n and not m:return [F(0)]
    matrix=[]
    for k in range(m):matrix.append([[F(0)]]*k+list(reversed(p))+[[F(0)]]*(m-1-k))
    for k in range(n):matrix.append([[F(0)]]*k+list(reversed(q))+[[F(0)]]*(n-1-k))
    previous=[F(1)];sign=1;size=n+m
    for k in range(size-1):
        pivot=next((i for i in range(k,size) if matrix[i][k]!=[0]),None)
        if pivot is None:return [F(0)]
        if pivot!=k:matrix[k],matrix[pivot]=matrix[pivot],matrix[k];sign=-sign
        value=matrix[k][k]
        for i in range(k+1,size):
            for j in range(k+1,size):
                numerator=add(mul(matrix[i][j],value),scale(mul(matrix[i][k],matrix[k][j]),-1))
                quotient,remainder=_divide(numerator,previous)
                if remainder!=[0]:raise ArithmeticError('Inexact polynomial elimination')
                matrix[i][j]=quotient
            matrix[i][k]=[F(0)]
        previous=value
    return _primitive(scale(matrix[-1][-1],sign))


class PolynomialConeMotion:
    """Exact represented cone with polynomial apex and fixed basis/slope/axes.

    Critical resultants cover real angular branch births, deaths, mergers and
    tangencies; complex critical roots may add conservative subdivisions. The
    infinity chart is explicit, not a longitude seam. Persistent degeneracy
    returns an incomplete certificate rather than fabricated branch counts.
    """
    def __init__(self,apex,axis,slope,axes):
        if len(apex)!=3:raise ValueError('Three apex polynomials required')
        self.apex=tuple(tuple(map(F,p)) for p in apex)
        template=ConeSections(tuple(float(p[0]) for p in self.apex),axis,slope,axes)
        self.template=template
        A=[scale(p,1/F(r)) for p,r in zip(self.apex,template.axes)]
        C=[F(-1)]
        for p in A:C=add(C,mul(p,p))
        d=[[F(template.axis[i])+F(template.slope)*F(template.e[i]),
            2*F(template.slope)*F(template.f[i]),F(template.axis[i])-F(template.slope)*F(template.e[i])]
           for i in range(3)]
        n=[[d[i][j]/F(template.axes[i]) for i in range(3)] for j in range(3)]
        v=[]
        for part in n:
            poly=[F(0)]
            for p,k in zip(A,part):poly=add(poly,scale(p,k))
            v.append(poly)
        coefficients=[[F(0)] for _ in range(5)]
        for i in range(3):
            for j in range(3):
                coefficients[i+j]=add(coefficients[i+j],add(mul(v[i],v[j]),
                    scale(C,-sum(a*b for a,b in zip(n[i],n[j])))))
        self.coefficients=coefficients

    def critical_events(self):
        p=self.coefficients;q=[scale(p[i],i) for i in range(1,len(p))]
        return (CriticalPolynomial('angular-discriminant','topology',tuple(polynomial_resultant(p,q))),
                CriticalPolynomial('infinity-chart','chart_transition',tuple(p[-1])))

    def partition(self,start,end,**options):
        plan=temporal_partition(self.critical_events(),start,end,**options)
        plan['scope']='Polynomial fixed-basis double-cone algebraic section topology only'
        plan['missing_physical_obligations']=[
            'Bounded DE440/light-time/frame/time-scale approximation over time',
            'Daylight, occluder order and solar/lunar limb visibility boundaries',
            'Singular component graph inside every isolated critical box',
            'Uniform spatial and temporal interpolation of complete components',
            'Envelope reduction F=0 and dF/dt=0 plus endpoints/visibility boundaries']
        return plan
