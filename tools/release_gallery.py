"""Reproduce the documented 0.2 cut, without opening a window.

Default: PNG/SVG/HTML for 19 examples in 100/200 DPI. Matplotlib is never
imported unless --reference is requested in a separate development environment.
The latter renders the SAME Azimlib Scene through Agg for selected maps and
also builds independent native Axes references for series/numeric colorbars.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import platform
import sys
import xml.etree.ElementTree as ET

import azimlib as azl
from azimlib.renderers import render_png, render_svg
from azimlib.scene import Text
from azimlib.layout_engine import primitive_bounds

ROOT = Path(__file__).resolve().parents[1]
CATALOG = {
    'components': ('components.py', 'create', 'territories, rivers, styled routes, legend, compass, scale, halo annotation'),
    'brazil': ('regions.py', 'create', 'complete country and optional components'),
    'state': ('regions.py', 'create', 'isolated state and overview'),
    'focus': ('regions.py', 'create', 'zoomed state and black overview focus'),
    'series-light': ('series_styles.py', 'build', 'matrix/data=, edited diamond, styles and legend'),
    'series-dark': ('series_styles.py', 'build', 'same edited series with dark style'),
    'colorbar': ('scientific.py', 'colorbar_example', 'continuous choropleth, vertical editable bar'),
    'colorbar-horizontal': ('scientific.py', 'horizontal_example', 'same choropleth, horizontal editable bar'),
    'hatch-catalog': ('scientific.py', 'hatch_catalog', 'ten basic hatches, repetition, combinations and polygon holes'),
    'contours-before': ('contour_refinement.py', 'create', 'per-level isolines, labels and two line colorbars'),
    'contours-after': ('contour_refinement.py', 'create', 'edited colormap and reversible inline label gaps'),
    'terrain': ('scientific.py', 'terrain_example', 'synthetic scalar elevation, hillshade, isolines and coast'),
    'globe': ('scientific.py', 'globe_example', 'orthographic globe, graticule, spherical routes and vectors'),
    'numeric-vertical': ('numeric_formatting.py', 'build', 'scientific notation and additive offset, vertical bars'),
    'numeric-horizontal': ('numeric_formatting.py', 'build', 'scientific notation and additive offset, horizontal bars'),
    'thematic': ('gallery.py', 'thematic', 'synthetic regional values, proportional points, routes and inset'),
    'density': ('gallery.py', 'density', 'seeded synthetic events, smoothed angular counts'),
    'projections': ('gallery.py', 'projections', 'six own spherical projections'),
    'atlas': ('gridspec_atlas.py', 'create', 'spans, shared colorbar and explicit ornaments'),
}


def module(name):
    path = ROOT / 'examples' / name
    spec = importlib.util.spec_from_file_location('release_example_' + path.stem, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def create(name, *, library=azl):
    filename, function, _ = CATALOG[name]
    example = module(filename)
    if name in ('brazil', 'state', 'focus'):
        return example.create(name)
    if name.startswith('series-'):
        theme = name.split('-', 1)[1]
        fig, axes, lines, named = example.build(theme, module=library)
        example.edit(axes, lines, named, theme, module=library)
        return fig
    if name.startswith('numeric-'):
        return example.build(name.split('-', 1)[1], module=library)[0]
    if name.startswith('contours-'):
        fig, contours, labels = example.create()
        if name.endswith('after'):
            from azimlib.colors import ListedColormap
            for contour, texts in zip(contours, labels):
                contour.set(cmap=ListedColormap(['#7b3294', '#008837', '#d95f02']), linewidths=[.7, .9, 1.1])
                azl.setp(texts, inline=True, inline_spacing=5, fontsize=9)
            fig.suptitle('Azimlib · cortes sob rótulos e paleta atualizada', fontsize=14)
        return fig
    result = getattr(example, function)()
    return result[0] if isinstance(result, tuple) else result


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(scene, svg, png):
    from PIL import Image
    from azimlib.renderers._common import validate
    validate(scene)
    root = ET.fromstring(svg)
    ns = '{http://www.w3.org/2000/svg}'
    assert root.tag == ns + 'svg'
    assert all(math.isclose(a, b, abs_tol=.001) for a, b in zip(
        map(float, root.attrib['viewBox'].split()), (0, 0, scene.width, scene.height)))
    assert not root.findall('.//' + ns + 'script')
    assert '<foreignObject' not in svg and 'http://127.0.0.1' not in svg
    texts = [item.text for item in scene.items if isinstance(item, Text)]
    assert texts == [''.join(node.itertext()) for node in root.findall('.//' + ns + 'text')]
    with Image.open(png) as image:
        assert image.size == (round(scene.width), round(scene.height))
        assert image.convert('RGB').getextrema() != ((255, 255),) * 3
        rgba_hash = hashlib.sha256(image.convert('RGBA').tobytes()).hexdigest()
    # Record free-text overflow rather than hiding manual-placement differences.
    outside = []
    for item in scene.items:
        if not isinstance(item, Text) or item.clip is not None:
            continue
        x, y, width, height = primitive_bounds(item)
        right, bottom = x + width, y + height
        if x < -.01 or y < -.01 or right > scene.width + .01 or bottom > scene.height + .01:
            outside.append(dict(text=item.text, bounds=[x, y, right, bottom]))
    return dict(pixels=[round(scene.width), round(scene.height)], items=len(scene.items),
                texts=len(texts), clips=len({item.clip for item in scene.items if item.clip is not None}),
                svg_texts_match_scene=True, static_without_ui=True, rgba_sha256=rgba_hash,
                outside_unclipped_text=outside)


def pair(own_path, ref_path, output, label):
    from PIL import Image, ImageDraw
    with Image.open(own_path) as own, Image.open(ref_path) as ref:
        assert own.size == ref.size, 'References must use the same physical size and export DPI'
        result = Image.new('RGB', (own.width + ref.width, max(own.height, ref.height) + 26), 'white')
        result.paste(own, (0, 26)); result.paste(ref, (own.width, 26))
        draw = ImageDraw.Draw(result)
        draw.text((8, 7), 'Azimlib / renderer próprio', fill='black')
        draw.text((own.width + 8, 7), label, fill='black')
        result.save(output)


def overview(folder, cases):
    from PIL import Image, ImageDraw
    cells = []
    for case in cases:
        if case['dpi'] != min(c['dpi'] for c in cases):
            continue
        with Image.open(folder / case['files']['png']) as image:
            image = image.convert('RGB'); image.thumbnail((330, 300))
            cell = Image.new('RGB', (350, 330), 'white')
            cell.paste(image, ((350 - image.width) // 2, 25))
            ImageDraw.Draw(cell).text((8, 8), case['name'], fill='black')
            cells.append(cell)
    sheet = Image.new('RGB', (350 * 4, 330 * math.ceil(len(cells) / 4)), '#e8e8e8')
    for i, cell in enumerate(cells):
        sheet.paste(cell, (350 * (i % 4), 330 * (i // 4)))
    sheet.save(folder / 'release-overview.png')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', nargs='+', choices=CATALOG, default=list(CATALOG))
    parser.add_argument('--dpi', type=int, nargs='+', default=[100, 200])
    parser.add_argument('--gallery', type=Path, default=ROOT / 'gallery')
    parser.add_argument('--report', type=Path, default=ROOT / 'docs/release-gallery.json')
    parser.add_argument('--reference', action='store_true')
    args = parser.parse_args()
    if any(value < 1 for value in args.dpi): parser.error('dpi must be positive')
    args.gallery.mkdir(parents=True, exist_ok=True)
    runtime = Path(azl.__file__).resolve().parent
    sources = {str(path.relative_to(runtime)).replace('\\', '/'): sha256(path) for path in sorted(runtime.rglob('*'))
               if path.is_file() and path.suffix in ('.py', '.js', '.css', '.ttf', '.json', '.gz')}
    report = dict(azimlib=azl.__version__, python=platform.python_version(), platform=platform.platform(),
                  runtime_sha256=sources, tool_sha256=sha256(Path(__file__)),
                  example_sha256={name: sha256(ROOT / 'examples' / name) for name, _, _ in CATALOG.values()},
                  notes=['Own cartographic scenes; fields, regional values, routes and events are synthetic.',
                         'PNG/SVG static exports share the scene. HTML is separate and is not a live Python canvas.',
                         'Same-Scene Agg checks isolate rasterization, not native Axes/projections/layout/hatch generation.',
                         'Native Axes checks independently build only series and numeric colorbar examples.',
                         'Pixel differences are descriptive, not perceptual scores or performance results.'], cases=[])
    if args.reference:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as mpl
        from compare_map_quality import reference, differences
        report['matplotlib'] = matplotlib.__version__
    for name in args.cases:
        for dpi in args.dpi:
            print(f'{name} / {dpi} DPI: composing', flush=True)
            fig = create(name)
            try:
                fig.set_dpi(dpi)
                scene = fig.to_scene(cull=True)
                prefix = f'release-{name}-{dpi}'
                png = args.gallery / (prefix + '.png')
                svg = render_svg(scene)
                (args.gallery / (prefix + '.svg')).write_text(svg, encoding='utf-8')
                render_png(scene, png)
                (args.gallery / (prefix + '.html')).write_text(fig.to_html(), encoding='utf-8')
                result = dict(name=name, dpi=dpi, source=CATALOG[name][0], covers=CATALOG[name][2],
                              files={ext: prefix + '.' + ext for ext in ('png', 'svg', 'html')},
                              audit=audit(scene, svg, png))
                if args.reference and name in ('components', 'state', 'focus', 'hatch-catalog', 'globe') and dpi == min(args.dpi):
                    from PIL import Image
                    agg = reference(scene, dpi)
                    ref_path = args.gallery / (prefix + '-agg.png'); agg.save(ref_path)
                    with Image.open(png) as own: metrics = differences(own, agg)
                    result['same_scene_agg'] = dict(file=ref_path.name, metrics=metrics)
                    pair(png, ref_path, args.gallery / (prefix + '-raster-comparison.png'),
                         f'Same Scene -> Matplotlib {matplotlib.__version__} / Agg')
                if args.reference and name.startswith(('series-', 'numeric-')):
                    native = create(name, library=mpl)
                    try:
                        native.set_dpi(dpi)
                        ref_path = args.gallery / (prefix + '-matplotlib.png')
                        # Matplotlib's savefig.dpi='figure' uses _original_dpi,
                        # even after set_dpi; request the comparison DPI explicitly.
                        native.savefig(ref_path, dpi=dpi)
                        native.savefig(args.gallery / (prefix + '-matplotlib.svg'), dpi=dpi)
                    finally: mpl.close(native)
                    result['native_axes'] = dict(file=ref_path.name,
                        difference='Series maps have Azimlib-only scale/north ornaments; reference has ordinary equal-aspect geographic degree axes.')
                    pair(png, ref_path, args.gallery / (prefix + '-native-comparison.png'),
                         f'Matplotlib {matplotlib.__version__} / native Axes + Agg')
                result['files_sha256'] = {path.name: sha256(path) for path in sorted(args.gallery.glob(prefix + '.*'))}
                if args.reference:
                    result['reference_sha256'] = {path.name: sha256(path) for path in sorted(args.gallery.glob(prefix + '-*'))}
                report['cases'].append(result)
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
                print(f'{name} / {dpi} DPI: {result["audit"]["items"]} primitives; '
                      f'{len(result["audit"]["outside_unclipped_text"])} outside texts', flush=True)
            finally: azl.close(fig)
    overview(args.gallery, report['cases'])
    report['overview_sha256'] = sha256(args.gallery / 'release-overview.png')
    report['runtime_imports_external_cartography'] = any(name.split('.')[0] in
        {'matplotlib', 'cartopy', 'geopandas', 'shapely', 'pyproj', 'folium'} for name in sys.modules) if not args.reference else None
    if not args.reference: assert report['runtime_imports_external_cartography'] is False
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'{len(report["cases"])} exports audited; {args.report}', flush=True)


if __name__ == '__main__': main()
