"""Fail-closed frozen scientific corpus and complete timed-row parsing."""
import importlib.util,unittest,hashlib,json,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('eclipse_corpus_validation',ROOT/'tools/validate_eclipse_corpus.py')
tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)

class CorpusContracts(unittest.TestCase):
    def test_limits_unchanged(self):
        self.assertEqual(tool.LIMITS,dict(center_m=2000,boundary_m=3000,solar_contact_s=30,lunar_contact_s=60,magnitude=.001,obscuration=.001))
    def test_checked_in_oracles_rejected(self):
        with self.assertRaisesRegex(ValueError,'outside checkout'):tool.frozen(ROOT/'anything.json','0'*64)
    def test_integrity_rejected_before_parsing(self):
        with patch.object(Path,'read_bytes',return_value=b'{}'),self.assertRaisesRegex(ValueError,'integrity'):
            tool.frozen(ROOT.parent/'frozen-oracle.json','0'*64)
    def test_relaxed_limits_and_incomplete_coverage_rejected(self):
        for record,reason in ((dict(limits=dict(tool.LIMITS,center_m=3000)),'limits'),(dict(limits=tool.LIMITS,solar=[],lunar=[]),'coverage')):
            raw=json.dumps(record).encode()
            with patch.object(Path,'read_bytes',return_value=raw),self.assertRaisesRegex(ValueError,reason):
                tool.frozen(ROOT.parent/'frozen-oracle.json',hashlib.sha256(raw).hexdigest())
    def test_timed_rows_preserve_missing_limb_and_midnight(self):
        raw='Delta dummy\n&Delta;T = 70.5\n 00:02    -    -    12 30.0N 042 12.0W    11 20.0N 043 10.0W\n 00:03  10 00.0S 044 00.0W 12 00.0S 045 00.0W 11 00.0S 044 30.0W'
        delta,rows=tool.timed_rows(raw)
        self.assertEqual(delta,70.5);self.assertEqual(len(rows),2);self.assertIsNone(rows[0]['points'][0]);self.assertEqual(rows[0]['seconds'],120)
        self.assertEqual(rows[1]['points'][2],(-44.5,-11))
    def test_duplicate_and_partial_rows_rejected(self):
        row='12:00 10 00.0N 010 00.0W 11 00.0N 011 00.0W 12 00.0N 012 00.0W'
        for raw in ('&Delta;T = 70\n'+row+'\n'+row,'&Delta;T = 70\n12:00 10 00.0N 010 00.0W'):
            with self.subTest(raw=raw),self.assertRaisesRegex(ValueError,'Incomplete|duplicate'):tool.timed_rows(raw)
    def test_explicit_missing_south_is_not_mistaken_for_missing_north(self):
        _,rows=tool.timed_rows('&Delta;T = 42.3\n10:25 76 27.9S 137 03.6W - - 70 42.7S 142 27.4W')
        self.assertIsNone(rows[0]['points'][1]);self.assertIsNotNone(rows[0]['points'][0]);self.assertIsNotNone(rows[0]['points'][2])
    def test_half_missing_coordinate_and_trailing_circumstance_placeholders(self):
        _,rows=tool.timed_rows('&Delta;T = 70\n04:04 - 179 08.9E 01 15.9S 177 10.3E 00 37.4S 178 08.7E\n04:06 01 00.0N 170 00.0E - - - - - - -')
        self.assertIsNone(rows[0]['points'][0]);self.assertIsNone(rows[1]['points'][2]);self.assertEqual(len(rows),2)
    def test_empty_reference_rejected(self):
        with self.assertRaisesRegex(ValueError,'No timed'):tool.timed_rows('&Delta;T = 70.5')
    def test_statistics_keep_extreme_cases(self):
        self.assertEqual(tool.statistics([0,1,2,3,1000])['maximum'],1000)
        self.assertEqual(tool.statistics([])['n'],0)

if __name__=='__main__':unittest.main()
