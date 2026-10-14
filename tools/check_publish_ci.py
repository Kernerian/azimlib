"""Require the full successful hosted test matrix for the exact release commit."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ci_contract import verify_jobs
import argparse
import json
import os
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--sha', required=True)
    args = parser.parse_args()
    token = os.environ['GH_TOKEN']
    root = 'https://api.github.com/repos/' + args.repository

    def get(path):
        request = urllib.request.Request(root + path, headers={
            'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'})
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    assert get('/branches/main')['commit']['sha'] == args.sha, 'Release must use current main'
    runs = get('/actions/workflows/tests.yml/runs?branch=main&per_page=100')['workflow_runs']
    exact = [r for r in runs if r['head_sha'] == args.sha]
    assert exact, 'No CI run for the release commit'
    run = exact[0]
    assert run['status'] == 'completed' and run['conclusion'] == 'success', 'Release CI is not successful'
    jobs = get('/actions/runs/' + str(run['id']) + '/jobs?per_page=100')['jobs']
    count=verify_jobs(jobs,args.sha)
    import tomllib
    version=tomllib.loads((Path(__file__).resolve().parents[1]/'pyproject.toml').read_text('utf8'))['project']['version']
    if version=='0.4.0':
        from audit_candidate040_ci import verify
        runs040=get('/actions/workflows/candidate-0.4.yml/runs?branch=main&per_page=100')['workflow_runs']
        exact040=[r for r in runs040 if r['head_sha']==args.sha]
        assert exact040,'No complete 0.4 scoped CI at this exact main SHA'
        full=get('/actions/runs/'+str(exact040[0]['id']))
        jobs040=get('/actions/runs/'+str(full['id'])+'/jobs?per_page=100')['jobs']
        proof=verify(full,jobs040,sha=args.sha,branch='main',workflow='candidate-0.4.yml')
        print('Scoped 0.4 CI verified:',proof['url'],proof['jobs'])
    print('Release CI verified:',run['html_url'],f'{count}/{count} successful jobs at',args.sha)


if __name__ == '__main__':
    main()
