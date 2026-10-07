"""Verify recorded installed stage-8 proofs, not historical stage-7 acceptance."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((ROOT/'docs'/name).read_text('utf8'))
def audit():
    current={p.relative_to(ROOT/'src/azimlib').as_posix():sha(p) for p in sorted((ROOT/'src/azimlib').rglob('*.py'))}
    names=('terrain3d-validation-0.3.json','terrain3d-core-validation-0.3.json','terrain3d-desktop-0.3.json','terrain3d-tk-0.3.json','terrain3d-qt-0.3.json','terrain3d-qt-2d-0.3.json')
    for name in names:
        data=read(name);assert data['passed'] and data['version']=='0.3.0.dev0',name
        assert data['runtime_sha256']==current,name
        if 'unittest' in data:
            assert data['unittest']['tests']>=933 and not data['unittest']['failures'] and not data['unittest']['errors'],name
            assert data['tool_sha256']==sha(ROOT/'tools/run_release_checks.py')
            assert data['forbidden_imports']==[]
    for name,backend in (('terrain3d-tk-0.3.json','tk'),('terrain3d-qt-0.3.json','qt')):
        proof=read(name);assert proof['platform']=='Windows' and proof['backend']==backend
        assert proof['tool_sha256']==sha(ROOT/'tools/smoke_terrain3d.py')
        assert all(proof[k] for k in ('orbit','history','cleanup'))
    assert read('terrain3d-tk-0.3.json')['zoom']
    desktop=read('terrain3d-desktop-0.3.json')
    assert {p['tool'] for p in desktop['scripts']}=={'smoke_pan_interaction_tk.py','smoke_interaction_tk.py','smoke_transform_composition_tk.py','smoke_terrain3d.py'}
    assert all(p['returncode']==0 and p['sha256']==sha(ROOT/'tools'/p['tool']) for p in desktop['scripts'])
    qt2d=read('terrain3d-qt-2d-0.3.json');assert qt2d['tool_sha256']==sha(ROOT/'tools/smoke_interaction_qt.py') and qt2d['qpa']=='windows'
    assert all(qt2d[k] for k in ('picking','pan','history','widgets','stroke_points','cleanup'))
    bench=read('terrain3d-benchmark-0.3.json');assert bench['runtime_sha256']==current and bench['platform']=='Windows'
    assert bench['tool_sha256']==sha(ROOT/'tools/benchmark_terrain3d.py')
    assert [(v['grid'],v['triangles'],v['accelerate']) for v in bench['cases']]==[(16,450,False),(32,1922,True),(64,7938,True)]
    assert all(len(v['seconds'])==3 and min(v['seconds'])>0 for v in bench['cases'])
    folder=ROOT/'docs/_static/terrain3d';manifest=json.loads((folder/'manifest.json').read_text('utf8'))
    assert manifest['runtime_sha256']==current and manifest['generator_sha256']==sha(ROOT/manifest['generator'])
    for name,digest in manifest['files'].items():assert sha(folder/name)==digest,name
    progress=(ROOT/'docs/release-progress-0.3.md').read_text('utf8');assert '- [ ] **7.08**' in progress
    return dict(passed=True,runtime_files=len(current),gallery_files=len(manifest['files']),native_windows=True,linux_macos_native='pending 7.08',remote_ci_executed=False,own_camera_depth_contracts=True,scope='Local installed numeric/depth/exports and programmatic Tk/Qt proofs; no human acceptance, GPU/FPS, other-platform GUI or remote CI claim')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);args=p.parse_args();report=audit()
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(report,indent=2))
