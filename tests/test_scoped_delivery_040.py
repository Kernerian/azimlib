"""0.4 scoped acceptance never substitutes CI or human/final authorization."""
import importlib.util,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name):
 s=importlib.util.spec_from_file_location(name,ROOT/'tools'/f'{name}.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
candidate=load('check_release_candidate');progress=load('check_release_progress_040')
D={'2.08','9.08','13.06','13.07'}
def text(pending=()):
 pending=set(pending);lines=[f"- [{' ' if (item:=f'{s}.{i:02}') in D|pending else 'x'}] **{item}** Criterion" for s in range(1,15) for i in range(1,9)]
 return f'**{108-len(pending)} concluídos / 4 adiados / {len(pending)} pendentes de entrega ou revalidação**\n'+'\n'.join(lines)+'\n'+'\n'.join(f'  Estado: **ADIADO** ({i})' for i in sorted(D))+'\n'+'\n'.join(f'### Lote {s} — Evidence' for s in range(1,15))
class ScopedDelivery(unittest.TestCase):
 def test_exact_108_active_and_four_preserved_deferments(self):
  # Inventory completion alone must not stand in for post-publication evidence.
  with self.assertRaises(AssertionError):candidate.check('0.4.0',text())
  self.assertTrue(progress.check(text(),require_complete=True)['release_ready'])
 def test_preparation_is_separate_and_never_final_acceptance(self):
  p=text(('14.04','14.05','14.07','14.08'))
  self.assertEqual(candidate.check('0.4.0',p,purpose='prepare'),'0.4.0')
  with self.assertRaises(AssertionError):candidate.check('0.4.0',p)
 def test_each_active_gate_still_blocks_publication(self):
  for s in range(1,15):
   for i in range(1,9):
    item=f'{s}.{i:02}'
    if item in D:continue
    with self.subTest(item=item),self.assertRaises(AssertionError):candidate.check('0.4.0',text((item,)))
 def test_preparation_cannot_skip_regression_docs_benchmark_or_audit(self):
  for item in ('1.01','14.01','14.02','14.03','14.06'):
   with self.subTest(item=item),self.assertRaises(AssertionError):candidate.check('0.4.0',text((item,)),purpose='prepare')
 def test_no_unknown_or_missing_deferment(self):
  for changed in (text().replace('ADIADO** (9.08)','ADIADO** (14.04)'),text().replace('  Estado: **ADIADO** (9.08)','')):
   with self.assertRaises(AssertionError):candidate.check('0.4.0',changed)
 def test_checked_deferment_and_wrong_totals_rejected(self):
  for changed in (text().replace('- [ ] **2.08**','- [x] **2.08**'),text().replace('108 concluídos','112 concluídos')):
   with self.assertRaises(AssertionError):candidate.check('0.4.0',changed)
 def test_wrong_purpose_or_prerelease_rejected(self):
  for purpose in ('auto','skip','release'):
   with self.assertRaises(AssertionError):candidate.check('0.4.0',text(),purpose=purpose)
  with self.assertRaises(AssertionError):candidate.check('0.4.0rc1',text(),purpose='prepare')
 def test_legacy_112_claim_cannot_publish_040(self):
  old=text().replace('108 concluídos / 4 adiados / 0 pendentes de entrega ou revalidação','112 concluídos / 0 pendentes')
  old=re.sub(r'^  Estado:.*\n','',old,flags=re.M).replace('[ ]','[x]')
  with self.assertRaises(AssertionError):candidate.check('0.4.0',old)
if __name__=='__main__':unittest.main()
