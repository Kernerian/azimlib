"""Audit current gallery artifacts, installed-runtime parity and documentation.

Run after release_gallery.py / check_documentation.py. Does not import any
renderer, optional dependency or reference library.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name): return json.loads((ROOT / 'docs' / name).read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wheel-gallery', type=Path, required=True)
    args = parser.parse_args()
    source = read('release-gallery.json'); installed = read('release-gallery-wheel.json')
    assert source['runtime_sha256'] == installed['runtime_sha256']
    assert source['example_sha256'] == installed['example_sha256']
    assert source['tool_sha256'] == installed['tool_sha256'] == digest(ROOT / 'tools/release_gallery.py')
    for name, value in source['runtime_sha256'].items():
        path=ROOT/'src/azimlib'/name
        candidates=[path,*(ROOT/'tools/baselines').rglob(path.name)]
        assert value in {digest(candidate) for candidate in candidates if candidate.is_file()},name
    for name, value in source['example_sha256'].items(): assert value == digest(ROOT / 'examples' / name), name
    assert installed['runtime_imports_external_cartography'] is False
    assert len(source['cases']) == 38 and len(installed['cases']) == 19
    own = {(case['name'], case['dpi']): case for case in source['cases']}
    assert len(own) == 38 and {case['dpi'] for case in source['cases']} == {100, 200}
    assert len({case['name'] for case in source['cases']}) == 19
    for report, folder in ((source, ROOT / 'gallery'), (installed, args.wheel_gallery)):
        assert digest(folder / 'release-overview.png') == report['overview_sha256']
        for case in report['cases']:
            assert not case['audit']['outside_unclipped_text'], (case['name'], case['dpi'])
            assert case['audit']['svg_texts_match_scene'] and case['audit']['static_without_ui']
            for key in ('files_sha256', 'reference_sha256'):
                for name, value in case.get(key, {}).items(): assert digest(folder / name) == value, name
            if report is installed:
                expected = own[(case['name'], case['dpi'])]
                assert case['audit'] == expected['audit'], case['name']
                assert case['files_sha256'] == expected['files_sha256'], case['name']
    assert sum('native_axes' in case for case in source['cases']) == 8
    assert sum('same_scene_agg' in case for case in source['cases']) == 5
    snippet_sets = []
    for name in ('documentation-check.json', 'documentation-core.json', 'documentation-wheel.json'):
        report = read(name)
        assert not report['broken'] and not report['external_cartography_imports']
        assert len(report['snippet_exports']) == 3
        if name == 'documentation-core.json': assert not any(report['optional_modules_available'].values())
        assert report['tool_sha256'] == digest(ROOT / 'tools/check_documentation.py')
        for path, value in report['markdown_sha256'].items(): assert value == digest(ROOT / path), (name, path)
        snippet_sets.append(report['snippet_exports'])
    assert snippet_sets[0] == snippet_sets[1] == snippet_sets[2]
    result = dict(exports=38, installed_exports_identical=19, native_axes_pairs=8,
                  same_scene_agg_pairs=5, snippet_runs=9, local_links=report['checked_local_targets'],
                  recorded_runtime_and_artifact_hashes_verified=True,
                  scope='0.1.0 gallery evidence remains historical when modules resolve to preserved snapshots; current release exports are checked separately.')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__': main()
