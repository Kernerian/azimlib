"""Development-only Tk widget comparison, NOT a visible-window screenshot.

Real widgets/PhotoImages from both libraries, physical Tk sizes/font/state in
96/120/144/192 DPI. Native OS input, window chrome and presentation remain out
of scope. Matplotlib is a reference here, never an Azimlib backend.
"""
import hashlib
import json
from pathlib import Path
import platform
import re
import tkinter as tk
import tkinter.font as tkfont
from types import SimpleNamespace
from unittest.mock import patch

import azimlib as azl
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from PIL import Image, ImageTk, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def snapshot(toolbar, buttons, widget):
    rows = {}
    for name, button in buttons.items():
        row = dict(widget=button.winfo_class(), request=[button.winfo_reqwidth(), button.winfo_reqheight()])
        for key in ('width', 'height', 'padx', 'pady', 'borderwidth', 'relief', 'overrelief', 'offrelief', 'indicatoron'):
            if key in button.keys(): row[key] = str(button.cget(key))
        rows[name] = row
    labels = [dict(font=tkfont.Font(root=widget, font=w.cget('font')).actual(),
                   request=[w.winfo_reqwidth(), w.winfo_reqheight()])
              for w in toolbar.winfo_children() if isinstance(w, tk.Label)]
    groups=[[]];names={str(button):name for name,button in buttons.items()}
    for child in toolbar.winfo_children():
        if str(child) in names:groups[-1].append(names[str(child)])
        elif isinstance(child,tk.Frame) and groups[-1]:groups.append([])
    return dict(groups=[group for group in groups if group],
                toolbar_request=[toolbar.winfo_reqwidth(), toolbar.winfo_reqheight()],
                canvas_request=[widget.winfo_reqwidth(), widget.winfo_reqheight()],
                buttons=rows, labels=labels)


def tooltip(button):
    def bound(sequence):
        # Tk drops Enter/Leave for unmapped widgets. Invoke the actual registered
        # binding with Tk's substituted event fields; this is synthetic input.
        command=re.search(r'\[([^\s]+)',button.bind(sequence)).group(1)
        fields={'%W':str(button),'%T':'7' if sequence=='<Enter>' else '8'}
        button.tk.call(command,*(fields.get(field,'0') for field in button._subst_format))
    bound('<Enter>')
    tips=[child for child in button.winfo_children() if isinstance(child,tk.Toplevel)]
    assert len(tips)==1,'Tooltip must be created synchronously on Enter'
    tip=tips[0];tip.update_idletasks()
    label=tip.winfo_children()[0]
    result=dict(immediate=True,relative_xy=[tip.winfo_x()-button.winfo_rootx(),tip.winfo_y()-button.winfo_rooty()],
                label_widget=label.winfo_class(),justify=str(label.cget('justify')),
                relief=str(label.cget('relief')),borderwidth=str(label.cget('borderwidth')))
    assert result['relative_xy']==[button.winfo_width(),0]
    bound('<Leave>')
    assert not tip.winfo_exists()
    return result


def inspect(dpi):
    real = tk.Tk
    def hidden(*args, **kwargs):
        root = real(*args, **kwargs); root.withdraw()
        root.tk.call('tk', 'scaling', dpi / 72)
        return root
    fig, ax = azl.subplots()
    viewer = root = None
    try:
        with patch.object(tk, 'Tk', hidden): viewer = fig.show(block=False)
        root = hidden()
        nativefig = Figure(figsize=(6.4, 4.8), dpi=100)
        nativefig.subplots()
        canvas = FigureCanvasTkAgg(nativefig, master=root)
        bar = NavigationToolbar2Tk(canvas, root)
        canvas.get_tk_widget().pack(side='top', fill='both', expand=True)
        root.update_idletasks(); viewer.window.update_idletasks()
        own = snapshot(viewer.toolbar, viewer.buttons, viewer.widget)
        native = snapshot(bar, bar._buttons, canvas.get_tk_widget())
        # Modern flat hover is an documented presentation difference from
        # Tk's legacy groove; widget metrics/fonts/state must still match.
        normalized=json.loads(json.dumps(own))
        for button in normalized['buttons'].values():button['overrelief']='groove'
        assert normalized == native, (dpi, own, native)
        own_tip=tooltip(viewer.buttons['Home']);native_tip=tooltip(bar._buttons['Home'])
        assert own_tip==native_tip,(own_tip,native_tip)
        states = []
        for mode in ('pan', 'zoom', 'zoom', 'pan', 'pan'):
            viewer.buttons['Pan' if mode == 'pan' else 'Zoom'].invoke()
            bar._buttons['Pan' if mode == 'pan' else 'Zoom'].invoke()
            checked = [viewer.buttons[name].var.get() for name in ('Pan', 'Zoom')]
            expected = [bar._buttons[name].var.get() for name in ('Pan', 'Zoom')]
            assert checked == expected
            states.append(dict(command=mode, checked=checked))
        # Synthetic motion reaches the registered own handler; these are not
        # physical input tests. Native cursor policy is separately recorded.
        x, y, w, h = viewer.scene.maps[0]['box']
        cursors = []
        for mode in ('pan', 'zoom'):
            viewer.set_mode(mode)
            for px, py in ((x+w/2, y+h/2), (0, 0)):
                viewer.motion(SimpleNamespace(x=px, y=py, state=0))
                cursors.append(str(viewer.widget.cget('cursor')))
            viewer.set_mode(mode)
        assert cursors == ['fleur', '', 'crosshair', '']
        if dpi == 96:
            # Ship a preview of OUR artwork only, never reference icon pixels.
            sheet = Image.new('RGB', (560, 70), 'white'); draw = ImageDraw.Draw(sheet)
            for col, (name, button) in enumerate(viewer.buttons.items()):
                im = ImageTk.getimage(viewer._icons[col])
                sheet.paste(im, (col*80+20, 5), im)
                draw.text((col*80+6, 38), name, fill='black')
            sheet.save(ROOT / 'gallery/toolbar-icon-assets.png')
        return dict(tk_dpi=dpi, azimlib=own, matplotlib=native, toggle_states=states,
                    own_cursors_inside_outside=cursors,tooltip=own_tip)
    finally:
        if viewer is not None: viewer.close()
        azl.close(fig)
        if root is not None: root.destroy()


if __name__ == '__main__':
    report = dict(python=platform.python_version(), platform=platform.platform(),
        matplotlib=matplotlib.__version__, cases=[inspect(dpi) for dpi in (96, 120, 144, 192)],
        sha256={name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in
                ('src/azimlib/backends/tk.py', 'src/azimlib/_toolbar_icons.py', 'tools/inspect_toolbar.py')},
        scope='Withdrawn widgets; original Azimlib icons; flat-hover intentional difference; not visible screenshots or physical input. Does not close 3.08.')
    (ROOT / 'docs/toolbar-reference.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('4 physical Tk DPI states: widget geometry/fonts/toggle states match reference; intentional flat hover; visible acceptance pending.')
