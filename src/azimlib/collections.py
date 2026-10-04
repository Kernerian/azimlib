"""Editable geographic collections, independent of plotting frameworks."""
import math
from numbers import Real
from .layers import Layer
from .geometry import position
from .cm import _UNSET
from .artist import artist_mutation


class ScatterCollection(Layer):
    """A scatter handle with lon/lat offsets and marker areas in points squared.

    Unlike Matplotlib's generic PathCollection, offsets are geographic degrees.
    Explicit sizes/colors cycle; scalar color data must match the point count.
    """
    @staticmethod
    def _prepare_offsets(values):
        if isinstance(values,(str,bytes)):raise ValueError('offsets must be geographic coordinate pairs')
        values=list(values)
        if len(values)==2 and all(isinstance(v,Real) for v in values):values=[values]
        result=[]
        for value in values:
            point=position(value)
            if len(point)!=2:raise ValueError('scatter offsets must have shape (N, 2)')
            result.append(point)
        return tuple(result)

    @staticmethod
    def _prepare_sizes(values):
        if values is None:return []
        if isinstance(values,(str,bytes,Real)):raise TypeError('sizes must be a sequence of marker areas')
        result=[float(v) for v in values]
        if any(not math.isfinite(v) or v<0 for v in result):raise ValueError('sizes must be finite and non-negative')
        return result

    def get_offsets(self):return [list(p) for p in self.data]
    def get_sizes(self):return list(self.options['sizes'])
    def set_offsets(self,values):self.set(offsets=values)
    def set_sizes(self,sizes,dpi=72.):
        # Areas are physical units; the scene's DPI conversion is performed later.
        if not math.isfinite(float(dpi)) or float(dpi)<=0:raise ValueError('dpi must be finite and positive')
        self.set(sizes=sizes)

    @artist_mutation
    def set(self,**kwargs):
        """Edit points, areas and color data together before notifying observers."""
        kwargs=dict(kwargs)
        offsets=self._prepare_offsets(kwargs.pop('offsets')) if 'offsets' in kwargs else self.data
        sizes=self._prepare_sizes(kwargs.pop('sizes')) if 'sizes' in kwargs else self.options['sizes']
        replace_array='array' in kwargs
        array=kwargs.pop('array') if replace_array else self._array
        if replace_array and array is not None:array=[None if v is None else float(v) for v in array]
        if array is not None and len(array)!=len(offsets):
            raise ValueError('Numeric colors must match offsets; use set(offsets=..., array=...) to change both')
        prepared=self._prepare_set(kwargs,array=array if replace_array else _UNSET)
        self.data=offsets;self.options['sizes']=list(sizes)
        self._apply_set(prepared)
        return self

    def _scatter_size(self,index):
        sizes=self.options['sizes']
        return sizes[index%len(sizes)] if sizes else 0.

    def _scatter_style(self,index):
        style=dict(self.style)
        colors=self.options.get('colors')
        if colors:style['color']=colors[index%len(colors)]
        if self._array is not None:style['color']=self.to_color(self._array[index])
        if 'linewidth' in style and 'markeredgewidth' not in style:style['markeredgewidth']=style['linewidth']
        return style
