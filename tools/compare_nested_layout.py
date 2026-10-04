"""Development-only manual nested allocation and map-rendering reference."""
from pathlib import Path
import azimlib as azl
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw

folder=Path(__file__).resolve().parents[1]/'gallery'
data=azl.read_geojson(azl.datasets.country('brazil'))
arrangement=[['A',[['B','C'],['D','C']]]]
for name,library in (('azimlib',azl),('matplotlib',plt)):
    fig,axes=library.subplot_mosaic(arrangement,figsize=(6,5),dpi=100,
        gridspec_kw={'wspace':.35,'hspace':.45})
    for key,ax in axes.items():
        ax.set_xlim(-76,-30);ax.set_ylim(-35,10)
        ax.set_xticks([-70,-50,-30]);ax.set_yticks([-30,-10,10]);ax.tick_params(labelsize=8)
        ax.set_title('Mapa '+key,fontsize=10)
        if name=='azimlib':ax.geojson(data,facecolor='#f0f0f0',edgecolor='#555555',linewidth=.6,fit=False)
        else:
            ax.set_aspect('equal')
            for feature in data:
                for polygon in feature.geometry.coordinates:
                    xs,ys=zip(*polygon[0]);ax.fill(xs,ys,facecolor='#f0f0f0',edgecolor='#555555',linewidth=.6)
    fig.savefig(folder/f'nested-reference-{name}.png');library.close(fig)
canvas=Image.new('RGB',(1200,526),'white');draw=ImageDraw.Draw(canvas)
for i,(name,label) in enumerate((('matplotlib',f'Matplotlib {matplotlib.__version__} / Agg'),('azimlib','Azimlib / renderer próprio'))):
    with Image.open(folder/f'nested-reference-{name}.png') as pic:canvas.paste(pic,(i*600,26))
    draw.text((i*600+12,8),label,fill='black')
canvas.save(folder/'nested-reference.png');print(folder/'nested-reference.png')
