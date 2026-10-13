"""Known spatial minima across disconnected components, poles and seams."""
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from eclipse_global_metric import GlobalGeodesicCurve
from azimlib.geodesy import Geodesic


class GlobalMetric(unittest.TestCase):
    def assertDistance(self,curve,point,expected):
        result=GlobalGeodesicCurve(curve).distance(point,tolerance_m=.1)
        self.assertEqual(result['status'],'bounded')
        self.assertLessEqual(result['lower_m'],expected+.01)
        self.assertGreaterEqual(result['upper_m'],expected-.01)
        self.assertLessEqual(result['uncertainty_m'],.1)
        self.assertFalse(result['physical_curve_completeness_certified'])
        return result

    def test_equator_and_hidden_disconnected_nearer_branch(self):
        geo=Geodesic();point=(0,.02);expected=geo.inverse(*point,0,0).distance
        for curves in ((((-5,-1),(5,-1)),((-1,0),(1,0))), (((1,0),(-1,0)),((5,-1),(-5,-1)))):
            result=self.assertDistance(curves,point,expected)
            self.assertAlmostEqual(result['nearest']['point'][1],0,places=10)

    def test_antimeridian_and_polar_symmetry(self):
        geo=Geodesic()
        self.assertDistance((((179,0),(-179,0)),), (180,.01),geo.inverse(180,.01,180,0).distance)
        self.assertDistance((((0,89),(180,89)),), (90,90),0)

    def test_point_empty_and_zero_are_distinct(self):
        self.assertDistance((((10,20),),), (10,20),0)
        result=GlobalGeodesicCurve(((),)).distance((0,0))
        self.assertEqual(result['status'],'no_represented_geometry')
        self.assertFalse(result['physical_absence_certified'])
        self.assertIsNone(result['distance_m'])

    def test_search_limit_never_certifies(self):
        result=GlobalGeodesicCurve((((-5,0),(5,0)),)).distance((0,.02),max_evaluations=1)
        self.assertEqual(result['status'],'search_limit')
        self.assertFalse(result['global_represented_curve_certified'])

    def test_invalid_parameters(self):
        curve=GlobalGeodesicCurve((((0,0),(1,0)),))
        for value in (0,-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):curve.distance((0,0),tolerance_m=value)
        with self.assertRaises(ValueError):curve.distance((0,0),max_evaluations=0)

    def test_local_branch_diagnostics_cannot_approve_global_scientific_gate(self):
        from validate_eclipse_corpus import finalize_boundaries
        rows=[dict(quantity='boundary_m',side=side,reference=(0,.02),error=2000.,passed=True,
                   certificate=dict(point=(x,0),residual=0.),temporal_minimum_is_interior=True,
                   closest_ut1_seconds=t,branch=dict(verified=False))
              for side,x,t in (('north',-.01,0),('north',.01,1))]
        finalize_boundaries(rows)
        for row in rows:
            self.assertTrue(row['represented_curve_numeric_pass'])
            self.assertFalse(row['passed'])
            self.assertTrue(row['global_certificate']['global_represented_curve_certified'])
            self.assertFalse(row['branch']['verified'])

    def test_absent_discovered_graph_is_not_physical_absence(self):
        from validate_eclipse_corpus import finalize_boundaries
        row=dict(quantity='boundary_m',side='north',reference=(0,0),error=None,passed=False)
        finalize_boundaries([row])
        self.assertFalse(row['passed']);self.assertFalse(row['represented_curve_numeric_pass'])
        self.assertEqual(row['global_certificate']['status'],'no_represented_geometry')

if __name__=='__main__':unittest.main()
