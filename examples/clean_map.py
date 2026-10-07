"""Recommended light figure: default style, only explicitly requested content."""
import argparse
from pathlib import Path
import azimlib as azl

def create():
    with azl.style.context('default'):
        fig,ax=azl.subplots(figsize=(6.4,6),dpi=150,layout='constrained')
        ax.map('brazil',facecolor='#f2f2f2',edgecolor='#444444',linewidth=.6)
        ax.states(edgecolor='#999999',linewidth=.35)
        ax.set_title('Brazil')
        ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
    return fig

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('gallery/composition'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    fig=create()
    for extension in ('png','svg'):fig.savefig(args.output/f'clean-map.{extension}')
    (args.output/'clean-map.html').write_text(fig.to_html(),encoding='utf8',newline='\n')
    azl.close(fig)
