"""Inventory honesty and immutable deferred criteria, not final release acceptance."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]


def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'tools'/f'{name}.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


progress=load('check_release_progress_040')
candidate=load('check_release_candidate')


class Rescope040(unittest.TestCase):
    def setUp(self):
        self.text=(ROOT/'docs/release-progress-0.4.md').read_text('utf8')
        self.registry=json.loads((ROOT/'docs/deferred-gates-0.4.json').read_text('utf8'))

    def test_exact_inventory_and_final_revalidation_counts(self):
        result=progress.check(self.text)
        self.assertEqual(result['total'],112);self.assertEqual(result['completed'],108-len(result['pending']))
        self.assertEqual(result['active_total'],108)
        self.assertEqual(result['deferred'],['2.08','9.08','13.06','13.07'])
        self.assertTrue(set(result['pending']) <= {f'14.{i:02}' for i in range(1,9)})
        self.assertIn('14.08',result['pending'])
        self.assertTrue(set(result['revalidation_required']) <= {'14.01','14.06'})
        self.assertFalse(result['active_scope_complete']);self.assertFalse(result['release_ready'])

    def test_every_original_title_and_id_is_unchanged(self):
        def titles(text):return re.findall(r'^- \[[ x]\] \*\*(\d+\.\d{2})\*\* (.+)$',text,re.M)
        old=(ROOT/self.registry['historical_checklist']['path']).read_text('utf8')
        self.assertEqual(titles(old),titles(self.text));self.assertEqual(len(titles(old)),112)
        self.assertEqual(self.registry['historical_completed'],102)

    def test_historical_snapshot_and_frozen_contracts_match_original_hashes(self):
        for record in [self.registry['historical_checklist'],*self.registry['historical_contracts'],*self.registry['copied_frozen_contracts']]:
            with self.subTest(path=record['path']):
                self.assertEqual(hashlib.sha256((ROOT/record['path']).read_bytes()).hexdigest(),record['sha256'])
        source_hashes={r['evidence_key']:r['sha256'] for r in self.registry['external_evidence']}
        self.assertEqual(source_hashes['eclipse-global-budget-frozen.json'],hashlib.sha256((ROOT/'docs/deferred-eclipse-budget-0.4.json').read_bytes()).hexdigest())
        self.assertEqual(source_hashes['round8/benchmark-protocol-frozen.json'],hashlib.sha256((ROOT/'docs/deferred-gpu-protocol-0.4.json').read_bytes()).hexdigest())

    def test_deferred_criteria_are_original_and_not_completed(self):
        original=dict(re.findall(r'^- \[[ x]\] \*\*(\d+\.\d{2})\*\* (.+)$',self.text,re.M))
        self.assertEqual({r['id'] for r in self.registry['gates']},progress.DEFERRED_040)
        for record in self.registry['gates']:
            self.assertEqual(record['original_criterion'],original[record['id']])
            self.assertEqual(hashlib.sha256(record['original_criterion'].encode()).hexdigest(),record['original_criterion_sha256'])
            self.assertFalse(record['completed']);self.assertEqual(record['status'],'deferred')

    def test_budgets_and_protocol_are_not_relaxed(self):
        self.assertEqual(self.registry['gpu_limits'],dict(exact_frame_p95_ms=33,complete_response_ms=100,physical_arm64_gpu_required=True))
        self.assertEqual(self.registry['scientific_limits'],dict(centers_m=2000,boundaries_m=3000,solar_contacts_s=30,lunar_contacts_s=60,magnitude=.001,obscuration=.001))
        protocol=json.loads((ROOT/'docs/deferred-gpu-protocol-0.4.json').read_text())
        self.assertEqual((protocol['repetitions'],protocol['frames_per_phase'],protocol['warmup_frames_per_phase']),(5,120,24))

    def test_scoped_status_cannot_silently_defer_any_other_id(self):
        changed=self.text.replace('Estado: **ADIADO** (9.08)','Estado: **ADIADO** (14.04)')
        with self.assertRaises(ValueError):progress.check(changed)
        with self.assertRaises(ValueError):progress.check(self.text+'\n  Estado: **REVALIDAÇÃO FINAL** (1.01)\n')

    def test_deferred_or_unrevalidated_item_cannot_be_checked(self):
        for item in ('2.08','9.08','13.06','13.07',*progress.check(self.text)['revalidation_required']):
            with self.subTest(item=item),self.assertRaises(ValueError):
                progress.check(self.text.replace(f'- [ ] **{item}**',f'- [x] **{item}**'))

    def test_wrong_counts_and_duplicate_statuses_are_rejected(self):
        for text in (re.sub(r'\d+ concluídos', '999 concluídos', self.text, count=1),
                     self.text.replace('4 adiados','3 adiados',1),
                     self.text+'\n  Estado: **ADIADO** (9.08)\n'):
            with self.assertRaises(ValueError):progress.check(text)

    def test_strict_publication_still_rejects_rescoped_development(self):
        with self.assertRaises(ValueError):progress.check(self.text,require_complete=True)
        with self.assertRaises(AssertionError):candidate.check('0.4.0',self.text)

    def test_legacy_completed_or_incomplete_counter_remains_supported(self):
        lines=[f'- [x] **{s}.{i:02}** Gate' for s in range(1,15) for i in range(1,9)]
        legacy='**112 concluídos / 0 pendentes**\n'+'\n'.join(lines)+'\n'+'\n'.join(f'### Lote {s} — Evidence' for s in range(1,15))
        self.assertTrue(progress.check(legacy,require_complete=True)['release_ready'])
        pending=legacy.replace('112 concluídos / 0','111 concluídos / 1').replace('- [x] **2.08**','- [ ] **2.08**')
        self.assertFalse(progress.check(pending)['release_ready'])

    def test_observed_results_do_not_claim_certification(self):
        result=json.loads((ROOT/'docs/observed-validation-0.4.json').read_text())
        self.assertFalse(result['physical_arm64_gpu_performance_established'])
        self.assertFalse(result['scientific']['global_accuracy_certified'])
        self.assertIsNone(result['scientific']['certified_interval'])
        self.assertEqual(result['scientific']['unresolved_boundary_checks'],221)
        self.assertFalse(result['pbf']['planet_scale_confirmed'])
        self.assertEqual(result['exact_gpu_previous_oracle']['identical'],97)

    def test_future_sequence_and_final_approval_are_preserved(self):
        self.assertEqual(self.registry['future']['v050'],'Planetary Cartography / Beyond Earth')
        self.assertEqual(self.registry['future']['v060'],'Orbits')
        self.assertFalse(self.registry['future']['global_eclipse_certification_required_for_050'])
        self.assertFalse(self.registry['publication_authorized'])
        self.assertFalse(self.registry['stage14_started_by_rescope'])


if __name__=='__main__':unittest.main()
