"""Own planar urban clipping and spherical global Boolean regions.

Urban blocks are synthetic; background countries are bundled Natural Earth.
The spherical fill uses an explicitly sampled 3-degree geographic mesh.
"""
import argparse
from pathlib import Path
import azimlib as azl


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('topology-output'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    def box(w,s,e,n):return azl.Geometry('Polygon',(((w,s),(e,s),(e,n),(w,n),(w,s)),))
    a,b=box(-47,-24,-45,-22),box(-46,-23.5,-44,-21.5)
    fig=azl.figure(figsize=(12,4.4),layout='constrained')
    ax=fig.add_subplot(1,3,1)
    ax.geojson(a,facecolor='#dce9ec',edgecolor='#42687b',label='Área A')
    ax.geojson(b,facecolor='none',edgecolor='#b35e49',linestyle='--',label='Área B')
    ax.geojson(azl.intersection(a,b).geometry,facecolor='#77a9bb',edgecolor='#254b5b',hatch='///',label='Interseção')
    ax.set_extent((-48,-43,-25,-20));ax.set_title('Overlay planar · recorte explícito');ax.set_xlabel('Longitude');ax.set_ylabel('Latitude');ax.legend(fontsize=8)
    north=azl.SphericalRegion.hemisphere(0,90);east=azl.SphericalRegion.hemisphere(0,0)
    ax=fig.add_subplot(1,3,2,projection='orthographic',projection_kw={'central_longitude':35,'central_latitude':35})
    ax.countries(facecolor='#edf0f2',edgecolor='#89969f',linewidth=.35)
    ax.region(azl.intersection(north,east,domain='spherical').geometry,fill_step=3,facecolor='#3994b0',alpha=.55)
    ax.grid(True,labels=False,step=30,color='#c5ccd2',linewidth=.4)
    ax.tick_params(labelbottom=False,labelleft=False,bottom=False,left=False)
    ax.set_title('Esfera · interseção de hemisférios')
    seam=azl.SphericalRegion.from_geometry(box(170,-20,190,20))
    ax=fig.add_subplot(1,3,3,projection='orthographic',projection_kw={'central_longitude':180,'central_latitude':15})
    ax.countries(facecolor='#edf0f2',edgecolor='#89969f',linewidth=.35)
    ax.region(seam.complement(),fill_step=3,facecolor='#3994b0',alpha=.5)
    ax.grid(True,labels=False,step=30,color='#c5ccd2',linewidth=.4)
    ax.tick_params(labelbottom=False,labelleft=False,bottom=False,left=False)
    ax.set_title('Complemento · antimeridiano')
    fig.suptitle('Azimlib · topologia própria planar e esférica',fontsize=14)
    for extension in ('svg','png'):fig.savefig(args.output/f'topology-overlay.{extension}',dpi=120)
    azl.close(fig)


if __name__=='__main__':main()
