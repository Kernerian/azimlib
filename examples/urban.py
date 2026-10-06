"""A wholly synthetic urban atlas; no real street/building/POI data.

Run python examples/urban.py --output gallery/urban [--show].
"""
import argparse
from pathlib import Path

import azimlib as azl


def data():
    def polygon(w, s, e, n, **properties):
        return azl.Feature(azl.Geometry('Polygon', (((w, s), (e, s), (e, n), (w, n), (w, s)),)), properties)
    neighborhoods = azl.FeatureCollection((
        polygon(-46.65, -23.57, -46.63, -23.55, name='West', zone='residential'),
        polygon(-46.63, -23.57, -46.61, -23.55, name='East', zone='mixed'),
    ))
    streets = azl.FeatureCollection(tuple(
        azl.Feature(azl.Geometry('LineString', coordinates), {'name': name, 'class': category})
        for coordinates, name, category in (
            (((-46.65, -23.56), (-46.61, -23.56)), 'Main avenue', 'arterial'),
            (((-46.64, -23.57), (-46.64, -23.55)), 'West street', 'local'),
            (((-46.62, -23.57), (-46.62, -23.55)), 'East street', 'local'),
            (((-46.65, -23.568), (-46.635, -23.556)), 'Walking route', 'footway'),
        )))
    buildings = azl.FeatureCollection(tuple(
        polygon(lon, lat, lon+.002, lat+.0014, name=f'Block {i+1}', use='mixed')
        for i, (lon, lat) in enumerate(((-46.647, -23.564), (-46.638, -23.558),
                                       (-46.627, -23.566), (-46.617, -23.557)))))
    cities = azl.read_csv('id,name,lon,lat,priority\n1,West station,-46.642,-23.561,2\n2,East station,-46.618,-23.562,1\n',
                         id_column='id', converters={'priority': int})
    return neighborhoods, streets, buildings, cities


def create():
    neighborhoods, streets, buildings, cities = data()
    fig, axes = azl.subplots(1, 2, figsize=(10, 5), subplot_kw={'projection': 'mercator'})
    left, right = axes
    for ax in axes:
        ax.set_facecolor('#fafafa')
        ax.neighborhoods(neighborhoods)
        ax.buildings(buildings, label='Building footprints')
        for category, color, width, dash, title in (
            ('arterial', '#ce7548', 2.5, '-', 'Avenue'),
            ('local', '#8d9aa3', 1.2, '-', 'Local street'),
            ('footway', '#508777', 1.2, '--', 'Walking route'),
        ):
            ax.streets(streets, where={'class': category}, color=color, linewidth=width,
                       linestyle=dash, label=title)
        points = ax.cities(cities, color='#7755a0', marker='D', markersize=7, label='Stations')
        ax.labels(points, fontsize=9, halo_width=1.5, offsets=((0, -14), (0, 14), (16, -14)))
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.scale_bar(loc='lower left')
    left.set_extent((-46.653, -46.607, -23.573, -23.547))
    left.set_title('Urban layers')
    left.legend(loc='upper right', fontsize=8)
    left.north_arrow(loc='upper left', size=22)
    right.set_extent((-46.633, -46.610, -23.571, -23.550))
    right.set_title('Neighborhood focus')
    right.grid(step=.005, linestyle=':', linewidth=.5, alpha=.5)
    right.set_xticks([-46.63, -46.62, -46.61])
    right.set_yticks([-23.57, -23.56, -23.55])
    fig.suptitle('Azimlib · synthetic urban atlas', fontsize=16)
    fig.text(.5, .02, 'Synthetic coordinates and names; not a navigable street map.',
             ha='center', fontsize=9, color='#555555')
    fig.subplots_adjust(left=.105, right=.98, bottom=.17, top=.83, wspace=.30)
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('gallery/urban'))
    parser.add_argument('--show', action='store_true')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    fig = create()
    for extension in ('svg', 'png'):
        fig.savefig(args.output / f'urban.{extension}')
    if args.show:
        azl.show()
