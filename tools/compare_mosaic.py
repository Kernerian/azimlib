"""Development-only same geographic data/layout/DPI against Matplotlib/Agg."""
from pathlib import Path
import azimlib as azl
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw

folder=Path(__file__).resolve().parents[1]/'gallery'
data=azl.read_geojson(azl.datasets.country('brazil'))
for name,library in (('azimlib',azl),('matplotlib',plt)):
    fig,axes=library.subplot_mosaic('AA;BC',figsize=(5,6),dpi=100,height_ratios=[2,1])
    for key,ax in axes.items():
        ax.set_xlim(-76,-33);ax.set_ylim(-35,7)
        ax.set_xticks([-70,-50,-30]);ax.set_yticks([-30,-10,10])
        ax.set_title('Mapa '+key);ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
        if name=='azimlib':ax.geojson(data,facecolor='#f0f0f0',edgecolor='#555555',linewidth=.6,fit=False)
        else:
            ax.set_aspect('equal')
            for feature in data:
                for polygon in feature.geometry.coordinates:
                    xs,ys=zip(*polygon[0]);ax.fill(xs,ys,facecolor='#f0f0f0',edgecolor='#555555',linewidth=.6)
    fig.savefig(folder/f'mosaic-reference-{name}.png')
    library.close(fig)
canvas=Image.new('RGB',(1000,626),'white');draw=ImageDraw.Draw(canvas)
for i,(name,label) in enumerate((('matplotlib',f'Matplotlib {matplotlib.__version__} / Agg'),('azimlib','Azimlib / renderer próprio'))):
    with Image.open(folder/f'mosaic-reference-{name}.png') as pic:canvas.paste(pic,(i*500,26))
    draw.text((i*500+12,8),label,fill='black')
canvas.save(folder/'mosaic-reference.png');print(folder/'mosaic-reference.png')
