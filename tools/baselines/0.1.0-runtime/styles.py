"""Plotting styles and small, dependency-free color scales."""
from __future__ import annotations

import math

PALETTES = {
    'gray':('#000000','#ffffff'),'Greys':('#ffffff','#000000'),
    "ocean": ("#e0f4ef", "#98d4ce", "#42a6ab", "#19758b", "#123b60"),
    "viridis": ("#440154", "#3b528b", "#21918c", "#5ec962", "#fde725"),
    # ColorBrewer Blues (5); see THIRD_PARTY_LICENSES and LicenseRef-ColorBrewer.
    "blues": ("#eff3ff", "#bdd7e7", "#6baed6", "#3182bd", "#08519c"),
    "sunset": ("#fff2cc", "#f7c675", "#e9854d", "#bc4848", "#692f59"),
    "terrain": ("#e5edc9", "#abc58b", "#7a9e6b", "#a3946a", "#f6f1e8"),
}
CATEGORY_COLORS = ("#147d92", "#e49b48", "#709755", "#9b6ca6", "#db6c69", "#6b8cae", "#c5b25f", "#6fa9a0")
_KEYS = {
    "color", "facecolor", "edgecolor", "linewidth", "linestyle", "alpha",
    "zorder", "label", "linecap", "linejoin", "arrow", "arrowstyle",
    "arrowsize", "curved", "marker", "markersize", "rotation", "fontfamily",
    "fontsize", "fontweight", "ha", "va", "rotation_mode", "background", "halo", "halo_width",
    "priority", "symbol", "fill_alpha", "edge_alpha", "fontstyle",
    "markerfacecolor", "markeredgecolor", "markeredgewidth",
    "hatch","hatch_color","hatch_linewidth","hatch_spacing","antialiased",
    "solid_capstyle", "dash_capstyle", "solid_joinstyle", "dash_joinstyle",
}
_ALIASES = {"lw": "linewidth", "ls": "linestyle", "c": "color", "fc": "facecolor",
            "ec": "edgecolor", "ms": "markersize", "size": "fontsize", "weight": "fontweight",
            "mfc":"markerfacecolor", "mec":"markeredgecolor", "mew":"markeredgewidth",
            "family":"fontfamily", "horizontalalignment":"ha", "verticalalignment":"va","aa":"antialiased"}


def normalize_aliases(values):
    """Resolve explicit property names before merging internal defaults.

    Two spellings of the same caller property are ambiguous even if their
    values agree. Internal defaults may be overridden through either spelling.
    This helper deliberately leaves non-style control keys untouched.
    """
    result={};spellings={}
    for original,value in values.items():
        key=_ALIASES.get(original,original)
        if key in result:
            raise TypeError(f'{spellings[key]!r} and {original!r} are aliases of {key!r}; pass only one')
        result[key]=value;spellings[key]=original
    return result


def style_dict(values=None, **kwargs):
    result = {}
    for key, value in normalize_aliases(dict(values or {}, **kwargs)).items():
        if key not in _KEYS:
            raise TypeError(f"Unknown style {key!r}; supported: {', '.join(sorted(_KEYS))}")
        result[key] = value
    for key in ("linewidth", "arrowsize", "markersize", "fontsize", "halo_width", "markeredgewidth","hatch_linewidth","hatch_spacing"):
        if key in result:
            result[key]=float(result[key])
            if not math.isfinite(result[key]) or result[key]<0 or key=='fontsize' and result[key]==0:
                raise ValueError(f"{key} must be finite and {'positive' if key=='fontsize' else 'non-negative'}")
    for key in ("alpha", "fill_alpha", "edge_alpha"):
        if key in result:
            result[key]=float(result[key])
            if not 0<=result[key]<=1:raise ValueError(f"{key} must lie in [0, 1]")
    for key in ("zorder", "rotation", "priority", "curved"):
        if key in result:
            if key=='rotation':
                result[key]={'vertical':90,'horizontal':0,None:0}.get(result[key],result[key])
            result[key]=float(result[key])
            if not math.isfinite(result[key]):raise ValueError(f"{key} must be finite")
    if 'fontfamily' in result and (not isinstance(result['fontfamily'],str) or not result['fontfamily'].strip()):
        raise ValueError('fontfamily must be a nonempty string; family lists are not implemented')
    if 'fontstyle' in result and result['fontstyle'] not in ('normal','italic','oblique'):
        raise ValueError('fontstyle must be normal, italic, or oblique')
    if 'fontweight' in result and str(result['fontweight']) not in ('normal','bold',*(str(v) for v in range(100,1000,100))):
        raise ValueError('fontweight must be normal, bold, or a multiple of 100 from 100 to 900')
    if 'ha' in result and result['ha'] not in ('left','center','right'):
        raise ValueError('ha must be left, center, or right')
    if 'va' in result and result['va'] not in ('top','center','bottom','baseline'):
        raise ValueError('va must be top, center, bottom, or baseline')
    if 'rotation_mode' in result:
        result['rotation_mode']=result['rotation_mode'] or 'default'
        if result['rotation_mode'] not in ('default','anchor','xtick','ytick'):
            raise ValueError('rotation_mode must be default, anchor, xtick or ytick')
    if 'hatch' in result and (not isinstance(result['hatch'],str) or set(result['hatch'])-set('/\\|-+x.oO*')):raise ValueError('Invalid hatch pattern')
    if result.get('hatch_spacing',1)<=0:raise ValueError('hatch_spacing must be positive')
    if 'antialiased' in result and not isinstance(result['antialiased'],bool):raise ValueError('antialiased must be a bool')
    if "linecap" in result and result["linecap"] not in ("butt", "round", "square"):
        raise ValueError("linecap must be butt, round, or square")
    if "linejoin" in result and result["linejoin"] not in ("miter", "round", "bevel"):
        raise ValueError("linejoin must be miter, round, or bevel")
    for key in ('solid_capstyle','dash_capstyle'):
        if key in result and result[key] not in ('butt','round','projecting'):
            raise ValueError(f'{key} must be butt, round, or projecting')
    for key in ('solid_joinstyle','dash_joinstyle'):
        if key in result and result[key] not in ('miter','round','bevel'):
            raise ValueError(f'{key} must be miter, round, or bevel')
    if 'marker' in result and result['marker'] not in (None,'None','none','',' ','o','circle','s','square','^','v','D','d','diamond','*','p','h','+','x'):
        raise ValueError('Unsupported marker; use o,s,^,v,D,*,p,h,+,x or None')
    if "arrowstyle" in result and result["arrowstyle"] not in ("triangle", "open", "stealth"):
        raise ValueError("arrowstyle must be triangle, open, or stealth")
    if "arrow" in result and result["arrow"] not in (False, True, "start", "end", "both"):
        raise ValueError("arrow must be False, True, start, end, or both")
    if "linestyle" in result:
        pattern=dash_pattern(result["linestyle"])
        if not isinstance(result['linestyle'],str):result['linestyle']=pattern
    return result


def dash_pattern(value):
    patterns = {"-": (), "solid": (), "--": (7, 4), "dashed": (7, 4),
                ":": (1, 3), "dotted": (1, 3), "-.": (7, 3, 1, 3), "dashdot": (7, 3, 1, 3),
                'None':(), 'none':(), '':(), ' ':()}
    if isinstance(value, str):
        if value not in patterns:
            raise ValueError(f"Unknown linestyle {value!r}")
        return patterns[value]
    try:
        result = tuple(float(x) for x in value)
    except (TypeError, ValueError) as exc:
        raise ValueError("linestyle must be a style name or a sequence of positive dash lengths") from exc
    if not result or any(not math.isfinite(x) or x <= 0 for x in result):
        raise ValueError("Dash lengths must be finite and positive")
    return result


def validate_text_properties(style):
    """Reject point/area-only styles on a text handle before committing it."""
    incompatible=set(style)&{'marker','markersize','markerfacecolor','markeredgecolor','markeredgewidth',
        'symbol','hatch','hatch_color','hatch_linewidth','hatch_spacing'}
    if incompatible:raise TypeError(f'Text does not support point/area properties: {sorted(incompatible)}')


def path_style(style, polygon=False):
    from .typography import POINT
    width=style.get("linewidth",.8)
    dash=dash_pattern(style.get("linestyle","-"))
    # Named dashes follow the reference's linewidth-scaled point units.
    named={"--":(3.7,1.6),"dashed":(3.7,1.6),":":(1,1.65),"dotted":(1,1.65),"-.":(6.4,1.6,1,1.6),"dashdot":(6.4,1.6,1,1.6)}
    if isinstance(style.get('linestyle'),str) and style['linestyle'] in named:
        dash=tuple(v*max(width,.01) for v in named[style['linestyle']])
    family='dash' if dash else 'solid'
    cap=style.get(family+'_capstyle',style.get('linecap','butt' if dash else 'round'))
    cap='square' if cap=='projecting' else cap
    result=dict(fill=style.get("facecolor", style.get("color", "#e9e7de")) if polygon else "none",
                stroke=style.get("edgecolor", style.get("color", "#375461")),
                stroke_width=width*POINT, opacity=style.get("alpha", 1),
                dash=tuple(v*POINT for v in dash),
                linecap=cap, linejoin=style.get(family+'_joinstyle',style.get('linejoin','round')),
                fill_opacity=style.get("fill_alpha", 1), stroke_opacity=style.get("edge_alpha", 1))
    if not style.get('antialiased',True):result['shape_rendering']='crispEdges'
    if isinstance(style.get('linestyle'),str) and style['linestyle'] in ('None','none','',' '):result['stroke']='none'
    return result


def text_style(style):
    # Public angles follow plotting conventions (positive = counterclockwise).
    # Scene/SVG pixels have y pointing down, so their rotation has the opposite sign.
    anchor = {"left": "start", "center": "middle", "right": "end"}
    baseline = {"top": "top", "center": "middle", "bottom": "bottom", "baseline": "alphabetic"}
    ha, va = style.get("ha", "left"), style.get("va", "baseline")
    if ha not in anchor or va not in baseline:
        raise ValueError("ha: left/center/right; va: top/center/bottom/baseline")
    return dict(fill=style.get("color", "black"), opacity=style.get("alpha", 1),
                font_family=style.get("fontfamily", "DejaVu Sans"),
                font_size=style.get("fontsize", 10)*100/72, font_weight=style.get("fontweight", "normal"),
                font_style=style.get("fontstyle","normal"),
                anchor=anchor[ha], baseline=baseline[va], rotation=-float(style.get("rotation", 0)),
                rotation_mode=style.get('rotation_mode') or 'default',
                stroke=style.get("halo", "none"), stroke_width=style.get("halo_width", 2) if style.get("halo") else 0,
                background=style.get("background"))


def sample_color(cmap, t):
    colors = PALETTES.get(cmap) if isinstance(cmap, str) else tuple(cmap)
    if not colors or len(colors) < 2:
        raise ValueError(f"Colormap needs at least two #RRGGBB colors; available: {', '.join(PALETTES)}")
    t = max(0., min(1., float(t))) * (len(colors) - 1)
    i = min(int(t), len(colors) - 2)
    def rgb(color):
        if not isinstance(color, str) or len(color) != 7 or not color.startswith("#"):
            raise ValueError("Color scale stops must be #RRGGBB")
        return tuple(int(color[j:j+2], 16) for j in (1, 3, 5))
    a, b = rgb(colors[i]), rgb(colors[i+1])
    return "#" + "".join(f"{round(x+(y-x)*(t-i)):02x}" for x, y in zip(a, b))
