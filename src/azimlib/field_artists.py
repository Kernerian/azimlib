"""Own editable scalar meshes/images and east/north vector fields."""
import math
from numbers import Real
from .layers import Layer
from .collections import ScatterCollection
from .artist import artist_mutation
from .cm import _UNSET


def scalar_rows(values):
    if isinstance(values,(str,bytes)):raise ValueError('Expected a rectangular scalar matrix')
    from .scientific import scalar
    rows=tuple(tuple(scalar(v) for v in row) for row in values)
    if not rows or not rows[0] or any(len(row)!=len(rows[0]) for row in rows):
        raise ValueError('Expected a nonempty rectangular scalar matrix')
    return rows


def image_extent(values):
    values=tuple(float(v) for v in values)
    if len(values)!=4 or any(not math.isfinite(v) for v in values):raise ValueError('extent needs four finite coordinates')
    w,e,s,n=values
    if not -180<=w<e<=180 or not -90<=s<n<=90:raise ValueError('extent must be increasing geographic bounds')
    return values


def image_edges(extent,nx,ny):
    w,e,s,n=extent
    return (tuple(w+(e-w)*i/nx for i in range(nx+1)),tuple(s+(n-s)*j/ny for j in range(ny+1)))


class MeshCollection(Layer):
    """Projected scalar cells with fixed lon/lat edges and editable values."""
    def _unsupported_properties(self):
        return super()._unsupported_properties()

    def get_coordinates(self):
        x,y,_=self.data
        return [[[lon,lat] for lon in x] for lat in y]

    def _prepare_array(self,values):
        if values is None:return None
        values=list(values);nx,ny=len(self.data[0])-1,len(self.data[1])-1
        if values and not isinstance(values[0],(Real,str,bytes)) and values[0] is not None:
            rows=scalar_rows(values)
            if len(rows)!=ny or len(rows[0])!=nx:raise ValueError('Array shape must match mesh cells')
            values=[v for row in rows for v in row]
        else:
            from .scientific import scalar
            values=[scalar(v) for v in values]
        if len(values)!=nx*ny:raise ValueError('Array size must match mesh cells')
        return values

    def set_array(self,values):return self.set(array=values)

    @artist_mutation
    def set(self,**kwargs):
        kwargs=dict(kwargs);replace='array' in kwargs
        values=self._prepare_array(kwargs.pop('array')) if replace else None
        prepared=self._prepare_set(kwargs,array=values if replace else _UNSET)
        if replace and values is not None:
            x,y,_=self.data;nx=len(x)-1
            self.data=(x,y,tuple(tuple(values[j*nx:(j+1)*nx]) for j in range(len(y)-1)))
        self._apply_set(prepared)
        return self


class ScalarImage(MeshCollection):
    """Scalar image with editable matrix shape, geographic extent and origin."""
    def _unsupported_properties(self):
        return super()._unsupported_properties()-{'data'}

    def get_data(self):
        rows=self.data[2]
        if self.options['origin']=='upper':rows=rows[::-1]
        return [list(row) for row in rows]

    def get_extent(self):return tuple(self.options['image_extent'])
    def set_data(self,values):self.set(data=values)
    def set_extent(self,extent):self.set(extent=extent)

    def _image_input(self,values):
        if values is None:raise ValueError('A scalar image requires a matrix')
        values=list(values)
        # Preserve the older Azimlib flat-array path in geographic row order.
        if not values or isinstance(values[0],(Real,str,bytes)) or values[0] is None:
            flat=self._prepare_array(values);nx=len(self.data[0])-1
            rows=[flat[j*nx:(j+1)*nx] for j in range(len(self.data[1])-1)]
            if self.options['origin']=='upper':rows.reverse()
            return rows
        return scalar_rows(values)

    def set_array(self,values):return self.set_data(self._image_input(values))

    @artist_mutation
    def set(self,**kwargs):
        kwargs=dict(kwargs)
        if 'data' in kwargs and 'array' in kwargs:raise ValueError('Use data or array, not both')
        if 'array' in kwargs:
            kwargs['data']=self._image_input(kwargs.pop('array'))
        if not ({'data','extent'}&set(kwargs)):
            Layer.set(self,**kwargs)
            return self
        extent=image_extent(kwargs.pop('extent')) if 'extent' in kwargs else self.get_extent()
        rows=scalar_rows(kwargs.pop('data')) if 'data' in kwargs else tuple(tuple(r) for r in self.get_data())
        if self.options['origin']=='upper':rows=rows[::-1]
        flat=[v for row in rows for v in row]
        prepared=self._prepare_set(kwargs,array=flat)
        x,y=image_edges(extent,len(rows[0]),len(rows))
        self.data=(x,y,rows);self.options['image_extent']=extent
        self._apply_set(prepared)
        return self


class VectorCollection(Layer):
    """Fixed-count east/north vectors with set_UVC and geographic offsets."""
    @staticmethod
    def _values(values,count,*,colors=False):
        values=[values] if isinstance(values,Real) else list(values)
        if len(values)==1:values=values*count
        if len(values)!=count:raise ValueError('Vector arrays must match the origin count')
        result=[None if colors and v is None else float(v) for v in values]
        if not colors and any(not math.isfinite(v) for v in result):raise ValueError('Vectors must be finite')
        return result

    @staticmethod
    def _scale(value):
        if value is None:return None
        value=float(value)
        if not math.isfinite(value) or value<=0:raise ValueError('scale must be finite and positive')
        return value

    def legend_elements(self,num=3):
        """Own magnitude proxies: fixed arrow markers, labels in vector units.

        Handles are a snapshot; regenerate after editing U/V. Colors use the
        vector style, not the separate C scalar (which belongs to a colorbar).
        """
        from .geometry import Feature,FeatureCollection,Geometry
        if not isinstance(num,int) or isinstance(num,bool) or not 1<=num<=20:raise ValueError('num must be in [1,20]')
        magnitudes=[math.hypot(p[2],p[3]) for p in self.data]
        if not magnitudes:return [],[]
        low,high=min(magnitudes),max(magnitudes)
        values=[low] if num==1 or low==high else [low+(high-low)*i/(num-1) for i in range(num)]
        handles=[Layer('geometry',FeatureCollection([Feature(Geometry('LineString',[(0,0),(1,0)]))]),dict(color=self.style.get('color','#444444'),linewidth=self.style.get('linewidth',.8),marker='^',rotation=-90,markersize=3+4*(v/high if high else 0))) for v in values]
        return handles,[f'{v:g}' for v in values]

    def get_offsets(self):return [list(p[:2]) for p in self.data]
    def set_offsets(self,values):self.set(offsets=values)
    def get_UVC(self):return ([p[2] for p in self.data],[p[3] for p in self.data],self.get_array())
    def set_UVC(self,U,V,C=None):self.set(UVC=(U,V,C))
    def get_scale(self):return self.options['scale']
    def set_scale(self,value):self.set(scale=value)

    @artist_mutation
    def set(self,**kwargs):
        kwargs=dict(kwargs);count=len(self.data)
        offsets=ScatterCollection._prepare_offsets(kwargs.pop('offsets')) if 'offsets' in kwargs else tuple(tuple(p[:2]) for p in self.data)
        if len(offsets)!=count:raise ValueError('Offsets must preserve the vector count')
        scale=self._scale(kwargs.pop('scale')) if 'scale' in kwargs else self.get_scale()
        u,v,colors=self.get_UVC();replace_array='array' in kwargs
        if 'UVC' in kwargs:
            args=tuple(kwargs.pop('UVC'))
            if len(args) not in (2,3):raise ValueError('UVC requires U, V and optionally C')
            u=self._values(args[0],count);v=self._values(args[1],count)
            if len(args)==3 and args[2] is not None:
                if replace_array:raise ValueError('Use C in UVC or array, not both')
                colors=self._values(args[2],count,colors=True);replace_array=True
        if 'array' in kwargs:
            values=kwargs.pop('array')
            colors=None if values is None else [None if v is None else float(v) for v in values]
            if colors is not None and len(colors)!=count:raise ValueError('Color array must match the vector count')
        prepared=self._prepare_set(kwargs,array=colors if replace_array else _UNSET)
        self.data=tuple((*p,a,b) for p,a,b in zip(offsets,u,v));self.options['scale']=scale
        self._apply_set(prepared)
        return self
