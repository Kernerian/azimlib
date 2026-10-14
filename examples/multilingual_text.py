"""0.4 source development: explicit optional fonts and shared glyph composition."""
import argparse
from pathlib import Path
import azimlib as azl


def make():
    """Call after registering the two pinned optional Noto validation fonts."""
    with azl.text_context(fallback=('Noto Devanagari','Noto CJK')):
        fig,ax=azl.subplots(figsize=(9,5.8))
        ax.countries(facecolor='#f0f2f3',edgecolor='#9da7b0',linewidth=.45)
        ax.set_extent((-85,155,-40,65));ax.grid(False)
        ax.set_title('Mapas · العربية · हिन्दी · 中文',fontsize=16)
        ax.set_xlabel('Longitude / 经度');ax.set_ylabel('Latitude / अक्षांश')
        cities=[(-46.63,-23.55,'São Paulo'),(31.24,30.04,'القاهرة'),(77.21,28.61,'नई दिल्ली'),(139.69,35.68,'東京')]
        ax.scatter([r[0] for r in cities],[r[1] for r in cities],s=24,color='#287e9e',label='Cities / مدن / 城市')
        for lon,lat,name in cities:
            ax.annotate(name,(lon,lat),xytext=(5,9),textcoords='offset points',fontsize=11,halo='white',halo_width=2)
        ax.legend(loc='lower right',fontsize=10)
        route=azl.FeatureCollection((azl.Feature(azl.Geometry('LineString',((-65,-8),(-30,0),(0,-5))),{'name':'العربية'}),))
        ax.geojson(route,color='#aa688c',linewidth=1)
        ax.labels(route,placement='curve',fontsize=10,halo='white',halo_width=2)
        points=ax.scatter([-20,10,60],[-25,-20,-25],c=[0,1,2],cmap='viridis',s=35)
        fig.colorbar(points,ax=ax,orientation='horizontal',label='Synthetic values / قيم / 数值',shrink=.7,pad=.16)
        fig.subplots_adjust(left=.11,right=.96,top=.85,bottom=.27)
        return fig


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fonts',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--show',action='store_true')
    args=parser.parse_args()
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
    from acquire_text_fonts import register_acquired
    register_acquired(args.fonts);fig=make();args.output.mkdir(parents=True,exist_ok=True)
    for extension in ('png','svg','pdf'):fig.savefig(args.output/f'multilingual-map.{extension}',dpi=150)
    if args.show:fig.show(block=True)
    azl.close(fig)
