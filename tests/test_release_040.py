"""Fail closed on incomplete 0.4 publication and exact checklist identities."""
import importlib.util,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/f'{name}.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
candidate=load('check_release_candidate');progress=load('check_release_progress_040')
def fixture(pending=(), *, scoped=False):
    lines=[f"- [{' ' if f'{s}.{n:02}' in pending else 'x'}] **{s}.{n:02}** Technical gate" for s in range(1,15) for n in range(1,9)]
    if scoped:
        deferred={'2.08','9.08','13.06','13.07'}
        lines=[line.replace('[x]','[ ]')+'\n  Estado: **ADIADO** ('+item+')' if (item:=line.split('**')[1]) in deferred else line for line in lines]
        return f'**{108-len(pending)} concluídos / 4 adiados / {len(pending)} pendentes de entrega ou revalidação**\n'+'\n'.join(lines)+''.join(f'\n### Lote {s} — Technical evidence\n' for s in range(1,15))
    return f'**{112-len(pending)} concluídos / {len(pending)} pendentes**\n'+'\n'.join(lines)+''.join(f'\n### Lote {s} — Technical evidence\n' for s in range(1,15))
class Delivery040(unittest.TestCase):
    def test_complete_contract(self):
        self.assertEqual(candidate.check('0.4.0',fixture(scoped=True)),'0.4.0');self.assertTrue(progress.check(fixture(),require_complete=True)['release_ready'])
    def test_unannotated_original_and_active_pending_gates_fail_closed(self):
        for item in ('2.08','7.08','8.08','9.08','13.06','13.07','14.04','14.05','14.07','14.08'):
            with self.subTest(item=item),self.assertRaises(AssertionError):candidate.check('0.4.0',fixture((item,)))
    def test_old_or_empty_checklist_cannot_pass_new_release(self):
        for text in ('','\n'.join(f'- [x] **{s}.{n:02}** Gate' for s in range(1,11) for n in range(1,9))):
            with self.assertRaises(AssertionError):candidate.check('0.4.0',text)
    def test_unknown_or_development_version_rejected(self):
        for version in ('0.4.0.dev0','0.4.0rc1','0.5.0','0.6.0','1.0.0'):
            with self.subTest(version=version),self.assertRaises(AssertionError):candidate.check(version,fixture())
    def test_duplicate_reordered_and_wrong_count_rejected(self):
        text=fixture()
        for altered in (text.replace('**1.02**','**1.01**'),text.replace('**1.01**','**99.01**'),text.replace('112 concluídos','111 concluídos'),text.replace('### Lote 14 ','### Other 14 ')):
            with self.assertRaises(ValueError):progress.check(altered)
    def test_pending_development_is_valid_but_not_release(self):
        result=progress.check(fixture(('2.08',)));self.assertFalse(result['release_ready']);self.assertEqual(result['pending'],['2.08'])
        with self.assertRaises(ValueError):progress.check(fixture(('2.08',)),require_complete=True)
    def test_integration_ci_is_manual_read_only_and_has_explicit_platforms(self):
        import yaml
        text=(ROOT/'.github/workflows/integration-0.4.yml').read_text('utf8')
        workflow=yaml.safe_load(text)
        # PyYAML's YAML 1.1 parser represents the unquoted Actions "on" as True.
        self.assertEqual(workflow.get('on',workflow.get(True)),{'workflow_dispatch':None,'workflow_call':None})
        self.assertEqual(workflow['permissions'],{'contents':'read'})
        jobs=workflow['jobs'];self.assertEqual(set(jobs),{'core','native','no-gpu','software-gpu'})
        self.assertEqual(jobs['core']['strategy']['matrix'],{'os':['ubuntu-latest','windows-latest','macos-latest'],'python':['3.10','3.11','3.12','3.13','3.14']})
        for name in ('native','no-gpu'):
            self.assertEqual(jobs[name]['strategy']['matrix']['os'],jobs['core']['strategy']['matrix']['os'])
        self.assertEqual(jobs['software-gpu']['env']['LIBGL_ALWAYS_SOFTWARE'],'1')
        self.assertTrue(any('--gpu-context egl' in step.get('run','') for step in jobs['software-gpu']['steps']))
        for prohibited in ('pypa/gh-action-pypi-publish','actions/deploy-pages','git push','gh release','id-token: write'):
            self.assertNotIn(prohibited,text)
    def test_repository_checklist_is_consistent_without_inferred_acceptance(self):
        text=(ROOT/'docs/release-progress-0.4.md').read_text('utf8')
        result=progress.check(text)
        if not result['release_ready']:
            with self.assertRaises(AssertionError):candidate.check('0.4.0',text)
if __name__=='__main__':unittest.main()
