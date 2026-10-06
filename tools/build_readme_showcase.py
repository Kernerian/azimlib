"""Render the public README showcase with Azimlib, without Matplotlib or UI."""
import hashlib
import json
from pathlib import Path
from PIL import Image
import azimlib as azl
from release_gallery import create

ROOT = Path(__file__).resolve().parents[1]


def main():
    folder = ROOT / 'docs/_static/showcase'
    folder.mkdir(parents=True, exist_ok=True)
    records = []
    panels = []
    for name in ('brazil', 'colorbar-horizontal', 'globe', 'terrain'):
        fig = create(name)
        png = folder / (name + '.png')
        fig.savefig(png, dpi=110)
        azl.close(fig)
        with Image.open(png) as im:
            original_size = list(im.size)
            im = im.convert('RGB')
            im.thumbnail((580, 525), Image.Resampling.LANCZOS)
            panel = Image.new('RGB', (600, 545), 'white')
            panel.paste(im, ((600-im.width)//2, (545-im.height)//2))
            panels.append(panel)
        records.append({'file': png.name, 'pixels': original_size,
                        'sha256': hashlib.sha256(png.read_bytes()).hexdigest(),
                        'example': name})
    overview = Image.new('RGB', (1200, 1090), 'white')
    for i, panel in enumerate(panels):
        overview.paste(panel, (600*(i%2), 545*(i//2)))
    path = folder / 'overview.png'
    overview.save(path, optimize=True)
    records.append({'file': path.name, 'pixels': list(overview.size),
                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    report = {'renderer': 'Azimlib', 'version': azl.__version__,
              'data': 'Natural Earth boundaries/rivers; synthetic thematic values, terrain and vectors',
              'generator': 'tools/build_readme_showcase.py', 'files': records}
    (folder / 'manifest.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('Rendered four own-library examples and README overview.')


if __name__ == '__main__':
    main()
