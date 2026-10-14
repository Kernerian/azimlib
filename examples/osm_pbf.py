"""Plot an explicitly supplied OSM PBF extract with own urban layers; no download."""
import argparse
from pathlib import Path

import azimlib as azl


def create(source, *, bbox, missing='error', max_disk_bytes=8_000_000_000,
           reserve_free_bytes=15_000_000_000):
    data = azl.read_osm_pbf(source, bbox=bbox, missing=missing,
                          max_disk_bytes=max_disk_bytes, reserve_free_bytes=reserve_free_bytes)
    polygons = data.select(geometry_types=('Polygon', 'MultiPolygon'))
    streets = data.select(geometry_types=('LineString', 'MultiLineString'),
                          predicate=lambda f: 'highway' in f.properties)
    buildings = polygons.select(predicate=lambda f: f.properties.get('building') not in (None, 'no'))
    green = polygons.select(predicate=lambda f: f.properties.get('leisure') in ('park', 'garden') or f.properties.get('landuse') in ('forest', 'grass'))
    water = polygons.select(where={'natural': 'water'})
    fig, ax = azl.subplots(figsize=(8, 7), projection='mercator')
    ax.set_facecolor('#faf9f5')
    ax.geojson(green, facecolor='#d4dfc2', edgecolor='#a1b28d', linewidth=.4)
    ax.geojson(water, facecolor='#d5e9f2', edgecolor='#91b8c8', linewidth=.4)
    ax.buildings(buildings, facecolor='#d5dce1', edgecolor='#87949e', linewidth=.4)
    for classes, color, width in (
        (('primary', 'secondary', 'tertiary', 'trunk', 'motorway'), '#c38059', 1.7),
        (('residential', 'service', 'unclassified'), '#a4a5a2', .9),
        (('pedestrian', 'footway', 'steps', 'path'), '#76909a', .55),
    ):
        ax.streets(streets.select(predicate=lambda f: f.properties.get('highway') in classes), color=color, linewidth=width)
    west, south, east, north = bbox
    ax.set_extent((west, east, south, north))
    ax.set_title('OpenStreetMap · own PBF reader')
    ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
    ax.scale_bar(); ax.north_arrow(size=23)
    fig.text(.5, .035, '© OpenStreetMap contributors · ODbL 1.0 · openstreetmap.org/copyright', ha='center', fontsize=8)
    fig.subplots_adjust(left=.14, right=.97, bottom=.16, top=.92)
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--bbox', type=float, nargs=4, required=True, metavar=('WEST', 'SOUTH', 'EAST', 'NORTH'))
    parser.add_argument('--allow-incomplete', action='store_true', help='Explicitly skip incomplete derived ways/relations')
    parser.add_argument('--output', type=Path, default=Path('gallery/osm-pbf'))
    args = parser.parse_args()
    # The extraction is bounded; this example is regional, not a planet trial.
    fig = create(args.input, bbox=args.bbox, missing='skip' if args.allow_incomplete else 'error')
    args.output.mkdir(parents=True, exist_ok=True)
    for extension in ('png', 'svg'):
        fig.savefig(args.output / f'osm-pbf.{extension}')
