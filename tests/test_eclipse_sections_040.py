"""Known cone/sphere branch counts; exact polynomial multiplicities and seams."""
import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from eclipse_cone_sections import ConeSections,isolate_real_roots

class Sections(unittest.TestCase):
    def test_sturm_counts_hidden_close_and_multiple_roots(self):
        for coefficients,count,repeated in (([4,0,-5,0,1],4,False),([1,-2,1],1,True),([-1,0,1],2,False),([1,0,1],0,False),([0,1],1,False)):
            result=isolate_real_roots(coefficients)
            self.assertEqual(len(result['brackets']),count);self.assertEqual(result['repeated'],repeated)

    def test_two_closed_branches_known_shape_no_seeds(self):
        slope=.2;model=ConeSections((0,0,3),(0,0,-1),slope,axes=(1,1,1));components=model.components(65)
        self.assertEqual(len(components),2)
        # r^2 = slope^2 (z-3)^2, r^2+z^2=1.
        A=1+slope*slope;B=-6*slope*slope;C=9*slope*slope-1
        expected=sorted(((-B-math.sqrt(B*B-4*A*C))/(2*A),(-B+math.sqrt(B*B-4*A*C))/(2*A)))
        actual=sorted(sum(p[2] for p in component)/len(component) for component in components)
        for a,b in zip(actual,expected):self.assertAlmostEqual(a,b,places=12)
        for component in components:
            self.assertLess(math.dist(component[0],component[-1]),1e-12)
            for point in component:self.assertAlmostEqual(sum(x*x for x in point),1,places=12)
        self.assertFalse(model.contract()['event_envelope_complete'])

    def test_no_intersection_is_distinct_from_numerical_failure(self):
        # Cone larger than the sphere's angular radius has no surface section.
        model=ConeSections((0,0,3),(0,0,-1),.5,axes=(1,1,1))
        self.assertEqual(model.components(),())
        with self.assertRaises(ArithmeticError):model.intersections(0)

    def test_oblique_section_covers_both_intersections_without_north_south(self):
        model=ConeSections((0,0,3),(.25,0,-1),.2,axes=(1,1,1))
        components=model.components(65);self.assertTrue(components)
        for component in components:
            for p in component:self.assertAlmostEqual(sum(x*x for x in p),1,places=10)
        self.assertTrue(model.contract()['all_represented_polynomial_roots_isolated'])

    def test_invalid_data_and_limits(self):
        with self.assertRaises(ValueError):ConeSections((0,0,3),(0,0,0),.2)
        with self.assertRaises(ValueError):ConeSections((0,0,3),(0,0,-1),-.2)
        with self.assertRaises(ValueError):ConeSections((0,0,3),(0,0,-1),.2,axes=(1,0,1))

    def test_small_branch_birth_and_death_near_tangency(self):
        critical=math.tan(math.atan(.6)-math.asin(1/3))
        absent=ConeSections((0,0,3),(.6,0,-1),critical-1e-6,axes=(1,1,1))
        present=ConeSections((0,0,3),(.6,0,-1),critical+1e-6,axes=(1,1,1))
        self.assertEqual(absent.components(),())
        curves=present.components(33);self.assertEqual(len(curves),1)
        self.assertEqual(len(present.isolation['brackets']),2)
        self.assertLess(math.dist(curves[0][0],curves[0][-1]),1e-6)
        for point in curves[0]:
            self.assertAlmostEqual(sum(v*v for v in point),1,places=10)
            q=[v-a for v,a in zip(point,present.apex)];z=sum(v*a for v,a in zip(q,present.axis))
            self.assertAlmostEqual(sum(v*v for v in q)-(1+present.slope**2)*z*z,0,places=10)

    def test_identical_tangent_circle_not_two_spurious_loops(self):
        model=ConeSections((0,0,5),(0,0,-1),.75,axes=(3,3,3))
        self.assertTrue(model.identically_tangent);self.assertEqual(len(model.components(33)),1)
        self.assertFalse(model.contract()['all_represented_polynomial_roots_isolated'])
        self.assertTrue(model.contract()['singular_topology'])

    def test_cartesian_seam_does_not_split_a_closed_component(self):
        model=ConeSections((0,0,3),(0,0,-1),.2,axes=(1,1,1))
        curve=model.components(65)[0]
        longitudes=[math.degrees(math.atan2(p[1],p[0])) for p in curve]
        self.assertTrue(any(abs(a-b)>180 for a,b in zip(longitudes,longitudes[1:])))
        self.assertEqual(len(model.components(65)),2)

if __name__=='__main__':unittest.main()
