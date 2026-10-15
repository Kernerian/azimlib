"""Exact-candidate preflight; reads versioned authorization and audited bytes.

Default mode never uploads. Real mode additionally requires exact main CI and
the separately versioned human record explicitly permitting execution.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_release_artifact import SafeRedirect, validate
from release_state040 import AUTH_BRANCH, AUTH_PATH, VERSION, preflight

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repository', required=True)
    p.add_argument('--sha', required=True)
    p.add_argument('--authorization-ref', required=True)
    p.add_argument('--expected-branch', required=True)
    p.add_argument('--run-id', required=True, type=int)
    p.add_argument('--artifact-id', required=True, type=int)
    p.add_argument('--wheel-sha256', required=True)
    p.add_argument('--sdist-sha256', required=True)
    p.add_argument('--mode', choices=('dry-run', 'publish'), default='dry-run')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert a.repository == 'Kernerian/azimlib'
    assert re.fullmatch('[0-9a-f]{40}', a.authorization_ref), 'Immutable authorization commit required'
    assert a.expected_branch == ('main' if a.mode == 'publish' else 'validation/0.4-candidate'), 'Explicit contextual branch mismatch'
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip() == a.sha
    assert not a.output.exists(), 'Output must be new'
    token = os.environ['GH_TOKEN']
    opener = urllib.request.build_opener(SafeRedirect())
    def get(path):
        request = urllib.request.Request('https://api.github.com/repos/'+a.repository+path,
            headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json',
                     'User-Agent':'Azimlib-Release-Preflight'})
        with opener.open(request,timeout=90) as response:return response.read()
    def obj(path):return json.loads(get(path))
    assert obj('/git/ref/heads/'+a.expected_branch)['object']['sha'] == a.sha
    assert obj('/git/ref/heads/'+AUTH_BRANCH)['object']['sha'] == a.authorization_ref, 'Stale/unversioned authorization ref'
    content = obj('/contents/'+AUTH_PATH+'?ref='+a.authorization_ref)
    assert content['type'] == 'file' and content['encoding'] == 'base64'
    raw_auth = base64.b64decode(content['content'])
    record = json.loads(raw_auth)
    hashes = {'azimlib-0.4.0-py3-none-any.whl':a.wheel_sha256,
              'azimlib-0.4.0.tar.gz':a.sdist_sha256}
    assert record['artifact'] == dict(run_id=a.run_id,artifact_id=a.artifact_id)
    visual=(ROOT/'docs/visual-acceptance-0.4.json').read_bytes()
    assert record['visual_acceptance_sha256'] == hashlib.sha256(visual).hexdigest()
    assert json.loads(visual)['explicit_human_acceptance'] is True
    evidence={}
    for workflow in ('tests.yml','candidate-0.4.yml'):
        runs=obj('/actions/workflows/'+workflow+'/runs?branch='+a.expected_branch+'&head_sha='+a.sha+'&per_page=100')['workflow_runs']
        exact=[r for r in runs if r['head_sha']==a.sha and r['head_branch']==a.expected_branch]
        assert exact, 'Missing exact-context CI'
        run=obj('/actions/runs/'+str(exact[0]['id']))
        jobs=obj('/actions/runs/'+str(run['id'])+'/jobs?per_page=100')['jobs']
        evidence[workflow]=dict(run=run,jobs=jobs)
    progress=(ROOT/'docs/release-progress-0.4.md').read_text('utf8')
    proof=preflight(progress,record,sha=a.sha,hashes=hashes,ci=evidence,
                    expected_branch=a.expected_branch,execute=a.mode=='publish')
    # Reuse the strict candidate checker too; neither path may infer completion.
    from check_release_candidate import check
    assert check(VERSION,progress,authorization=record,sha=a.sha,hashes=hashes,
                 ci=evidence,expected_branch=a.expected_branch,execute=a.mode=='publish') == VERSION
    run=obj('/actions/runs/'+str(a.run_id));artifact=obj('/actions/artifacts/'+str(a.artifact_id))
    payload=get('/actions/artifacts/'+str(a.artifact_id)+'/zip')
    assert artifact['digest']=='sha256:'+hashlib.sha256(payload).hexdigest()
    files=validate(run,artifact,a.repository,a.sha,a.wheel_sha256,a.sdist_sha256,payload,version=VERSION)
    a.output.mkdir(parents=True)
    dist=a.output/'dist';dist.mkdir()
    for name,data in files.items():(dist/name).write_bytes(data)
    (a.output/'authorization.json').write_bytes(raw_auth)
    (a.output/'ci.json').write_text(json.dumps(evidence,indent=2)+'\n')
    proof.update(mode=a.mode,authorization_ref=a.authorization_ref,
                 authorization_sha256=hashlib.sha256(raw_auth).hexdigest(),
                 artifact_id=a.artifact_id,artifact_run_id=a.run_id,
                 uploaded=False,tag_created=False,documentation_deployed=False)
    (a.output/'preflight.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof,indent=2))


if __name__ == '__main__':main()
