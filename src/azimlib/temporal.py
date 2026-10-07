"""Immutable indexed times and independently prepared scalar frame bindings."""
from bisect import bisect_left
from collections.abc import Mapping,Sequence
from dataclasses import dataclass
from types import MappingProxyType
from numbers import Real,Integral
from copy import copy
import datetime as dt
import math
from .callbacks import CallbackRegistry

def bounded(value):
    return not isinstance(value,(str,bytes,Mapping)) and hasattr(value,'__len__') and hasattr(value,'__getitem__')

def freeze(value):
    if isinstance(value,Mapping):
        if any(not isinstance(k,str) for k in value):raise TypeError('Frame mapping keys must be strings')
        return MappingProxyType({k:freeze(v) for k,v in value.items()})
    if isinstance(value,Sequence) and not isinstance(value,(str,bytes)):return tuple(freeze(v) for v in value)
    if value is None or isinstance(value,(str,bool,int,float,dt.date)):return value
    if isinstance(value,Integral):return int(value)
    if isinstance(value,Real):return float(value)
    if hasattr(value,'tolist'):return freeze(value.tolist())
    raise TypeError('Frame payload must be numeric, text, dates, arrays or mappings')

def time_key(value,kind):
    if kind=='date':
        if isinstance(value,dt.datetime):
            if value.tzinfo is None:value=value.replace(tzinfo=dt.timezone.utc)
            value=value.astimezone(dt.timezone.utc)
        elif isinstance(value,dt.date):value=dt.datetime.combine(value,dt.time(),dt.timezone.utc)
        else:raise TypeError('Date series require date/datetime instants')
        return value.timestamp(),value
    if isinstance(value,bool) or not isinstance(value,Real):raise TypeError('Numeric series require numeric instants')
    key=float(value)
    if not math.isfinite(key):raise ValueError('Time must be finite')
    return key,key

@dataclass(frozen=True)
class Frame:
    time:object
    data:object

class TemporalSeries(Sequence):
    """Strictly increasing numeric times with explicit units, or UTC dates."""
    def __init__(self,times,values,*,unit=None,name=''):
        if not bounded(times) or not bounded(values):raise TypeError('Times/values require bounded sequences')
        if not 1<=len(times)<=10000 or len(times)!=len(values):raise ValueError('Require 1..10000 times and one payload per time')
        kind='date' if isinstance(times[0],dt.date) else 'numeric'
        if kind=='numeric' and (not isinstance(unit,str) or not unit.strip()):raise ValueError('Numeric times require an explicit unit')
        if kind=='date' and unit not in (None,'UTC'):raise ValueError('Date series use UTC, not numeric units')
        prepared=tuple(time_key(t,kind) for t in times);keys=tuple(p[0] for p in prepared)
        if any(a>=b for a,b in zip(keys,keys[1:])):raise ValueError('Times must be strictly increasing and unique')
        self._keys=keys;self._frames=tuple(Frame(p[1],freeze(v)) for p,v in zip(prepared,values))
        self.kind,self.unit,self.name=kind,'UTC' if kind=='date' else unit.strip(),str(name)
    def __len__(self):return len(self._frames)
    def __getitem__(self,index):return self._frames[index]
    @property
    def times(self):return tuple(f.time for f in self)
    def index_at(self,time,*,method='nearest'):
        if method not in ('exact','nearest','previous','next'):raise ValueError('Unknown temporal selection method')
        key,_=time_key(time,self.kind);i=bisect_left(self._keys,key)
        if i<len(self) and self._keys[i]==key:return i
        if method=='exact':raise KeyError(time)
        if method=='previous':
            if i==0:raise KeyError(time)
            return i-1
        if method=='next':
            if i==len(self):raise KeyError(time)
            return i
        if i==0:return 0
        if i==len(self):return i-1
        return i-1 if key-self._keys[i-1]<=self._keys[i]-key else i
    def at(self,time,*,method='nearest'):return self[self.index_at(time,method=method)]
    def bind(self,artist,*,scale='global',norm=None):return ScalarBinding(self,artist,scale=scale,norm=norm)

def normalizer(template,values,*,rescale):
    from .colors import Normalize,BoundaryNorm
    if not isinstance(template,Normalize):raise TypeError('Require an Azimlib Normalize')
    result=copy(template);result.callbacks=CallbackRegistry(('changed',))
    valid=[v for v in values if v is not None and math.isfinite(v)]
    if not valid:raise ValueError('No finite scalar values for automatic limits')
    if rescale and not isinstance(result,BoundaryNorm):result.autoscale(valid)
    else:result.autoscale_None(valid)
    result._validate();return result

class ScalarBinding:
    """Prevalidate every frame before editing an existing owned scalar Artist.

    Changing values does not recreate geometry, camera, legends or components.
    Global limits are inferred across the series unless an explicit norm is given.
    Frame limits are independent; wholly missing frames retain the global limits.
    """
    def __init__(self,series,artist,*,scale='global',norm=None):
        from .layers import Layer
        from .field_artists import MeshCollection,ScalarImage,scalar_rows
        from .terrain_axes import SurfaceArtist
        from .scientific import scalar
        if not isinstance(series,TemporalSeries):raise TypeError('Require a TemporalSeries')
        if scale not in ('global','frame'):raise ValueError('scale must be global or frame')
        if not isinstance(artist,(Layer,SurfaceArtist)) or artist.get_figure() is None:raise ValueError('Binding requires an attached scalar Artist')
        if isinstance(artist,Layer) and artist.kind not in ('scatter','mesh','image','geometry'):raise ValueError('Unsupported scalar binding kind')
        if isinstance(artist,Layer) and artist.kind=='geometry' and not artist.options.get('mapped'):raise ValueError('Geometry bindings require an existing choropleth')
        self.series,self.artist,self.scale=series,artist,scale;self.index=None
        self._image=isinstance(artist,ScalarImage);self._shape=tuple(map(len,artist.get_data())) if self._image else None;arrays=[];payloads=[]
        for frame in series:
            if self._image:
                rows=scalar_rows(frame.data)
                if tuple(map(len,rows))!=tuple(map(len,artist.get_data())):raise ValueError('Temporal image frames must preserve the image shape')
                flat=[v for row in (rows[::-1] if artist.options['origin']=='upper' else rows) for v in row];payload=rows
            elif isinstance(artist,SurfaceArtist):
                flat=[scalar(v) for v in frame.data];payload=tuple(flat)
                if len(flat)!=len(artist.mesh.vertices):raise ValueError('Surface frame must match vertices')
            else:
                flat=artist._prepare_array(frame.data);payload=tuple(flat)
            # Preview only; callbacks and source norm/array are not changed.
            if isinstance(artist,SurfaceArtist):artist._prepare_mapping({},array=flat)
            else:artist._prepare_set({},array=flat)
            arrays.append(tuple(flat));payloads.append(payload)
        if sum(len(a) for a in arrays)>2000000:raise ValueError('Scalar timeline budget is 2 million values')
        template=artist.norm if norm is None else norm;allvalues=[v for a in arrays for v in a]
        global_norm=normalizer(template,allvalues,rescale=norm is None)
        norms=[]
        for a in arrays:
            valid=any(v is not None and math.isfinite(v) for v in a)
            norms.append(normalizer(template,a,rescale=True) if scale=='frame' and valid else global_norm)
        self._payloads=tuple(payloads);self._arrays=tuple(arrays);self._norms=tuple(norms)
    def apply(self,index):
        if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<len(self.series):raise IndexError('Invalid frame index')
        artist=self.artist
        if artist.get_figure() is None:raise RuntimeError('Temporal Artist has been removed')
        from .terrain_axes import SurfaceArtist
        values=self._payloads[index];norm=self._norms[index]
        if isinstance(artist,SurfaceArtist):
            if len(values)!=len(artist.mesh.vertices):raise ValueError('Surface topology changed')
            with artist._batch_changes():artist.set_array(values);artist.set_norm(norm)
        elif self._image:
            if tuple(map(len,artist.get_data()))!=self._shape:raise ValueError('Temporal image shape changed outside its binding')
            artist.set(data=values,norm=norm)
        else:artist.set(array=values,norm=norm)
        self.index=index;return artist
