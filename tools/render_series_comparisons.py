"""Development reference only: real Matplotlib styles and multi-series routes."""
import importlib.util
from pathlib import Path
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('series_examples',ROOT/'examples/series_styles.py')
example=importlib.util.module_from_spec(spec);spec.loader.exec_module(example)


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as mpl
    for theme in ('light','dark'):
        fig,axes,lines,named=example.build(theme,module=mpl)
        try:
            example.edit(axes,lines,named,theme,module=mpl);fig.savefig(ROOT/f'gallery/series-{theme}-matplotlib.png')
        finally:mpl.close(fig)
        with Image.open(ROOT/f'gallery/series-{theme}-after.png') as own, Image.open(ROOT/f'gallery/series-{theme}-matplotlib.png') as reference:
            composite=Image.new('RGB',(own.width+reference.width,max(own.height,reference.height)+24),'white')
            composite.paste(own,(0,24));composite.paste(reference,(own.width,24));draw=ImageDraw.Draw(composite)
            draw.text((8,6),'Azimlib / renderer proprio',fill='black')
            draw.text((own.width+8,6),f'Matplotlib {matplotlib.__version__} / Agg',fill='black')
            composite.save(ROOT/f'gallery/series-{theme}-comparison.png');composite.close()


if __name__=='__main__':main()
