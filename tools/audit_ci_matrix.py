"""Audit downloaded GitHub Actions run, jobs, reports and log hashes.

Uses provided evidence files, not GitHub credentials. A configured workflow or
local report cannot pass this remote matrix audit. Hidden Tk is not human input.
"""
import argparse,hashlib,json,re,zipfile
from pathlib import Path


def sha(data): return hashlib.sha256(data).hexdigest()


def audit(folder,version):
    run=json.loads((folder/'run.json').read_text(encoding='utf-8'))
    jobs=json.loads((folder/'jobs.json').read_text(encoding='utf-8'))['jobs']
    assert run['status']=='completed' and run['conclusion']=='success'
    assert run['repository']['full_name']=='Kernerian/azimlib'
    systems=('ubuntu-latest','windows-latest','macos-latest')
    expected={f'test ({os}, {py})' for os in systems for py in ('3.10','3.11','3.12','3.13','3.14')}
    expected|={f'accelerator ({os}, {py})' for os in systems for py in ('3.10','3.14')}
    expected|={f'desktop ({os})' for os in systems}
    assert len(jobs)==24 and {j['name'] for j in jobs}==expected
    assert all(j['status']=='completed' and j['conclusion']=='success' and j['head_sha']==run['head_sha'] for j in jobs)
    artifacts=json.loads((folder/'artifacts.json').read_text(encoding='utf-8'))['artifacts']
    assert len(artifacts)==24 and not any(a['expired'] for a in artifacts)
    rows=[]
    for artifact in artifacts:
        name=artifact['name'];path=folder/(name+'.zip')
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            kind='unit' if name.startswith('test-') else 'accelerator' if name.startswith('accelerator-') else 'desktop'
            result=json.loads(archive.read(kind+'/result.json'))
            assert result['passed'] and not result['forbidden_imports'] and result['version']==version
            assert result['execution_context']=='github-actions'
            assert result['github']['GITHUB_RUN_ID']==str(run['id'])
            assert result['github']['GITHUB_REPOSITORY']=='Kernerian/azimlib'
            assert 'site-packages' in result['runtime_origin']
            if kind in ('unit','accelerator'):
                checks=result['unittest'];log=archive.read(kind+'/unittest.log')
                assert checks['log_sha256']==sha(log) and not checks['failures'] and not checks['errors']
                assert checks['tests']==(675 if kind=='unit' else 11)
                if kind=='accelerator':assert not checks['skipped'] and checks['subtests']==5470
                else:assert len(checks['skipped'])==2 and checks['subtests']==16792
            else:
                assert len(result['scripts'])==13 and len({row['tool'] for row in result['scripts']})==13
                for row in result['scripts']:
                    assert row['returncode']==0
                    log=archive.read(kind+'/'+Path(row['tool']).stem+'.log')
                    assert sha(log)==row['log_sha256']
                    assert all(signal not in log for signal in (b'Tcl_AsyncDelete',b'main thread is not in main loop',b'Traceback (most recent call last)'))
                    if 'report_file' in row:assert sha(archive.read(kind+'/'+row['report_file']))==row['report_sha256']
            distribution=json.loads(archive.read('distribution.json')) if kind=='unit' else None
            if distribution:
                assert distribution['version']==version and not distribution['mandatory_dependencies']
                assert distribution['runtime_files_exact']==111 and distribution['own_icons']==21
                assert distribution['external_original_ibge_data_excluded']
            rows.append(dict(name=name,archive_sha256=sha(path.read_bytes()),result=result,distribution=distribution))
    return dict(schema_version=1,version=version,run_url=run['html_url'],run_id=run['id'],
                head_sha=run['head_sha'],event=run['event'],status='success',jobs=jobs,artifact_reports=rows,
                expected_jobs=24,verified_jobs=24,
                scope='Actual hosted CI: 15 installed suites/build/audit/core, 6 optional compiler contracts, 3 withdrawn Tk integrations. No native human visual approval on Linux/macOS. GITHUB_SHA in a PR report identifies its synthetic merge commit; head_sha identifies the PR branch revision.')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--folder',type=Path,required=True)
    parser.add_argument('--version',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();report=audit(args.folder,args.version)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'24/24 hosted jobs and 24 artifact reports verified for {args.version}; {report["head_sha"]}')


if __name__=='__main__':main()
