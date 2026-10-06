"""Synthetic scalar georaster and an optional colorbar, using the own renderer."""
import argparse
from math import exp
from pathlib import Path
import azimlib as azl


def create():
    values = tuple(tuple(100 * exp(-((i-16)**2+(j-12)**2)/80) for i in range(32)) for j in range(24))
    raster = azl.GeoRaster(values, (.1, 0, -49, 0, -.1, -20), nodata=None)
    fig, ax = azl.subplots(figsize=(7, 5))
    layer = ax.raster(raster, cmap='viridis')
    fig.colorbar(layer, ax=ax, label='Synthetic intensity')
    ax.set_title('Georeferenced scalar raster')
    ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
    fig.subplots_adjust(left=.16, bottom=.16, top=.88)
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('gallery/georaster'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    fig = create()
    for extension in ('png', 'svg'):
        fig.savefig(args.output / f'georaster.{extension}')
