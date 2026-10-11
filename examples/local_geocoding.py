"""0.4 development: offline search and reverse on the optional licensed catalog.

Run from the source checkout. No residential addresses or network are requested.
Output includes attribution; the source database remains under its own terms.
"""
import argparse,tempfile
from pathlib import Path
import azimlib as azl


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    catalog=azl.DatasetCatalog(Path(__file__).resolve().parents[1]/'optional-data/urban-sao-paulo-1.0/catalog.json')
    data=catalog.load('urban-sao-paulo')
    with tempfile.TemporaryDirectory(prefix='geocoding-example-',dir=args.output) as folder:
        with azl.LocalGeocoder.from_catalog(catalog,'urban-sao-paulo',Path(folder)/'index',
                max_bytes=32*1024*1024,min_free_bytes=15_000_000_000) as index:
            # A named public street from the verified data, not an invented address.
            name=index.search(kinds=('street',),limit=1)[0].name
            results=index.search(name,kinds=('street',),limit=100)
            reverse=index.reverse(-46.639,-23.545,kinds=('street',),radius_m=300,limit=1)
            fig,axes=azl.subplots(1,2,figsize=(10,5))
            for ax in axes:
                ax.geojson(data,facecolor='#f3f3f3',edgecolor='#adb5bd',linewidth=.5)
                ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
                ax.xaxis.set_major_formatter(azl.ticker.LongitudeFormatter(number_format='.3f'))
                ax.yaxis.set_major_formatter(azl.ticker.LatitudeFormatter(number_format='.3f'))
            layer=axes[0].geojson(results.to_features(boundary=True),color='#2878b5',linewidth=2,label='Busca local')
            layer.set_picker(True);axes[0].labels(layer,halo='white',fontsize=9)
            axes[0].set_title(name,fontsize=11);axes[0].legend()
            layer=axes[1].geojson(reverse.to_features(),color='#d95f40')
            axes[1].scatter([r.coordinate[0] for r in reverse],[r.coordinate[1] for r in reverse],
                            color='#d95f40',label='Via mais próxima')
            layer.set_picker(True);axes[1].set_title('Busca reversa · distância esférica',fontsize=11);axes[1].legend()
            fig.suptitle('Pesquisa urbana local · Azimlib',fontsize=14)
            fig.text(.5,.015,index.sources['urban-sao-paulo'].attribution,ha='center',fontsize=8)
            fig.subplots_adjust(left=.12,right=.97,bottom=.17,top=.83,wspace=.42)
            for extension in ('png','svg'):fig.savefig(args.output/f'local-geocoding.{extension}',dpi=150)
            azl.close(fig)


if __name__=='__main__':main()
