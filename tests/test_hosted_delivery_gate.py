"""Release context gates: explicit branch, exact SHA and all 28 job identities."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('hosted_delivery_gate',ROOT/'tools/audit_hosted_delivery.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
from ci_contract import expected_jobs

class HostedDeliveryGateTests(unittest.TestCase):
    def setUp(self):
        self.sha='1'*40
        self.run={'repository':{'full_name':'Kernerian/azimlib'},'event':'push',
                  'head_branch':'dev/0.3.0','head_sha':self.sha,'status':'completed','conclusion':'success'}
        self.jobs=[{'name':name,'head_sha':self.sha,'status':'completed','conclusion':'success'} for name in sorted(expected_jobs())]

    def check(self,branch,run=None,jobs=None):
        return gate.verify_delivery_context(self.run if run is None else run,
            self.jobs if jobs is None else jobs,self.sha,expected_branch=branch)

    def test_candidate_branch(self):
        self.assertEqual(self.check('dev/0.3.0'),28)

    def test_final_main_branch(self):
        self.run['head_branch']='main'
        self.assertEqual(self.check('main'),28)

    def test_branch_mismatch(self):
        for expected,actual in (('main','dev/0.3.0'),('dev/0.3.0','main'),('main','feature/other')):
            with self.subTest(expected=expected,actual=actual):
                self.run['head_branch']=actual
                with self.assertRaises(AssertionError):self.check(expected)

    def test_exact_run_and_job_sha(self):
        changed=copy.deepcopy(self.run);changed['head_sha']='2'*40
        with self.assertRaises(AssertionError):self.check('dev/0.3.0',run=changed)
        jobs=copy.deepcopy(self.jobs);jobs[0]['head_sha']='2'*40
        with self.assertRaises(AssertionError):self.check('dev/0.3.0',jobs=jobs)

    def test_incomplete_or_unsuccessful_jobs(self):
        with self.assertRaises(AssertionError):self.check('dev/0.3.0',jobs=self.jobs[:-1])
        jobs=copy.deepcopy(self.jobs);jobs[-1]=copy.deepcopy(jobs[0])
        with self.assertRaises(AssertionError):self.check('dev/0.3.0',jobs=jobs)
        jobs=copy.deepcopy(self.jobs);jobs[0]['name']='Unexpected job'
        with self.assertRaises(AssertionError):self.check('dev/0.3.0',jobs=jobs)
        for outcome in ('failure','cancelled','timed_out','skipped',None):
            with self.subTest(outcome=outcome):
                jobs=copy.deepcopy(self.jobs);jobs[0]['conclusion']=outcome
                with self.assertRaises(AssertionError):self.check('dev/0.3.0',jobs=jobs)
        jobs=copy.deepcopy(self.jobs);jobs[0]['status']='in_progress'
        with self.assertRaises(AssertionError):self.check('dev/0.3.0',jobs=jobs)

    def test_unsuccessful_run(self):
        for field,value in (('status','in_progress'),('conclusion','failure'),('conclusion',None)):
            with self.subTest(field=field,value=value):
                changed=copy.deepcopy(self.run);changed[field]=value
                with self.assertRaises(AssertionError):self.check('dev/0.3.0',run=changed)

    def test_repository_and_event_provenance(self):
        changed=copy.deepcopy(self.run);changed['repository']['full_name']='other/azimlib'
        with self.assertRaises(AssertionError):self.check('dev/0.3.0',run=changed)
        changed=copy.deepcopy(self.run);changed['event']='workflow_dispatch'
        with self.assertRaises(AssertionError):self.check('dev/0.3.0',run=changed)

    def test_branch_argument_is_required(self):
        with self.assertRaises(TypeError):gate.verify_delivery_context(self.run,self.jobs,self.sha)
        for branch in ('',None,['main','dev/0.3.0'],' dev/0.3.0 '):
            with self.subTest(branch=branch):
                with self.assertRaises(AssertionError):self.check(branch)

if __name__=='__main__':unittest.main()
