"""Verify retained local installed-runtime evidence, including failed deadlines.

This audit does not turn local results into CI or physical GUI approval.
Raw logs live in the originating work directory; their hashes are retained.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = json.loads((ROOT/'docs/release-validation-local.json').read_text(encoding='utf-8'))
    current = {p.relative_to(ROOT/'src/azimlib').as_posix(): sha(p)
               for p in sorted((ROOT/'src/azimlib').rglob('*.py')) if '__pycache__' not in p.parts}
    runners = {sha(ROOT/'tools/run_release_checks.py'),
               sha(ROOT/'tools/baselines/release-checks-300/run_release_checks.py')}
    def verify(run):
        data = run['result']
        assert data['runtime_sha256'] == current and data['tool_sha256'] in runners
        assert data['version'] == report['version'] == '0.1.0'
        assert data['execution_context'] == 'local' and data['github'] is None
        assert not data['forbidden_imports']
        assert 'site-packages' in data['runtime_origin']
        for row in data.get('scripts', []):
            assert row['sha256'] == sha(ROOT/'tools'/row['tool'])
        return data
    assert len(report['unit_runs']) == 2
    for run in report['unit_runs']:
        data = verify(run); checks = data['unittest']
        assert data['passed'] and checks['tests'] == 675 and checks['subtests'] == 16792
        assert not checks['failures'] and not checks['errors'] and len(checks['skipped']) == 2
    data = verify(report['accelerator_run']); checks = data['unittest']
    assert data['passed'] and checks['tests'] == 11 and checks['subtests'] == 5470
    assert not checks['skipped'] and not checks['failures'] and not checks['errors']
    for run in report['desktop_runs']:
        first = verify(run['first_attempt']); retry = verify(run['retry'])
        assert first['python'] == retry['python'] == run['python']
        failed = [row for row in first['scripts'] if row['returncode']]
        assert len(first['scripts']) == 13 and len(failed) == 1 and not first['passed']
        assert failed[0]['returncode'] == 124 and failed[0]['tool'] == 'smoke_layout_acceptance_tk.py'
        assert len(retry['scripts']) == 1 and retry['passed']
        assert retry['scripts'][0]['tool'] == failed[0]['tool'] and retry['scripts'][0]['returncode'] == 0
        effective = {row['tool']: row for row in first['scripts']}
        effective.update({row['tool']: row for row in retry['scripts']})
        assert len(effective) == run['effective_unique_scripts'] == 13
        assert run['effective_passed'] and all(row['returncode'] == 0 for row in effective.values())
        detail = run['retry']['desktop_details']['smoke_layout_acceptance_tk.py']
        assert len(detail['checks']) == 30 and len(detail['frames']) == 18 and detail['independent_runtime']
    negative = verify(report['timeout_cleanup_negative_probe'])
    assert not negative['passed'] and negative['scripts'][0]['returncode'] == 124
    assert not report['ci']['executed_remotely'] and report['ci']['configured_jobs'] == 24
    assert report['ci']['workflow_sha256'] == sha(ROOT/'.github/workflows/tests.yml')
    assert len(report['core_installations']) == 2 and all(row['passed'] for row in report['core_installations'])
    print('Local evidence: current runtime, 2 x 675 tests, compiler contracts, 2 x 13 unique Tk scripts; failed deadlines/retries preserved. Remote CI/native Linux/macOS remain pending.')


if __name__ == '__main__': main()
