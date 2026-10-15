"""Publication states are separate from the immutable source checklist.

Authorization is a separately versioned, exact-candidate record. A preflight
never completes 14.08. Completion consumes separately audited observations.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_release_progress_040 import check as inventory
from audit_candidate040_ci import verify

VERSION = '0.4.0'
DEFERRED = ['2.08', '9.08', '13.06', '13.07']
AUTH_BRANCH = 'release/0.4.0-authorization'
AUTH_PATH = 'release-authorizations/0.4.0.json'


def package_names():
    return {f'azimlib-{VERSION}-py3-none-any.whl', f'azimlib-{VERSION}.tar.gz'}


def identity(sha, hashes):
    assert isinstance(sha, str) and re.fullmatch('[0-9a-f]{40}', sha) and sha != '0'*40, 'Exact candidate SHA required'
    assert isinstance(hashes, dict) and set(hashes) == package_names(), 'Exact wheel/sdist pair required'
    assert all(isinstance(h, str) and re.fullmatch('[0-9a-f]{64}', h) for h in hashes.values()), 'Invalid package SHA-256'


def ci_proofs(evidence, sha, branch):
    assert branch, 'Explicit expected CI branch required'
    assert isinstance(evidence, dict), 'Both exact-SHA CI records required'
    assert set(evidence) == {'tests.yml', 'candidate-0.4.yml'}, 'Both CI matrices required'
    return [verify(evidence[w]['run'], evidence[w]['jobs'], sha=sha, branch=branch, workflow=w)
            for w in ('tests.yml', 'candidate-0.4.yml')]


def authorization_record(record, sha, hashes, *, execute=False):
    identity(sha, hashes)
    assert isinstance(record, dict), 'Final human authorization required'
    assert record.get('schema') == 1 and record.get('version') == VERSION
    assert record.get('state') == 'authorized', 'A completed/pending record cannot authorize preflight'
    assert record.get('candidate_sha') == sha, 'Authorization SHA mismatch'
    assert record.get('package_sha256') == hashes, 'Authorization package hashes mismatch'
    assert record.get('expected_inventory') == dict(original=112, completed=107, deferred=DEFERRED,
                                                   authorized_item='14.08', active_completed=107, active_total=108)
    assert record.get('human_final_acceptance') is True, 'Explicit final human acceptance required'
    assert record.get('allows_start_14_08') is True
    assert record.get('considers_14_08_completed') is False, 'Authorized must not mean completed'
    assert record.get('approval_reference') and record.get('visual_acceptance_reference')
    assert isinstance(record.get('publication_execution_permitted'), bool)
    if execute:
        assert record['publication_execution_permitted'], 'Human authorization permits dry-run only'
    return record


def preflight(progress, record, *, sha, hashes, ci, expected_branch, execute=False):
    state = inventory(progress)
    assert state['completed'] == 107 and state['pending'] == ['14.08'], 'Only 14.08 may remain active and unchecked'
    assert state['deferred'] == DEFERRED and state['active_total'] == 108
    authorization_record(record, sha, hashes, execute=execute)
    if execute:
        assert expected_branch == 'main', 'Real publication requires exact main CI'
    proofs = ci_proofs(ci, sha, expected_branch)
    return dict(version=VERSION, candidate_sha=sha, state='authorized',
                active_completed=107, active_total=108, deferred=DEFERRED,
                preflight_allowed=True, execution_permitted=bool(execute),
                completed=False, release_published=False, package_sha256=hashes, ci=proofs)


def completed(progress, record, observations, *, sha, hashes):
    """Validate structured observations from post-publication audits, not a flag.

    Callers must collect these observations from GitHub/PyPI, clean installation
    and deployed-site audits. This offline contract does not collect them itself.
    """
    state = inventory(progress)
    assert state['deferred'] == DEFERRED and state['active_total'] == 108
    assert ((state['completed'] == 107 and state['pending'] == ['14.08']) or
            (state['completed'] == 108 and not state['pending']))
    authorization_record(record, sha, hashes, execute=True)
    assert isinstance(observations, dict), 'Post-publication evidence required'
    assert {'version','candidate_sha','main','ci','tag','release','pypi','clean_install','documentation'} <= observations.keys(), 'Incomplete post-publication evidence'
    assert observations.get('version') == VERSION and observations.get('candidate_sha') == sha
    assert observations['main'] == dict(ref='refs/heads/main', sha=sha)
    proofs = ci_proofs(observations['ci'], sha, 'main')
    tag = observations['tag']
    assert tag['name'] == 'v0.4.0' and tag['target_sha'] == sha and tag['annotated'] is True
    release = observations['release']
    assert release['tag_name'] == tag['name'] and release['target_sha'] == sha
    assert isinstance(release['id'], int) and release['id'] > 0
    assert release['published'] is True and release['url'] == 'https://github.com/Kernerian/azimlib/releases/tag/v0.4.0'
    pypi = observations['pypi']
    assert pypi['version'] == VERSION and pypi['index'] == 'https://pypi.org/simple'
    assert pypi['metadata_hashes'] == pypi['downloaded_hashes'] == hashes
    install = observations['clean_install']
    assert install['version'] == VERSION and install['index'] == 'https://pypi.org/simple'
    assert install['isolated_environment'] is True and install['smoke_passed'] is True
    assert set(install['imports']) >= {'azimlib', 'azimlib.pyplot'}
    assert re.fullmatch('[0-9a-f]{64}', install['log_sha256'])
    docs = observations['documentation']
    assert docs['version'] == VERSION and docs['public'] is True and docs['links_passed'] is True
    assert docs['url'].startswith('https://kernerian.github.io/azimlib/')
    assert docs['source_sha'] == sha and docs['verified_files'] > 0
    assert re.fullmatch('[0-9a-f]{64}', docs['audit_sha256'])
    return dict(version=VERSION, candidate_sha=sha, state='completed', completed=True,
                release_published=True, active_completed=108, active_total=108,
                original_total=112, deferred=DEFERRED, ci=proofs,
                evidence_sha256=hashlib.sha256(json.dumps(observations, sort_keys=True).encode()).hexdigest())


def status(progress, record=None, *, sha=None, hashes=None, ci=None, expected_branch=None,
           post_publication=None, execute=False):
    state = inventory(progress)
    if post_publication is not None:
        return completed(progress, record, post_publication, sha=sha, hashes=hashes)
    assert state['completed'] == 107 and state['pending'] == ['14.08'], 'Completed checklist requires validated post-publication evidence'
    if record is None:
        return dict(state='pending', completed=False, preflight_allowed=False,
                    active_completed=107, active_total=108, deferred=DEFERRED)
    return preflight(progress, record, sha=sha, hashes=hashes, ci=ci,
                     expected_branch=expected_branch, execute=execute)
