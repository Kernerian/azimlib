"""Validated named rectangular subplot selections using our own GridSpec."""
import inspect
from collections.abc import Mapping
from .gridspec import GridSpec
from .projections import get_projection


def prepare(mosaic,figure,*,empty_sentinel='.',subplot_kw=None,per_subplot_kw=None,
            gridspec_kw=None,width_ratios=None,height_ratios=None,
            projection='equirectangular',projection_kw=None):
    """Prepare every slot/projection before creating or attaching any axes."""
    string_layout=isinstance(mosaic,str)
    rows=_rows(mosaic)
    grid_options=dict(gridspec_kw or {})
    for name,value in (('width_ratios',width_ratios),('height_ratios',height_ratios)):
        if value is not None:
            if name in grid_options:raise ValueError(name+' supplied both directly and in gridspec_kw')
            grid_options[name]=value
    grid=GridSpec(len(rows),len(rows[0]),figure=figure,**grid_options)
    specs={}
    def walk(rows,grid,depth):
        if depth>64:raise ValueError('Mosaic nesting exceeds 64 levels')
        positions={};nested={}
        for r,row in enumerate(rows):
            for c,key in enumerate(row):
                if isinstance(key,list):
                    token=object();nested[token]=_rows(key);positions[token]=[(r,c)]
                    continue
                try:hash(key)
                except TypeError:raise TypeError('Mosaic labels must be hashable or nested 2D lists') from None
                if key==empty_sentinel:continue
                positions.setdefault(key,[]).append((r,c))
        selections={}
        for key,cells in positions.items():
            r0=min(r for r,c in cells);r1=max(r for r,c in cells)+1
            c0=min(c for r,c in cells);c1=max(c for r,c in cells)+1
            if len(cells)!=(r1-r0)*(c1-c0):raise ValueError(f'Mosaic label {key!r} must occupy one rectangle')
            selections[key]=grid[r0:r1,c0:c1]
        # Walk cells in appearance order, descending into a nested cell there.
        for key,spec in selections.items():
            if key in nested:
                child_rows=nested[key]
                child=spec.subgridspec(len(child_rows),len(child_rows[0]))
                walk(child_rows,child,depth+1)
                continue
            if key in specs:raise ValueError(f'Mosaic label {key!r} is repeated across nested layouts')
            specs[key]=spec
    walk(rows,grid,0)
    base=dict(projection=projection,projection_kw=projection_kw)
    base.update(dict(subplot_kw or {}))
    if set(base)-{'projection','projection_kw'}:raise TypeError('Unsupported subplot_kw')
    overrides={}
    for selection,options in dict(per_subplot_kw or {}).items():
        if not isinstance(options,Mapping):raise TypeError('per_subplot_kw values must be mappings')
        keys=tuple(selection) if isinstance(selection,tuple) else tuple(selection) if string_layout and isinstance(selection,str) else (selection,)
        for key in keys:
            if key not in specs:raise ValueError(f'Unknown mosaic label {key!r}')
            if key in overrides:raise ValueError(f'Duplicate subplot properties for {key!r}')
            if set(options)-{'projection','projection_kw'}:raise TypeError('Unsupported per_subplot_kw')
            overrides[key]=dict(options)
    resolved={}
    for key in specs:
        options=dict(base,**overrides.get(key,{}))
        resolved[key]=get_projection(options['projection'],**(options['projection_kw'] or {}))
    return grid,specs,resolved


def _rows(mosaic):
    if isinstance(mosaic,str):
        rows=inspect.cleandoc(mosaic).splitlines()
        if len(rows)==1:rows=rows[0].split(';')
        rows=[list(row) for row in rows]
    else:
        source=list(mosaic)
        if any(isinstance(row,str) for row in source):raise ValueError('A list mosaic requires 2D rows, not strings')
        rows=[list(row) for row in source]
    if not rows or not rows[0] or any(len(row)!=len(rows[0]) for row in rows):
        raise ValueError('Mosaic must be a nonempty rectangular 2D layout')
    return rows
