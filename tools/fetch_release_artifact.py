"""Retrieve exact audited release bytes; never rebuild or publish a package."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request
import zipfile


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, url):
        redirected = super().redirect_request(request, fp, code, message, headers, url)
        if redirected is not None and urllib.parse.urlsplit(url).hostname != 'api.github.com':
            redirected.remove_header('Authorization')
        return redirected


def validate(run, artifact, repository, commit, wheel_hash, sdist_hash, payload):
    assert re.fullmatch(r'[0-9a-f]{40}', commit), 'Invalid commit'
    assert all(re.fullmatch(r'[0-9a-f]{64}', h) for h in (wheel_hash, sdist_hash)), 'Invalid SHA-256'
    assert run['repository']['full_name'] == repository, 'Wrong artifact repository'
    assert run['head_sha'] == commit and run['status'] == 'completed' and run['conclusion'] == 'success', 'Build must succeed at exact final commit'
    assert run['path'] == '.github/workflows/release-candidate.yml', 'Wrong build workflow'
    assert artifact['workflow_run']['id'] == run['id'] and artifact['workflow_run']['head_sha'] == commit, 'Wrong artifact provenance'
    assert artifact['name'] == 'azimlib-0.3.0-unpublished-candidate' and not artifact['expired'], 'Wrong or expired artifact'
    expected = {'azimlib-0.3.0-py3-none-any.whl': wheel_hash, 'azimlib-0.3.0.tar.gz': sdist_hash}
    files = {}
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        assert archive.testzip() is None, 'Corrupt artifact archive'
        names = archive.namelist()
        assert len(names) == len(set(names)), 'Duplicate archive entries'
        for name, digest in expected.items():
            data = archive.read('candidate-dist/' + name)
            assert hashlib.sha256(data).hexdigest() == digest, 'Unexpected distribution hash'
            files[name] = data
        distribution = json.loads(archive.read('candidate-audits/distribution.json'))
        assert distribution['version'] == '0.3.0' and not distribution['mandatory_dependencies']
        assert distribution['license_expression'].startswith('BSD-3-Clause AND ')
        assert {row['file']: row['sha256'] for row in distribution['archives']} == expected, 'Audit hash mismatch'
        for name in ('licenses', 'privacy-source', 'privacy-archives'):
            proof = json.loads(archive.read('candidate-audits/' + name + '.json'))
            assert proof['passed'], 'Build audit did not pass'
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--sha', required=True)
    parser.add_argument('--run-id', type=int, required=True)
    parser.add_argument('--artifact-id', type=int, required=True)
    parser.add_argument('--wheel-sha256', required=True)
    parser.add_argument('--sdist-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', args.repository)
    token = os.environ['GH_TOKEN']
    opener = urllib.request.build_opener(SafeRedirect())
    def get(path):
        request = urllib.request.Request('https://api.github.com/repos/' + args.repository + path,
            headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                     'User-Agent': 'Azimlib-Release-Provenance'})
        with opener.open(request, timeout=90) as response:
            return response.read()
    run = json.loads(get('/actions/runs/' + str(args.run_id)))
    artifact = json.loads(get('/actions/artifacts/' + str(args.artifact_id)))
    payload = get('/actions/artifacts/' + str(args.artifact_id) + '/zip')
    files = validate(run, artifact, args.repository, args.sha, args.wheel_sha256, args.sdist_sha256, payload)
    assert not args.output.exists(), 'Output must be new'
    args.output.mkdir(parents=True)
    for name, data in files.items():
        (args.output / name).write_bytes(data)
    print('Exact audited release artifact verified:', args.run_id, args.artifact_id, args.sha)


if __name__ == '__main__':
    main()
