"""Own projections and ellipsoidal routes; Natural Earth geographic context."""
import argparse
from pathlib import Path
import azimlib as azl


def create():
    fig=azl.figure(figsize=(12,8),dpi=125)
    settings=[('stereographic',dict(central_longitude=-54,central_latitude=-16)),
              ('azimuthal_equidistant',dict(central_longitude=-54,central_latitude=-16)),
              ('transverse_mercator',dict(central_longitude=-51,false_easting=500000,false_northing=10000000)),
              ('orthographic',dict(central_longitude=-30,central_latitude=20))]
    titles=['Stereographic · spherical','Azimuthal equidistant · spherical','Regional TM · WGS84 ellipsoid','Orthographic · ellipsoidal routes']
    for i,((name,kw),title) in enumerate(zip(settings,titles),1):
        ax=fig.add_subplot(2,2,i,projection=name,projection_kw=kw)
        ax.set_title(title,fontsize=11)
        if i<3:
            ax.map('brazil',facecolor='#e9eef1',edgecolor='#647887',linewidth=.6)
            ax.states(linewidth=.35,edgecolor='#8b9aa3')
            ax.route([(-60,-3),(-46.63,-23.55)],ellipsoid=azl.WGS84,color='#cb5145',linewidth=1.3,label='Ellipsoidal route')
            ax.set_extent((-78,-30,-36,9));ax.legend(loc='lower right',fontsize=8)
        elif i==3:
            ax.state('sc',facecolor='#e9eef1',edgecolor='#647887',linewidth=.6)
            xy=azl.transform(-48.55,-27.59,4326,32722)
            points=azl.read_geojson({'type':'Point','coordinates':xy},crs=32722)
            ax.geojson(points,marker='o',color='#cb5145',markersize=4,fit=False)
            ax.set_extent((-54,-48,-30,-25))
        else:
            ax.countries(facecolor='#e9eef1',edgecolor='#647887',linewidth=.3)
            for endpoints,color in [([(-74,40.7),(-.12,51.5)],'#277ea4'),([(-46.63,-23.55),(2.35,48.85)],'#cb5145'),([(-43.17,-22.9),(-17.44,14.69)],'#26966c')]:
                ax.route(endpoints,ellipsoid=azl.WGS84,color=color,linewidth=1.2)
            ax.set_extent((-180,180,-90,90))
        ax.grid(True,color='#c3cbd0',linewidth=.4,linestyle=':')
        ax.set_xlabel('Longitude',fontsize=9);ax.set_ylabel('Latitude',fontsize=9)
        ax.tick_params(labelsize=8)
    fig.suptitle('Azimlib · geographic core',fontsize=15)
    fig.subplots_adjust(left=.09,right=.96,bottom=.1,top=.89,wspace=.24,hspace=.30)
    fig.text(.5,.015,'Natural Earth (public domain) · synthetic routes · own Azimlib renderer',ha='center',fontsize=8,color='#60717a')
    return fig


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('gallery/geodesy'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    fig=create()
    for extension in ('png','svg'):fig.savefig(args.output/f'geodesy-atlas.{extension}')
    (args.output/'geodesy-atlas.html').write_text(fig.to_html(),encoding='utf8',newline='\n')
