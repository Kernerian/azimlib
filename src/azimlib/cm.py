"""ScalarMappable couples data, normalization and colors across components."""
from .colors import Normalize,get_cmap
from .callbacks import CallbackRegistry
from .artist import Artist
from contextlib import contextmanager
from copy import copy

_UNSET=object()

class ScalarMappable:
    def __init__(self,norm=None,cmap='viridis'):
        self.callbacks=CallbackRegistry(('changed',))
        self._change_depth=0;self._change_pending=False
        self._norm=None;self._norm_cid=None;self._array=None
        self._cmap=get_cmap('viridis' if cmap is None else cmap)
        value=norm if norm is not None else Normalize()
        if not isinstance(value,Normalize):raise TypeError('norm must be an Azimlib Normalize')
        self._norm=value;self._norm_cid=value.callbacks.connect('changed',self.changed)
    @property
    def norm(self):return self._norm
    @norm.setter
    def norm(self,value):self.set_norm(value)
    @property
    def cmap(self):return self._cmap
    @cmap.setter
    def cmap(self,value):self.set_cmap(value)
    def _changed(self):
        if isinstance(self,Artist):Artist._changed(self)
    def changed(self):
        if self._change_depth:
            self._change_pending=True
            return
        self._changed()
        self.callbacks.process('changed',self)
    @contextmanager
    def _batch_changes(self):
        self._change_depth+=1
        try:yield
        finally:
            self._change_depth-=1
            if not self._change_depth and self._change_pending:
                self._change_pending=False;self.changed()
    def set_array(self,values):
        from .scientific import scalar
        values=None if values is None else [scalar(v) for v in values]
        self._apply_mapping(self._prepare_mapping({},array=values))
    def get_array(self):return None if self._array is None else list(self._array)
    def set_cmap(self,value):
        self._cmap=get_cmap('viridis' if value is None else value);self.changed()
    def get_cmap(self):return self.cmap
    def set_norm(self,value):
        value=Normalize() if value is None else value
        if not isinstance(value,Normalize):raise TypeError('norm must be an Azimlib Normalize')
        if value is self._norm:return
        self._apply_mapping(self._prepare_mapping({'norm':value}))
    def get_norm(self):return self.norm
    def set_clim(self,vmin=None,vmax=None):
        if vmax is None and isinstance(vmin,(tuple,list)):vmin,vmax=vmin
        low=self.norm.vmin if vmin is None else float(vmin)
        high=self.norm.vmax if vmax is None else float(vmax)
        self.norm._set_limits(low,high)
    def get_clim(self):return self.norm.vmin,self.norm.vmax
    def autoscale(self):self.norm.autoscale(self._array or [])
    def autoscale_None(self):self.norm.autoscale_None(self._array or [])
    def to_color(self,value):return self.cmap(self.norm(value))

    def to_rgba(self,values,alpha=None,bytes=False,norm=True):
        """Map scalars/matrices to RGBA, or pass RGB/RGBA images through.

        Missing/nonfinite/masked scalar values use cmap.bad; image masks use
        transparent pixels. bytes=True returns integer channels in 0..255.
        """
        from numbers import Real,Integral
        from .scientific import scalar,is_color,color_rows
        from .colors import to_rgba
        def is_scalar(value):return value is None or isinstance(value,Real) or getattr(value,'ndim',None)==0
        scalar_input=is_scalar(values)
        def rgba_scalar(value):
            result=scalar(value)
            return int(value) if result is not None and isinstance(value,Integral) else result
        if scalar_input:data=rgba_scalar(values)
        else:
            values=list(values)
            nested=bool(values) and not is_scalar(values[0])
            if nested:
                rows=tuple(tuple(row) for row in values)
                if is_color(rows):
                    pixels=color_rows(rows)
                    if alpha is not None:
                        a=to_rgba('white',alpha)[3]
                        pixels=tuple(tuple(p[:3]+(a if p[3] else 0.,) for p in row) for row in pixels)
                    return [[tuple(round(v*255) for v in p) if bytes else p for p in row] for row in pixels]
                data=[[rgba_scalar(v) for v in row] for row in rows]
            else:data=[rgba_scalar(v) for v in values]
        flat=[data] if scalar_input else [v for row in data for v in row] if nested else data
        if norm:self.norm.autoscale_None(flat)
        def convert(value):
            p=to_rgba(self.cmap(self.norm(value) if norm else value),alpha)
            if value is None:p=p[:3]+(0.,) if self.cmap.bad in ('none','#00000000') else to_rgba(self.cmap.bad)
            return tuple(round(v*255) for v in p) if bytes else p
        if scalar_input:return convert(data)
        return [[convert(v) for v in row] for row in data] if nested else [convert(v) for v in data]

    def _prepare_mapping(self,options,*,array=_UNSET):
        """Validate a final batch on an isolated normalizer preview.

        options is the caller's owned dictionary. Preview callbacks never reach
        real artists. This is not rollback of arbitrary custom norm side effects.
        """
        keys=set(options)&{'norm','cmap','clim'}
        if not keys and array is _UNSET:return None
        norm=options.pop('norm') if 'norm' in options else self.norm
        norm=Normalize() if norm is None else norm
        if not isinstance(norm,Normalize):raise TypeError('norm must be an Azimlib Normalize')
        palette=options.pop('cmap') if 'cmap' in options else self.cmap
        palette=get_cmap('viridis' if palette is None else palette)
        preview=copy(norm);preview.callbacks=CallbackRegistry(('changed',))
        if 'clim' in options:
            clim=options.pop('clim')
            if isinstance(clim,(tuple,list)):
                if len(clim)!=2:raise ValueError('clim needs (vmin, vmax)')
                low,high=clim
            else:low,high=clim,None
            preview._set_limits(preview.vmin if low is None else low,
                                preview.vmax if high is None else high)
        preview._validate()
        values=self._array if array is _UNSET else array
        if values is not None and ('norm' in keys or array is not _UNSET):
            # Explicit complete clim wins over automatic limits in this batch.
            if 'clim' not in keys or not preview.scaled():preview.autoscale_None(values)
        preview._validate()
        return norm,palette,preview.vmin,preview.vmax,'cmap' in keys,array

    def _apply_mapping(self,prepared):
        if prepared is None:return
        norm,palette,low,high,palette_set,array=prepared
        replaced=norm is not self._norm
        with self._batch_changes():
            if array is not _UNSET:self._array=array
            if replaced:
                self._norm.callbacks.disconnect(self._norm_cid)
                self._norm=norm;self._norm_cid=norm.callbacks.connect('changed',self.changed)
            if palette_set:self._cmap=palette
            norm._set_limits(low,high)
            if replaced or palette_set or array is not _UNSET:self.changed()
