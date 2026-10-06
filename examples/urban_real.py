"""Real, explicitly loaded ODbL urban sample; no network or implicit datasets."""
import argparse
from pathlib import Path
import azimlib as azl


def create(catalog_path):
    catalog = azl.DatasetCatalog(catalog_path)
    data = catalog.load('urban-sao-paulo', version='1.0')
    buildings = data.select(predicate=lambda f: f.properties.get('building') not in (None, 'no'))
    gardens = data.select(predicate=lambda f: f.properties.get('leisure') in ('park', 'garden'))
    streets = data.select(geometry_types=('LineString',))
    fig, ax = azl.subplots(figsize=(8, 8), projection='mercator')
    ax.set_facecolor('#faf9f5')
    ax.geojson(gardens, facecolor='#d4dfc2', edgecolor='#a1b28d', linewidth=.5, label='Gardens')
    ax.buildings(buildings, facecolor='#d5dce1', edgecolor='#87949e', linewidth=.45, label='Buildings')
    for classes, color, width, name in (
        (('primary', 'secondary', 'tertiary', 'trunk'), '#c38059', 2, 'Roads'),
        (('residential', 'service'), '#a4a5a2', 1.2, 'Local streets'),
        (('pedestrian', 'footway', 'steps'), '#76909a', .7, 'Walking paths'),
    ):
        ax.streets(streets.select(predicate=lambda f: f.properties.get('highway') in classes),
                   color=color, linewidth=width, label=name)
    theatre = buildings.select(where={'name': 'Teatro Municipal de São Paulo'})
    layer = ax.buildings(theatre, facecolor='#c4b4d1', edgecolor='#785989', linewidth=.8)
    ax.text(-46.63865, -23.54545, 'Theatro Municipal', fontsize=9, ha='center', halo='white', halo_width=1.7)
    ax.set_extent((-46.641, -46.637, -23.547, -23.543))
    ax.set_xticks([-46.641, -46.640, -46.639, -46.638, -46.637])
    ax.set_yticks([-23.547, -23.546, -23.545, -23.544, -23.543])
    ax.ticklabel_format(axis='both', style='plain', useOffset=False)
    ax.set_title('São Paulo · Praça Ramos de Azevedo', fontsize=14)
    ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
    ax.legend(loc='lower right', fontsize=9)
    ax.scale_bar(loc='lower left', length=100, units='m')
    ax.north_arrow(loc='upper right', size=23)
    fig.text(.5, .045, '© OpenStreetMap contributors · ODbL 1.0 · openstreetmap.org/copyright',
             ha='center', fontsize=9, color='#555555')
    fig.text(.5, .022, 'Frozen sample 1.0 · 2026-10-06 · not for navigation',
             ha='center', fontsize=8, color='#777777')
    fig.subplots_adjust(left=.15, right=.97, bottom=.15, top=.91)
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=Path('gallery/urban-real'))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    fig = create(args.catalog)
    for extension in ('png', 'svg'):
        fig.savefig(args.output / f'urban-real.{extension}')
