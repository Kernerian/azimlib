"""Mutable artist handles over immutable geographic inputs."""
from __future__ import annotations
from dataclasses import dataclass, field
from .styles import style_dict,validate_text_properties
from .cm import ScalarMappable,_UNSET
from .components import LayoutArtist
from .artist import Artist,artist_mutation


@dataclass
class Layer(ScalarMappable,LayoutArtist):
    kind: str
    data: object
    style: dict = field(default_factory=dict)
    options: dict = field(default_factory=dict)
    visible: bool = True
    legend_entries: list = field(default_factory=list)
    _axes: object = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        if self.kind in ('text','annotation','labels'):validate_text_properties(self.style)
        Artist.__init__(self,self._axes)
        ScalarMappable.__init__(self)

    @property
    def axes(self):return self._axes
    @property
    def figure(self):return self.get_figure()

    def _unsupported_properties(self):
        excluded=set()
        if self.kind not in ('text','annotation'):excluded.add('text')
        try:self._line_geometry()
        except TypeError:excluded.update(('data','xdata','ydata'))
        return excluded

    def _prepare_array(self,values):
        values=None if values is None else list(values)
        if values is not None and self.kind in ('geometry','scatter') and len(values)!=len(self.data):raise ValueError('Values must match features or points')
        if values is not None and self.kind=='vectors' and len(values)!=len(self.data):raise ValueError('Values must match vectors')
        if values is not None and self.kind=='mesh' and len(values)!=(len(self.data[0])-1)*(len(self.data[1])-1):raise ValueError('Values must match mesh cells')
        return None if values is None else [None if v is None else float(v) for v in values]

    def set_array(self,values):return self.set(array=values)

    def to_color(self,value):
        from .colors import BoundaryNorm
        t=self.norm(value)
        if t is None:return self.options.get('missing_color',self.cmap.bad)
        if self.options.get('mapped') and not self.options.get('continuous') and not isinstance(self.norm,BoundaryNorm):
            count=self.options['bins'];index=max(0,min(count-1,int(t*count)))
            if self.options.get('scheme')=='quantile':
                scale=self.options['color_scale'];span=scale['vmax']-scale['vmin']
                if span:index=max(0,min(count-1,sum(t>=(v-scale['vmin'])/span for v in scale['edges'][1:])))
            t=(index+.5)/count
        return self.cmap(t)

    @property
    def zorder(self):
        if self.kind=='grid' and 'zorder' not in self.style and self._axes is not None:
            below=self._axes.get_axisbelow()
            return .5 if below is True else 2.5 if below is False else 1.5
        if self.kind=='geometry' and 'zorder' not in self.style:
            return 1 if any(f.geometry and f.geometry.type in ('Polygon','MultiPolygon') for f in self.data) else 2
        return self.style.get("zorder", 2)

    @artist_mutation
    def set(self, **kwargs):
        """Edit supported data/text, styles and colors after batch validation."""
        options=dict(kwargs);data=self.data
        if set(options)&{'data','xdata','ydata'}:
            self._line_geometry()
            if 'data' in options:
                if 'xdata' in options or 'ydata' in options:raise ValueError('Use data or xdata/ydata, not both')
                x,y=options.pop('data')
            else:
                x=options.pop('xdata',self.get_xdata());y=options.pop('ydata',self.get_ydata())
            x,y=list(x),list(y)
            if len(x)!=len(y):raise ValueError('x and y must have the same length')
            from .geometry import Geometry,Feature,FeatureCollection
            feature=self.data[0]
            geometry=Geometry('MultiPoint' if len(x)==1 else 'LineString',tuple(zip(x,y)))
            data=FeatureCollection((Feature(geometry,feature.properties,feature.id),))
        if 'text' in options:
            if self.kind not in ('text','annotation'):raise TypeError('This layer is not a text artist')
            data=(*data[:2],str(options.pop('text')))
        prepared=self._prepare_set(options)
        self.data=data
        self._apply_set(prepared)
        return self

    def _prepare_set(self,kwargs,*,array=_UNSET):
        options=dict(kwargs)
        if 'array' in options:
            if array is not _UNSET:raise ValueError('Color array specified twice')
            array=self._prepare_array(options.pop('array'))
        mapping=self._prepare_mapping(options,array=array)
        controls={key:options.pop(key) for key in ('visible','in_layout') if key in options}
        clear_alpha='alpha' in options and options['alpha'] is None
        if clear_alpha:options.pop('alpha')
        updates=style_dict(options)
        if self.kind in ('text','annotation','labels'):validate_text_properties(updates)
        return updates,controls,clear_alpha,mapping

    def _apply_set(self,prepared):
        updates,controls,clear_alpha,mapping=prepared
        if 'visible' in controls:self.set_visible(controls['visible'])
        if 'in_layout' in controls:self.set_in_layout(controls['in_layout'])
        if clear_alpha:self.style.pop('alpha',None)
        self.style.update(updates)
        if self.kind=='grid':
            for config in self.options.get('axes_config',{}).values():
                if clear_alpha:config['style'].pop('alpha',None)
                config['style'].update(updates)
        self._apply_mapping(mapping)

    @artist_mutation
    def set_text(self,value):
        if self.kind not in ('text','annotation'):raise TypeError('This layer is not a text artist')
        self.data=(*self.data[:2],str(value))

    def get_text(self):
        if self.kind not in ('text','annotation'):raise TypeError('This layer is not a text artist')
        return self.data[2]

    def _line_geometry(self):
        if self.kind!='geometry' or len(self.data)!=1 or self.data[0].geometry is None or self.data[0].geometry.type not in ('LineString','MultiPoint'):
            raise TypeError('Data editing requires a single line or plot point series')
        return self.data[0].geometry

    def get_data(self):
        coordinates=self._line_geometry().coordinates
        return [p[0] for p in coordinates],[p[1] for p in coordinates]

    @artist_mutation
    def set_data(self,*args):
        """Replace a geographic plot series; explicit map limits stay unchanged."""
        self._line_geometry()
        if len(args)==1:x,y=args[0]
        elif len(args)==2:x,y=args
        else:raise TypeError('Use set_data(x,y) or set_data((x,y))')
        self.set(data=(x,y))

    def get_xdata(self):return self.get_data()[0]
    def get_ydata(self):return self.get_data()[1]
    def set_xdata(self,value):return self.set_data(value,self.get_ydata())
    def set_ydata(self,value):return self.set_data(self.get_xdata(),value)

    def set_color(self,value):return self.set(color=value)
    def get_color(self):return self.style.get("color","#1f77b4")
    def set_linewidth(self,value):return self.set(linewidth=value)
    def get_linewidth(self):return self.style.get("linewidth",.8)
    def set_linestyle(self,value):return self.set(linestyle=value)
    def get_linestyle(self):return self.style.get("linestyle","-")
    def set_alpha(self,value):return self.set(alpha=value)
    def get_alpha(self):return self.style.get("alpha")
    def set_label(self,value):return self.set(label=value)
    def get_label(self):return self.style.get("label","")
    def set_zorder(self,value):return self.set(zorder=value)
    def get_zorder(self):return self.zorder
    def get_visible(self):return self.visible
    def set_facecolor(self,value):return self.set(facecolor=value)
    def set_edgecolor(self,value):return self.set(edgecolor=value)
    def get_facecolor(self):return self.style.get('facecolor',self.get_color())
    def get_edgecolor(self):return self.style.get('edgecolor',self.get_color())
    def set_marker(self,value):return self.set(marker=value)
    def get_marker(self):return self.style.get('marker','None')
    def set_markersize(self,value):return self.set(markersize=value)
    def get_markersize(self):return self.style.get('markersize',6)
    def set_markerfacecolor(self,value):return self.set(markerfacecolor=value)
    def get_markerfacecolor(self):
        value=self.style.get('markerfacecolor','auto')
        return self.get_color() if value=='auto' else value
    def set_markeredgecolor(self,value):return self.set(markeredgecolor=value)
    def get_markeredgecolor(self):
        value=self.style.get('markeredgecolor','auto')
        return self.get_color() if value=='auto' else value
    def set_markeredgewidth(self,value):return self.set(markeredgewidth=value)
    def get_markeredgewidth(self):return self.style.get('markeredgewidth',1.)
    def set_solid_capstyle(self,value):return self.set(solid_capstyle=value)
    def get_solid_capstyle(self):return self.style.get('solid_capstyle',{'square':'projecting'}.get(self.style.get('linecap'),self.style.get('linecap','round')))
    def set_dash_capstyle(self,value):return self.set(dash_capstyle=value)
    def get_dash_capstyle(self):return self.style.get('dash_capstyle',{'square':'projecting'}.get(self.style.get('linecap'),self.style.get('linecap','butt')))
    def set_solid_joinstyle(self,value):return self.set(solid_joinstyle=value)
    def get_solid_joinstyle(self):return self.style.get('solid_joinstyle',self.style.get('linejoin','round'))
    def set_dash_joinstyle(self,value):return self.set(dash_joinstyle=value)
    def get_dash_joinstyle(self):return self.style.get('dash_joinstyle',self.style.get('linejoin','round'))
    def set_antialiased(self,value):return self.set(antialiased=value)
    def get_antialiased(self):return self.style.get('antialiased',True)
    def set_fontsize(self,value):return self.set(fontsize=value)
    def get_fontsize(self):return self.style.get('fontsize',10)
    def set_fontweight(self,value):return self.set(fontweight=value)
    def get_fontweight(self):return self.style.get('fontweight','normal')
    def set_rotation(self,value):return self.set(rotation=value)
    def get_rotation(self):return self.style.get('rotation',0)

    @artist_mutation
    def set_visible(self, visible):
        self.visible = bool(visible)
        return self

    def remove(self):
        if self._axes is not None:
            self._axes.layers[:]=[layer for layer in self._axes.layers if layer is not self]
        self._changed()
        self._axes = None
        self._bind_parent(None)

