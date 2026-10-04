"""Development comparison of shared views, outer labels and equal map aspect."""
from pathlib import Path
import azimlib as azl
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw

folder=Path(__file__).resolve().parents[1]/'gallery'
data=azl.read_geojson(azl.datasets.country('brazil'))
for name,library in (('azimlib',azl),('matplotlib',plt)):
    fig,axes=library.subplots(2,2,sharex=True,sharey=True,figsize=(6,5),dpi=100,
        gridspec_kw={'wspace':.2,'hspace':.35})
    for i,ax in enumerate(axes.flat):
        ax.set_xlabel('Longitude',fontsize=9);ax.set_ylabel('Latitude',fontsize=9);ax.label_outer()
        ax.set_title('Camada '+str(i+1),fontsize=10)
        ax.plot([-52,-48,-44],[-26,-22,-20],'o--',color='#d62728',linewidth=1,markersize=3)
        if name=='azimlib':ax.geojson(data,facecolor='#f0f0f0',edgecolor='#555555',linewidth=.5,fit=False)
        else:
            ax.set_aspect('equal')
            for feature in data:
                for polygon in feature.geometry.coordinates:
                    xs,ys=zip(*polygon[0]);ax.fill(xs,ys,facecolor='#f0f0f0',edgecolor='#555555',linewidth=.5,zorder=1)
        ax.tick_params(labelsize=8)
    axes[1,1].set_xlim(-56,-40);axes[1,1].set_ylim(-30,-16)
    axes[1,1].set_xticks([-56,-48,-40]);axes[1,1].set_yticks([-30,-23,-16])
    fig.savefig(folder/f'shared-axes-reference-{name}.png');library.close(fig)
canvas=Image.new('RGB',(1200,526),'white');draw=ImageDraw.Draw(canvas)
for i,(name,label) in enumerate((('matplotlib',f'Matplotlib {matplotlib.__version__} / Agg'),('azimlib','Azimlib / renderer próprio'))):
    with Image.open(folder/f'shared-axes-reference-{name}.png') as pic:canvas.paste(pic,(i*600,26))
    draw.text((i*600+12,8),label,fill='black')
canvas.save(folder/'shared-axes-reference.png');print(folder/'shared-axes-reference.png')
