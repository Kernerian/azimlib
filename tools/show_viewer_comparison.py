"""Open ONE real viewer for manual side-by-side inspection of criterion 3.08.

Run --library azimlib in the GUI wheel environment, --library matplotlib in
the isolated reference environment. Matplotlib is imported only by that mode.
Equal-aspect longitude/latitude axes compare UI/layout, not GIS algorithms.
"""
import argparse
import sys
import azimlib as azl


def build(library):
    own = library is azl
    fig, ax = library.subplots(figsize=(6.4, 4.8), dpi=100)
    if own:
        ax.map('brazil', facecolor='#eeeeee', edgecolor='#333333', linewidth=.8)
    else:
        from matplotlib.patches import Polygon
        for feature in azl.datasets.country('brazil')['features']:
            geometry = feature['geometry']
            polygons = [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']
            for polygon in polygons:
                ax.add_patch(Polygon(polygon[0], facecolor='#eeeeee', edgecolor='#333333', linewidth=.8))
        ax.set_aspect('equal', adjustable='box')
    ax.set_xlim(-76, -32); ax.set_ylim(-36, 8)
    ax.set_xticks([-70, -60, -50, -40]); ax.set_yticks([-30, -20, -10, 0])
    ax.set_title('Brasil · referência do viewer')
    ax.set_xlabel('Longitude', labelpad=4); ax.set_ylabel('Latitude', labelpad=4)
    ax.plot([-67, -60, -52], [-8, -3, -1], 'o--', color='#d62728', linewidth=1,
            markersize=4, label='Rota sintética')
    ax.legend(loc='lower right', fontsize=9)
    return fig


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', choices=('azimlib', 'matplotlib'), default='azimlib')
    parser.add_argument('--labels', action='store_true', help='Show optional Azimlib toolbar names below icons.')
    parser.add_argument('--subplots', action='store_true', help='Also open the subplot editor for inspection.')
    parser.add_argument('--window-title', help='Distinct title for the current Azimlib review window.')
    parser.add_argument('--reference-backend', choices=('TkAgg','QtAgg'), default='TkAgg',
                        help='Matplotlib reference toolkit; has no effect on the independent Azimlib viewer.')
    args = parser.parse_args()
    if args.library == 'matplotlib':
        import matplotlib
        matplotlib.use(args.reference_backend)
        import matplotlib.pyplot as library
    else:
        library = azl
    fig = build(library)
    if args.library == 'azimlib':
        viewer = fig.show(block=False)
        viewer.window.title(args.window_title or 'Azimlib · aceite visual 3.08')
        viewer.window.geometry('+40+80')
        if args.labels:viewer.set_toolbar_labels(True)
        if args.subplots:viewer.configure_subplots()
        assert 'matplotlib' not in sys.modules
    else:
        fig.canvas.manager.set_window_title('Matplotlib · referência 3.08')
        if args.reference_backend=='TkAgg':fig.canvas.manager.window.geometry('+710+80')
        else:fig.canvas.manager.window.move(710,80)
        if args.subplots:fig.canvas.manager.toolbar.configure_subplots()
    print(f'{args.library}: viewer created; visible UI still requires manual inspection.', flush=True)
    library.show()
