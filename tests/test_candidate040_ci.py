"""Exact hosted branch/SHA/job identity remains mandatory after rescope."""
import importlib.util,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import audit_candidate040_ci as audit
class CandidateCI(unittest.TestCase):
 def fixture(self,workflow):
  names=audit.expected_jobs() if workflow=='tests.yml' else audit.extra_jobs()
  run=dict(head_sha='a'*40,head_branch='validation/0.4-candidate',path='.github/workflows/'+workflow,status='completed',conclusion='success',head_repository=dict(full_name='Kernerian/azimlib'),html_url='https://github.com/Kernerian/azimlib/actions')
  jobs=[dict(name=n,head_sha='a'*40,status='completed',conclusion='success') for n in names]
  return run,jobs
 def check(self,run,jobs,workflow):return audit.verify(run,jobs,sha='a'*40,branch='validation/0.4-candidate',workflow=workflow)
 def test_both_complete_matrices_same_identity(self):
  for workflow,count in (('tests.yml',28),('candidate-0.4.yml',42)):
   self.assertEqual(self.check(*self.fixture(workflow),workflow)['jobs'],count)
 def test_wrong_branch_sha_or_workflow(self):
  for key,value in (('head_sha','b'*40),('head_branch','main'),('path','.github/workflows/publish.yml'),('conclusion','failure'),('status','in_progress')):
   run,jobs=self.fixture('tests.yml');run[key]=value
   with self.subTest(key=key),self.assertRaises(AssertionError):self.check(run,jobs,'tests.yml')
 def test_missing_duplicate_failed_skipped_or_other_sha_job(self):
  for workflow in ('tests.yml','candidate-0.4.yml'):
   run,jobs=self.fixture(workflow)
   for changed in (jobs[:-1],jobs+[jobs[0]],[dict(j,conclusion='skipped') if i==0 else j for i,j in enumerate(jobs)],[dict(j,head_sha='b'*40) if i==0 else j for i,j in enumerate(jobs)]):
    with self.assertRaises(AssertionError):self.check(run,changed,workflow)
if __name__=='__main__':unittest.main()
