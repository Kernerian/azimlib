"""Own scientific Artists; geometry and mapping share the existing lifecycle."""
from .layers import Layer
from .artist import artist_mutation
from .field_artists import image_extent,image_edges
from .scientific import color_rows,color_hex,band_polygons,filled_levels
from .geometry import Geometry,Feature,FeatureCollection
from .colors import NoNorm


class ColorImage(Layer):
    """Editable RGB/RGBA cells, with pixel alpha and geographic extent.

    True color has no scalar colorbar. It uses the same projected cell scene in
    PNG and SVG; SVG stays available without Pillow or a raster data dependency.
    """
    def _unsupported_properties(self): return super()._unsupported_properties()-{'data'}
    def get_data(self): return [[tuple(p) for p in row] for row in self.data]
    def get_extent(self): return tuple(self.options['image_extent'])
    def set_norm(self,value):raise ValueError('True color has no scalar normalizer')
    def set_cmap(self,value):raise ValueError('True color has no scalar colormap')
    def set_clim(self,*args,**kwargs):raise ValueError('True color has no scalar limits')
    def set_data(self,values): return self.set(data=values)
    def set_array(self,values): return self.set_data(values)
    def set_extent(self,extent): return self.set(extent=extent)
    @artist_mutation
    def set(self,**kwargs):
        kwargs=dict(kwargs)
        if {'norm','cmap','clim','array'}&set(kwargs): raise ValueError('True color uses data/alpha, not scalar mapping')
        rows=color_rows(kwargs.pop('data')) if 'data' in kwargs else self.data
        extent=image_extent(kwargs.pop('extent')) if 'extent' in kwargs else self.get_extent()
        prepared=self._prepare_set(kwargs)
        self.data=rows;self.options['image_extent']=extent;self._apply_set(prepared)
        return self


def filled_features(triangles,levels):
    features=[]
    for index,(low,high) in enumerate(zip(levels,levels[1:])):
        for rings in band_polygons(triangles,low,high,include_upper=index==len(levels)-2):
            features.append(Feature(Geometry('Polygon',rings),{'band':index}))
    return FeatureCollection(features)


class FilledContourSet(Layer):
    """Own piecewise-linear filled bands with true inner rings/masked holes.

    Unlike contour's bilinear marching squares, contourf divides each valid
    quadrilateral along SW–NE. set_levels recomputes from retained triangles;
    set_array only recolors intervals. No spherical or constrained triangulation.
    """
    levels=property(lambda self:tuple(self.options['levels']))
    cvalues=property(lambda self:self.get_array())
    filled=property(lambda self:True)
    allsegs=property(lambda self:[[list(f.geometry.coordinates) for f in self.data if f.properties['band']==i] for i in range(len(self.levels)-1)])
    def _prepare_array(self,values):
        if values is None: raise ValueError('Filled bands require scalar colors')
        from .scientific import scalar
        values=[scalar(v) for v in values]
        if len(values)!=len(self.levels)-1: raise ValueError('Color values must match filled intervals')
        return values
    def _mapped_color(self,index):
        value=self._array[index]
        if isinstance(self.norm,NoNorm) and value is not None and float(value).is_integer(): value=int(value)
        return self.to_color(value)
    def _feature_style(self,index,feature,style=None):
        return dict(self.style if style is None else style,facecolor=self._mapped_color(feature.properties['band']))
    def get_legend_entries(self):
        return [(f'{a:g} – {b:g}',dict(facecolor=self._mapped_color(i),edgecolor='none'),'polygon')
                for i,(a,b) in enumerate(zip(self.levels,self.levels[1:]))]
    @artist_mutation
    def set_levels(self,levels):
        levels=filled_levels([p[2] for t in self.options['triangles'] for p in t if p[2] is not None],levels)
        if isinstance(self.norm,NoNorm): raise ValueError('Explicit color-index bands require a new contourf to change levels')
        data=filled_features(self.options['triangles'],levels)
        values=[a/2+b/2 for a,b in zip(levels,levels[1:])]
        prepared=self._prepare_set({},array=values)
        self.data=data;self.options['levels']=levels;self._apply_set(prepared)
        return self
    def _line_geometry(self): raise TypeError('Filled bands use set_levels; paths are not line data')


class FlowCollection(Layer):
    """Routes with independently mapped flow magnitude and physical width."""
    def _line_geometry(self):raise TypeError('Flow endpoints are fixed; create a new flow')
    def _prepare_array(self,values):
        values=super()._prepare_array(values)
        if values is None or any(v is not None and v<0 for v in values):raise ValueError('Flow values must be nonnegative')
        return values
    def _feature_style(self,index,feature,style=None):
        value=self._array[index];t=self._fraction(value)
        width=self.options['minwidth']+(self.options['maxwidth']-self.options['minwidth'])*t
        return dict(self.style if style is None else style,color=self.to_color(value),linewidth=width if value is not None else 0)
    def _fraction(self,value):
        low,high=self.get_clim()
        if value is None or low is None or high is None or low==high:return 0.
        return max(0,min(1,(value-low)/(high-low)))
    def get_legend_entries(self):
        low,high=self.get_clim()
        if low is None or high is None:return []
        values=[low,high] if low==high else [low,(low+high)/2,high]
        return [(f'{value:g}',dict(color=self.to_color(value),linewidth=self.options['minwidth']+(self.options['maxwidth']-self.options['minwidth'])*self._fraction(value)),'line') for value in dict.fromkeys(values)]
