"""Scientific conventions remain explicit; no best-fitting automatic radius."""
import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import azimlib as azl
from azimlib._eclipse_ephemeris import EclipseState
from azimlib._timescales import JulianCoordinate
from azimlib._frames import Observer

class Disk(unittest.TestCase):
    def state(self):
        return EclipseState(azl.ShadowSphere.from_xyz((149600000000.,0,0),radius_m=695700000.),azl.ShadowSphere.from_xyz((380000000.,0,0),radius_m=1737400.),JulianCoordinate(2451545,0,'TT'),JulianCoordinate(2451545,0,'UT1'),'0'*64)
    def test_models_metadata_nominal_is_not_photosphere(self):
        self.assertEqual(azl.IAU2015_NOMINAL.radius_m,695700000.)
        self.assertIn('not a measured',azl.IAU2015_NOMINAL.definition)
        self.assertIn('not an inferred GSFC Canon',azl.NASA_SVS_696000.definition)
    def test_typed_comparison_preserves_state_and_selects_no_winner(self):
        state=self.state();observer=Observer(0,0)
        result=state.compare_solar_disks(observer,(azl.IAU2015_NOMINAL,azl.NASA_SVS_696000))
        self.assertEqual(len(result.results),2);self.assertFalse(result.accuracy_validated)
        self.assertGreater(result.results[1][1].source_radius_degrees,result.results[0][1].source_radius_degrees)
        self.assertEqual(state.sun.radius_m,695700000.)
        self.assertEqual(state.solar(observer),state.solar(observer,solar_limb=azl.IAU2015_NOMINAL))
        geometry=azl.EclipseGeometry(state.sun,state.moon,'Synthetic case')
        self.assertEqual(geometry.solar(observer),geometry.solar(observer,solar_disk=azl.IAU2015_NOMINAL))
    def test_bad_models_and_duplicate_names_rejected(self):
        for radius in (0,-1,float('nan'),True):
            with self.assertRaises(ValueError):azl.SolarDiskConvention('explicit',radius,'definition','source')
        state=self.state()
        with self.assertRaises(ValueError):state.compare_solar_disks(Observer(0,0),(azl.IAU2015_NOMINAL,)*2)

    def test_grazing_classification_dependency_is_returned_explicitly(self):
        from dataclasses import replace
        state=self.state();earth=6378137.;dx=360000000.-earth;ds=149600000000.-earth
        mean_sun=(math.asin(695700000./ds)+math.asin(696000000./ds))/2
        lo,hi=0.,1000000.
        for _ in range(70):
            mid=(lo+hi)/2
            margin=math.atan2(mid,dx)-(math.asin(1737400./math.hypot(dx,mid))-mean_sun)
            if margin>0:hi=mid
            else:lo=mid
        state=replace(state,moon=azl.ShadowSphere.from_xyz((360000000.,(lo+hi)/2,0),radius_m=1737400.))
        result=state.compare_solar_disks(Observer(0,0),(azl.IAU2015_NOMINAL,azl.NASA_SVS_696000))
        self.assertTrue(result.classification_sensitive)
        self.assertEqual({r.classification for c,r in result.results},{'umbra','penumbra'})

if __name__=='__main__':unittest.main()
