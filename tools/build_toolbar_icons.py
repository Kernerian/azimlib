"""Build Azimlib's own vector/bitmap assets; never imports Matplotlib."""
import hashlib
import json
from pathlib import Path
from azimlib._toolbar_icons import NAMES,icon_svg,icon_image
import azimlib._toolbar_icons as geometry

ROOT=Path(__file__).resolve().parents[1]


def build():
    target=ROOT/'src/azimlib/assets/icons'; target.mkdir(parents=True,exist_ok=True)
    rows={}
    for name in NAMES:
        path=target/(name+'.svg'); path.write_bytes(icon_svg(name).encode('utf-8'))
        rows[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
        for size,suffix in ((24,'.png'),(48,'_large.png')):
            path=target/(name+suffix)
            with icon_image(name,size) as image:image.save(path)
            rows[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    report=dict(source='Original Azimlib geometry',license='BSD-3-Clause',
                geometry_sha256=hashlib.sha256(Path(geometry.__file__).read_bytes()).hexdigest(),
                generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),files_sha256=rows)
    (target/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('21 original Azimlib assets generated from shared vector geometry')


if __name__=='__main__':build()
