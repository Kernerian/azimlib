"""Self-contained browser viewer with familiar figure navigation controls."""
from __future__ import annotations
from html import escape
import json
import base64
from importlib.resources import files
from .renderers import render_svg
from ._toolbar_icons import icon_svg


def render_html(scene, title="Figure 1"):
    """Serialize SVG plus offline pan/zoom UI; no server or CDN is required."""
    # One background node makes the primitive-index mapping unambiguous even
    # for figures whose vector/raster background is otherwise transparent.
    if scene.background is None:
        from dataclasses import replace
        scene=replace(scene,background="white")
    svg=render_svg(scene)
    metadata=json.dumps([m for m in getattr(scene,"maps",[]) if not m.get("terrain3d")],ensure_ascii=True,allow_nan=False).replace("<","\\u003c")
    root=files(__package__).joinpath("assets")
    css=root.joinpath("viewer.css").read_text(encoding="utf-8")
    js=root.joinpath("viewer.js").read_text(encoding="utf-8")
    navigation=root.joinpath("navigation.js").read_text(encoding="utf-8")
    components=root.joinpath("components.js").read_text(encoding="utf-8")
    # Original shared vector geometry, embedded offline without external UI.
    icon_names={'home':'home','back':'back','forward':'forward','pan':'move',
                'zoom':'zoom_to_rect','save':'filesave'}
    icons={name:base64.b64encode(icon_svg(file).encode('utf-8')).decode('ascii')
           for name,file in icon_names.items()}
    labels={"home":"Home — restore original view (H)","back":"Back (Left)","forward":"Forward (Right)",
            "pan":"Pan — drag map (P)","zoom":"Zoom to rectangle (O)","minus":"Zoom out (−)",
            "plus":"Zoom in (+)","settings":"Configure view","save":"Save current view as SVG (Ctrl+S)"}
    labels.update(home="Reset original view",back="Back to previous view",forward="Forward to next view",
                  pan="Left button pans, Right button zooms — x/y fixes axis, CTRL fixes aspect",
                  zoom="Zoom to rectangle — x/y fixes axis",save="Download plot")
    buttons=[]
    for group in (("home","back","forward"),("pan","zoom"),("save",)):
        buttons.append('<span class="button-group">')
        for name in group:
            buttons.append(f'<button id="{name}" type="button" title="{labels[name]}" aria-label="{labels[name]}"'+
                           (' aria-pressed="false"' if name in ("pan","zoom") else '')+
                           f'><img src="data:image/svg+xml;base64,{icons[name]}" width="24" height="24" alt="" aria-hidden="true"></button>')
        buttons.append('</span>')
    return f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} — Azimlib</title><style>{css}</style></head><body>
<section id="figure-window"><header class="figure-title">{escape(title)}</header>
<main id="canvas" tabindex="0" aria-label="Figura cartográfica interativa" style="width:{scene.width:g}px;height:{scene.height:g}px">{svg}</main>
<aside id="overview" aria-label="Visão geral do mapa" hidden><div class="overview-title">Visão geral <span id="zoom-level">1.00×</span></div><svg id="mini" role="img" aria-label="Mapa completo e retângulo da área visível"></svg></aside>
<footer class="toolbar" role="toolbar" aria-label="Figure navigation">{''.join(buttons)}
<select id="save-format" aria-label="File format"><option value="png" selected>png</option><option value="svg">svg</option></select>
<select id="axes-select" aria-label="Mapa ativo"></select><output id="coordinates" aria-live="off"></output></footer></section>
<script id="map-data" type="application/json">{metadata}</script><script>{navigation}</script><script>{components}</script><script>{js}</script>
</body></html>'''
