"""Verify configured matrix identity equals the stable publish gate contract."""
import sys,json,itertools
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ci_contract import expected_jobs
import yaml
ROOT=Path(__file__).resolve().parents[1]
def main():
    workflow=yaml.safe_load((ROOT/'.github/workflows/tests.yml').read_text('utf8'));names=set()
    for name,job in workflow['jobs'].items():
        matrix=job.get('strategy',{}).get('matrix')
        if not matrix:names.add(name);continue
        assert not {'exclude','include'}&set(matrix),'Explicit job contract must be updated for matrix changes'
        for values in itertools.product(*matrix.values()):names.add(name+' ('+', '.join(values)+')')
    assert names==expected_jobs(),('CI config/publication contract mismatch',sorted(names^expected_jobs()))
    publish=(ROOT/'tools/check_publish_ci.py').read_text('utf8');assert 'verify_jobs(jobs,args.sha)' in publish
    assert 'tools/check_release_candidate.py' in (ROOT/'.github/workflows/publish.yml').read_text('utf8')
    print(json.dumps(dict(passed=True,required_jobs=len(names),systems=3,python_versions=5,qt_jobs=3,documentation_job=True)))
if __name__=='__main__':main()
