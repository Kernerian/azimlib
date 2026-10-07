"""Exact current CI identity contract; no network or credentials."""
SYSTEMS=('ubuntu-latest','windows-latest','macos-latest')
PYTHONS=('3.10','3.11','3.12','3.13','3.14')
def expected_jobs():
    names={f'test ({os}, {py})' for os in SYSTEMS for py in PYTHONS}
    names|={f'accelerator ({os}, {py})' for os in SYSTEMS for py in ('3.10','3.14')}
    names|={f'{kind} ({os})' for os in SYSTEMS for kind in ('desktop','qt')}
    return names|{'documentation'}
def verify_jobs(jobs,sha):
    expected=expected_jobs()
    assert len(jobs)==len(expected) and {j['name'] for j in jobs}==expected,'Incomplete, duplicate or unexpected CI jobs'
    assert all(j.get('head_sha')==sha and j.get('status')=='completed' and j.get('conclusion')=='success' for j in jobs),'Every exact-commit job must succeed'
    return len(expected)
