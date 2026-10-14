"""Conformance must match declared Unicode data, without skipping failures."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('unicode_review',ROOT/'tools/validate_unicode_text.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)


class FixtureContractTests(unittest.TestCase):
    def test_bidi_stays_pinned_for_every_supported_grapheme_version(self):
        for version in review.GRAPHEMES:
            with self.subTest(version=version):
                contract=review.fixture_contract(version+'.0')
                self.assertEqual(contract['BidiTest.txt'],('15.1.0',*review.FIXTURES['BidiTest.txt']))
                self.assertEqual(contract['BidiCharacterTest.txt'],('15.1.0',*review.FIXTURES['BidiCharacterTest.txt']))
                self.assertEqual(contract['GraphemeBreakTest.txt'][0],version)
                self.assertEqual(len(contract),3)

    def test_unknown_version_fails_instead_of_using_permissive_fallback(self):
        for version in ('14.0.0.0','18.0.0.0','17.1.0.0','bad'):
            with self.subTest(version=version),self.assertRaisesRegex(ValueError,'Unpinned'):
                review.fixture_contract(version)

    def test_all_grapheme_contracts_have_exact_size_and_sha256(self):
        for version,(size,sha) in review.GRAPHEMES.items():
            self.assertGreater(size,80000)
            self.assertEqual(len(sha),64)
            int(sha,16)


if __name__=='__main__':unittest.main()
