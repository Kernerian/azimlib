"""Own non-modal subplot editor with themed Tk widgets; no reference imports."""
from __future__ import annotations
import math
import tkinter as tk
from tkinter import ttk


class SubplotEditor:
    def __init__(self, viewer):
        self.viewer = viewer
        self.figure = viewer.figure
        self.defaults = dict(self.figure.subplotpars)
        self._loading = True
        self.window = tk.Toplevel(viewer.window)
        self.window.title('Subplot configuration')
        self.window.transient(viewer.window)
        self.window.resizable(True, False)
        body = ttk.Frame(self.window, padding=12)
        body.pack(fill='both', expand=True)
        body.columnconfigure(0, weight=2); body.columnconfigure(1, weight=1)
        self.values = {}; self.sliders = {}; self.spinboxes = {}; self.buttons = {}
        for column, (title, names) in enumerate((('Borders', ('top', 'bottom', 'left', 'right')),
                                                ('Spacings', ('hspace', 'wspace')))):
            group = ttk.LabelFrame(body, text=title, padding=10)
            group.grid(row=0, column=column, sticky='nsew', padx=(0, 12) if not column else 0)
            group.columnconfigure(1, weight=1)
            for row, name in enumerate(names):
                var = tk.DoubleVar(self.window, self.defaults[name]); self.values[name] = var
                ttk.Label(group, text=name).grid(row=row, column=0, sticky='w', padx=(0, 8), pady=6)
                slider = ttk.Scale(group, from_=0, to=1, variable=var, length=130,
                                   command=lambda value, n=name: self.apply(n))
                slider.grid(row=row, column=1, sticky='ew', padx=(0, 8), pady=6)
                spin = ttk.Spinbox(group, from_=0, to=max(1, self.defaults[name]), increment=.005,
                                   format='%.3f', width=7, textvariable=var,
                                   command=lambda n=name: self.apply(n))
                spin.grid(row=row, column=2, pady=6)
                spin.bind('<Return>', lambda event, n=name: self.apply(n))
                spin.bind('<FocusOut>', lambda event, n=name: self.apply(n))
                self.sliders[name] = slider; self.spinboxes[name] = spin
        controls = ttk.Frame(body); controls.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(12, 0))
        for name, callback in (('Export values', self.export), ('Tight layout', self.tight),
                               ('Reset', self.reset), ('Close', self.window.destroy)):
            button = ttk.Button(controls, text=name, command=callback)
            button.pack(side='left' if name != 'Close' else 'right', padx=(0, 6))
            self.buttons[name] = button
        self.status = tk.StringVar(self.window)
        ttk.Label(body, textvariable=self.status, wraplength=500).grid(
            row=2, column=0, columnspan=2, sticky='w', pady=(8, 0))
        self._loading = False
        self._ranges()
        self._compatible()
        self.window.bind('<Escape>', lambda event: self.window.destroy())

    def _compatible(self):
        engine = self.figure.get_layout_engine()
        allowed = engine is None or engine.adjust_compatible
        for widget in (*self.sliders.values(), *self.spinboxes.values()):
            widget.state(['!disabled'] if allowed else ['disabled'])
        self.buttons['Reset'].state(['!disabled'] if allowed else ['disabled'])
        if not allowed: self.status.set('Automatic layout controls these borders. Use Tight layout to switch to manual adjustments.')
        return allowed

    def dispose(self):
        """Release owned Tcl resources on the viewer's UI thread."""
        if self.window is not None and self.window.winfo_exists():
            self.window.destroy()
        self.values.clear(); self.sliders.clear(); self.spinboxes.clear(); self.buttons.clear()
        self.status = self.window = self.viewer = None

    def _read(self, changed=None):
        values = {name: float(var.get()) for name, var in self.values.items()}
        if not all(math.isfinite(value) for value in values.values()): raise ValueError('Use finite numbers.')
        for lower, higher in (('bottom', 'top'), ('left', 'right')):
            values[lower] = max(0., min(.999, values[lower]))
            values[higher] = max(.001, min(1., values[higher]))
            if values[lower] >= values[higher]:
                if changed == higher: values[higher] = min(1., values[lower] + .001)
                else: values[lower] = max(0., values[higher] - .001)
        for name in ('wspace', 'hspace'): values[name] = max(0., values[name])
        return values

    def _set(self, values):
        self._loading = True
        try:
            for name, value in values.items(): self.values[name].set(value)
        finally: self._loading = False
        self._ranges()

    def _ranges(self):
        for lower, higher in (('bottom', 'top'), ('left', 'right')):
            self.spinboxes[lower].configure(to=max(0., float(self.values[higher].get()) - .001))
            self.spinboxes[higher].configure(from_=min(1., float(self.values[lower].get()) + .001))

    def apply(self, changed=None):
        if self._loading or not self._compatible(): return
        try:
            values = self._read(changed)
            self.figure.subplots_adjust(**values)
        except (ValueError, tk.TclError) as exc:
            self.status.set(str(exc)); self._set(self.figure.subplotpars); return
        self._set(values); self.status.set(''); self.viewer.draw_idle()

    def reset(self):
        if not self._compatible(): return
        self._set(self.defaults); self.apply()

    def tight(self):
        try: self.figure.tight_layout()
        except ValueError as exc: self.status.set(str(exc)); return
        self._set(self.figure.subplotpars); self.status.set(''); self._compatible(); self.viewer.draw_idle()

    def export_values(self):
        return 'fig.subplots_adjust(\n' + ''.join(
            f'    {name}={value:.3f},\n' for name, value in self.figure.subplotpars.items()) + ')'

    def export(self):
        dialog = tk.Toplevel(self.window); dialog.title('Subplot values'); dialog.transient(self.window)
        body = ttk.Frame(dialog, padding=12); body.pack(fill='both', expand=True)
        text = tk.Text(body, width=38, height=9, relief='flat', borderwidth=0, padx=8, pady=8)
        text.insert('1.0', self.export_values()); text.configure(state='disabled'); text.pack(fill='both', expand=True)
        def copy():
            dialog.clipboard_clear(); dialog.clipboard_append(self.export_values())
        ttk.Button(body, text='Copy', command=copy).pack(side='left', pady=(10, 0))
        ttk.Button(body, text='Close', command=dialog.destroy).pack(side='right', pady=(10, 0))
        return dialog
