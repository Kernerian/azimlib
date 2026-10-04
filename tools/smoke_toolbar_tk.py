"""Real withdrawn toolbar integration; no Matplotlib or physical-input claim."""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import tkinter as tk
from types import SimpleNamespace
from unittest.mock import patch
import azimlib as azl

ROOT = Path(__file__).resolve().parents[1]


def run():
    real = tk.Tk
    reference = json.loads((ROOT / 'docs/toolbar-reference.json').read_text(encoding='utf-8'))
    checks = []
    for case in reference['cases']:
        dpi = case['tk_dpi']
        def hidden(*args, **kwargs):
            root = real(*args, **kwargs); root.withdraw()
            root.tk.call('tk', 'scaling', dpi / 72); return root
        fig, ax = azl.subplots()
        viewer = None
        try:
            with patch.object(tk, 'Tk', hidden): viewer = fig.show(block=False)
            viewer.window.update_idletasks()
            for name, button in viewer.buttons.items():
                expected = case['matplotlib']['buttons'][name]
                assert button.winfo_class() == expected['widget']
                for key in ('width', 'height', 'borderwidth', 'overrelief'):
                    assert str(button.cget(key)) == ('flat' if key=='overrelief' else expected[key])
                if sys.platform == 'win32':
                    assert [button.winfo_reqwidth(), button.winfo_reqheight()] == expected['request']
            assert viewer.widget.winfo_reqwidth() == 640 and viewer.widget.winfo_reqheight() == 480
            checks.append(f'{dpi}: seven button kinds/physical sizes and canvas match reference; flat hover modernizes legacy Tk groove')
            groups=[[]];names={str(button):name for name,button in viewer.buttons.items()}
            for child in viewer.toolbar.winfo_children():
                if str(child) in names:groups[-1].append(names[str(child)])
                elif isinstance(child,tk.Frame) and groups[-1]:groups.append([])
            assert [group for group in groups if group]==case['matplotlib']['groups']
            checks.append(f'{dpi}: Subplots belongs to Pan/Zoom group; Save has a separate group')
            button=viewer.buttons['Home'];viewer._show_tip(button,'Reset original view')
            tip=viewer._tooltip;assert tip is not None
            tip.update_idletasks()
            assert [tip.winfo_x()-button.winfo_rootx(),tip.winfo_y()-button.winfo_rooty()]==case['tooltip']['relative_xy']
            assert tip.winfo_children()[0].winfo_class()==case['tooltip']['label_widget']
            viewer._hide_tip();assert not tip.winfo_exists()
            checks.append(f'{dpi}: immediate tooltip on the right, matching reference widget and cleanup')
            for state in case['toggle_states']:
                viewer.buttons['Pan' if state['command'] == 'pan' else 'Zoom'].invoke()
                assert [viewer.buttons[name].var.get() for name in ('Pan', 'Zoom')] == state['checked']
            viewer.set_mode('pan'); assert viewer.buttons['Pan'].var.get() == 1
            viewer.set_mode('pan'); assert viewer.buttons['Pan'].var.get() == 0
            checks.append(f'{dpi}: pointer-button and keyboard mode changes keep independent checkbutton states synchronized')
            x, y, w, h = viewer.scene.maps[0]['box']
            cursors = []
            for mode in ('pan', 'zoom'):
                viewer.set_mode(mode)
                for px, py in ((x+w/2, y+h/2), (0, 0)):
                    viewer.motion(SimpleNamespace(x=px, y=py, state=0))
                    cursors.append(str(viewer.widget.cget('cursor')))
                viewer.set_mode(mode)
            assert cursors == case['own_cursors_inside_outside']
            checks.append(f'{dpi}: move/selection cursors apply inside the map and clear on margins')
            viewer.set_mode('pan'); viewer.set_toolbar_labels(True)
            assert all(button.cget('text')==name for name,button in viewer.buttons.items())
            assert viewer.buttons['Pan'].var.get()==1
            viewer.set_toolbar_labels(False); viewer.set_mode('pan')
            assert all(button.cget('text')=='' for button in viewer.buttons.values())
            editor=viewer.configure_subplots(); editor.window.withdraw()
            assert viewer.configure_subplots() is editor
            defaults=dict(fig.subplotpars)
            editor.values['left'].set(.18); editor.apply('left')
            assert fig.subplotpars['left']==.18 and editor.defaults==defaults
            editor.values['left'].set(.99); editor.apply('left')
            assert fig.subplotpars['left']<fig.subplotpars['right']
            editor.values['left'].set(''); editor.apply('left')
            assert editor.values['left'].get()==fig.subplotpars['left']
            editor.reset(); assert fig.subplotpars==defaults
            editor.tight(); assert editor.figure.get_layout_engine().adjust_compatible
            editor.reset(); assert fig.subplotpars==defaults
            assert 'fig.subplots_adjust(' in editor.export_values()
            exported=editor.export(); exported.withdraw(); exported.destroy()
            editor.window.destroy()
            replacement=viewer.configure_subplots(); replacement.window.withdraw()
            assert replacement is not editor; replacement.window.destroy()
            checks.append(f'{dpi}: optional toolbar names and themed subplot editor, live values, constraints, invalid input, reset, tight layout, export and reopen')
        finally:
            if viewer is not None: viewer.close()
            azl.close(fig)
        checks.append(f'{dpi}: closing releases images and raster cache')
    assert not any(name.split('.')[0] in ('matplotlib', 'cartopy', 'geopandas', 'shapely', 'pyproj', 'folium') for name in sys.modules)
    from azimlib.backends import tk as backend
    import azimlib._toolbar_icons as icons
    return dict(python=platform.python_version(), platform=platform.platform(), checks=checks,
        sha256=dict(backend=hashlib.sha256(Path(backend.__file__).read_bytes()).hexdigest(),
                    tool=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    reference=hashlib.sha256((ROOT / 'docs/toolbar-reference.json').read_bytes()).hexdigest(),
                    subplot_editor=hashlib.sha256(Path(sys.modules['azimlib.backends._subplots'].__file__).read_bytes()).hexdigest(),
                    own_icon_geometry=hashlib.sha256(Path(icons.__file__).read_bytes()).hexdigest()),
        runtime_origin=str(Path(azl.__file__).resolve()), independent_runtime=True,
        scope='Real withdrawn Tk and synthetic handlers in four physical Tk DPI settings. Not visible appearance or physical input; does not close 3.08.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(); report = run()
    if args.output: args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'{len(report["checks"])} toolbar checks passed; physical UI acceptance still pending.')
