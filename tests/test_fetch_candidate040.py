"""Explicit artifact version preserves exact hashes, audit and workflow provenance."""
import hashlib,io,json,sys,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from fetch_release_artifact import validate
class Fetch040(unittest.TestCase):
 def fixture(self):
  sha='a'*40;files={'azimlib-0.4.0-py3-none-any.whl':b'wheel','azimlib-0.4.0.tar.gz':b'sdist'}
  hashes={n:hashlib.sha256(d).hexdigest() for n,d in files.items()}
  run=dict(id=1,repository=dict(full_name='Kernerian/azimlib'),head_sha=sha,status='completed',conclusion='success',path='.github/workflows/candidate-0.4.yml')
  artifact=dict(workflow_run=dict(id=1,head_sha=sha),name='azimlib-0.4.0-unpublished-candidate',expired=False)
  stream=io.BytesIO()
  with zipfile.ZipFile(stream,'w') as z:
   for n,d in files.items():z.writestr('candidate-dist/'+n,d)
   z.writestr('candidate-audits/distribution.json',json.dumps(dict(version='0.4.0',mandatory_dependencies=[],license_expression='BSD-3-Clause AND CC0-1.0',archives=[dict(file=n,sha256=h) for n,h in hashes.items()])))
   for name in ('licenses','privacy-source','privacy-archives'):z.writestr('candidate-audits/'+name+'.json',json.dumps(dict(passed=True)))
  return run,artifact,sha,list(hashes.values()),stream.getvalue(),files
 def test_explicit_040_files_and_hashes(self):
  r,a,s,h,p,f=self.fixture();self.assertEqual(validate(r,a,'Kernerian/azimlib',s,*h,p,version='0.4.0'),f)
 def test_wrong_profile_and_wrong_hash_rejected(self):
  r,a,s,h,p,f=self.fixture()
  with self.assertRaises(AssertionError):validate(r,a,'Kernerian/azimlib',s,*h,p,version='0.3.0')
  with self.assertRaises(AssertionError):validate(r,a,'Kernerian/azimlib',s,'f'*64,h[1],p,version='0.4.0')
 def test_other_sha_or_expired_artifact_rejected(self):
  r,a,s,h,p,f=self.fixture()
  with self.assertRaises(AssertionError):validate(r,a,'Kernerian/azimlib','b'*40,*h,p,version='0.4.0')
  a['expired']=True
  with self.assertRaises(AssertionError):validate(r,a,'Kernerian/azimlib',s,*h,p,version='0.4.0')
if __name__=='__main__':unittest.main()
