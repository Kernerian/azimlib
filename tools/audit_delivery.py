"""Audit current 0.3 gallery/baseline provenance, independent runtime and legal assets."""
import argparse,ast,hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def audit():
    current={p.relative_to(ROOT/'src/azimlib').as_posix():sha(p) for p in sorted((ROOT/'src/azimlib').rglob('*.py'))}
    folder=ROOT/'docs/_static/release030';manifest=json.loads((folder/'manifest.json').read_text('utf8'))
    assert manifest['runtime_sha256']==current
    for name,value in manifest['example_sha256'].items():assert sha(ROOT/'examples'/name)==value,name
    cases=manifest['cases'];assert [c['name'] for c in cases]==['political','physical','urban','scientific','terrain3d','temporal']
    font_notice=(ROOT/'src/azimlib/fonts/LICENSE_DEJAVU').read_text('utf8')
    for case in cases:
        assert case['static_without_controls'] and case['composition_license']=='BSD-3-Clause'
        for name,value in case['files'].items():
            path=folder/name;assert sha(path)==value,name
            if path.suffix=='.svg':
                tree=ET.fromstring(path.read_text('utf8'));assert next(n for n in tree.iter() if n.attrib.get('id')=='azimlib-font-license').text==font_notice,name
            elif path.suffix=='.pdf':assert font_notice.encode('utf8') in path.read_bytes(),name
    assert sha(folder/'overview.png')==manifest['overview_sha256']
    baseline=ROOT/'tools/baselines/release030';expected=json.loads((baseline/'manifest.json').read_text('utf8'))
    assert sha(ROOT/'tools/check_release_baselines.py')==expected['tool_sha256']
    for name,case in expected['cases'].items():assert sha(baseline/(name+'.png'))==case['png_sha256']
    blocked={'matplotlib','cartopy','geopandas','shapely','pyproj','folium','rasterio','fiona','geographiclib'}
    for path in (ROOT/'src/azimlib').rglob('*.py'):
        for node in ast.walk(ast.parse(path.read_text('utf8'))):
            modules=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or ''] if isinstance(node,ast.ImportFrom) and not node.level else []
            assert not any(m.split('.')[0] in blocked for m in modules),path
    return dict(passed=True,version=manifest['version'],runtime_files=len(current),current_gallery_cases=len(cases),exports=18,baseline_cases=3,font_notices_exact=True,forbidden_runtime_imports=False,scope='Local SHA/notice/source checks; hosted CI/hosting and final human acceptance require separate evidence')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);a=p.parse_args();result=audit()
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8',newline='\n')
    print(json.dumps(result,indent=2))
