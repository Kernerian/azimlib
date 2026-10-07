"""Dependency-free, deterministic SVG serialization."""
from __future__ import annotations

from html import escape
import base64

from ..scene import Circle, Path, Rect, Scene, Text
from ._common import number as n, validate


def _attr(name, value):
    return f' {name}="{escape(str(value), quote=True)}"'


def _paint(style, text=False):
    attrs = _attr("fill", style.get("fill", "#172b38" if text else "none") or "none")
    attrs += _attr("stroke", style.get("stroke", "none") or "none")
    attrs += _attr("stroke-width", n(style.get("stroke_width", 1)))
    attrs += _attr("stroke-linecap", style.get("linecap", "butt"))
    attrs += _attr("stroke-linejoin", style.get("linejoin", "round"))
    for key in ("opacity", "fill_opacity", "stroke_opacity"):
        if key in style:
            attrs += _attr(key.replace("_", "-"), n(style[key]))
    if style.get("dash"):
        attrs += _attr("stroke-dasharray", " ".join(n(v) for v in style["dash"]))
    if 'shape_rendering' in style:attrs += _attr('shape-rendering',style['shape_rendering'])
    return attrs


def render_svg(scene: Scene) -> str:
    """Serialize a scene as SVG without any optional dependencies.

    Units are pixels. Text remains editable vector text. Used bundled DejaVu
    faces are embedded; other families are resolved by the SVG viewer.
    """
    validate(scene)
    clips = {}
    for item in scene.items:
        if item.clip is not None:
            clips.setdefault(tuple(item.clip), f"clip-{len(clips)}")
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{n(scene.width)}" height="{n(scene.height)}" viewBox="0 0 {n(scene.width)} {n(scene.height)}">']
    if scene._material_notices:
        import json
        out.append('<metadata id="azimlib-material-provenance">'+escape(json.dumps(scene._material_notices,ensure_ascii=True,sort_keys=True))+'</metadata>')
    # Embed only used DejaVu faces so standalone SVG/HTML matches desktop
    # typography even on a computer without those fonts installed.
    from ..typography import font_path
    faces={}
    for item in scene.items:
        if isinstance(item,Text):
            path=font_path(item.style)
            if path is not None:faces[path]=item.style
    if faces:
        from ..typography import FONTS
        out.append('<metadata id="azimlib-font-license">'+escape((FONTS/'LICENSE_DEJAVU').read_text('utf8'))+'</metadata>')
        out.append('<defs><style>')
        for path,style in faces.items():
            data=base64.b64encode(path.read_bytes()).decode('ascii')
            weight='bold' if 'Bold' in path.stem else 'normal'
            slant='oblique' if 'Oblique' in path.stem else 'normal'
            out.append(f'@font-face{{font-family:"DejaVu Sans";font-weight:{weight};font-style:{slant};src:url(data:font/ttf;base64,{data}) format("truetype");}}')
        out.append('</style></defs>')
    if clips:
        out.append("<defs>")
        for (x, y, width, height), clip_id in clips.items():
            out.append(f'<clipPath id="{clip_id}"><rect x="{n(x)}" y="{n(y)}" width="{n(width)}" height="{n(height)}"/></clipPath>')
        out.append("</defs>")
    if scene.background is not None:
        out.append(f'<rect width="100%" height="100%"{_attr("fill", scene.background)}/>')
    for item in scene.items:
        clip = _attr("clip-path", f"url(#{clips[tuple(item.clip)]})") if item.clip is not None else ""
        if isinstance(item, Path):
            commands = []
            for part in item.paths:
                if len(part)<2 or not any(p!=part[0] for p in part):
                    continue
                commands.append("M " + " L ".join(f"{n(x)} {n(y)}" for x, y in part) + (" Z" if item.closed else ""))
            out.append(f'<path{_attr("d", " ".join(commands))} fill-rule="evenodd"{_paint(item.style)}{clip}/>')
        elif isinstance(item, Circle):
            out.append(f'<circle cx="{n(item.x)}" cy="{n(item.y)}" r="{n(item.r)}"{_paint(item.style)}{clip}/>')
        elif isinstance(item, Rect):
            out.append(f'<rect x="{n(item.x)}" y="{n(item.y)}" width="{n(item.width)}" height="{n(item.height)}"{_paint(item.style)}{clip}/>')
        elif isinstance(item, Text):
            s = item.style
            attrs = _paint(s, text=True)
            attrs += _attr("font-family", s.get("font_family", "sans-serif"))
            attrs += _attr("font-size", n(s.get("font_size", 12)))
            attrs += _attr("font-weight", s.get("font_weight", "normal"))
            attrs += _attr("font-style", s.get("font_style", "normal"))
            attrs += _attr("text-anchor", s.get("anchor", "start"))
            from ..typography import text_baseline_offset
            baseline_y=item.y+text_baseline_offset(item.text,s)
            attrs += _attr("dominant-baseline", "alphabetic")
            # Keep clipping in scene coordinates, outside the rotated text group.
            out.append(f"<g{clip}>")
            rotation = s.get("rotation", 0)
            transform = _attr("transform", f"rotate({n(rotation)} {n(item.x)} {n(item.y)})") if rotation else ""
            out.append(f"<g{transform}>")
            if s.get("background"):
                from ..typography import text_bounds
                bx,by,width,height=text_bounds(item.text,s)
                x,y=item.x+bx,item.y+by
                out.append(f'<rect x="{n(x - 3)}" y="{n(y - 3)}" width="{n(width + 6)}" height="{n(height + 6)}"{_attr("fill", s["background"])}{_attr("opacity", n(s.get("opacity", 1)))}/>')
            attrs += ' paint-order="stroke fill"'
            out.append(f'<text x="{n(item.x)}" y="{n(baseline_y)}"{attrs}>{escape(str(item.text))}</text>')
            out.append("</g></g>")
    out.append("</svg>")
    return "\n".join(out) + "\n"
