"""0.4 development: XYZ input rendered on an own spherical equal-area map."""
import argparse
from pathlib import Path

import azimlib as azl


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    args.output.mkdir(parents=True, exist_ok=True)
    to_xyz = azl.Transformer(4979, 4978)
    # Synthetic demonstration points with explicit ellipsoidal heights.
    points = [(-60,-5,0),(-50,-15,1000),(-43,-24,200)]
    raw = {'type':'LineString','coordinates':[to_xyz.transform(*point) for point in points]}
    data = azl.read_geojson(raw, crs=4978)
    projection = azl.LambertAzimuthalEqualArea(central_longitude=-54, central_latitude=-15)
    fig, ax = azl.subplots(figsize=(6,6), projection=projection)
    ax.map('brazil', facecolor='#eef2f3', edgecolor='#5d6970', linewidth=.6)
    ax.geojson(data, color='#2284aa', linewidth=1.5, label='Synthetic XYZ input')
    ax.scatter(lon=[p[0] for p in points], lat=[p[1] for p in points], s=25, color='#2284aa')
    ax.set_extent((-76,-32,-35,8))
    ax.set_title('Spherical Lambert azimuthal equal area')
    ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude'); ax.grid(linewidth=.4, alpha=.4)
    ax.legend(loc='lower left')
    fig.savefig(args.output/'crs-pipeline.png', dpi=150)
    fig.savefig(args.output/'crs-pipeline.svg')
    fig.show(backend='browser', open_browser=False, path=args.output/'crs-pipeline.html')
    azl.close(fig)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
