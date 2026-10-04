"""Own scalar image, fixed mesh and vector edits on a shared color scale."""
import math
from pathlib import Path
import azimlib as azl
from azimlib.colors import Normalize
from azimlib.ticker import LongitudeFormatter,LatitudeFormatter,MultipleLocator

EXTENT=(-54,-43,-28,-18)

def field(nx,ny,*,center=.35,amplitude=90):
    return [[amplitude*math.exp(-(((i+.5)/nx-center)**2/.07+((j+.5)/ny-.5)**2/.16))
             for i in range(nx)] for j in range(ny)]

def create():
    fig,axs=azl.subplots(1,3,figsize=(11.5,5.3),projection='mercator',layout='constrained')
    norm=Normalize(0,100)
    image=axs[0].imshow(field(10,8),extent=EXTENT,origin='lower',norm=norm)
    x=[-54+11*i/6 for i in range(7)];y=[-28+10*j/5 for j in range(6)]
    mesh=axs[1].pcolormesh(x,y,field(6,5),norm=norm)
    lon=[-52,-49,-46]*3;lat=[-26]*3+[-23]*3+[-20]*3
    vectors=axs[2].quiver(lon,lat,[1,1.4,1.8]*3,[.3,.7,1]*3,[20,50,80]*3,norm=norm,scale=10,linewidth=.8)
    for ax,title in zip(axs,('Imagem escalar','Mesh de células','Vetores leste/norte')):
        ax.map('brazil',fit=False,facecolor='none',edgecolor='#666666',linewidth=.45,zorder=3)
        ax.states(fit=False,edgecolor='#888888',linewidth=.3,zorder=3)
        ax.set_extent(EXTENT);ax.set_title(title,fontsize=11)
        ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
        ax.xaxis.set_major_formatter(LongitudeFormatter());ax.yaxis.set_major_formatter(LatitudeFormatter())
    bar=fig.colorbar(image,ax=axs,orientation='horizontal',label='Valor sintético · escala compartilhada')
    bar.locator=MultipleLocator(25)
    fig.suptitle('Campos 2D · dados iniciais',fontsize=13)
    return fig,image,mesh,vectors,norm

def export(fig,name):
    folder=Path(__file__).resolve().parents[1]/'gallery'
    for extension in ('png','svg'):fig.savefig(folder/f'{name}.{extension}')
    fig.show(backend='browser',open_browser=False,path=folder/f'{name}.html')
    print(name,flush=True)

if __name__=='__main__':
    fig,image,mesh,vectors,norm=create();export(fig,'fields-before')
    image.set_data(field(16,12,center=.65,amplitude=180))
    mesh.set_array(field(6,5,center=.65,amplitude=180))
    vectors.set_UVC([-.6,-1,-1.4]*3,[1.6,1.2,.8]*3,[40,100,160]*3)
    norm.vmax=200
    fig.suptitle('Campos 2D · valores e direções editados')
    export(fig,'fields-after');azl.close(fig)
