"""Development-only visual reference; never imported by Azimlib."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'examples'))
from contour_refinement import field
import azimlib as azl
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw

x,y,z=field()
folder=root/'gallery'
for name,library in (('azimlib',azl),('matplotlib',plt)):
    # Both use longitude/latitude here to isolate strokes/labels/colorbar.
    fig,ax=library.subplots(figsize=(5,5),dpi=100)
    ax.set_xlim(-54,-43);ax.set_ylim(-28,-18)
    ax.set_xticks([-54,-52,-50,-48,-46,-44])
    ax.set_yticks([-28,-26,-24,-22,-20,-18])
    if name=='matplotlib':ax.set_aspect('equal')
    ax.set_title('Isolinhas e rótulos inline')
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    ax.set_facecolor('#eef2f5')
    cs=ax.contour(x,y,z,levels=[20,40,80],colors=['#225ea8','#1b9e77','#c75b12'],
                  linewidths=[.65,.85,1.05],linestyles=['--',':','-'])
    options=dict(fmt='%g',fontsize=9,inline=True,inline_spacing=5)
    if name=='azimlib':options.update(halo=None,padding=0)
    ax.clabel(cs,**options)
    fig.colorbar(cs,ax=ax,orientation='horizontal',spacing='uniform',label='Intensidade sintética')
    fig.savefig(folder/f'contour-reference-{name}.png')
    library.close(fig)
canvas=Image.new('RGB',(1000,526),'white');draw=ImageDraw.Draw(canvas)
for i,(name,label) in enumerate((('matplotlib',f'Matplotlib {matplotlib.__version__} / Agg'),('azimlib','Azimlib / renderer próprio'))):
    with Image.open(folder/f'contour-reference-{name}.png') as pic:canvas.paste(pic,(i*500,26))
    draw.text((i*500+12,8),label,fill='black')
canvas.save(folder/'contour-reference.png')
print(folder/'contour-reference.png')
