"""Reject stale/incomplete release evidence and accidental development publication."""
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/(name+'.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
ci=load('ci_contract');candidate=load('check_release_candidate')

class ReleaseGateTests(unittest.TestCase):
    def jobs(self):return [dict(name=name,head_sha='a'*40,status='completed',conclusion='success') for name in ci.expected_jobs()]
    def test_exact_current_matrix(self):self.assertEqual(ci.verify_jobs(self.jobs(),'a'*40),28)
    def test_old_twenty_four_matrix_rejected(self):
        jobs=[j for j in self.jobs() if not j['name'].startswith('qt (') and j['name']!='documentation']
        with self.assertRaises(AssertionError):ci.verify_jobs(jobs,'a'*40)
    def test_duplicate_cannot_replace_required_job(self):
        jobs=self.jobs();jobs[-1]=dict(jobs[0])
        with self.assertRaises(AssertionError):ci.verify_jobs(jobs,'a'*40)
    def test_stale_sha_and_failed_cancelled_job_rejected(self):
        for edit in ({'head_sha':'b'*40},{'conclusion':'failure'},{'conclusion':'cancelled'},{'conclusion':'skipped'},{'status':'queued'}):
            jobs=self.jobs();jobs[0].update(edit)
            with self.subTest(edit=edit),self.assertRaises(AssertionError):ci.verify_jobs(jobs,'a'*40)
    def test_no_development_stable_upload(self):
        for version in ('0.3.0.dev0','0.3.0rc1','0.3.0a1'):
            with self.subTest(version=version),self.assertRaises(AssertionError):candidate.check(version,'')
    def test_native_and_final_acceptance_required(self):
        for pending in ('7.08','10.08'):
            with self.subTest(pending=pending),self.assertRaises(AssertionError):candidate.check('0.3.0',f'- [ ] **{pending}** Gate')
    def test_final_version_without_checklist_rejected(self):
        with self.assertRaises(AssertionError):candidate.check('0.3.0','')
    def test_privacy_network_url_is_not_local_home_path(self):
        privacy=load('publication_privacy')
        url='https://matplotlib.org/stable/users/explain/figure/interactive.html'
        self.assertEqual(privacy.findings(url.encode()),[])
        self.assertEqual(privacy.sanitize_text(url),url)
    def test_privacy_local_and_file_uri_remain_detected(self):
        privacy=load('publication_privacy')
        path='/'+'/'.join(('home','example','data.txt'))
        windows='C:'+chr(92)+chr(92).join(('Users','example','data.txt'))
        for value in (path,'file://'+path,windows):
            with self.subTest(value=value):
                self.assertIn('personal-home-path',privacy.findings(value.encode()))
                self.assertNotEqual(privacy.sanitize_text(value),value)
    def test_documentation_path_escape_rejected(self):
        docs=load('build_documentation')
        with self.assertRaises(ValueError):docs.link_target(ROOT/'docs/index.md','../../../../secret.txt','dev/0.3.0')
    def test_documentation_keeps_fragment_and_source_ref(self):
        docs=load('build_documentation')
        self.assertEqual(docs.link_target(ROOT/'docs/index.md','temporal.md#animation','dev/0.3.0'),'temporal.html#animation')
        self.assertIn('/blob/dev/0.3.0/examples/temporal_atlas.py',docs.link_target(ROOT/'docs/index.md','../examples/temporal_atlas.py','dev/0.3.0'))

if __name__=='__main__':unittest.main()
