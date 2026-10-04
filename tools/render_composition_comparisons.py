"""Development-only real-map comparison; Matplotlib is never a backend."""
from pathlib import Path
from PIL import Image, ImageDraw
from compare_composition_matrix import example, azl, ROOT


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as mpl
    output=ROOT/'gallery'
    for kind in ('single','atlas'):
        fig,_,_=example.build(kind,real_data=True,module=mpl)
        try:fig.savefig(output/f'composition-{kind}-matplotlib.png')
        finally:mpl.close(fig)
        with Image.open(output/f'composition-{kind}.png') as own, Image.open(output/f'composition-{kind}-matplotlib.png') as reference:
            result=Image.new('RGB',(own.width+reference.width,max(own.height,reference.height)+24),'white')
            result.paste(own,(0,24));result.paste(reference,(own.width,24))
            draw=ImageDraw.Draw(result)
            draw.text((8,6),'Azimlib / renderer proprio',fill='black')
            draw.text((own.width+8,6),f'Matplotlib {matplotlib.__version__} / Agg',fill='black')
            result.save(output/f'composition-{kind}-comparison.png')
            result.close()


if __name__=='__main__':main()
