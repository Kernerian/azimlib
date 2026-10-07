"""Verify recorded installed interaction evidence and original gallery bytes.

Offline audit of this recorded Windows batch. Does not execute a GUI, hosted CI,
Jupyter frontend or browser, and does not turn local evidence into acceptance.
"""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(name):return json.loads((ROOT/'docs'/name).read_text('utf8'))
def audit():
    current={p.relative_to(ROOT/'src/azimlib').as_posix():sha(p) for p in sorted((ROOT/'src/azimlib').rglob('*.py'))}
    names=('interaction-validation-0.3.json','interaction-core-validation-0.3.json','interaction-desktop-0.3.json','interaction-qt-0.3.json','interaction-notebook-0.3.json')
    for name in names:
        data=read(name);assert data['passed'] and data['version']=='0.3.0.dev0',name
        assert data['runtime_sha256']==current,name
        if 'unittest' in data:assert data['unittest']['tests']>=896 and not data['unittest']['failures'] and not data['unittest']['errors']
    qt=read('interaction-qt-0.3.json');assert qt['platform']=='Windows' and qt['qpa']=='windows' and qt['tool_sha256']==sha(ROOT/'tools/smoke_interaction_qt.py')
    nb=read('interaction-notebook-0.3.json');assert nb['tool_sha256']==sha(ROOT/'tools/smoke_notebook.py')
    assert all(qt[k] for k in ('picking','pan','history','widgets','stroke_points','cleanup'))
    assert all(nb[k] for k in ('display_handle','cell_hook','cleanup'))
    tk=read('interaction-desktop-0.3.json');assert {v['tool'] for v in tk['scripts']}=={'smoke_interaction_tk.py','smoke_pan_interaction_tk.py'}
    assert all(v['returncode']==0 and v['sha256']==sha(ROOT/'tools'/v['tool']) for v in tk['scripts'])
    earlier=read('interaction-desktop-regression-0.3.json');assert earlier['passed'] and len(earlier['scripts'])==17
    # The earlier broad Tk run predates ONLY the HTTP timeout; this module is
    # not used by Tk. Keep the unmodified report, not a false same-runtime stamp.
    differences=[name for name,digest in current.items() if earlier['runtime_sha256'].get(name)!=digest]
    assert differences==['backends/live.py'],differences
    assert all(v['returncode']==0 and v['sha256']==sha(ROOT/'tools'/v['tool']) for v in earlier['scripts'])
    gallery=ROOT/'docs/_static/interaction';manifest=json.loads((gallery/'manifest.json').read_text('utf8'))
    assert manifest['generator_sha256']==sha(ROOT/manifest['generator'])
    for name,digest in manifest['files'].items():assert sha(gallery/name)==digest
    bench=read('interaction-benchmark-0.3.json');assert bench['passed'] and bench['platform']=='Windows'
    assert [(v['scenario'],v['features']) for v in bench['scenarios']]==[('urban',400),('dense',5000)]
    for row in bench['scenarios']:
        assert row['pan_total']['samples']==4 and row['tile_cache']['payload_bytes']<=row['tile_cache']['max_bytes']
        assert row['cache']['payload_bytes']<=row['cache']['max_bytes'] and {e['format'] for e in row['exports']}=={'png','svg','pdf'}
    return dict(passed=True,installed_runtime_files=len(current),native_windows=True,hosted_ci_executed=False,
        linux_macos_native_gate='pending',gallery_files=len(manifest['files']),earlier_tk_http_only_difference=differences,
        scope='Recorded local installed suites, real native Windows Qt/Tk programmatic input/paint, actual IPython shell, mathematical circle/simplification and exports. Not human input/visual approval, browser/Jupyter frontend acceptance or remote/cross-platform CI.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);args=p.parse_args();report=audit()
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,indent=2))
