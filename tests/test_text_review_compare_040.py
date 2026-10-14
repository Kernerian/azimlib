"""Review integrity gates cannot silently become visual acceptance."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('text_review_compare',Path(__file__).resolve().parents[1]/'tools/compare_text_review.py')
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)


class ReviewComparisonTests(unittest.TestCase):
    def packet(self,root,system,source='same'):
        folder=root/system;folder.mkdir()
        files={}
        for name in ('tk.png','qt.png'):
            (folder/name).write_bytes(b'original fixture');files[name]=hashlib.sha256(b'original fixture').hexdigest()
        manifest=dict(stage='7.08',status='awaiting-three-platform-human-approval',system=system,
            source_sha256={'source.py':source},fonts=[{'sha256':'same-font'}],files=files,engines={},
            native=[dict(backend=b,file=b+'.png') for b in ('tk','qt')])
        (folder/'manifest.json').write_text(json.dumps(manifest))
        return folder

    def test_all_platforms_integrity_still_requires_human(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);packets=[self.packet(root,s) for s in ('Windows','Linux','Darwin')]
            result=review.compare(packets)
            self.assertTrue(result['all_platforms_present'])
            self.assertFalse(result['human_approval'])
            self.assertEqual(result['status'],'awaiting-human-review')

    def test_missing_platform_requires_explicit_partial_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet=self.packet(Path(temporary),'Windows')
            with self.assertRaises(ValueError):review.compare([packet])
            result=review.compare([packet],allow_partial=True)
            self.assertFalse(result['all_platforms_present'])
            self.assertFalse(result['human_approval'])

    def test_tampering_and_different_source_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);a=self.packet(root,'Windows');b=self.packet(root,'Linux','changed')
            with self.assertRaises(ValueError):review.compare([a,b],allow_partial=True)
            (a/'tk.png').write_bytes(b'tampered')
            with self.assertRaises(ValueError):review.compare([a],allow_partial=True)
