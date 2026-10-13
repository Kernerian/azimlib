"""Global distance to every represented WGS84 geodesic curve component.

This certifies a finite curve representation, never completeness or interpolation
accuracy of a physical eclipse envelope. No north/south labels or local seed
select a branch. A failed inverse, exhausted search or incomplete representation
must not be interpreted as absence of an eclipse or a passed scientific gate.
"""
import heapq
import itertools
import math
from azimlib.geodesy import Geodesic, WGS84
from azimlib.geometry import position


def _xyz(point):
    lon, lat = map(math.radians, point)
    n = WGS84.semi_major_axis / math.sqrt(1-WGS84.eccentricity_squared*math.sin(lat)**2)
    return (n*math.cos(lat)*math.cos(lon), n*math.cos(lat)*math.sin(lon),
            n*(1-WGS84.eccentricity_squared)*math.sin(lat))


def _box_distance(point, bounds):
    return math.sqrt(sum(max(low-v, 0., v-high)**2 for v, (low, high) in zip(point, bounds)))


class GlobalGeodesicCurve:
    """All shortest geodesic segments of all explicitly supplied components.

    Isolated points are allowed; empty components mean no represented geometry,
    not physical absence. The numerical margin is explicit and conditional on
    the geodesic solver's accuracy. Search intervals bound distance on the whole
    supplied curve, not just distance to its vertices. Inputs are lon/lat.
    """
    def __init__(self, components):
        self.geo = Geodesic()
        self.segments = []
        for component, points in enumerate(components):
            points = tuple(position(p) for p in points)
            for index, (a, b) in enumerate(zip(points, points[1:]) if len(points)>1 else ((points[0], points[0]),) if points else ()):
                inverse = self.geo.inverse(*a, *b)
                length = inverse.distance
                middle = self.geo.direct(*a, inverse.azimuth1, length/2)
                center = _xyz((middle.longitude, middle.latitude))
                # Chord length cannot exceed geodesic arclength. Every point
                # of a segment lies in this box about its arclength midpoint.
                box = tuple((v-length/2-.01, v+length/2+.01) for v in center)
                self.segments.append(dict(a=a, length=length, azimuth=inverse.azimuth1,
                    component=component, index=index, box=box, center=center))
        def build(indices):
            bounds = tuple((min(self.segments[i]['box'][j][0] for i in indices),
                            max(self.segments[i]['box'][j][1] for i in indices)) for j in range(3))
            if len(indices)==1:return bounds, indices[0], None
            axis = max(range(3), key=lambda j: bounds[j][1]-bounds[j][0])
            ordered = sorted(indices, key=lambda i:(self.segments[i]['center'][axis], i))
            split = len(ordered)//2
            return bounds, build(ordered[:split]), build(ordered[split:])
        self.root = build(list(range(len(self.segments)))) if self.segments else None

    def distance(self, reference, *, tolerance_m=1., numerical_margin_m=.001, max_evaluations=100000):
        reference = position(reference)
        if not math.isfinite(tolerance_m) or tolerance_m<=0 or not math.isfinite(numerical_margin_m) or numerical_margin_m<=0 or tolerance_m<=2*numerical_margin_m:
            raise ValueError('Require a positive tolerance exceeding twice the numerical margin')
        if not isinstance(max_evaluations,int) or max_evaluations<1:raise ValueError('Positive evaluation limit required')
        if self.root is None:
            return dict(status='no_represented_geometry', physical_absence_certified=False,
                        global_represented_curve_certified=False, distance_m=None)
        xyz = _xyz(reference); serial = itertools.count(); queue = []
        best = math.inf; winner = None; evaluations = 0
        def push_box(node):
            lower = max(0., _box_distance(xyz,node[0])-numerical_margin_m)
            if lower<best:heapq.heappush(queue,(lower,next(serial),'box',node))
        def push_arc(segment, start, end):
            nonlocal best, winner, evaluations
            s = (start+end)/2
            p = self.geo.direct(*segment['a'],segment['azimuth'],s)
            point = (p.longitude,p.latitude)
            d = self.geo.inverse(*reference,*point).distance
            evaluations += 1
            if d+numerical_margin_m<best:
                best=d+numerical_margin_m
                winner=dict(point=point, component=segment['component'], segment=segment['index'], arclength_m=s)
            # The distance function is 1-Lipschitz in segment arclength.
            lower=max(0.,d-(end-start)/2-numerical_margin_m)
            if lower<best:heapq.heappush(queue,(lower,next(serial),'arc',(segment,start,end)))
        push_box(self.root)
        status='bounded'
        while queue:
            if best-queue[0][0]<=tolerance_m:break
            if evaluations>=max_evaluations:status='search_limit';break
            lower, _, kind, item = heapq.heappop(queue)
            if lower>=best:continue
            if kind=='box':
                if item[2] is None:push_arc(self.segments[item[1]],0.,self.segments[item[1]]['length'])
                else:push_box(item[1]);push_box(item[2])
            else:
                segment,start,end=item;middle=(start+end)/2
                push_arc(segment,start,middle);push_arc(segment,middle,end)
        lower=min(best,queue[0][0]) if queue else best
        return dict(status=status, distance_m=best-numerical_margin_m,
                    lower_m=lower, upper_m=best, uncertainty_m=best-lower,
                    global_represented_curve_certified=status=='bounded',
                    physical_curve_completeness_certified=False,
                    numerical_margin_m=numerical_margin_m, evaluations=evaluations,
                    represented_segments=len(self.segments), nearest=winner,
                    metric='Global WGS84 geodesic branch-and-bound over all represented components')
