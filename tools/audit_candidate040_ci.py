"""Verify the complete unpublished 0.4 matrices at one explicit branch and SHA."""
import argparse,json
from pathlib import Path
from ci_contract import expected_jobs,verify_jobs
SYSTEMS=('ubuntu-latest','windows-latest','macos-latest')
def extra_jobs():
 names={f'integration / core ({os}, {py})' for os in SYSTEMS for py in ('3.10','3.11','3.12','3.13','3.14')}
 names|={f'integration / {kind} ({os})' for os in SYSTEMS for kind in ('native','no-gpu')}
 names|={'integration / software-gpu'}
 names|={f'{kind} / {label}-{os}' for kind,label in (('text','complex-text'),('tex','real-tex')) for os in ('linux','macos','windows')}
 names|={f'gpu / without-gpu ({os})' for os in SYSTEMS}
 names|={'gpu / mesa-reference','preview / mesa-contracts-only'}
 names|={f'preview / contracts-without-gpu ({os})' for os in (*SYSTEMS,'ubuntu-24.04-arm','macos-15-intel')}
 names|={f'visual ({os})' for os in SYSTEMS}|{'package'}
 return names
def verify(run,jobs,*,sha,branch,workflow):
 if not sha or not branch:raise AssertionError('Explicit SHA and expected branch required')
 assert run['head_sha']==sha and run['head_branch']==branch,'Exact SHA/branch mismatch'
 assert run['path']=='.github/workflows/'+workflow,'Wrong workflow identity'
 assert run['status']=='completed' and run['conclusion']=='success','Complete successful run required'
 assert run['head_repository']['full_name']=='Kernerian/azimlib','Wrong source repository'
 expected=expected_jobs() if workflow=='tests.yml' else extra_jobs() if workflow=='candidate-0.4.yml' else None
 assert expected is not None,'Unknown required workflow'
 assert len(jobs)==len(expected) and {j['name'] for j in jobs}==expected,'Missing, duplicate or unexpected jobs'
 assert all(j['head_sha']==sha and j['status']=='completed' and j['conclusion']=='success' for j in jobs),'All exact-commit jobs must succeed'
 return dict(passed=True,sha=sha,branch=branch,workflow=workflow,jobs=len(jobs),url=run['html_url'],human_acceptance=False,publication_authorized=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--sha',required=True);p.add_argument('--branch',required=True);p.add_argument('--run',type=Path,required=True);p.add_argument('--jobs',type=Path,required=True);p.add_argument('--workflow',choices=('tests.yml','candidate-0.4.yml'),required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 r=verify(json.loads(a.run.read_text()),json.loads(a.jobs.read_text())['jobs'],sha=a.sha,branch=a.branch,workflow=a.workflow)
 a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
