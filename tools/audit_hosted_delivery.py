"""Verify actual downloaded current CI jobs/artifacts, never configured/local substitutes."""
import argparse,ast,hashlib,json,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from ci_contract import verify_jobs
ROOT=Path(__file__).resolve().parents[1]
def sha(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads(path.read_text('utf8'))
def audit(folder,expected_sha):
    run=read(folder/'run.json');assert run['repository']['full_name']=='Kernerian/azimlib'
    assert run['event']=='push' and run['head_branch']=='dev/0.3.0' and run['head_sha']==expected_sha
    assert run['status']=='completed' and run['conclusion']=='success'
    jobs=read(folder/'jobs.json')['jobs'];count=verify_jobs(jobs,expected_sha)
    artifacts=read(folder/'artifacts.json')['artifacts'];assert len(artifacts)==count and not any(a['expired'] for a in artifacts)
    current={p.relative_to(ROOT/'src/azimlib').as_posix():sha(p.read_bytes()) for p in sorted((ROOT/'src/azimlib').rglob('*.py'))}
    expected={'documentation'}
    for job in jobs:
        name=job['name']
        if name=='documentation':continue
        parts=name[name.index('(')+1:-1].split(', ');kind=name.split(' ')[0]
        expected.add(kind+'-'+parts[0]+('-py'+parts[1] if len(parts)==2 else ''))
    assert {a['name'] for a in artifacts}==expected
    rows=[]
    for artifact in artifacts:
        name=artifact['name'];path=folder/(name+'.zip');verified=[]
        with zipfile.ZipFile(path) as archive:
            assert archive.testzip() is None
            if name=='documentation':
                proof=json.loads(archive.read('site-check.json'));assert proof['passed'] and not proof['broken']
                proof=json.loads(archive.read('migration/result.json'));assert proof['passed'] and proof['snippets']==3
                proof=json.loads(archive.read('documentation.json'));assert not proof['broken']
                verified=['site files/anchors','three migration snippets','documentation source targets']
            elif name.startswith('qt-'):
                for file,tool in (('qt/result.json','smoke_interaction_qt.py'),('terrain3d/result.json','smoke_terrain3d.py'),('temporal/result.json','smoke_temporal.py'),('notebook/result.json','smoke_notebook.py')):
                    proof=json.loads(archive.read(file));assert proof['passed'] and proof['runtime_sha256']==current and proof['version']=='0.3.0.dev0'
                    assert proof['tool_sha256']==sha((ROOT/'tools'/tool).read_bytes());verified.append(tool)
            else:
                kind='unit' if name.startswith('test-') else 'accelerator' if name.startswith('accelerator-') else 'desktop'
                proof=json.loads(archive.read(kind+'/result.json'));assert proof['passed'] and proof['runtime_sha256']==current and proof['version']=='0.3.0.dev0' and not proof['forbidden_imports']
                assert proof['execution_context']=='github-actions' and proof['github']['GITHUB_RUN_ID']==str(run['id']) and proof['github']['GITHUB_SHA']==expected_sha
                assert proof['tool_sha256']==sha((ROOT/'tools/run_release_checks.py').read_bytes())
                if kind!='desktop':
                    u=proof['unittest'];assert not u['failures'] and not u['errors'] and u['log_sha256']==sha(archive.read(kind+'/unittest.log'))
                    if kind=='unit':assert u['tests']==997
                    else:assert proof['optional_packages']['numba'] and not u['skipped'] and u['tests']>=11
                else:
                    tree=ast.parse((ROOT/'tools/run_release_checks.py').read_text('utf8'))
                    required=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DESKTOP' for t in n.targets))
                    assert {row['tool'] for row in proof['scripts']}==set(required)
                    for row in proof['scripts']:
                        assert row['returncode']==0 and row['sha256']==sha((ROOT/'tools'/row['tool']).read_bytes())
                        assert row['log_sha256']==sha(archive.read(kind+'/'+Path(row['tool']).stem+'.log'))
                        if 'report_file' in row:assert row['report_sha256']==sha(archive.read(kind+'/'+row['report_file']))
                if kind=='unit':
                    for file in ('privacy-source.json','privacy-archives.json','licenses.json','optional-data.json','baselines/result.json'):
                        item=json.loads(archive.read(file));assert item['passed'],file
                    item=json.loads(archive.read('distribution.json'));assert item['version']=='0.3.0.dev0' and not item['mandatory_dependencies'] and item['license_expression'].startswith('BSD-3-Clause AND ')
                verified.append(kind)
        rows.append(dict(name=name,archive_sha256=sha(path.read_bytes()),verified=verified))
    return dict(passed=True,run_url=run['html_url'],run_id=run['id'],head_sha=expected_sha,verified_jobs=count,artifacts=rows,runtime_files=len(current),scope='Actual hosted 28-job installed/build/audit/core/Tk/Qt/notebook/docs validation; not human Linux/macOS visual acceptance, PyPI publication or docs hosting')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--sha',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=audit(a.folder,a.sha)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n');print(json.dumps({k:result[k] for k in ('passed','run_url','head_sha','verified_jobs','runtime_files')},indent=2))
