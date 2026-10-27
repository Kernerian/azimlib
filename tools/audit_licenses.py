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
    grids = json.loads((ROOT/'src/azimlib/data/optional-grids.json').read_text('utf8'))
    assert grids == json.loads((ROOT/'docs/grid-models-0.4.json').read_text('utf8'))
    for grid in grids['datasets']:
        assert grid['license'] == 'CC-BY-4.0' and grid['version'] == '20200110'
        assert grid['upstream_commit'] in grid['source']
        assert grid['files']['CC-BY-4.0.txt'] == sha(ROOT/'licenses/CC-BY-4.0.txt')
        assert 'Land Information New Zealand' in grid['attribution']
        assert not (ROOT/'src/azimlib/data'/grid['file']).exists(), 'Optional grids must not be bundled'
    assert 'Optional official datum grids' in notices
    fonts_optional=json.loads((ROOT/'src/azimlib/data/optional-fonts.json').read_text('utf8'))['fonts']
    for font in fonts_optional:
        assert font['commit'] in font['url'] and font['commit'] in font['source']
        assert font['license_id']=='OFL-1.1'
        assert sha(ROOT/font['license_file'])==font['license_sha256']
        assert not (ROOT/'src/azimlib/fonts'/font['filename']).exists(), 'Optional Noto fonts must not be bundled'
    text_dependencies=json.loads((ROOT/'docs/text-dependencies-0.4.json').read_text('utf8'))['licenses']
    for entry in text_dependencies:assert sha(ROOT/entry['file'])==entry['sha256']
    assert 'Optional complex typography' in notices
    tex_dependencies=json.loads((ROOT/'docs/tex-dependencies-0.4.json').read_text('utf8'))['licenses']
    for entry in tex_dependencies:assert sha(ROOT/entry['file'])==entry['sha256']
    assert 'Optional real TeX integration' in notices
    gpu_dependencies=json.loads((ROOT/'docs/gpu-dependencies-0.4.json').read_text('utf8'))['licenses']
    for entry in gpu_dependencies:assert sha(ROOT/entry['file'])==entry['sha256']
    assert 'Optional GPU rendering' in notices
    for item in manifest['immutable_resources']:
        assert sha(ROOT / item['file']) == item['sha256'], item['file']
    retired = set(manifest['retired_palette_fingerprints'])
    def color_fingerprint(values):
        return hashlib.sha256(','.join(v.lower() for v in values).encode()).hexdigest()
    assert color_fingerprint(AZIM10) not in retired
    dark = tuple(row['color'] for row in style.library['dark_background']['axes.prop_cycle'])
    assert color_fingerprint(dark) not in retired
    oracle=json.loads((ROOT / 'docs/series-styles-reference.json').read_text('utf-8'))
    for library in ('azimlib','matplotlib'):
        roles=[row['color'] for group in ('multi','columns','broadcast_x','matrix_pair','data','implicit') for row in oracle[library][group]]
        assert roles == [f'cycle:{i}' for i in range(10)]
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
    for folder in ('branding', 'showcase', 'urban'):
        asset_root = ROOT / 'docs/_static' / folder
        asset_manifest = json.loads((asset_root / 'manifest.json').read_text('utf-8'))
        for asset in asset_manifest['files']:
            path = asset_root / asset['file']
            assert sha(path) == asset['sha256'], path
            raw = path.read_bytes()
            assert raw[:8] == b'\x89PNG\r\n\x1a\n', path
            assert [int.from_bytes(raw[16:20], 'big'), int.from_bytes(raw[20:24], 'big')] == asset['pixels'], path
    assert json.loads((ROOT / 'docs/_static/branding/manifest.json').read_text('utf-8'))['copyright'] == 'Copyright (c) 2026 Kernerian'
    typography=json.loads((ROOT/'docs/_static/branding/manifest.json').read_text('utf8'))['wordmark_typography']
    assert typography['family']=='Carlito' and typography['style']=='Bold Italic' and typography['license']=='OFL-1.1'
    assert 'Carlito Bold Italic' in notices and 'rasterized lettering' in notices
    assert not any('carlito' in p.name.lower() and p.suffix.lower() in ('.ttf','.otf','.woff','.woff2') for p in ROOT.rglob('*') if '.git' not in p.parts)
    lunar=json.loads((ROOT/'docs/lunar-model-0.4.json').read_text('utf8'))
    from azimlib.lunar import LONGITUDE_TERMS,LATITUDE_TERMS,PARALLAX_TERMS,MOON_RADIUS_M
    assert lunar['model_coefficients']==json.loads(json.dumps(dict(longitude=LONGITUDE_TERMS,latitude=LATITUDE_TERMS,parallax=PARALLAX_TERMS)))
    assert lunar['moon_mean_radius_m']==MOON_RADIUS_M and lunar['historic_model_earth_radius_m']==6378140.
    assert lunar['source']=='https://ntrs.nasa.gov/citations/19990040527'
    assert not lunar['third_party_implementation_incorporated'] and not lunar['raw_reference_data_distributed']
    assert 'Lunar model definitions and reference-only validation' in notices
    lighting=json.loads((ROOT/'docs/lighting-model-0.4.json').read_text('utf8'))
    from azimlib.eclipse import SUN_RADIUS_M,EARTH_SHADOW_RADIUS_M
    assert lighting['sun_nominal_radius_m']==SUN_RADIUS_M and lighting['earth_shadow_radius_m']==EARTH_SHADOW_RADIUS_M
    assert not lighting['third_party_implementation_incorporated'] and not lighting['raw_reference_data_distributed']
    assert 'Physical light and finite-source geometry' in notices
    # Own example assets remain separate from third-party material notices.
    own=json.loads((ROOT/'examples/thematic/assets/provenance.json').read_text('utf8'))
    for name,item in own.items():
        assert sha(ROOT/'examples/thematic/assets'/name)==item['sha256'],name
        assert item['license']=='BSD-3-Clause' and 'Kernerian' in item['credit'],name
    from azimlib.thematic_assets import symbol_catalog
    assert all(s.source.origin=='azimlib:programmatic-catalog' and s.source.license=='BSD-3-Clause' for s in symbol_catalog("original").values())
    lucide=json.loads((ROOT/'src/azimlib/assets/lucide/manifest.json').read_text('utf8'))
    assert sha(ROOT/lucide['license_file'])==lucide['license_sha256']
    assert sha(ROOT/'src/azimlib/assets/lucide/LICENSE.txt')==lucide['license_sha256']
    assert lucide['commit']=='c29c276f16590cf017126671535ad8c792be64d8'
    for icon in lucide['icons']:
        assert sha(ROOT/'src/azimlib/assets/lucide'/icon['file'])==icon['sha256']
        assert lucide['commit'] in icon['source'] and not icon['modified']
    assert 'Lucide cartographic icon subset' in notices
    return {'passed': True, 'original_code_license': 'BSD-3-Clause', 'copyright_identifier': 'Kernerian',
            'lucide_svg_assets_verified':len(lucide['icons']), 'lucide_license_sha256':lucide['license_sha256'],
            'materials': ['Lucide pinned SVG subset / ISC and Feather MIT','ColorBrewer Blues 5', 'BIDS CC0 colormaps', 'Natural Earth', 'DejaVu and metrics', 'Carlito wordmark artwork credit (font not shipped)', 'LINZ optional grid metadata and CC BY 4.0 notice (grids not shipped)'],
            'license_texts_verified': len(manifest['license_texts'])+len(text_dependencies)+len(fonts_optional)+len(tex_dependencies)+len(gpu_dependencies), 'own_cycle_colors': len(AZIM10),
            'optional_gpu_notices':len(gpu_dependencies),
            'optional_tex_reference_notices':len(tex_dependencies),
            'optional_text_dependencies_and_font_notices': len(text_dependencies)+len(fonts_optional),
            'unchanged_geographic_layers': len(data['layers']), 'unchanged_upstream_fonts': len(fonts['files']),
            'unchanged_colormap_and_font_metric_resources': len(manifest['immutable_resources']),
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
