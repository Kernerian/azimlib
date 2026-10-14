"""Experimental clock/frame/geometry contracts; never an accuracy certification."""
from dataclasses import replace
from pathlib import Path
import math
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from azimlib._eclipse_ephemeris import EclipseState,EclipseEphemeris,contact_roots
from azimlib._spk import SpkKernel,State
from azimlib._timescales import JulianCoordinate
from azimlib.eclipse import ShadowSphere
from azimlib._frames import Observer


class EphemerisContracts(unittest.TestCase):
    def scene(self,moon=(384000000.,0.,0.)):
        return EclipseState(ShadowSphere.from_xyz((149600000000.,0.,0.),radius_m=695700000.),
            ShadowSphere.from_xyz(moon,radius_m=1737400.),JulianCoordinate(2451545,0,'TT'),JulianCoordinate(2451545,0,'UT1'),'0'*64)

    def test_axis_ellipsoid_intersection_occultation_and_miss(self):
        scene=self.scene();lon,lat=scene.central_point()
        self.assertAlmostEqual(lon,0);self.assertAlmostEqual(lat,0)
        self.assertEqual(scene.solar(Observer(0,0)).classification,'antumbra')
        self.assertEqual(self.scene((360000000.,0.,0.)).solar(Observer(0,0)).classification,'umbra')
        self.assertIsNone(self.scene((384000000.,20000000.,0.)).central_point())
        self.assertFalse(scene.accuracy_validated)

    def test_lunar_convention_is_explicit_and_atmosphere_separate(self):
        scene=self.scene((-384000000.,0.,0.))
        air=scene.lunar_margins(shadow_convention='airless-mean')
        atmosphere=scene.lunar_margins(shadow_convention='danjon-mean')
        self.assertTrue(all(b<a<0 for a,b in zip(air,atmosphere)))
        with self.assertRaises(ValueError):scene.lunar_margins(shadow_convention='auto')

    def test_solar_lunar_limb_presets_do_not_change_physical_state(self):
        scene=self.scene();observer=Observer(0,0)
        physical=scene.solar(observer)
        inner=scene.solar(observer,lunar_limb='nasa-bulletin-internal')
        outer=scene.solar(observer,lunar_limb='nasa-bulletin-external')
        canon=scene.solar(observer,lunar_limb='nasa-canon-external')
        expected=math.degrees(math.asin(6378137.*.272488/(384000000.-6378137.)))
        self.assertAlmostEqual(canon.occulter_radius_degrees,expected,places=12)
        self.assertLess(inner.occulter_radius_degrees,physical.occulter_radius_degrees)
        self.assertGreater(outer.occulter_radius_degrees,physical.occulter_radius_degrees)
        self.assertEqual(inner.source_radius_degrees,physical.source_radius_degrees)
        self.assertEqual(scene.moon.radius_m,1737400.)
        self.assertEqual(scene.central_point(),(0.,0.))
        with self.assertRaises(ValueError):scene.solar(observer,lunar_limb='auto')

    def test_sign_change_roots_and_search_guards(self):
        roots=contact_roots(lambda x:(x-2)*(x-8),0,10,step=.7,tolerance=.0001)
        self.assertEqual(len(roots),2)
        for expected,actual in zip((2.,8.),roots):self.assertLess(abs(expected-actual),.0001)
        self.assertEqual(contact_roots(lambda x:1,0,10),())
        self.assertEqual(contact_roots(lambda x:x,0,10),(0,))
        self.assertEqual(contact_roots(lambda x:x-10,0,10),(10,))
        for kwargs in (dict(step=0),dict(step=.001),dict(tolerance=-1)):
            with self.assertRaises(ValueError):contact_roots(lambda x:x,0,10,**kwargs)
        with self.assertRaises(ValueError):contact_roots(lambda x:float('nan'),0,10)

    def test_independent_solar_limb_convention_preserves_state_and_clocks(self):
        scene=self.scene();observer=Observer(0,0)
        original=scene.solar(observer)
        usno=scene.solar(observer,solar_limb='usno-696000km')
        expected=math.degrees(math.asin(696000000./(149600000000.-6378137.)))
        self.assertAlmostEqual(usno.source_radius_degrees,expected,places=12)
        self.assertGreater(usno.source_radius_degrees,original.source_radius_degrees)
        self.assertEqual(usno.occulter_radius_degrees,original.occulter_radius_degrees)
        self.assertEqual(scene.sun.radius_m,695700000.)
        self.assertEqual(scene.tt.scale,'TT');self.assertEqual(scene.ut1.scale,'UT1')
        with self.assertRaises(ValueError):scene.solar(observer,solar_limb='auto')

    def test_time_scales_are_not_inferred_and_no_accuracy_inherited(self):
        kernel=object.__new__(SpkKernel);kernel.sha256='0'*64
        def state(target,epoch):
            p={399:(0.,0.,0.),10:(149600000000.,0.,0.),301:(384000000.,0.,0.)}[target]
            return State(p,(0.,0.,0.),epoch)
        kernel.state=state;model=EclipseEphemeris(kernel)
        tt=JulianCoordinate(2451545,64,'TT');ut1=JulianCoordinate(2451545,0,'UT1')
        actual=model.at(tt,ut1);self.assertFalse(actual.accuracy_validated)
        self.assertAlmostEqual(math.dist(actual.sun.center.xyz,(0,0,0)),149600000000.,delta=.001)
        with self.assertRaises(ValueError):model.at(ut1,tt)
        with self.assertRaises(ValueError):model.at(tt,JulianCoordinate(2451545,0,'UTC'))
        with self.assertRaises(ValueError):model.at(JulianCoordinate(2451545,300,'TT'),ut1)


if __name__=='__main__':unittest.main()
