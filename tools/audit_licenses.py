"""Offline checks of shipped notices, provenance, palettes and immutable assets."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    import sys
    sys.path.insert(0, str(ROOT / 'src'))
    from azimlib.cycles import AZIM10, TAB10
    from azimlib.styles import PALETTES
    from azimlib import style
    manifest = json.loads((ROOT / 'src/azimlib/data/materials.json').read_text('utf-8'))
    assert (ROOT / 'LICENSE').read_text('utf-8').startswith('BSD 3-Clause License')
    assert 'Copyright (c) 2026 Kernerian' in (ROOT / 'LICENSE').read_text('utf-8')
    notices = (ROOT / 'THIRD_PARTY_LICENSES.md').read_text('utf-8')
    assert 'This product includes color specifications and designs developed by Cynthia' in notices
    assert 'Brewer (http://colorbrewer.org/).' in notices
    assert tuple(manifest['azim10']['colors']) == AZIM10 == TAB10
    assert len(AZIM10) == len(set(AZIM10)) == 10
    assert tuple(PALETTES['blues']) == tuple(manifest['colorbrewer_blues']['colors'])
    for item in manifest['license_texts']:
        assert sha(ROOT / item['file']) == item['sha256'], item['file']
    retired = set(manifest['retired_palette_fingerprints'])
    def color_fingerprint(values):
        return hashlib.sha256(','.join(v.lower() for v in values).encode()).hexdigest()
    assert color_fingerprint(AZIM10) not in retired
    dark = tuple(row['color'] for row in style.library['dark_background']['axes.prop_cycle'])
    assert color_fingerprint(dark) not in retired
    for directory in (ROOT / 'src', ROOT / 'tools/baselines'):
        for path in directory.rglob('*.py'):
            for node in ast.walk(ast.parse(path.read_text('utf-8'))):
                if isinstance(node, (ast.List, ast.Tuple)) and len(node.elts) == 10:
                    values = [n.value for n in node.elts if isinstance(n, ast.Constant) and isinstance(n.value, str)]
                    if len(values) == 10 and all(v.startswith('#') for v in values):
                        assert color_fingerprint(values) not in retired, path
    data = json.loads((ROOT / 'src/azimlib/data/manifest.json').read_text('utf-8'))
    for item in data['layers'].values():
        assert sha(ROOT / 'src/azimlib/data' / item['filename']) == item['sha256']
    fonts = json.loads((ROOT / 'docs/fonts-upstream.json').read_text('utf-8'))
    for item in fonts['files']:
        assert item['identical'] and sha(ROOT / 'src/azimlib/fonts' / item['file']) == item['sha256']
    return {'passed': True, 'original_code_license': 'BSD-3-Clause', 'copyright_identifier': 'Kernerian',
            'materials': ['ColorBrewer Blues 5', 'BIDS CC0 colormaps', 'Natural Earth', 'DejaVu and metrics'],
            'license_texts_verified': len(manifest['license_texts']), 'own_cycle_colors': len(AZIM10),
            'unchanged_geographic_layers': len(data['layers']), 'unchanged_upstream_fonts': len(fonts['files']),
            'scope': 'Local notice/hash/palette checks; does not establish legal title, trademark clearance or licenses of future dependency resolutions.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = audit()
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
