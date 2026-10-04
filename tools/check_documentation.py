"""Audit local Markdown targets and execute the self-contained starter examples.

Checks local target existence, not external URLs or Markdown anchor resolution.
No network, viewer window, Matplotlib or GIS imports are needed.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def markdown_links(text):
    text = re.sub(r'^```.*?^```[^\n]*', '', text, flags=re.M | re.S)
    text = re.sub(r'`[^`\n]*`', '', text)
    # Actual repository links use normal or angle-bracket targets. Scan balanced
    # parentheses so a link to a file with parentheses is not truncated.
    for match in re.finditer(r'!?\[[^\]\n]*\]\(', text):
        start = match.end(); depth = 1; escaped = False; end = start
        while end < len(text) and depth:
            char = text[end]
            if escaped: escaped = False
            elif char == '\\': escaped = True
            elif char == '(': depth += 1
            elif char == ')': depth -= 1
            end += 1
        if not depth:
            target = text[start:end-1].strip()
            if target.startswith('<'): target = target[1:target.index('>')]
            else: target = target.split(' "', 1)[0].split(" '", 1)[0]
            yield target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=ROOT / 'docs/documentation-check.json')
    parser.add_argument('--output', type=Path, required=True, help='directory for snippet SVGs')
    parser.add_argument('--links-only', action='store_true')
    args = parser.parse_args()
    files = sorted([*ROOT.glob('*.md'), *(ROOT / 'docs').rglob('*.md')])
    broken = []; checked = 0; external = 0
    for path in files:
        for target in markdown_links(path.read_text(encoding='utf-8')):
            parts = urlsplit(target)
            if parts.scheme or target.startswith('//'): external += 1; continue
            if not parts.path: continue
            checked += 1
            if not (path.parent / unquote(parts.path)).exists():
                broken.append(dict(source=path.relative_to(ROOT).as_posix(), target=target))
    report = dict(python=platform.python_version(), platform=platform.platform(),
                  tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  markdown_sha256={path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
                  markdown_files=len(files), checked_local_targets=checked, skipped_external_targets=external,
                  broken=broken, snippet_exports=[], notes=['Local target existence; external links and heading anchors are not checked.'])
    if not args.links_only:
        import azimlib as azl
        report['azimlib'] = azl.__version__
        report['runtime_path'] = str(Path(azl.__file__).resolve())
        report['optional_modules_available'] = {name: importlib.util.find_spec(name) is not None
                                                for name in ('PIL', 'numpy', 'fontTools')}
        args.output.mkdir(parents=True, exist_ok=True)
        snippets = re.findall(r'^```python\s*\n(.*?)^```', (ROOT / 'docs/getting-started.md').read_text(encoding='utf-8'), re.M | re.S)
        previous = Path.cwd()
        try:
            os.chdir(args.output.resolve())
            for i, code in enumerate(snippets, 1):
                exec(compile(code, f'getting-started.md:snippet-{i}', 'exec'), {})
            for path in sorted(Path.cwd().glob('*.svg')):
                text = path.read_text(encoding='utf-8')
                assert text.startswith('<svg') and '<script' not in text
                report['snippet_exports'].append(dict(file=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
            assert len(report['snippet_exports']) == len(snippets) == 3
        finally:
            azl.close('all'); os.chdir(previous)
        forbidden = {'matplotlib', 'cartopy', 'geopandas', 'shapely', 'pyproj', 'folium'}
        report['external_cartography_imports'] = sorted(name for name in sys.modules if name.split('.')[0] in forbidden)
        assert not report['external_cartography_imports']
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('markdown_files', 'checked_local_targets', 'broken', 'snippet_exports')}, ensure_ascii=False))
    if broken: raise SystemExit(1)


if __name__ == '__main__': main()
