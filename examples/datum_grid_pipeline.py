"""Own synthetic vertical-grid/raster example; no physical geoid claim/download."""
import argparse
from dataclasses import replace
from pathlib import Path
import struct

import azimlib as azl


def make_figure():
    # Analytic offset N = 10 + 5*x + 5*y metres at four nodes.
    raw=struct.pack('>4d2i',-30.,-60.,20.,20.,2,2)+struct.pack('>4f',10.,15.,15.,20.)
    source=azl.CoordinateFrame('WGS84 synthetic demonstration','geographic')
    target=replace(source,height_reference='synthetic gravity-related height')
    operation=azl.GridOperation(source,target,azl.read_gtx(raw),'vertical',factor=-1)
    values=tuple(tuple(100+8*i+3*j for i in range(12)) for j in range(10))
    original=azl.GeoRaster(values,(1.,0.,-56.,0.,1.,-29.),height_frame=source)
    corrected=operation.transform_raster(original)
    fig,axes=azl.subplots(1,2,figsize=(9,4),layout='constrained')
    for ax,raster,title in zip(axes,(original,corrected),('Ellipsoidal input','Corrected synthetic heights')):
        mesh=ax.raster(raster,cmap='viridis',vmin=80,vmax=220)
        ax.set_extent((-56,-44,-29,-19));ax.set_title(title,fontsize=11)
        ax.set_xlabel('Longitude');ax.set_ylabel('Latitude')
        fig.colorbar(mesh,ax=ax,label='Height (m)',shrink=.8)
    fig.suptitle('Explicit vertical grid — synthetic example',fontsize=13)
    return fig


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('datum-grid-example'))
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    fig=make_figure()
    try:
        for suffix in ('svg','png'):fig.savefig(args.output/f'datum-grid.{suffix}',dpi=160)
    finally:azl.close(fig)


if __name__ == '__main__':main()
