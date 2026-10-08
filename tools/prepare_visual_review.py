"""Deterministic installed-package visual packet; never records human approval."""
from __future__ import annotations
import argparse
import hashlib
import html
import importlib.util
import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'tools/baselines/visual-review030'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_digest(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def example(name):
    path = ROOT / 'examples' / (name + '.py')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def specimens(azl):
    fig, axes = azl.subplots(1, 2, figsize=(10, 4.8), layout='constrained')
    for ax in axes:
        ax.set_extent((-10, 10, -10, 10))
        ax.set_xlabel('Longitude', labelpad=7)
        ax.set_ylabel('Latitude', labelpad=7)
        ax.grid(color='#c5c5c5', linewidth=.4, linestyle='--')
    ax = axes[0]
    ax.set_title('Text / markers\nAccents and alignment', pad=9)
    ax.tick_params(labelrotation=30)
    ax.text(-8, 7, 'São Paulo · Ångström · Δ', fontsize=12)
    ax.text(-8, 4, 'Bold / italic', fontsize=12, fontweight='bold', fontstyle='italic')
    ax.text(0, 1, 'Rotation 30°', rotation=30, ha='center', fontsize=11)
    ax.annotate('Offset in points', (-3, -3), (22, 18), textcoords='offset points', fontsize=10)
    for x, marker, color in zip((-7, -3, 1, 5), ('o', 's', 'D', '^'), ('#b64847', '#308564', '#8150a0', '#2e739e')):
        ax.plot([x, x+1], [-7, -6], marker=marker, markersize=8, linewidth=.8, color=color, label=marker)
    ax.legend(loc='lower right', title='Symbols', fontsize=8)
    ax = axes[1]
    ax.set_title('Physical strokes / caps / joins')
    for y, width in zip((8, 6, 4, 2), (.4, .8, 1.5, 3)):
        ax.line([(-7, y), (2, y)], color='#266783', linewidth=width)
        ax.text(3, y, f'{width:g} pt', fontsize=9, va='center')
    for y, cap, join in zip((0, -2, -4), ('butt', 'round', 'projecting'), ('miter', 'round', 'bevel')):
        ax.plot([-7, -3, 1], [y, y+1, y], linewidth=3, solid_capstyle=cap, solid_joinstyle=join, linestyle='--', dash_capstyle=cap, dash_joinstyle=join, label=cap)
        ax.text(2, y, f'{cap} / {join}', fontsize=8, va='center')
    from azimlib.path import Path as GeoPath
    from azimlib.patches import PathPatch
    path = GeoPath([(-7, -8), (-5, -4), (1, -10), (6, -6)], [1, 4, 4, 4])
    ax.add_patch(PathPatch(path, facecolor='none', edgecolor='#b64847', linewidth=1.2))
    return fig


CASES = [
    ('political', 'Countries, boundaries, scale, north, legend'),
    ('physical', 'Rivers, lakes, physical map and legend'),
    ('urban', 'Synthetic streets, buildings, neighbourhoods, symbols'),
    ('scientific', 'Raster / continuous horizontal colorbar'),
    ('terrain3d', 'Perspective / orthographic terrain and extruded buildings'),
    ('temporal', 'Frame 2: colors, labels, proportional markers'),
    ('series', 'Marker aspect, physical strokes, line cycles, legends'),
    ('text', 'Edited annotation, title, axis labels, legend / colorbar'),
    ('geodesy', 'Ellipsoidal UTM, stereographic, azimuthal, globe clipping'),
    ('contours', 'Contour labels, NoData, triangulation, colorbar layout'),
    ('labels', 'Collision priorities, inset and explicit annotation obstacles'),
    ('regional-labels', 'Real river labels, Manaus halo, leader, overview focus'),
    ('projections', 'Six spherical projections, graticules and hemispherical clipping'),
    ('specimens', 'Accents, rotation, physical points, caps and cubic curve'),
]
HIGH_DPI = {'series', 'text', 'specimens'}


def make(name, azl):
    if name in {case[0] for case in CASES[:6]}:
        return example('release_atlas').create(name)
    if name == 'series': return example('series_styles').build(module=azl)[0]
    if name == 'text':
        module = example('text_edits'); fig, *parts = module.build(); module.edit(*parts); return fig
    if name == 'geodesy': return example('geodesy_atlas').create()
    if name == 'contours': return example('scientific_atlas').create()
    if name == 'labels': return example('labels').obstacles()
    if name == 'regional-labels': return example('labels').hydrography((-64, -52, -8, 0), 'Regional hydrography / Manaus', regional=True)
    if name == 'projections': return example('gallery').projections()
    if name == 'specimens': return specimens(azl)
    raise ValueError(name)


def native(output, backend, azl):
    from PIL import Image, ImageGrab
    records = []
    def pump(viewer):
        for _ in range(8):
            viewer.flush_events(); time.sleep(.04)
        viewer.draw(); viewer.flush_events()

    def capture(viewer, key, window=None):
        window = window or viewer.window
        target = output / f'{backend}-{key}.png'
        if backend == 'qt':
            pump(viewer)
            expected = {'Linux': 'xcb', 'Darwin': 'cocoa', 'Windows': 'windows'}[platform.system()]
            if viewer.application.platformName() != expected:
                raise RuntimeError('Review requires a native Qt platform plugin')
            if not window.grab().save(str(target)): raise RuntimeError('Qt window capture failed')
            mode = 'native-window-grab'
        else:
            window.deiconify(); window.lift(); window.update_idletasks(); window.update()
            pump(viewer)
            window.update()
            x, y = window.winfo_rootx(), window.winfo_rooty()
            w, h = window.winfo_width(), window.winfo_height()
            kwargs = {'bbox': (x, y, x+w, y+h)}
            if platform.system() == 'Linux': kwargs['xdisplay'] = ''
            if platform.system() == 'Darwin': kwargs['scale_down'] = True
            # Capture the mapped application rectangle, never the whole desktop.
            ImageGrab.grab(**kwargs).save(target)
            mode = 'mapped-native-window-crop'
        with Image.open(target) as image:
            image.load()
            if min(image.size) < 100 or image.convert('RGB').getextrema() == ((0, 0),)*3:
                raise RuntimeError('Empty native capture')
            size = list(image.size)
        records.append({'file': target.name, 'backend': backend, 'capture': mode, 'pixels': size, 'sha256': digest(target)})

    for name in ('urban', 'terrain3d', 'temporal'):
        movie = None
        if name == 'temporal':
            from azimlib.animation import FuncAnimation
            module = example('temporal_atlas')
            fig, ax = azl.subplots(figsize=(6, 4))
            fig.subplots_adjust(bottom=.27, right=.82)
            image = ax.imshow(module.climate(0, 8), extent=module.EXTENT, origin='lower', cmap='magma')
            ax.set_extent(module.EXTENT); ax.set_title('Temporal controls / synthetic climate')
            fig.colorbar(image, ax=ax, label='Temperature (°C)')
            series = azl.TemporalSeries(range(4), [module.climate(i, 8) for i in range(4)], unit='step')
            binding = series.bind(image)
            movie = FuncAnimation(fig, lambda index: binding.apply(index), 4, autoplay=False)
            movie.add_controls(fig.add_axes((.25, .04, .45, .07)), fig.add_axes((.75, .04, .1, .07)))
            movie.seek(2, draw=False)
        else: fig = make(name, azl)
        viewer = fig.show(backend=backend, block=False)
        try:
            pump(viewer); capture(viewer, name)
            if name == 'urban':
                original = fig.axes[0].get_extent()
                x, y, w, h = viewer.scene.maps[0]['box']
                if backend == 'qt':
                    from PySide6 import QtCore, QtTest
                    ratio = viewer.widget.devicePixelRatioF()
                    point = QtCore.QPoint(round((x+w/2)/ratio), round((y+h/2)/ratio))
                    viewer.command('pan')
                    QtTest.QTest.mousePress(viewer.widget, QtCore.Qt.MouseButton.LeftButton, pos=point)
                    QtTest.QTest.mouseMove(viewer.widget, point+QtCore.QPoint(25, 12))
                    QtTest.QTest.mouseRelease(viewer.widget, QtCore.Qt.MouseButton.LeftButton, pos=point+QtCore.QPoint(25, 12))
                else:
                    viewer.set_mode('pan')
                    for event, dx, dy in (('<ButtonPress-1>', 0, 0), ('<B1-Motion>', 25, 12), ('<ButtonRelease-1>', 25, 12)):
                        viewer.widget.event_generate(event, x=round(x+w/2+dx), y=round(y+h/2+dy)); viewer.flush_events()
                pump(viewer)
                if fig.axes[0].get_extent() == original: raise RuntimeError('Native pan did not change extent')
                capture(viewer, 'urban-pan')
                viewer.command('home') if backend == 'qt' else viewer.home()
                pump(viewer)
                if fig.axes[0].get_extent() != original: raise RuntimeError('Home did not restore extent')
                capture(viewer, 'urban-home')
                dialog = viewer.subplots_dialog() if backend == 'qt' else viewer.configure_subplots()
                capture(viewer, 'subplots', dialog if backend == 'qt' else dialog.window)
                dialog.close() if backend == 'qt' else dialog.window.destroy()
        finally:
            if movie is not None: movie.close()
            viewer.close(); azl.close(fig)
    return records


def audit_packet(output):
    sys.path.insert(0, str(ROOT / 'tools'))
    from publication_privacy import findings
    from PIL import Image
    for path in output.rglob('*'):
        if not path.is_file(): continue
        issues = findings(path.read_bytes())
        if path.suffix == '.png':
            with Image.open(path) as image:
                image.load()
                issues += findings(json.dumps(image.info, default=str).encode())
        if issues: raise RuntimeError(f'Privacy findings: {path.relative_to(output)}: {issues}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--record-reference', action='store_true')
    parser.add_argument('--native', action='store_true')
    args = parser.parse_args()
    import azimlib as azl
    runtime = Path(azl.__file__).resolve().parent
    assert runtime.is_relative_to(Path(sys.prefix).resolve()), 'Use an installed package'
    tracked_runtime = subprocess.check_output(['git', 'ls-files', 'src/azimlib/*.py'], cwd=ROOT, text=True).splitlines()
    installed_sources = {p.relative_to(runtime).as_posix(): source_digest(p) for p in runtime.rglob('*.py')}
    git_sources = {name.removeprefix('src/azimlib/'): hashlib.sha256(subprocess.check_output(['git', 'show', 'HEAD:'+name], cwd=ROOT).replace(b'\r\n', b'\n')).hexdigest() for name in tracked_runtime}
    if installed_sources != git_sources: raise RuntimeError('Installed runtime differs from the checked-out Git commit')
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()): raise RuntimeError('Use an empty output directory')
    sys.path.insert(0, str(ROOT / 'examples'))
    provenance = {'version': azl.__version__, 'platform': platform.system(), 'python': platform.python_version(),
        'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'human_approval': 'awaiting-human-approval',
        'runtime_sha256': {p.relative_to(runtime).as_posix(): digest(p) for p in sorted(runtime.rglob('*.py'))},
        'generator_sha256': source_digest(Path(__file__)),
        'examples_sha256': {p.name: source_digest(p) for p in sorted((ROOT / 'examples').glob('*.py'))},
        'runtime_canonical_sha256': {p.relative_to(runtime).as_posix(): source_digest(p) for p in sorted(runtime.rglob('*.py'))},
        'source_hash_policy': 'Normalize CRLF to LF only for .py source comparison; runtime_sha256 preserves raw installed bytes',
        'packages': {name: importlib.metadata.version(name) for name in ('Pillow', 'numpy', 'aggdraw')},
        'font_sha256': {p.name: digest(p) for p in sorted((runtime / 'fonts').glob('*.ttf'))},
        'reference_scope': 'Own Windows exports, comparison baseline only; not human approved and not Matplotlib'}
    records = []
    for name, description in CASES:
        fig = make(name, azl)
        try:
            for dpi in (100, 200) if name in HIGH_DPI else (100,):
                filename = f'{name}-{dpi}dpi.png'
                fig.savefig(output / filename, dpi=dpi)
                if not args.record_reference:
                    target = output / f'{name}-{dpi}dpi.svg'
                    fig.savefig(target, dpi=dpi)
                    example('temporal_atlas').portable_svg(target)
                records.append({'case': name, 'description': description, 'dpi': dpi, 'file': filename, 'sha256': digest(output / filename)})
        finally: azl.close(fig)
        print(f'Rendered {name}', flush=True)
    provenance['images'] = records
    if args.record_reference:
        (output / 'manifest.json').write_text(json.dumps(provenance, indent=2)+'\n', encoding='utf8', newline='\n')
        audit_packet(output)
        return
    reference = json.loads((REFERENCE / 'manifest.json').read_text('utf8'))
    # Source changes invalidate a reference even when an image still looks similar.
    if any(reference[key] != provenance[key] for key in ('version', 'generator_sha256', 'examples_sha256', 'runtime_canonical_sha256')):
        raise RuntimeError('Reference generator/examples are stale')
    (output / 'reference').mkdir()
    for record in reference['images']:
        path = REFERENCE / record['file']
        if digest(path) != record['sha256']: raise RuntimeError('Reference hash mismatch')
        shutil.copyfile(path, output / 'reference' / path.name)
    shutil.copyfile(REFERENCE / 'manifest.json', output / 'reference/manifest.json')
    provenance['native'] = []
    if args.native:
        for backend in ('tk', 'qt'):
            provenance['native'].extend(native(output, backend, azl))
    fig = make('urban', azl)
    try:
        fig.show(backend='browser', open_browser=False, path=output / 'urban-interactive.html')
    finally: azl.close(fig)
    for forbidden in ('matplotlib', 'cartopy', 'geopandas', 'shapely', 'pyproj'):
        assert forbidden not in sys.modules, f'Unexpected cartographic backend: {forbidden}'
    legal = output / 'legal'; legal.mkdir()
    for name in ('LICENSE', 'THIRD_PARTY_LICENSES.md', 'NOTICE_COLORMAPS'):
        shutil.copyfile(ROOT / name, legal / name)
    shutil.copytree(ROOT / 'licenses', legal / 'licenses')
    shutil.copyfile(ROOT / 'src/azimlib/fonts/LICENSE_DEJAVU', legal / 'LICENSE_DEJAVU')
    rows = []
    for record in records:
        filename = record['file']; svg = filename[:-3]+'svg'
        rows.append(f'<section><h2>{html.escape(record["case"])} · {record["dpi"]} dpi</h2><p>{html.escape(record["description"])}</p><a href="{svg}">SVG</a> · <a href="{filename}">PNG at full size</a><div class="pair"><figure><figcaption>Windows reference (not approved)</figcaption><a href="reference/{filename}"><img src="reference/{filename}"></a></figure><figure><figcaption>{html.escape(platform.system())} actual</figcaption><a href="{filename}"><img src="{filename}"></a></figure></div></section>')
    for record in provenance['native']:
        rows.append(f'<section><h2>{record["file"]}</h2><p>{record["capture"]}; toolkit chrome is platform specific.</p><a href="{record["file"]}"><img class="native" src="{record["file"]}"></a></section>')
    header = '<!doctype html><html lang="en"><meta charset="utf-8"><title>Azimlib 0.3 visual review</title><style>body{font:16px sans-serif;margin:24px;color:#222;background:white}.pair{display:flex;gap:16px}figure{margin:0;width:50%}img{width:100%;height:auto}.native{width:auto;max-width:100%}section{border-top:1px solid #ccc;margin-top:24px;padding-top:8px}</style><h1>Azimlib 0.3.0.dev0 — human review pending</h1><p>Open full size links to inspect pixels. Reference and actual use identical examples and DPI. 200 dpi must preserve physical proportions. SVG is vector; browser font fallback may differ from bundled-font PNG. Native windows are real Tk/Qt, driven programmatically; screenshots cannot establish physical mouse latency.</p><p><a href="urban-interactive.html">Portable browser viewer (offline; does not reproduce remote native mouse latency)</a></p>'
    (output / 'index.html').write_text(header+'\n'.join(rows)+'</html>\n', encoding='utf8', newline='\n')
    (output / 'README.md').write_text('# Visual review — approval pending\n\nOpen index.html locally after extracting the ZIP. Compare Windows reference (left) with native-runner exports (right); full-size PNG and SVG links accompany every case. References are produced by Azimlib itself, not Matplotlib, and are not a previously approved gold standard.\n\n- Text: accents, rotated ticks, labels, axis/title spacing, clipping and overlap.\n- Strokes: .4/.8/1.5/3 pt, dashes, caps, cubic curve; compare 100/200 dpi physical proportions.\n- Symbols: circle/square/diamond/triangle proportions in map and legend.\n- Cartography: boundaries, urban features, inset focus, label priorities, projection horizons.\n- Colorbars/raster/contours: labels, orientation, NoData and layout.\n- 3D: depth, buildings, camera, clipping and colors.\n- Native Tk/Qt: toolbar, canvas, Subplots; compare urban, pan, Home and temporal/3D screenshots. Native toolkit chrome differs legitimately by OS.\n\nLinux uses real Tk/Qt on Xvfb. macOS uses native Aqua/Cocoa. Still images do not prove physical input latency; no human acceptance or release is inferred from a passing CI. Record approval or defects separately for each OS.\n\nPNG/SVG are generated by the independent Azimlib engine. Natural Earth, DejaVu and palettes retain their notices in legal/.\n', encoding='utf8', newline='\n')
    provenance['files'] = {p.relative_to(output).as_posix(): digest(p) for p in sorted(output.rglob('*')) if p.is_file()}
    (output / 'manifest.json').write_text(json.dumps(provenance, indent=2)+'\n', encoding='utf8', newline='\n')
    audit_packet(output)
    print(f'Packet complete: {len(records)} static PNG/SVG pairs, {len(provenance["native"])} native captures; approval pending', flush=True)


if __name__ == '__main__': main()
