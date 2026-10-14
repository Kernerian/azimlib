"""Analytic fixtures, explicit failure contracts and existing facade regressions."""
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import io
import math
from pathlib import Path
import re
import unittest

import azimlib as azl
import azimlib.pyplot as plt
from azimlib._contracts import ResourceBudget, linear_error_bound
from azimlib._frames import (Body, Coordinates, EARTH, EARTH_FIXED, GEODETIC,
                             GeodeticFrame, Observer, ReferenceFrame, RigidTransform)
from azimlib._timescales import Instant, JulianCoordinate, TimeOffsets
from azimlib.renderers import get_capabilities
from azimlib.terrain3d import LocalFrame

ROOT = Path(__file__).resolve().parents[1]
UTC = timezone.utc


class FramesTests(unittest.TestCase):
    def assertVector(self, actual, expected, tolerance=1e-7):
        self.assertEqual(len(actual), len(expected))
        for a, b in zip(actual, expected):
            self.assertAlmostEqual(a, b, delta=tolerance)

    def test_wgs84_cardinal_axes(self):
        a, b = 6378137., 6356752.314245179
        for lon, lat, h, expected in ((0, 0, 0, (a, 0, 0)),
                                      (90, 0, 100, (0, a+100, 0)),
                                      (-90, 0, 0, (0, -a, 0)),
                                      (180, 0, 0, (-a, 0, 0)),
                                      (0, 90, 0, (0, 0, b)),
                                      (0, -90, 0, (0, 0, -b))):
            with self.subTest(lon=lon, lat=lat):
                self.assertVector(GEODETIC.to_fixed(lon, lat, h).xyz, expected)

    def test_oblique_analytic_fixture(self):
        # Independently derived with Decimal and sin(45)=cos(45)=sqrt(1/2).
        import json
        fixture = json.loads((ROOT/'tests/fixtures/foundation-040.json').read_text('utf8'))
        self.assertEqual(fixture['license'], 'BSD-3-Clause')
        for case in fixture['geodetic']:
            with self.subTest(case=case['name']):
                self.assertVector(GEODETIC.to_fixed(*case['input']).xyz, case['xyz_metres'])

    def test_global_roundtrip_including_poles_height_and_antimeridian(self):
        for lon in (-180, -145, -46.63, 0, 90, 180):
            for lat in (-90, -89.9999, -23.55, 0, 45, 89.9999, 90):
                for h in (-10000, 0, 1234, 35786000):
                    with self.subTest(lon=lon, lat=lat, h=h):
                        result = GEODETIC.from_fixed(GEODETIC.to_fixed(lon, lat, h))
                        if abs(lat) < 90:
                            self.assertAlmostEqual(result[0], lon, delta=1e-10)
                        self.assertAlmostEqual(result[1], lat, delta=1e-10)
                        self.assertAlmostEqual(result[2], h, delta=1e-7)

    def test_sphere_reuses_same_frame_system(self):
        frame = GeodeticFrame(ReferenceFrame('sphere fixed', Body('analytic sphere', azl.Ellipsoid(1000000, 0))))
        self.assertVector(frame.to_fixed(0, 0, 50).xyz, (1000050, 0, 0))
        self.assertVector(frame.from_fixed(frame.to_fixed(25, 45, 500)), (25, 45, 500))

    def test_geodetic_invalid_inputs_and_wrong_frames(self):
        for values in ((181, 0), (0, 91), (0, 0, -10001), (True, 0), (0, math.inf)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                GEODETIC.to_fixed(*values)
        with self.assertRaises(ValueError):
            GEODETIC.from_fixed(Coordinates((0, 0, 0)))
        with self.assertRaises(ValueError):
            GEODETIC.from_fixed(Coordinates((6378137, 0, 0), ReferenceFrame('other')))
        with self.assertRaises(ValueError):
            GeodeticFrame(ReferenceFrame('ENU', kind='local'))
        with self.assertRaises(ValueError):
            GEODETIC.from_fixed(Coordinates((1.7e308, 1.7e308, 1.7e308)))

    def test_frame_models_validate_and_freeze(self):
        with self.assertRaises(ValueError):
            Body('', azl.WGS84)
        with self.assertRaises(TypeError):
            ReferenceFrame('wrong', 'Earth')
        with self.assertRaises(ValueError):
            Coordinates((1, 2))
        with self.assertRaises(FrozenInstanceError):
            EARTH.name = 'changed'

    def test_rigid_composition_inverse_and_vector_translation(self):
        b, c = ReferenceFrame('b'), ReferenceFrame('c')
        first = RigidTransform(EARTH_FIXED, b, (0, -1, 0, 1, 0, 0, 0, 0, 1), (10, 20, 30))
        second = RigidTransform(b, c, translation=(3, 5, 7))
        point = Coordinates((2, 3, 4))
        self.assertVector(first.apply(point).xyz, (7, 22, 34))
        self.assertVector(first.apply(point, direction=True).xyz, (-3, 2, 4))
        composed = first.then(second)
        self.assertEqual(composed.apply(point), second.apply(first.apply(point)))
        self.assertVector(composed.inverse().apply(composed.apply(point)).xyz, point.xyz)

    def test_rigid_rejects_reflection_scaling_mismatches(self):
        b = ReferenceFrame('b')
        for rotation in ((-1, 0, 0, 0, 1, 0, 0, 0, 1), (2, 0, 0, 0, 1, 0, 0, 0, 1), (1, 2)):
            with self.subTest(rotation=rotation), self.assertRaises(ValueError):
                RigidTransform(EARTH_FIXED, b, rotation)
        with self.assertRaises(ValueError):
            RigidTransform(EARTH_FIXED, ReferenceFrame('other', Body('other', azl.GRS80)))
        with self.assertRaises(ValueError):
            RigidTransform(EARTH_FIXED, b).apply(Coordinates((1, 2, 3), b))
        with self.assertRaises(ValueError):
            RigidTransform(EARTH_FIXED, b).then(RigidTransform(EARTH_FIXED, b))

    def test_observer_enu_parallax_and_manual_angles(self):
        observer = Observer(0, 0, 100, horizon=5)
        self.assertVector(observer.to_local.apply(observer.fixed_position).xyz, (0, 0, 0))
        for az, el in ((0, 0), (90, 0), (180, -10), (270, 45)):
            with self.subTest(az=az):
                local = observer.local_direction(az, el)
                fixed = observer.to_local.inverse().apply(local, direction=True)
                self.assertVector(observer.azimuth_elevation(fixed, direction=True), (az, el))
                self.assertEqual(observer.above_horizon(fixed, direction=True), el >= 5)
        az, el = observer.azimuth_elevation(Coordinates((6378337, 0, 0)))
        self.assertIsNone(az)
        self.assertEqual(el, 90)
        with self.assertRaises(ValueError):
            observer.azimuth_elevation(observer.fixed_position)

    def test_local_terrain_preserves_zero_height_contract(self):
        # Analytic old ENU expression is retained here as a regression oracle.
        for lon, lat in ((0, 0), (-46, -23), (179.9, 45)):
            frame = LocalFrame(lon, lat)
            observer = Observer(lon, lat)
            self.assertVector(frame.horizontal(lon, lat), (0, 0))
            for dl, dp in ((.01, 0), (0, .01), (-.02, -.02)):
                source = GEODETIC.to_fixed(lon+dl, lat+dp).xyz
                origin = observer.fixed_position.xyz
                d = [s-o for s, o in zip(source, origin)]
                l, p = math.radians(lon), math.radians(lat)
                expected = (-math.sin(l)*d[0]+math.cos(l)*d[1],
                            -math.sin(p)*math.cos(l)*d[0]-math.sin(p)*math.sin(l)*d[1]+math.cos(p)*d[2])
                self.assertVector(frame.horizontal(lon+dl, lat+dp), expected, 2e-9)
            self.assertIs(frame._to_local, frame._to_local)


class TimeTests(unittest.TestCase):
    def setUp(self):
        self.start = datetime(2000, 1, 1, tzinfo=UTC)
        self.offsets = TimeOffsets(self.start, self.start+timedelta(days=1),
                                   'Azimlib synthetic offset fixture', 32, .25, .001)

    def test_j2000_noon_calendar_anchor(self):
        value = Instant(datetime(2000, 1, 1, 12, tzinfo=UTC))
        self.assertEqual(value.coordinate().jd_parts, (2451545, 0))
        self.assertEqual(value.coordinate('TT', offsets=self.offsets).seconds, 64.184)
        self.assertEqual(value.coordinate('TAI', offsets=self.offsets).seconds, 32)
        self.assertEqual(value.coordinate('UT1', offsets=self.offsets).seconds, .25)

    def test_timezone_normalizes_and_naive_is_rejected(self):
        value = Instant(datetime(2000, 1, 1, 9, tzinfo=timezone(timedelta(hours=-3))))
        self.assertEqual(value.utc.hour, 12)
        for dt in (datetime(2000, 1, 1), datetime(1971, 1, 1, tzinfo=UTC)):
            with self.assertRaises(ValueError):
                Instant(dt)

    def test_validity_end_is_exclusive_and_offsets_required(self):
        instant = Instant(self.start)
        with self.assertRaises(ValueError):
            instant.coordinate('TT')
        with self.assertRaises(ValueError):
            Instant(self.offsets.end).coordinate('TT', offsets=self.offsets)
        only_tai = TimeOffsets(self.start, self.offsets.end, 'synthetic', tai_minus_utc=32)
        with self.assertRaises(ValueError):
            instant.coordinate('UT1', offsets=only_tai)
        only_ut1 = TimeOffsets(self.start, self.offsets.end, 'synthetic', ut1_minus_utc=0)
        with self.assertRaises(ValueError):
            instant.coordinate('TT', offsets=only_ut1)

    def test_invalid_offsets_and_scale(self):
        for kwargs in ({'tai_minus_utc': True}, {'tai_minus_utc': 32.1}, {'ut1_minus_utc': 2},
                       {'ut1_minus_utc': math.nan}, {'uncertainty_seconds': -1}, {}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                TimeOffsets(self.start, self.offsets.end, 'synthetic', **kwargs)
        with self.assertRaises(ValueError):
            TimeOffsets(self.start, self.start, 'synthetic', 32)
        with self.assertRaises(ValueError):
            TimeOffsets(self.start, self.offsets.end, '', 32)
        with self.assertRaises(ValueError):
            Instant(self.start).coordinate('TDB')

    def test_split_precision_day_normalization_and_scale_identity(self):
        first = Instant(datetime(2000, 1, 1, 23, 59, 59, 999998, UTC))
        second = Instant(datetime(2000, 1, 1, 23, 59, 59, 999999, UTC))
        delta = second.coordinate('TT', offsets=self.offsets).seconds_since(first.coordinate('TT', offsets=self.offsets))
        self.assertAlmostEqual(delta, .000001, delta=3e-11)
        self.assertEqual(JulianCoordinate(2451545, -1, 'TT').jd_parts,
                         (2451544, 86399/86400))
        for other in (JulianCoordinate(2451545, 0, 'UTC'), JulianCoordinate(2451545, 0, 'UT1')):
            with self.assertRaises(ValueError):
                other.seconds_since(other)
        with self.assertRaises(ValueError):
            JulianCoordinate(2451545, 0, 'TT').seconds_since(JulianCoordinate(2451545, 0, 'TAI'))

    def test_elapsed_seconds_across_synthetic_leap_offset_change(self):
        boundary = self.offsets.end
        before = Instant(boundary-timedelta(seconds=1))
        after = Instant(boundary)
        next_offsets = TimeOffsets(boundary, boundary+timedelta(days=1), 'synthetic leap', 33)
        elapsed = after.coordinate('TAI', offsets=next_offsets).seconds_since(before.coordinate('TAI', offsets=self.offsets))
        self.assertEqual(elapsed, 2)

    def test_existing_temporal_naive_policy_is_unchanged(self):
        series = azl.TemporalSeries([datetime(2000, 1, 1), datetime(2000, 1, 2)], [1, 2])
        self.assertEqual(series.unit, 'UTC')
        self.assertEqual(series[0].time.tzinfo, UTC)


class ContractsTests(unittest.TestCase):
    def tearDown(self):
        plt.close('all')

    def test_time_units_preserve_dimension_validation(self):
        self.assertEqual(azl.DAY.convert(2, azl.SECOND), 172800)
        self.assertEqual(azl.SECOND.convert(43200, azl.DAY), .5)
        with self.assertRaises(ValueError):
            azl.SECOND.convert(1, azl.METRE)

    def test_local_linear_error_bound_is_conservative(self):
        self.assertEqual(linear_error_bound(((1, -2), (0, 3)), (.1, .2)), (.5, .6000000000000001))
        for matrix, bounds in ((((1,),), (1, 2)), (((1,),), (-1,)), ((), (1,))):
            with self.assertRaises(ValueError):
                linear_error_bound(matrix, bounds)

    def test_budget_boundaries_without_allocations(self):
        budget = ResourceBudget(10, 1024)
        budget.check(items=10, bytes_used=1024)
        for values in ({'items': 11}, {'bytes_used': 1025}, {'items': -1}, {'items': True}):
            with self.assertRaises(ValueError):
                budget.check(**values)
        with self.assertRaises(ValueError):
            ResourceBudget(1, 0)

    def test_renderer_capabilities_are_honest_and_immutable(self):
        for name in ('svg', 'png', 'pdf'):
            caps = get_capabilities(name)
            self.assertFalse(caps.gpu)
            self.assertEqual(caps.volumes,name!='svg' or __import__('importlib.util').util.find_spec('PIL') is not None)
            self.assertFalse(caps.complex_shaping)
            self.assertEqual(caps.vector_output, name != 'png')
            if caps.available:
                self.assertIs(caps.require('terrain_depth', 'raster_images'), caps)
                with self.assertRaises(NotImplementedError):
                    caps.require('gpu')
                with self.assertRaises(ValueError):
                    caps.require('made_up')
            with self.assertRaises(FrozenInstanceError):
                caps.gpu = True
        with self.assertRaises(ValueError):
            get_capabilities('GPU')

    def test_shared_root_pyplot_state_clean_defaults_edit_and_export(self):
        fig, ax = azl.subplots(figsize=(3, 2), dpi=100)
        self.assertIs(plt.gcf(), fig)
        line, = plt.plot([-48, -47], [-24, -23], label='route')
        self.assertIs(line.axes, ax)
        line.set_visible(False)
        self.assertFalse(line.get_visible())
        line.set_visible(True)
        ax.set_title('Foundation regression')
        stream = io.StringIO()
        fig.savefig(stream, format='svg')
        self.assertIn('<svg', stream.getvalue())
        self.assertNotIn('minimap', stream.getvalue().lower())
        stream = io.BytesIO()
        fig.savefig(stream, format='pdf')
        self.assertTrue(stream.getvalue().startswith(b'%PDF'))
        line.remove()
        self.assertIsNone(line.axes)

    def test_checklist_counts_stable_ids_and_evidence(self):
        text = (ROOT/'docs/release-progress-0.4.md').read_text('utf8')
        entries = re.findall(r'^- \[([ x])\] \*\*(\d+\.\d{2})\*\* ', text, re.M)
        self.assertEqual([item for _, item in entries], [f'{s}.{i:02}' for s in range(1, 15) for i in range(1, 9)])
        count = sum(mark == 'x' for mark, _ in entries)
        deferred = set(re.findall(r'Estado: \*\*ADIADO\*\* \((\d+\.\d{2})\)', text))
        revalidate = set(re.findall(r'Estado: \*\*REVALIDAÇÃO FINAL\*\* \((\d+\.\d{2})\)', text))
        self.assertEqual(deferred, {'2.08', '9.08', '13.06', '13.07'})
        self.assertTrue(revalidate <= {'14.01', '14.06'})
        pending = {item for mark, item in entries if mark == ' '} - deferred
        self.assertTrue(pending <= {f'14.{i:02}' for i in range(1, 9)})
        self.assertIn('14.08', pending)
        self.assertEqual(count + len(pending), 108)
        self.assertIn(f'**{count} concluídos / {len(deferred)} adiados / {len(pending)} pendentes de entrega ou revalidação**', text)
        for step in range(1, 15):
            if any(mark == 'x' and item.startswith(f'{step}.') for mark, item in entries):
                self.assertIn(f'### Lote {step} ', text)


if __name__ == '__main__':
    unittest.main()
