"""Whole-event corrections require frozen external evidence and unchanged limits."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from validate_eclipse_corpus import corrected_centers


class Corrections(unittest.TestCase):
    def fixture(self):
        source='a'*64
        corpus=dict(input_sha256={'central-oracle-v2-frozen.json':'b'*64},solar=[dict(date='2001-06-21',source_sha256=source),dict(date='2023-10-14',central_oracle={'version':2})])
        audit=dict(accepted_dates=['2001-06-21'],events=[dict(date='2001-06-21',acceptance_independent_of_Azimlib=True,decision='Correct whole-event central oracle',current_source_sha256=source,normalized_delta_t_s=64.,rows=1,comparisons=[dict(ut='12:00',presence_agrees=True,nasa_point=[1.,2.],nasa_to_DE440_m=10.,nasa_to_DE421_m=11.)])])
        change=dict(schema=3,limit_m=2000,original_corpus_sha256='c'*64,previous_2023_oracle_sha256='b'*64,cases=[dict(date='2001-06-21',source_sha256=source,delta_t_seconds=64.,rows=[dict(ut='12:00',longitude=1.,latitude=2.)])])
        return corpus,audit,change

    def invoke(self,corpus,audit,change,*,bad_hash=False):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);raw=json.dumps(audit).encode();(folder/'center-reference-audit.json').write_bytes(raw)
            change=dict(change,audit_sha256=hashlib.sha256(raw).hexdigest());raw=json.dumps(change).encode();path=folder/'correction.json';path.write_bytes(raw)
            return corrected_centers(corpus,path,'0'*64 if bad_hash else hashlib.sha256(raw).hexdigest(),'c'*64)

    def test_acceptance_is_explicit_and_preserves_original_and_2023(self):
        corpus,audit,change=self.fixture();before=copy.deepcopy(corpus)
        corrected=self.invoke(corpus,audit,change)
        self.assertEqual(corpus,before);self.assertEqual(corrected['solar'][1],before['solar'][1])
        self.assertEqual(corrected['solar'][0]['central_oracle']['version'],3)

    def test_relaxed_limit_tampering_and_failed_independent_reference_rejected(self):
        for failure in ('hash','limit','clock','point','primary','secondary','presence','approval','coverage','source','old_corpus','resolved_2023'):
            with self.subTest(failure=failure):
                corpus,audit,change=self.fixture();proof=audit['events'][0];row=proof['comparisons'][0]
                if failure=='limit':change['limit_m']=2001
                elif failure=='clock':change['cases'][0]['delta_t_seconds']=65
                elif failure=='point':change['cases'][0]['rows'][0]['longitude']=2.
                elif failure=='primary':row['nasa_to_DE440_m']=2001.
                elif failure=='secondary':row['nasa_to_DE421_m']=float('nan')
                elif failure=='presence':row['presence_agrees']=False
                elif failure=='approval':proof['acceptance_independent_of_Azimlib']=False
                elif failure=='coverage':audit['accepted_dates']=[]
                elif failure=='source':change['cases'][0]['source_sha256']='d'*64
                elif failure=='old_corpus':change['original_corpus_sha256']='d'*64
                elif failure=='resolved_2023':change['previous_2023_oracle_sha256']='d'*64
                with self.assertRaises(ValueError):self.invoke(corpus,audit,change,bad_hash=failure=='hash')

if __name__=='__main__':unittest.main()
