"""Rasterize the scene directly with Pillow, without an SVG/plotting backend.

Polygon masks use even-odd filling. Stroke geometry, dash subdivision, clipping,
opacity composition, font placement, and antialiasing are owned by this module.
Pillow supplies pixel buffers, polygon filling, font rasterization, and PNG I/O.
"""
from __future__ import annotations

import math
from pathlib import Path as FilePath

from ..scene import Circle, Path, Rect, Scene, Text
from ._common import validate


# Budget for a cropped source band, not total renderer/process memory. One
# output row needs three full-width source rows and can exceed this budget.
_BOX_BAND_BYTES = 4 * 1024 * 1024
_COMPOSITE_BAND_BYTES = 4 * 1024 * 1024
# Avoid extra crops/allocation sizes when the original full operation is small.
_BAND_THRESHOLD_BYTES = 16 * 1024 * 1024


def _composite_rgba(destination, source, origin):
    """Borrow RGBA images; composite an already-clipped tile in bounded bands.

    Alpha composition is independent per pixel. Avoid full-tile copies of the
    destination and composed result inside Pillow's in-place convenience API.
    The budget limits a source crop; other buffers/process memory are separate,
    and a single full-width row can exceed it. Small tiles keep the same path.
    """
    if source.width*source.height*4<=_BAND_THRESHOLD_BYTES:
        destination.alpha_composite(source,origin)
        return
    rows=max(1,_COMPOSITE_BAND_BYTES//(source.width*4))
    x,y=origin
    for top in range(0,source.height,rows):
        band=source.crop((0,top,source.width,min(source.height,top+rows)))
        try:destination.alpha_composite(band,(x,y+top))
        finally:band.close()


def _downsample_box(canvas, target, Image):
    """Borrow a 3x RGBA canvas; return the same BOX result using aligned bands.

    Pillow premultiplies RGBA before filtering. On a large canvas that creates
    another full-resolution buffer. BOX at our exact integer ratio uses only
    the three source rows per output row, so bands have no overlap/seams and
    preserve both passes' rounding and alpha filtering. Each band still uses
    Pillow's normal RGBA BOX path; no opaque-only shortcut or new filter.
    """
    width,height=target
    if canvas.mode!='RGBA' or canvas.size!=(width*3,height*3):
        raise ValueError('BOX reduction requires a 3x RGBA canvas')
    if canvas.width*canvas.height*4<=_BAND_THRESHOLD_BYTES:
        return canvas.resize(target,Image.Resampling.BOX)
    rows=max(1,_BOX_BAND_BYTES//(canvas.width*3*4))
    result=Image.new('RGBA',target)
    try:
        for top in range(0,height,rows):
            bottom=min(height,top+rows)
            source=canvas.crop((0,top*3,canvas.width,bottom*3))
            try:
                band=source.resize((width,bottom-top),Image.Resampling.BOX)
                try:result.paste(band,(0,top))
                finally:band.close()
            finally:source.close()
    except BaseException:
        result.close()
        raise
    return result


def _color(value, ImageColor):
    if value is None or value == "none":
        return (0, 0, 0, 0)
    try:
        return ImageColor.getcolor(value, "RGBA")
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Pillow cannot resolve color {value!r}; use a CSS color name or hex color") from exc


def _dash_parts(points, pattern):
    """Subdivide a polyline while preserving dash phase across vertices."""
    if not pattern:
        return [points]
    pattern = list(pattern)
    if len(pattern) % 2:
        pattern *= 2
    result, current = [], []
    index, remaining, on = 0, float(pattern[0]), True
    for a, b in zip(points, points[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length == 0:
            continue
        travelled = 0.0
        while travelled < length - 1e-9:
            step = min(remaining, length - travelled)
            p = (a[0] + dx * travelled / length, a[1] + dy * travelled / length)
            q = (a[0] + dx * (travelled + step) / length, a[1] + dy * (travelled + step) / length)
            if on:
                if not current:
                    current.append(p)
                current.append(q)
            travelled += step
            remaining -= step
            if remaining < 1e-9:
                if on and current:
                    result.append(current)
                    current = []
                index = (index + 1) % len(pattern)
                remaining = float(pattern[index])
                on = index % 2 == 0
    if current:
        result.append(current)
    # A closed ring with an unbroken dash across its seam has no endpoint cap.
    if len(result) > 1 and points[0] == points[-1] and result[0][0] == points[0] and result[-1][-1] == points[0]:
        result[0] = result[-1][:-1] + result[0]
        result.pop()
    return result


def _stroke(draw, points, width, cap, join, closed=False):
    """Construct stroke polygons, including explicit caps and joins."""
    points = [p for i, p in enumerate(points) if i == 0 or p != points[i - 1]]
    if not points or width <= 0:
        return
    radius = width / 2
    if closed and len(points) > 1 and points[-1] == points[0]:
        points = points[:-1]
    if len(points) == 1:
        x, y = points[0]
        if cap == "round":
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=255)
        elif cap == "square":
            draw.rectangle((x - radius, y - radius, x + radius, y + radius), fill=255)
        return
    segments = list(zip(points, points[1:] + ([points[0]] if closed else [])))
    directions = []
    for a, b in segments:
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        dx, dy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
        nx, ny = -dy * radius, dx * radius
        draw.polygon([(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny),
                      (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)], fill=255)
        directions.append((dx, dy))
    for i in (range(len(points)) if closed else range(1, len(points) - 1)):
        v = points[i]
        before, after = directions[(i - 1) % len(directions)], directions[i % len(directions)]
        if join == "round":
            draw.ellipse((v[0] - radius, v[1] - radius, v[0] + radius, v[1] + radius), fill=255)
            continue
        cross = before[0] * after[1] - before[1] * after[0]
        for side in (-1, 1):
            a = (v[0] - before[1] * radius * side, v[1] + before[0] * radius * side)
            b = (v[0] - after[1] * radius * side, v[1] + after[0] * radius * side)
            triangle = [v, a, b]
            if join == "miter" and abs(cross) > 1e-10:
                t = ((b[0] - a[0]) * after[1] - (b[1] - a[1]) * after[0]) / cross
                miter = (a[0] + t * before[0], a[1] + t * before[1])
                if math.hypot(miter[0] - v[0], miter[1] - v[1]) <= radius * 4:
                    triangle = [v, a, miter, b]
            draw.polygon(triangle, fill=255)
    if not closed:
        for point, direction, sign in ((points[0], directions[0], -1), (points[-1], directions[-1], 1)):
            x, y = point
            dx, dy = direction
            if cap == "round":
                draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=255)
            elif cap == "square":
                nx, ny = -dy * radius, dx * radius
                ex, ey = dx * radius * sign, dy * radius * sign
                draw.polygon([(x + nx, y + ny), (x + nx + ex, y + ny + ey),
                              (x - nx + ex, y - ny + ey), (x - nx, y - ny)], fill=255)


def _font(style, factor, ImageFont):
    family = str(style.get("font_family", "sans-serif"))
    weight = style.get("font_weight", "normal")
    bold = weight == "bold" or str(weight).isdigit() and int(weight) >= 600
    italic = style.get("font_style", "normal") != "normal"
    suffix = ("-BoldOblique" if bold and italic else "-Bold" if bold else "-Oblique" if italic else "")
    generic = {
        "sans-serif": [f"DejaVuSans{suffix}.ttf", "arialbi.ttf" if bold and italic else "arialbd.ttf" if bold else "ariali.ttf" if italic else "arial.ttf"],
        "serif": [f"DejaVuSerif{suffix.replace('Oblique', 'Italic')}.ttf", "timesbi.ttf" if bold and italic else "timesbd.ttf" if bold else "timesi.ttf" if italic else "times.ttf"],
        "monospace": [f"DejaVuSansMono{suffix}.ttf", "courbi.ttf" if bold and italic else "courbd.ttf" if bold else "couri.ttf" if italic else "cour.ttf"],
    }
    candidates = []
    from ..typography import font_path
    bundled=font_path(style)
    if bundled is not None:candidates.append(str(bundled))
    for part in family.split(","):
        part = part.strip().strip("\"'")
        normalized = part.lower().replace(" ", "")
        aliases = {"dejavusans": "sans-serif", "dejavuserif": "serif", "dejavusansmono": "monospace"}
        if normalized in aliases:
            candidates.extend(generic[aliases[normalized]])
        elif normalized in ("arial", "timesnewroman", "couriernew"):
            base = {"arial": "arial", "timesnewroman": "times", "couriernew": "cour"}[normalized]
            suffix_ms = "bi" if bold and italic else "bd" if bold else "i" if italic else ""
            candidates.extend([base + suffix_ms + ".ttf", part])
        else:
            candidates.extend(generic.get(part.lower(), [part, part + ".ttf", part.replace(" ", "") + ".ttf"]))
    size = max(1, round(style.get("font_size", 12) * factor))
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    if family in generic:
        # Pillow's bundled scalable font keeps PNG available on minimal systems.
        return ImageFont.load_default(size=size)
    raise ValueError(f"Font family {family!r} is unavailable; supply an installed font or its .ttf path")


def render_png(scene: Scene, path_or_stream, scale: float = 1) -> None:
    """Write a PNG with optional Pillow; no geographic/plotting dependency.

    ``scale`` multiplies dimensions, preserving the physical scene layout. An
    internal 3x supersampling pass antialiases polygons, lines, and text. File
    paths and binary writable streams are accepted. Install ``azimlib[png]``
    to enable this backend.
    """
    validate(scene)
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError("scale must be finite and positive")
    try:
        from PIL import Image, ImageColor, ImageDraw, ImageFont
    except ImportError as exc:
        raise ImportError("PNG export requires Pillow; install azimlib[png]") from exc

    factor = 3 * scale
    target = (max(1, round(scene.width * scale)), max(1, round(scene.height * scale)))
    size = (target[0] * 3, target[1] * 3)
    canvas = Image.new("RGBA", size, _color(scene.background, ImageColor))

    from .coverage import unit_circle
    fonts={};alpha_tables={}
    def remember_table(key,values):
        # Bound temporary lookup memory for maps with many distinct opacities.
        if len(alpha_tables)>=128:alpha_tables.pop(next(iter(alpha_tables)))
        alpha_tables[key]=values
    def attenuate(mask,alpha):
        if alpha==1:return mask
        key=('scale',alpha)
        if key not in alpha_tables:remember_table(key,[round(v*alpha) for v in range(256)])
        return mask.point(alpha_tables[key])
    def paint(layer, mask, color, opacity=1, *, empty=False):
        rgba = _color(color, ImageColor)
        if rgba[3] == 0 or opacity == 0:
            return False
        alpha = rgba[3] / 255 * opacity
        band = attenuate(mask,alpha)
        if empty:
            # First shape paint has no destination to blend with. Reuse its
            # tile, preserving exact alpha rounding and coverage. Text still
            # composites normally before rotation/filtering.
            layer.paste(rgba,(0,0,*layer.size))
            layer.putalpha(band)
        else:
            solid = Image.new("RGBA", layer.size, rgba)
            solid.putalpha(band)
            _composite_rgba(layer,solid,(0,0))
            solid.close()
        if band is not mask:band.close()
        return True

    for item in scene.items:
        style = item.style
        if isinstance(item, Circle) and item.r == 0:
            continue
        if isinstance(item, Rect) and (item.width == 0 or item.height == 0):
            continue
        fill = style.get("fill", "#172b38" if isinstance(item, Text) else "none")
        stroke = style.get("stroke", "none")
        stroke_width = style.get("stroke_width", 1) * factor
        if isinstance(item, Text):
            key=(style.get("font_family"),style.get("font_weight"),style.get("font_style"),style.get("font_size"))
            if key not in fonts:fonts[key]=_font(style,factor,ImageFont)
            font=fonts[key]
            anchor = {"start": "l", "middle": "m", "end": "r"}[style.get("anchor", "start")]
            anchor += 's'
            from ..typography import text_baseline_offset
            baseline_offset=text_baseline_offset(item.text,style)*factor
            text = str(item.text)
            outline = round(stroke_width / 2) if stroke not in (None, "none") else 0
            bounds = ImageDraw.Draw(Image.new("L",(1,1))).textbbox((0, 0), text, font=font, anchor=anchor, stroke_width=outline)
            pad = math.ceil(3 * factor)
            background_box=None
            if style.get('background'):
                from ..typography import text_bounds
                bx,by,bw,bh=text_bounds(text,style)
                by=by*factor-baseline_offset;bx*=factor;bw*=factor;bh*=factor
                background_box=(bx-pad,by-pad,bx+bw+pad,by+bh+pad)
                bounds=(min(bounds[0],bx),min(bounds[1],by),max(bounds[2],bx+bw),max(bounds[3],by+bh))
            box = (math.floor(bounds[0]) - pad, math.floor(bounds[1]) - pad,
                   math.ceil(bounds[2]) + pad, math.ceil(bounds[3]) + pad)
            tile = Image.new("RGBA", (max(1, box[2] - box[0]), max(1, box[3] - box[1])))
            if background_box:
                from .coverage import FillCoverageDraw
                left,top,right,bottom=background_box
                corners=[(left-box[0],top-box[1]),(right-box[0],top-box[1]),(right-box[0],bottom-box[1]),(left-box[0],bottom-box[1])]
                bgmask=Image.new('L',tile.size);FillCoverageDraw(bgmask).polygons([corners])
                paint(tile,bgmask,style['background'])
                bgmask.close()
            glyph = Image.new("L", tile.size)
            ImageDraw.Draw(glyph).text((-box[0], -box[1]), text, font=font, anchor=anchor, fill=255)
            def paint_text(mask, color, opacity):
                rgba = _color(color, ImageColor)
                ink = Image.new("RGBA", tile.size, rgba)
                key=('text',rgba[3],opacity)
                if key not in alpha_tables:
                    remember_table(key,[round(v*rgba[3]/255*opacity) for v in range(256)])
                band=mask.point(alpha_tables[key])
                ink.putalpha(band)
                band.close()
                _composite_rgba(tile,ink,(0,0))
                ink.close()
            if outline:
                border = Image.new("L", tile.size)
                ImageDraw.Draw(border).text((-box[0], -box[1]), text, font=font, anchor=anchor,
                                            fill=0, stroke_width=outline, stroke_fill=255)
                paint_text(border, stroke, style.get("stroke_opacity", 1))
                border.close()
            paint_text(glyph, fill, style.get("fill_opacity", 1))
            glyph.close()
            angle = style.get("rotation", 0)
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2+baseline_offset
            if angle:
                theta = math.radians(angle)
                cx, cy = cx * math.cos(theta) - cy * math.sin(theta), cx * math.sin(theta) + cy * math.cos(theta)
                rotated=tile.rotate(-angle, resample=Image.Resampling.BICUBIC, expand=True)
                tile.close();tile=rotated
            origin=(round(item.x*factor+cx-tile.width/2),round(item.y*factor+cy-tile.height/2))
            layer=tile
        else:
            if isinstance(item, Path):
                parts = [[(x * factor, y * factor) for x, y in p] for p in item.paths if p]
                closed = item.closed
            elif isinstance(item, Rect):
                x, y, w, h = item.x * factor, item.y * factor, item.width * factor, item.height * factor
                parts = [[(x, y), (x + w, y), (x + w, y + h), (x, y + h)]]
                closed = True
            elif isinstance(item, Circle):
                # Adaptive polygonization lets circles share dash/cap/join code.
                # A small circle needs enough vertices to conserve its area;
                # a circumference-based minimum of 24 visibly under-resolves it.
                count = max(64, min(4096, math.ceil(2 * math.pi * item.r * factor / 2)))
                parts = [[((item.x+item.r*c)*factor,(item.y+item.r*s)*factor) for c,s in unit_circle(count)]]
                closed = True
            else:
                raise TypeError(f"Unsupported primitive {type(item).__name__}")
            # Allocate only the affected tile. Integer origins preserve global
            # supersampling phase and exact stroke coverage.
            points=[p for part in parts for p in part]
            if not points:continue
            margin=max(2,stroke_width*4+2)
            left=max(0,math.floor(min(p[0] for p in points)-margin))
            top=max(0,math.floor(min(p[1] for p in points)-margin))
            right=min(size[0],math.ceil(max(p[0] for p in points)+margin))
            bottom=min(size[1],math.ceil(max(p[1] for p in points)+margin))
            if item.clip is not None:
                x,y,w,h=item.clip
                left=max(left,math.ceil(x*factor));top=max(top,math.ceil(y*factor))
                right=min(right,math.ceil((x+w)*factor));bottom=min(bottom,math.ceil((y+h)*factor))
            if left>=right or top>=bottom:continue
            origin=(left,top);tile_size=(right-left,bottom-top)
            parts=[[(x-left,y-top) for x,y in part] for part in parts]
            layer=Image.new('RGBA',tile_size)
            empty=True
            if fill not in (None, "none"):
                mask = Image.new("L", tile_size)
                from .coverage import FillCoverageDraw
                FillCoverageDraw(mask).polygons([part for part in parts if len(part)>=3],antialiased=style.get('shape_rendering')!='crispEdges')
                empty=not paint(layer, mask, fill, style.get("fill_opacity", 1),empty=empty)
                mask.close()
            if stroke not in (None, "none") and stroke_width > 0:
                mask = Image.new("L", tile_size)
                from .coverage import CoverageDraw
                draw = CoverageDraw(mask)
                dash = [v * factor for v in style["dash"]] if style.get("dash") else None
                for part in parts:
                    if closed and len(part) > 1 and part[-1] != part[0]:
                        part = part + [part[0]]
                    for run in _dash_parts(part, dash):
                        _stroke(draw, run, stroke_width, style.get("linecap", "butt"),
                                style.get("linejoin", "round"), closed=closed and not dash)
                paint(layer, mask, stroke, style.get("stroke_opacity", 1),empty=empty)
                del draw
                mask.close()
        if style.get('opacity',1)!=1:
            channel=layer.getchannel('A');band=attenuate(channel,style['opacity'])
            layer.putalpha(band)
            if band is not channel:band.close()
            channel.close()
        left,top=origin;right,bottom=left+layer.width,top+layer.height
        clip=(0,0,*size)
        if item.clip is not None:
            x,y,w,h=item.clip
            clip=(max(0,math.ceil(x*factor)),max(0,math.ceil(y*factor)),
                  min(size[0],math.ceil((x+w)*factor)),min(size[1],math.ceil((y+h)*factor)))
        x0,y0=max(left,clip[0]),max(top,clip[1])
        x1,y1=min(right,clip[2]),min(bottom,clip[3])
        if x0<x1 and y0<y1:
            if (x0,y0,x1,y1)!=(left,top,right,bottom):
                cropped=layer.crop((x0-left,y0-top,x1-left,y1-top))
                layer.close();layer=cropped
            _composite_rgba(canvas,layer,(x0,y0))
        layer.close()
    # Box averaging conserves stroke coverage. Lanczos ringing darkens thin
    # lines after negative lobes are clamped against a white background.
    try:resized=_downsample_box(canvas,target,Image)
    finally:canvas.close()
    canvas=resized
    try:
        if isinstance(path_or_stream, (str, FilePath)):
            canvas.save(str(path_or_stream), format="PNG")
        else:
            canvas.save(path_or_stream, format="PNG")
    finally:
        canvas.close()
