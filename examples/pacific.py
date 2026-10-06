"""Explicit antimeridian view; static output and portable navigation share a branch."""
import argparse
from pathlib import Path
import azimlib as azl


def create():
    fig,ax=azl.subplots(figsize=(8,5),dpi=125)
    ax.set_extent((165,-165,-30,5))
    ax.countries(facecolor='#e9eef1',edgecolor='#647887',linewidth=.5)
    # Point samples, not geographic claims or a licensed transport dataset.
    ax.route([(174.8,-21.1),(-171.8,-13.8)],ellipsoid=azl.WGS84,color='#cb5145',linewidth=1.7,label='Synthetic ellipsoidal route')
    ax.scatter([174.8,-171.8],[-21.1,-13.8],s=25,color='#cb5145',zorder=4)
    ax.set_title('Pacific · continuous antimeridian viewport')
    ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    ax.grid(True,labels=True,color='#c3cbd0',linestyle=':',linewidth=.5)
    ax.legend(loc='lower right',fontsize=9)
    ax.scale_bar(loc='lower left');ax.north_arrow(loc='upper right')
    fig.subplots_adjust(left=.15,right=.96,bottom=.15,top=.87)
    fig.text(.5,.02,'Natural Earth (public domain) · synthetic route',ha='center',fontsize=8,color='#60717a')
    return fig


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('gallery/geodesy'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    fig=create()
    for extension in ('png','svg'):fig.savefig(args.output/f'pacific.{extension}')
    (args.output/'pacific.html').write_text(fig.to_html(),encoding='utf8',newline='\n')
