"""Validation shared by the independent rendering backends."""
from __future__ import annotations

import math

from ..scene import Circle, Path, Rect, Scene, Text

SHAPE_STYLE = {
    "fill", "stroke", "stroke_width", "opacity", "dash", "linecap",
    "linejoin", "fill_opacity", "stroke_opacity", "shape_rendering",
}
TEXT_STYLE = (SHAPE_STYLE - {"dash", "linecap", "linejoin"}) | {
    "font_family", "font_size", "font_weight", "font_style", "anchor",
    "baseline", "rotation", "rotation_mode", "background", "multiline",
}


def number(value: float) -> str:
    if not math.isfinite(float(value)):
        raise ValueError("Drawing coordinates must be finite")
    return format(float(value), ".8g")


def validate(scene: Scene, *, _path_validator=None) -> None:
    for size in (scene.width, scene.height):
        if not math.isfinite(size) or size <= 0:
            raise ValueError("Scene width and height must be finite and positive")
    for item in scene.items:
        allowed = TEXT_STYLE if isinstance(item, Text) else SHAPE_STYLE
        unknown = set(item.style) - allowed
        if unknown:
            raise ValueError(f"Unsupported {type(item).__name__} style: {', '.join(sorted(unknown))}")
        s = item.style
        if s.get('shape_rendering','auto') not in ('auto','crispEdges'):raise ValueError('Invalid shape rendering hint')
        for key in ("opacity", "fill_opacity", "stroke_opacity"):
            value = s.get(key, 1)
            if not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{key} must be between zero and one")
        width = s.get("stroke_width", 1)
        if not math.isfinite(width) or width < 0:
            raise ValueError("stroke_width must be finite and nonnegative")
        if s.get("linecap", "butt") not in ("butt", "round", "square"):
            raise ValueError("linecap must be 'butt', 'round', or 'square'")
        if s.get("linejoin", "round") not in ("round", "miter", "bevel"):
            raise ValueError("linejoin must be 'round', 'miter', or 'bevel'")
        dash = s.get("dash")
        if dash is not None and any(not math.isfinite(v) or v <= 0 for v in dash):
            raise ValueError("dash must contain positive lengths; an empty sequence means solid")
        if item.clip is not None:
            if len(item.clip) != 4 or not all(math.isfinite(v) for v in item.clip):
                raise ValueError("clip must be a finite (x, y, width, height) tuple")
            if item.clip[2] < 0 or item.clip[3] < 0:
                raise ValueError("Clip dimensions cannot be negative")
        if isinstance(item, Path):
            if _path_validator is not None:
                _path_validator(item)
                continue
            for part in item.paths:
                for point in part:
                    if len(point) != 2 or not all(math.isfinite(v) for v in point):
                        raise ValueError("Path coordinates must be finite (x, y) pairs")
        elif isinstance(item, Text):
            if not isinstance(s.get('multiline',False),bool):raise ValueError('multiline must be boolean')
            number(item.x)
            number(item.y)
            number(s.get("rotation", 0))
            if s.get("anchor", "start") not in ("start", "middle", "end"):
                raise ValueError("anchor must be 'start', 'middle', or 'end'")
            if s.get("baseline", "alphabetic") not in ("top", "middle", "bottom", "alphabetic"):
                raise ValueError("baseline must be 'top', 'middle', 'bottom', or 'alphabetic'")
            if not math.isfinite(s.get("font_size", 12)) or s.get("font_size", 12) <= 0:
                raise ValueError("font_size must be finite and positive")
            if s.get("font_style", "normal") not in ("normal", "italic", "oblique"):
                raise ValueError("font_style must be 'normal', 'italic', or 'oblique'")
            weight = s.get("font_weight", "normal")
            if weight not in ("normal", "bold") and str(weight) not in {str(v) for v in range(100, 1000, 100)}:
                raise ValueError("font_weight must be 'normal', 'bold', or a multiple of 100 from 100 to 900")
            if "\n" in str(item.text) or "\r" in str(item.text):
                raise ValueError("A Text primitive holds one line; use one Text per line for multiline labels")
        elif isinstance(item, Circle):
            for value in (item.x, item.y, item.r):
                number(value)
            if item.r < 0:
                raise ValueError("Circle radius cannot be negative")
        elif isinstance(item, Rect):
            for value in (item.x, item.y, item.width, item.height):
                number(value)
            if item.width < 0 or item.height < 0:
                raise ValueError("Rectangle dimensions cannot be negative")
        else:
            raise TypeError(f"Unsupported scene primitive: {type(item).__name__}")
