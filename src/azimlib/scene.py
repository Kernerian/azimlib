"""Backend-neutral drawing primitives, in screen pixels.

The cartographic pipeline ends here: renderers receive only paths and graphic
objects, never longitude/latitude coordinates or geographic datasets.
Coordinates have y pointing down; primitive rotation is clockwise. Public
plotting angles are converted to this convention at the style boundary.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from contextlib import contextmanager
from typing import Any, Mapping, Sequence

Point = tuple[float, float]
Clip = tuple[float, float, float, float]
Style = Mapping[str, Any]


@dataclass(frozen=True)
class Path:
    """A multipart path; closed rings use the even-odd fill rule."""

    paths: Sequence[Sequence[Point]]
    closed: bool = False
    style: Style = field(default_factory=dict)
    clip: Clip | None = None


@dataclass(frozen=True)
class Text:
    x: float
    y: float
    text: str
    style: Style = field(default_factory=dict)
    clip: Clip | None = None

    def __post_init__(self):
        # Public styles may still request post-rotation alignment. Bake it
        # once so both renderers, clipping and primitive bounds agree.
        if self.style.get('rotation_mode','anchor')!='anchor':
            from .typography import text_rotation_offset
            dx,dy=text_rotation_offset(self.text,self.style)
            object.__setattr__(self,'x',self.x+dx);object.__setattr__(self,'y',self.y+dy)
            object.__setattr__(self,'style',dict(self.style,rotation_mode='anchor'))


@dataclass(frozen=True)
class Circle:
    x: float
    y: float
    r: float
    style: Style = field(default_factory=dict)
    clip: Clip | None = None


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    width: float
    height: float
    style: Style = field(default_factory=dict)
    clip: Clip | None = None


Primitive = Path | Text | Circle | Rect


@dataclass
class Scene:
    width: float
    height: float
    background: str | None = "#ffffff"
    items: list[Primitive] = field(default_factory=list)
    maps: list[dict[str, Any]] = field(default_factory=list)
    _layout_excluded: set[int] = field(default_factory=set, repr=False)
    _layout_groups: list = field(default_factory=list, repr=False)
    _layout_bars: list = field(default_factory=list, repr=False)
    _layout_free: list = field(default_factory=list, repr=False)
    _layout_scales: dict = field(default_factory=dict, repr=False)
    _text_blocks: list = field(default_factory=list, repr=False)
    _layout_suptitle: tuple | None = field(default=None, repr=False)
    _layout_supxlabel: tuple | None = field(default=None, repr=False)
    _layout_supylabel: tuple | None = field(default=None, repr=False)

    @contextmanager
    def layout_artist(self,artist):
        """An excluded artist remains painted, but does not reserve space."""
        start=len(self.items)
        yield
        if not getattr(artist,'get_in_layout',lambda:True)():
            self._layout_excluded.update(range(start,len(self.items)))

    def add(self, item: Primitive) -> Primitive:
        """Append a primitive in painting order and return it."""
        if not isinstance(item, (Path, Text, Circle, Rect)):
            raise TypeError("A scene accepts only Path, Text, Circle, or Rect primitives")
        self.items.append(item)
        return item

    def scaled(self, factor: float) -> Scene:
        """Scale screen units, preserving geography and scene item indexes."""
        import math
        if not math.isfinite(factor) or factor <= 0:
            raise ValueError("Scene scale must be finite and positive")
        result = Scene(self.width*factor, self.height*factor, self.background)
        for item in self.items:
            style = dict(item.style)
            style['stroke_width'] = style.get('stroke_width', 1)*factor
            if isinstance(item, Text):
                style['font_size'] = style.get('font_size', 12)*factor
            if style.get('dash'):
                style['dash'] = tuple(v*factor for v in style['dash'])
            clip = tuple(v*factor for v in item.clip) if item.clip is not None else None
            if isinstance(item, Path):
                new = Path([[(x*factor,y*factor) for x,y in part] for part in item.paths], item.closed, style, clip)
            elif isinstance(item, Text):
                new = Text(item.x*factor,item.y*factor,item.text,style,clip)
            elif isinstance(item, Circle):
                new = Circle(item.x*factor,item.y*factor,item.r*factor,style,clip)
            else:
                new = Rect(item.x*factor,item.y*factor,item.width*factor,item.height*factor,style,clip)
            result.add(new)
        for metadata in self.maps:
            scaled = dict(metadata)
            scaled['pixel_ratio']=metadata.get('pixel_ratio',1)*factor
            scaled['box'] = tuple(v*factor for v in metadata['box'])
            if 'navigation_box' in metadata:scaled['navigation_box']=tuple(v*factor for v in metadata['navigation_box'])
            if 'tick_area' in metadata:scaled['tick_area']=tuple(v*factor for v in metadata['tick_area'])
            for key in ('ox','oy','scale'):
                scaled[key] *= factor
            if 'overview_map' in metadata:
                mini=dict(metadata['overview_map'])
                for key in ('box','focus_box'):mini[key]=tuple(v*factor for v in mini[key])
                for key in ('ox','oy','scale'):mini[key]*=factor
                scaled['overview_map']=mini
            result.maps.append(scaled)
        result._layout_excluded=set(self._layout_excluded)
        result._layout_groups=[(owners,start,end,tuple(v*factor for v in slot)) for owners,start,end,slot in self._layout_groups]
        result._layout_bars=[(bar,start,end) for bar,start,end in self._layout_bars]
        result._layout_free=list(self._layout_free)
        result._layout_scales=dict(self._layout_scales)
        result._text_blocks=[(start,end,tuple(v*factor for v in box),
                             tuple(v*factor for v in clip) if clip is not None else None)
                            for start,end,box,clip in self._text_blocks]
        result._layout_suptitle=tuple(v*factor for v in self._layout_suptitle) if self._layout_suptitle is not None else None
        result._layout_supxlabel=tuple(v*factor for v in self._layout_supxlabel) if self._layout_supxlabel is not None else None
        result._layout_supylabel=tuple(v*factor for v in self._layout_supylabel) if self._layout_supylabel is not None else None
        return result
