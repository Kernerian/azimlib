"""Development-only side-by-side rotation reference; no production Mpl import."""
from pathlib import Path
import azimlib as azl

ROOT=Path(__file__).resolve().parents[1]


def build(module):
    own=module is azl
    fig=module.figure(figsize=(6.4,7),dpi=150)
    for angle,box in zip((0,35,-35,90),((.16,.60,.30,.28),(.66,.60,.30,.28),
                                         (.16,.16,.30,.28),(.66,.16,.30,.28))):
        ax=fig.add_axes(box)
        ax.set_xlim(-54,-42);ax.set_ylim(-28,-16)
        if own:ax.states(fc='#f1f1f1',ec='#aaaaaa',lw=.35,fit=False)
        else:
            from matplotlib.patches import Polygon
            ax.set_aspect('equal')
            for feature in azl.datasets.load('states',country='brazil')['features']:
                geom=feature['geometry']
                rings=[geom['coordinates']] if geom['type']=='Polygon' else geom['coordinates']
                for ring in rings:ax.add_patch(Polygon(ring[0],fc='#f1f1f1',ec='#aaaaaa',lw=.35))
        ax.plot([-52,-48,-44],[-26,-22,-18],'D--',c='#9467bd',lw=1.2,ms=5,label='Rota')
        ax.set_xticks([-52,-48,-44],labels=['52°W','48°W','44°W'])
        ax.set_yticks([-26,-22,-18],labels=['26°S','22°S','18°S'])
        ax.tick_params(labelrotation=angle,labelsize=10)
        ax.set_xlabel('Longitude',labelpad=4);ax.set_ylabel('Latitude',labelpad=4)
        ax.set_title(f'Rotação {angle}°\nDados sintéticos',fontsize=12)
        ax.grid(lw=.4,ls=':',color='#cccccc')
    return fig


def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import Image,ImageDraw
    out=ROOT/'gallery'
    own=build(azl);native=build(plt)
    try:
        own.savefig(out/'text-rotation-azimlib.png');own.savefig(out/'text-rotation.svg')
        (out/'text-rotation.html').write_text(own.to_html(),encoding='utf-8')
        native.savefig(out/'text-rotation-matplotlib.png')
    finally:azl.close(own);plt.close(native)
    images=[Image.open(out/f'text-rotation-{name}.png').convert('RGB') for name in ('azimlib','matplotlib')]
    result=Image.new('RGB',(sum(i.width for i in images),images[0].height+28),'white')
    draw=ImageDraw.Draw(result);x=0
    for label,im in zip(('Azimlib / renderer próprio',f'Matplotlib {matplotlib.__version__} / Agg'),images):
        draw.text((x+8,7),label,fill='black');result.paste(im,(x,28));x+=im.width
    result.save(out/'text-rotation-comparison.png')
    print('Four angles; PNG/SVG/HTML and direct Agg comparison generated.')


if __name__=='__main__':main()
