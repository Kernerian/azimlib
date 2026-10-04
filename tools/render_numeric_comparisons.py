"""Agg reference only; Azimlib exports are produced by its own renderers."""
import importlib.util
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('numeric_example',ROOT/'examples/numeric_formatting.py')
example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)

def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as mpl
    for orientation in ('vertical','horizontal'):
        fig,*_=example.build(orientation,module=mpl)
        try:fig.savefig(ROOT/f'gallery/numeric-{orientation}-matplotlib.png')
        finally:mpl.close(fig)
        with Image.open(ROOT/f'gallery/numeric-{orientation}.png') as own,Image.open(ROOT/f'gallery/numeric-{orientation}-matplotlib.png') as reference:
            joined=Image.new('RGB',(own.width+reference.width,max(own.height,reference.height)+24),'white')
            joined.paste(own,(0,24));joined.paste(reference,(own.width,24))
            draw=ImageDraw.Draw(joined);draw.text((8,6),'Azimlib / renderer proprio',fill='black')
            draw.text((own.width+8,6),f'Matplotlib {matplotlib.__version__} / Agg',fill='black')
            joined.save(ROOT/f'gallery/numeric-{orientation}-comparison.png');joined.close()

if __name__=='__main__':main()
