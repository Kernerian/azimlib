"""Exact temporal exclusions, known hidden events, and fail-closed certificates."""
from fractions import Fraction as F
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from eclipse_temporal_envelope import (add,mul,bernstein_bounds,roots_in_interval,
    temporal_partition,CriticalPolynomial,PolynomialConeMotion,polynomial_resultant,
    adaptive_interpolation,interpolation_bound,verify_sampling_coverage)
from eclipse_cone_sections import ConeSections,_value


def shifted_square(center,epsilon=F(0)):
    return (center*center-epsilon*epsilon,-2*center,F(1))


class TemporalEnvelopeTests(unittest.TestCase):
    def assert_contains(self,plan,time):
        self.assertTrue(any(b['start']<=time<=b['end'] for b in plan['critical_boxes']),time)

    def test_bernstein_range_encloses_all_rational_samples(self):
        p=(F(7),F(-19),F(3),F(11),F(-6))
        for a,b in ((F(-2),F(3)),(F(1,5),F(2,7)),(F(1),F(1))):
            lo,hi=bernstein_bounds(p,a,b)
            for i in range(101):self.assertTrue(lo<=_value(p,a+(b-a)*F(i,100))<=hi)

    def test_sturm_retains_even_roots_and_endpoints(self):
        p=mul(mul([0,1],[-1,1]),shifted_square(F(1,3)))
        result=roots_in_interval(p,0,1)
        self.assertTrue(result['complete']);self.assertEqual(len(result['roots']),3)
        for t in (F(0),F(1,3),F(1)):
            self.assertTrue(any(a<=t<=b for a,b in result['roots']))

    def test_short_lived_component_between_fixed_samples_is_not_lost(self):
        center=F(314159,1000000);epsilon=F(1,1000000)
        event=CriticalPolynomial('birth-death','topology',shifted_square(center,epsilon))
        plan=temporal_partition([event],0,1)
        self.assertTrue(plan['scalar_event_discovery_complete'])
        for t in (center-epsilon,center+epsilon):self.assert_contains(plan,t)
        self.assertFalse(verify_sampling_coverage(plan,[0,F(1,2),1])['coverage_passed'])
        self.assertTrue(any(a<center<b for a,b in plan['regular_open_intervals']))

    def test_instantaneous_tangency_without_sign_change(self):
        time=F(2,7)
        plan=temporal_partition([CriticalPolynomial('tangent','topology',shifted_square(time))],0,1)
        self.assertEqual(len(plan['critical_boxes']),1);self.assert_contains(plan,time)
        self.assertFalse(verify_sampling_coverage(plan,[0,1])['coverage_passed'])

    def test_small_component_topology_horizon_and_seam_all_required(self):
        events=[CriticalPolynomial('small','topology',shifted_square(F(1,5),F(1,1000000))),
                CriticalPolynomial('merge-split','topology',shifted_square(F(4,7))),
                CriticalPolynomial('horizon','visibility',(-F(3,8),F(1))),
                CriticalPolynomial('antimeridian','chart_transition',(-F(7,9),F(1)))]
        plan=temporal_partition(events,0,1)
        for t in (F(1,5)-F(1,1000000),F(1,5)+F(1,1000000),F(4,7),F(3,8),F(7,9)):
            self.assert_contains(plan,t)
        samples=[(a+b)/2 for a,b in plan['regular_open_intervals']]
        samples.extend((b['start']+b['end'])/2 for b in plan['critical_boxes'])
        self.assertTrue(verify_sampling_coverage(plan,samples)['coverage_passed'])
        for i in range(len(samples)):
            self.assertFalse(verify_sampling_coverage(plan,samples[:i]+samples[i+1:])['coverage_passed'])
        self.assertFalse(plan['physical_event_envelope_complete'])

    def test_persistent_degeneracy_and_exhaustion_are_not_approval(self):
        for polynomial,options in (((0,),{}),(shifted_square(F(1,3)),{'max_nodes':1})):
            plan=temporal_partition([CriticalPolynomial('unknown','topology',polynomial)],0,1,**options)
            self.assertFalse(plan['scalar_event_discovery_complete']);self.assertTrue(plan['failures'])
            self.assertFalse(verify_sampling_coverage(plan,[F(1,2)])['coverage_passed'])

    def test_interpolation_bound_detects_hidden_extreme(self):
        coordinates=((0,4,-4),(0,),(0,))
        self.assertEqual(interpolation_bound(coordinates,0,1),1)
        plan=adaptive_interpolation(coordinates,0,1,F(1,1000))
        self.assertTrue(plan['complete']);self.assertGreater(len(plan['intervals']),1)
        for a,b,bound in plan['intervals']:
            self.assertLessEqual(bound,F(1,1000))
            for i in range(21):
                t=a+(b-a)*F(i,20);line=_value(coordinates[0],a)+(t-a)/(b-a)*(_value(coordinates[0],b)-_value(coordinates[0],a))
                self.assertLessEqual(abs(_value(coordinates[0],t)-line),bound)

    def test_resultant_has_known_common_root_condition(self):
        # p(u,t)=u-t; q(u,t)=u+t, resultant = 2t up to positive normalization.
        r=polynomial_resultant([[0,-1],[1]],[[0,1],[1]])
        self.assertEqual(_value(r,0),0);self.assertNotEqual(_value(r,F(1,4)),0)

    def test_derived_cone_predicates_find_brief_physical_branch(self):
        center=F(3,10);epsilon=F(1,10000)
        apex_x=add([F(17,4)],shifted_square(center,epsilon))
        motion=PolynomialConeMotion((apex_x,(0,),(4,)),(0,0,1),F(3,4),(1,1,1))
        plan=motion.partition(0,1)
        self.assertTrue(plan['scalar_event_discovery_complete'])
        for t in (center-epsilon,center+epsilon):self.assert_contains(plan,t)
        def components(t):
            return ConeSections((float(_value(apex_x,t)),0,4),(0,0,1),.75,(1,1,1)).components(17)
        self.assertFalse(components(F(0)));self.assertFalse(components(F(1)))
        self.assertTrue(components(center))
        self.assertFalse(plan['physical_event_envelope_complete'])
        self.assertTrue(plan['missing_physical_obligations'])

    def test_derived_cone_predicates_keep_instantaneous_tangency(self):
        center=F(3,10);apex_x=add([F(17,4)],shifted_square(center))
        motion=PolynomialConeMotion((apex_x,(0,),(4,)),(0,0,1),F(3,4),(1,1,1))
        plan=motion.partition(0,1)
        self.assertTrue(plan['scalar_event_discovery_complete']);self.assert_contains(plan,center)
        points=ConeSections((4.25,0,4),(0,0,1),.75,(1,1,1)).components(17)
        self.assertTrue(points)

    def test_known_cassini_fusion_and_separation(self):
        # F=(x²+y²+1)²-4x²-q(t). Its real singularities require
        # y=0, x=0 or x=+-1: critical q=1 (fusion) or q=0 (birth).
        # q(t)=1-t²: two ovals except the instantaneous lemniscate at t=0;
        # neither a fixed endpoints-only grid nor sign-change detection works.
        q=(F(1),F(0),F(-1))
        events=[CriticalPolynomial('birth','topology',q),
                CriticalPolynomial('fusion-separation','topology',add(q,[-1]))]
        plan=temporal_partition(events,F(-1,2),F(1,2))
        self.assertTrue(plan['scalar_event_discovery_complete']);self.assert_contains(plan,F(0))
        self.assertFalse(verify_sampling_coverage(plan,[F(-1,2),F(1,2)])['coverage_passed'])
        # Independent exact implicit checks: separated oval centers and the
        # singular connecting origin only on the critical epoch.
        for t in (F(-1,4),F(0),F(1,4)):
            origin_residual=1-_value(q,t)
            self.assertEqual(origin_residual==0,t==0)
            self.assertLess(-_value(q,t),0)  # x=+-1,y=0 interior to both lobes

    def test_sphere_horizon_entry_exit_and_cartesian_antimeridian(self):
        import math
        # Rational unit circle: denominator 1+t² is strictly positive.
        # Visibility for Sun direction +x has numerator 1-t². The same
        # component reflected across y crosses the antimeridian at t=0.
        horizon=temporal_partition([CriticalPolynomial('horizon','visibility',(1,0,-1))],-2,2)
        for t in (F(-1),F(1)):self.assert_contains(horizon,t)
        seam=temporal_partition([CriticalPolynomial('seam','chart_transition',(0,1))],F(-1,2),F(1,2))
        self.assert_contains(seam,F(0));points=[];longitudes=[]
        for t in (F(-1,1000),F(0),F(1,1000)):
            x=-(1-t*t)/(1+t*t);y=-2*t/(1+t*t)
            self.assertEqual(x*x+y*y,1)
            points.append((float(x),float(y)));longitudes.append(math.atan2(float(y),float(x)))
        self.assertGreater(abs(longitudes[-1]-longitudes[0]),6)
        self.assertLess(math.dist(points[0],points[-1]),.005)
        self.assertFalse(verify_sampling_coverage(horizon,[-2,0,2])['coverage_passed'])

    def test_infinity_chart_repeated_root_marked_singular(self):
        section=ConeSections((0,5,0),(0,0,1),.75,(4,4,4))
        self.assertTrue(section.contract()['singular_topology'])


if __name__=='__main__':unittest.main()
