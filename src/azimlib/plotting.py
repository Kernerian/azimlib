"""Dependency-free preparation of one/many geographic line series."""
from collections.abc import Mapping
from numbers import Real


def columns(value):
    if isinstance(value,Real):return [[value]]
    if isinstance(value,(str,bytes,Mapping)) or value is None:raise ValueError('Line data must be numeric sequences')
    rows=list(value)
    rows=[float('nan') if getattr(v,'ndim',0)==0 and bool(getattr(v,'mask',False)) else v for v in rows]
    if not rows:return [[]]
    if all(isinstance(v,Real) for v in rows):return [rows]
    if any(isinstance(v,(str,bytes,Mapping,Real)) for v in rows):raise ValueError('Line matrices must be rectangular and at most 2D')
    rows=[list(row) for row in rows];width=len(rows[0])
    if any(len(row)!=width or any(not isinstance(v,Real) for v in row) for row in rows):
        raise ValueError('Line matrices must be rectangular numeric rows and at most 2D')
    return [list(column) for column in zip(*rows)]


def groups(args,data=None):
    """Return (x, y, fmt, default label); keep coordinate-pair shorthand explicit."""
    if data is not None:
        if not hasattr(data,'__getitem__'):raise TypeError('data must support named lookup')
        if len(args)>3:raise ValueError('Multiple argument groups with data are unsupported; use separate plot calls')
    original=list(args)
    def lookup(value):
        if data is not None and isinstance(value,str):
            try:return data[value],value
            except KeyError:pass
        return value,None
    def is_key(value):
        if data is None or not isinstance(value,str):return False
        try:data[value];return True
        except KeyError:return False
    result=[]
    while original:
        if result and len(original)==1 and not isinstance(original[0],str):
            raise ValueError('Trailing argument needs a lon/lat pair or a format string')
        first,key=lookup(original.pop(0));fmt=None
        if original and (not isinstance(original[0],str) or is_key(original[0])):
            second,label=lookup(original.pop(0));x,y=columns(first),columns(second)
        else:
            # Legacy geographic Nx2 input remains coordinates. For numeric y,
            # implicit longitude is the row index, matching pyplot's x indices.
            series=columns(first);label=key
            if len(series)==2:x,y=[series[0]],[series[1]]
            elif len(series)>1:raise ValueError('Single matrix input must contain coordinate pairs; pass lon, lat_matrix for series')
            else:y=series;x=[list(range(len(y[0])))]
        if original and isinstance(original[0],str):fmt=original.pop(0)
        if fmt is not None and data is not None and is_key(fmt):
            raise ValueError('Third argument must be a format string, not a data column')
        if x and y and len(x[0])!=len(y[0]):raise ValueError('lon and lat must have equal first dimensions')
        if len(x)>1 and len(y)>1 and len(x)!=len(y):raise ValueError('lon and lat matrices must have equal column counts')
        count=max(len(x),len(y)) if x and y else 0
        result.append(([(x[i%len(x)],y[i%len(y)]) for i in range(count)],fmt,label))
    return result


def labels(value,count):
    if value is None or isinstance(value,(str,Real)):return [value]*count
    values=list(value)
    if len(values)!=count:raise ValueError('label must be scalar or have one entry per series in each argument group')
    return values

def plot_collection(x,y,feature=None):
    import math
    from .geometry import Geometry,Feature,FeatureCollection,position
    if len(x)!=len(y):raise ValueError('x and y must have the same length')
    runs=[];run=[];raw=[]
    for a,b in zip(x,y):
        a,b=float(a),float(b);raw.append((a,b))
        if math.isinf(a) or math.isinf(b):raise ValueError('Infinite plot coordinates are invalid')
        if math.isnan(a) or math.isnan(b):
            if run:runs.append(run);run=[]
        else:run.append(position((a,b)))
    if run:runs.append(run)
    geometries=[Geometry('MultiPoint' if len(r)==1 else 'LineString',tuple(r)) for r in runs]
    geometry=geometries[0] if len(geometries)==1 else Geometry('GeometryCollection',geometries=tuple(geometries))
    collection=FeatureCollection((Feature(geometry,feature.properties if feature else {},feature.id if feature else None),))
    return collection,tuple(raw)
