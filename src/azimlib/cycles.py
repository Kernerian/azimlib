"""Finite property cycles built with standard Python, without cycler dependency."""
from copy import deepcopy
from collections.abc import Mapping
from numbers import Real
import math
from .styles import style_dict

# Independently selected Azimlib sequence; provenance: data/materials.json.
AZIM10=('#237f96','#d57736','#667d32','#9b5cb5','#c34968',
        '#4076bb','#ad8d27','#348e72','#85574b','#6e7387')
# Import compatibility only; this is not the Tableau/Matplotlib palette.
TAB10=AZIM10
LINE_KEYS={'color','linewidth','linestyle','marker','markersize','markerfacecolor',
           'markeredgecolor','markeredgewidth','alpha','solid_capstyle','dash_capstyle',
           'solid_joinstyle','dash_joinstyle','antialiased','zorder'}

def _color(value):
    short=dict(zip('bgrcmykw',('#0000ff','#008000','#ff0000','#00bfbf','#bf00bf','#bfbf00','#000000','#ffffff')))
    if isinstance(value,str):
        if not value:raise ValueError('Cycle colors must not be empty')
        if value.startswith('#'):
            if len(value) not in (4,5,7,9):raise ValueError('Invalid hex color')
            try:int(value[1:],16)
            except ValueError as exc:raise ValueError('Invalid hex color') from exc
        return short.get(value,value)
    values=tuple(value)
    if len(values) not in (3,4) or any(not isinstance(v,Real) or not math.isfinite(v) or not 0<=v<=1 for v in values):
        raise ValueError('Cycle RGB/RGBA values must lie in [0,1]')
    return '#'+''.join(f'{round(v*255):02x}' for v in values)


class Cycler:
    """Reusable finite rows; iteration and by_key return independent copies."""
    def __init__(self,rows):
        prepared=[];keys=None
        for row in rows:
            if not isinstance(row,Mapping):raise TypeError('Cycle rows must be mappings')
            value=style_dict(row)
            if len(value)!=len(row):raise ValueError('Cycle aliases must not duplicate a property')
            if not value or set(value)-LINE_KEYS:raise ValueError('Cycle requires supported line properties')
            if any(v is None for v in value.values()):raise ValueError('Cycle entries must not be None')
            for key in ('color','markerfacecolor','markeredgecolor'):
                if key in value:value[key]=_color(value[key])
            if keys is not None and set(value)!=keys:raise ValueError('Cycle rows must have identical keys')
            keys=set(value);prepared.append(deepcopy(value))
        if not prepared:raise ValueError('Property cycle must not be empty')
        self._rows=tuple(prepared)

    def __len__(self):return len(self._rows)
    def __iter__(self):return iter(deepcopy(self._rows))
    @property
    def keys(self):return set(self._rows[0])
    def by_key(self):return {key:[deepcopy(row[key]) for row in self._rows] for key in self._rows[0]}
    def __eq__(self,other):return isinstance(other,Cycler) and self._rows==other._rows
    def __repr__(self):return f'Cycler({self.by_key()!r})'

    def _compatible(self,other):
        if not isinstance(other,Cycler):return False
        if self.keys & other.keys:raise ValueError('Cannot combine cycles with overlapping properties')
        return True
    def __add__(self,other):
        if not self._compatible(other):return NotImplemented
        if len(self)!=len(other):raise ValueError('Added cycles must have equal lengths')
        return Cycler({**a,**b} for a,b in zip(self,other))
    def __mul__(self,other):
        if not self._compatible(other):return NotImplemented
        return Cycler({**a,**b} for a in self for b in other)


def cycler(*args,**kwargs):
    """Create zipped properties or combine cycles with + (zip) / * (product)."""
    if args and kwargs:raise TypeError('Use positional or keyword cycle properties')
    if len(args)==1:
        value=args[0]
        if isinstance(value,Mapping):kwargs=dict(value)
        else:return Cycler(value)
    elif len(args)==2:kwargs={args[0]:args[1]}
    elif args:raise TypeError('cycler accepts a key/values pair or property keywords')
    if not kwargs:raise TypeError('cycler requires properties')
    values={key:list(value) for key,value in kwargs.items()}
    lengths={len(value) for value in values.values()}
    if len(lengths)!=1:raise ValueError('Cycle property sequences must have equal lengths')
    return Cycler(dict(zip(values,row)) for row in zip(*values.values()))


def prepare_cycle(value):
    """Accept own cycles and finite iterable mapping rows, including generic Cycler."""
    return cycler(value)
