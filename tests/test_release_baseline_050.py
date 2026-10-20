"""0.5 inherits frozen 0.4 Earth oracles, never a newly favorable screenshot."""
import hashlib,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class SurfaceBaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=ROOT/'tools/check_release_baselines.py'
        spec=importlib.util.spec_from_file_location('baseline050',path);cls.tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.tool)
    def test_explicit_registered_minor_versions(self):
        for version,directory in (('0.3.0','release030'),('0.4.0','release040'),('0.5.0.dev0','release050')):
            self.assertEqual(self.tool.baseline_directory(version).name,directory)
    def test_unknown_version_does_not_fall_back_to_old_release(self):
        for version in ('0.6.0.dev0','1.0.0','unknown'):
            with self.assertRaises(ValueError):self.tool.baseline_directory(version)
    def test_inherited_oracles_and_pixels_are_exact(self):
        old=ROOT/'tools/baselines/release040/manifest.json'
        new=json.loads((ROOT/'tools/baselines/release050/manifest.json').read_text('utf8'))
        self.assertEqual(new['inherited_manifest_sha256'],hashlib.sha256(old.read_bytes()).hexdigest())
        self.assertEqual(new['cases'],json.loads(old.read_text('utf8'))['cases'])
        historical=old.parent.parent/'release050/inherited-verifier/check_release_baselines.py'
        self.assertEqual(hashlib.sha256(historical.read_bytes()).hexdigest(),json.loads(old.read_text('utf8'))['tool_sha256'])
        for name,row in new['cases'].items():
            self.assertEqual(hashlib.sha256((old.parent/(name+'.png')).read_bytes()).hexdigest(),row['png_sha256'])
    def test_verifier_bytes_remain_pinned(self):
        data=json.loads((ROOT/'tools/baselines/release050/manifest.json').read_text('utf8'))
        self.assertEqual(hashlib.sha256((ROOT/'tools/check_release_baselines.py').read_bytes()).hexdigest(),data['tool_sha256'])
    def test_record_cannot_overwrite_reviewed_data(self):
        with tempfile.TemporaryDirectory() as d:
            r=subprocess.run([sys.executable,str(ROOT/'tools/check_release_baselines.py'),'--record','--output',d],capture_output=True,text=True)
            self.assertNotEqual(r.returncode,0);self.assertIn('Reviewed baselines must not be overwritten',r.stderr)


if __name__=='__main__':unittest.main()
