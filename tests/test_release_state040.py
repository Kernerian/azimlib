"""The final authorization is not publication completion or a CI bypass."""
import sys
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import release_state040 as gate
from audit_candidate040_ci import expected_jobs,extra_jobs

SHA='a'*40
HASHES={'azimlib-0.4.0-py3-none-any.whl':'b'*64,'azimlib-0.4.0.tar.gz':'c'*64}

def checklist(extra_pending=(),checked_final=False):
    deferred=set(gate.DEFERRED);pending=deferred|set(extra_pending)|(set() if checked_final else {'14.08'})
    lines=[f"- [{' ' if (item:=f'{s}.{n:02}') in pending else 'x'}] **{item}** Technical gate" for s in range(1,15) for n in range(1,9)]
    for i,line in enumerate(lines):
        item=line.split('**')[1]
        if item in deferred:lines[i]+='\n  Estado: **ADIADO** ('+item+')'
    count=112-len(pending);active_pending=len(pending)-4
    return f'**{count} concluídos / 4 adiados / {active_pending} pendentes de entrega ou revalidação**\n'+'\n'.join(lines)+''.join(f'\n### Lote {i} — Evidence\n' for i in range(1,15))

def ci(branch='validation/0.4-candidate'):
    result={}
    for w,names in (('tests.yml',expected_jobs()),('candidate-0.4.yml',extra_jobs())):
        run=dict(head_sha=SHA,head_branch=branch,path='.github/workflows/'+w,status='completed',
                 conclusion='success',head_repository=dict(full_name='Kernerian/azimlib'),
                 html_url='https://github.com/Kernerian/azimlib/actions/runs/1')
        result[w]=dict(run=run,jobs=[dict(name=n,head_sha=SHA,status='completed',conclusion='success') for n in names])
    return result

def authorization(execute=False):
    return dict(schema=1,version='0.4.0',state='authorized',candidate_sha=SHA,
                package_sha256=HASHES.copy(),expected_inventory=dict(original=112,completed=107,
                deferred=gate.DEFERRED.copy(),authorized_item='14.08',active_completed=107,active_total=108),
                human_final_acceptance=True,allows_start_14_08=True,considers_14_08_completed=False,
                approval_reference='explicit final human acceptance',visual_acceptance_reference='docs/visual-acceptance-0.4.json',
                publication_execution_permitted=execute)

def observations():
    return dict(version='0.4.0',candidate_sha=SHA,main=dict(ref='refs/heads/main',sha=SHA),ci=ci('main'),
        tag=dict(name='v0.4.0',target_sha=SHA,annotated=True),
        release=dict(id=1,tag_name='v0.4.0',target_sha=SHA,published=True,url='https://github.com/Kernerian/azimlib/releases/tag/v0.4.0'),
        pypi=dict(version='0.4.0',index='https://pypi.org/simple',metadata_hashes=HASHES.copy(),downloaded_hashes=HASHES.copy()),
        clean_install=dict(version='0.4.0',index='https://pypi.org/simple',isolated_environment=True,smoke_passed=True,
                           imports=['azimlib','azimlib.pyplot'],log_sha256='d'*64),
        documentation=dict(version='0.4.0',public=True,links_passed=True,url='https://kernerian.github.io/azimlib/stable/',
                           source_sha=SHA,verified_files=100,audit_sha256='e'*64))

class ReleaseState040(unittest.TestCase):
    def preflight(self,record=None,**kw):
        params=dict(sha=SHA,hashes=HASHES,ci=ci(),expected_branch='validation/0.4-candidate')
        params.update(kw)
        return gate.preflight(checklist(),record,**params)

    def test_pending_without_authorization_is_blocked(self):
        state=gate.status(checklist());self.assertEqual(state['state'],'pending');self.assertFalse(state['preflight_allowed'])
        with self.assertRaises(AssertionError):self.preflight()

    def test_authorized_exact_candidate_and_hashes_permit_preflight_not_completion(self):
        state=self.preflight(authorization());self.assertEqual(state['state'],'authorized')
        self.assertTrue(state['preflight_allowed']);self.assertFalse(state['completed']);self.assertFalse(state['release_published'])
        self.assertEqual(state['active_completed'],107)

    def test_different_authorized_sha_is_rejected(self):
        a=authorization();a['candidate_sha']='f'*40
        with self.assertRaises(AssertionError):self.preflight(a)

    def test_different_hash_or_missing_package_is_rejected(self):
        for change in ('different','missing'):
            a=authorization()
            if change=='different':a['package_sha256']['azimlib-0.4.0.tar.gz']='f'*64
            else:del a['package_sha256']['azimlib-0.4.0.tar.gz']
            with self.subTest(change=change),self.assertRaises(AssertionError):self.preflight(a)

    def test_missing_or_unexpected_deferred_gate_is_rejected(self):
        for old,new in (('Estado: **ADIADO** (2.08)',''),('Estado: **ADIADO** (9.08)','Estado: **ADIADO** (1.08)')):
            with self.assertRaises((AssertionError,ValueError)):
                gate.preflight(checklist().replace(old,new),authorization(),sha=SHA,hashes=HASHES,ci=ci(),expected_branch='validation/0.4-candidate')

    def test_another_active_pending_item_is_rejected(self):
        with self.assertRaises(AssertionError):
            gate.preflight(checklist(('14.07',)),authorization(),sha=SHA,hashes=HASHES,ci=ci(),expected_branch='validation/0.4-candidate')

    def test_completed_checkbox_without_post_evidence_is_invalid(self):
        with self.assertRaises(AssertionError):gate.status(checklist(checked_final=True))
        with self.assertRaises(AssertionError):gate.completed(checklist(),authorization(True),None,sha=SHA,hashes=HASHES)

    def test_complete_validated_post_publication_evidence_completes_only_14_08(self):
        result=gate.completed(checklist(),authorization(True),observations(),sha=SHA,hashes=HASHES)
        self.assertEqual(result['state'],'completed');self.assertEqual(result['active_completed'],108)
        self.assertEqual(result['deferred'],gate.DEFERRED);self.assertTrue(result['release_published'])

    def test_stale_sha_branch_failed_or_incomplete_ci_is_rejected(self):
        for field,value in (('head_sha','f'*40),('head_branch','main'),('status','in_progress'),('conclusion','failure')):
            c=ci();c['tests.yml']['run'][field]=value
            with self.subTest(field=field),self.assertRaises(AssertionError):self.preflight(authorization(),ci=c)
        c=ci();c['candidate-0.4.yml']['jobs'].pop()
        with self.assertRaises(AssertionError):self.preflight(authorization(),ci=c)

    def test_authorized_cannot_claim_completed_or_replace_human_acceptance(self):
        for field,value in (('state','completed'),('considers_14_08_completed',True),('human_final_acceptance',False)):
            a=authorization();a[field]=value
            with self.subTest(field=field),self.assertRaises(AssertionError):self.preflight(a)

    def test_dry_run_authorization_does_not_allow_upload(self):
        with self.assertRaises(AssertionError):self.preflight(authorization(),execute=True,ci=ci('main'),expected_branch='main')
        state=self.preflight(authorization(True),execute=True,ci=ci('main'),expected_branch='main')
        self.assertTrue(state['execution_permitted']);self.assertFalse(state['completed'])

    def test_post_publication_missing_any_category_is_rejected(self):
        for field in ('main','ci','tag','release','pypi','clean_install','documentation'):
            o=observations();del o[field]
            with self.subTest(field=field),self.assertRaises((AssertionError,KeyError)):
                gate.completed(checklist(),authorization(True),o,sha=SHA,hashes=HASHES)

    def test_post_publication_hash_tag_install_or_docs_divergence_is_rejected(self):
        for field,key,value in (('tag','target_sha','f'*40),('main','sha','f'*40),('clean_install','smoke_passed',False),
                                ('documentation','source_sha','f'*40),('documentation','links_passed',False),
                                ('pypi','downloaded_hashes',dict(HASHES,extra='f'*64))):
            o=observations();o[field][key]=value
            with self.subTest(field=field,key=key),self.assertRaises(AssertionError):
                gate.completed(checklist(),authorization(True),o,sha=SHA,hashes=HASHES)

    def test_workflow_default_dry_run_has_no_upload_or_oidc_permission(self):
        import yaml
        w=yaml.safe_load((ROOT/'.github/workflows/publish.yml').read_text('utf8'))
        inputs=w.get('on',w.get(True))['workflow_dispatch']['inputs']
        self.assertTrue(inputs['dry_run']['default']);self.assertTrue(inputs['authorization_ref']['required'])
        self.assertEqual(w['jobs']['build']['permissions'],{'contents':'read','actions':'read'})
        self.assertIn('!inputs.dry_run',w['jobs']['publish']['if'])
        self.assertIn("refs/heads/main",w['jobs']['publish']['if'])
        self.assertEqual(w['jobs']['publish']['needs'],'build')

    def test_preflight_cli_imports_under_isolated_python(self):
        result=subprocess.run([sys.executable,'-I',str(ROOT/'tools/release_preflight040.py'),'--help'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('--authorization-ref',result.stdout)

if __name__=='__main__':unittest.main()
