"""Verify installed current temporal proofs without falsifying old stage snapshots."""
import argparse,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((ROOT/'docs'/name).read_text('utf8'))
def audit():
    current={p.relative_to(ROOT/'src/azimlib').as_posix():sha(p) for p in sorted((ROOT/'src/azimlib').rglob('*.py'))}
    names=('temporal-validation-0.3.json','temporal-core-validation-0.3.json','temporal-desktop-0.3.json','temporal-tk-0.3.json','temporal-qt-0.3.json','temporal-qt-2d-0.3.json','temporal-qt-3d-0.3.json')
    for name in names:
        proof=read(name);assert proof['passed'] and proof['version']=='0.3.0.dev0' and proof['runtime_sha256']==current,name
        if 'unittest' in proof:
            u=proof['unittest'];assert u['tests']==986 and not u['errors'] and not u['failures']
            assert proof['tool_sha256']==sha(ROOT/'tools/run_release_checks.py') and not proof['forbidden_imports']
    for name,backend in (('temporal-tk-0.3.json','tk'),('temporal-qt-0.3.json','qt')):
        p=read(name);assert p['platform']=='Windows' and p['backend']==backend and p['tool_sha256']==sha(ROOT/'tools/smoke_temporal.py')
        assert all(p[k] for k in ('automatic_ticks','finite_end','pause_resume','slider','controls','close_cleanup'))
    desktop=read('temporal-desktop-0.3.json');assert {p['tool'] for p in desktop['scripts']}=={'smoke_interaction_tk.py','smoke_terrain3d.py','smoke_temporal.py'}
    assert all(p['returncode']==0 and p['sha256']==sha(ROOT/'tools'/p['tool']) for p in desktop['scripts'])
    q=read('temporal-qt-2d-0.3.json');assert q['tool_sha256']==sha(ROOT/'tools/smoke_interaction_qt.py') and all(q[k] for k in ('picking','pan','history','widgets','stroke_points','cleanup'))
    q=read('temporal-qt-3d-0.3.json');assert q['tool_sha256']==sha(ROOT/'tools/smoke_terrain3d.py') and all(q[k] for k in ('orbit','history','cleanup'))
    folder=ROOT/'docs/_static/temporal';manifest=json.loads((folder/'manifest.json').read_text('utf8'))
    assert manifest['runtime_sha256']==current and manifest['generator_sha256']==sha(ROOT/manifest['generator'])
    for name,digest in manifest['files'].items():assert sha(folder/name)==digest,name
    notice=(ROOT/'src/azimlib/fonts/LICENSE_DEJAVU').read_text('utf8')
    for path in folder.rglob('*.svg'):
        tree=ET.fromstring(path.read_text('utf8'));assert next(n for n in tree.iter() if n.attrib.get('id')=='azimlib-font-license').text==notice
    pdf=read('temporal-pdf-0.3.json');assert pdf['passed'] and pdf['pages']==3 and pdf['font_notices_exact'] and pdf['tool_sha256']==sha(ROOT/'tools/audit_atlas_pdf.py') and pdf['pdf_sha256']==sha(folder/pdf['file'])
    progress=(ROOT/'docs/release-progress-0.3.md').read_text('utf8');assert '- [ ] **7.08**' in progress and all(f'- [x] **9.{i:02}**' in progress for i in range(1,9))
    return dict(passed=True,runtime_files=len(current),gallery_files=len(manifest['files']),native_windows=True,linux_macos_native='pending 7.08',remote_ci_executed=False,actual_video_codec_validated=False,scope='Installed current numerical/lifecycle/exports and programmatic native Windows proofs; no human/FPS/other-platform/video codec claim')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args();report=audit()
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(report,indent=2))
