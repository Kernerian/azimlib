"""Known geodesic surfaces, seams/poles and narrow double contacts."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from eclipse_spatial_metric import boundary_distance
from azimlib.geodesy import Geodesic
from azimlib._eclipse_ephemeris import contact_roots,EclipseEphemeris,EclipseDomainError
from validate_eclipse_corpus import same_boundary_branch

class SpatialMetric(unittest.TestCase):
    def test_cross_track_branch_must_match_and_missing_axis_is_unverified(self):
        class State:
            def __init__(self,t):self.t=t
            def central_point(self):return (self.t*.001,0)
        self.assertTrue(same_boundary_branch(State,0,(0,1),(0,1.01))['verified'])
        self.assertFalse(same_boundary_branch(State,0,(0,1),(0,-1))['verified'])
        class Missing:
            def central_point(self):return None
        self.assertFalse(same_boundary_branch(lambda t:Missing(),0,(0,1),(0,1))['verified'])
    def test_geodesic_circles_known_distances_latitudes_seams_and_poles(self):
        geo=Geodesic()
        for center in ((0,0),(179.9,0),(-179.9,70),(30,89.7),(-80,-69)):
            for az in (0,53,173,290):
                for offset in (-2000,3500,9000):
                    q=geo.direct(*center,az,20000+offset);p=(q.longitude,q.latitude)
                    result=boundary_distance(p,lambda lon,lat:(geo.inverse(*center,lon,lat).distance-20000)/111000)
                    self.assertLess(abs(result['distance_m']-abs(offset)),1.)
                    self.assertLess(abs(result['residual']),1e-9)
    def test_equator_known_distance_and_zero(self):
        geo=Geodesic()
        for lon in (-179.99,0,179.99):
            r=boundary_distance((lon,.02),lambda x,y:y)
            self.assertLess(abs(r['distance_m']-geo.inverse(lon,.02,lon,0).distance),1)
        self.assertEqual(boundary_distance((0,0),lambda x,y:y)['distance_m'],0)
    def test_absent_degenerate_or_outside_search_is_failure(self):
        for fn in (lambda x,y:1,lambda x,y:float('nan'),lambda x,y:y-30):
            with self.assertRaises(ArithmeticError):boundary_distance((0,0),fn)
    def test_narrow_contacts_require_extremum_not_reference_roots(self):
        f=lambda t:(t-44.5)**2-4
        self.assertEqual(contact_roots(f,0,90,step=30,tolerance=.001),())
        roots=contact_roots(f,0,90,step=30,tolerance=.001,critical_points=(44.5,))
        self.assertEqual(len(roots),2)
        self.assertAlmostEqual(roots[0],42.5,delta=.001);self.assertAlmostEqual(roots[1],46.5,delta=.001)
    def test_critical_points_and_domain_are_explicit(self):
        for points in ((float('nan'),),(-1,),(301,)):
            with self.assertRaises(ValueError):contact_roots(lambda t:t-1,0,300,critical_points=points)
        self.assertIsNone(EclipseEphemeris.domain_contract()['certified_accuracy_interval'])
        self.assertFalse(EclipseDomainError('out','TT-UT1',201).scientific_prediction_valid)

if __name__=='__main__':unittest.main()
