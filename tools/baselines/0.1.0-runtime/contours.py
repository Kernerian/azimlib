"""Own editable isolines and label handles over marching-squares geometry."""
from numbers import Real
import math
import weakref
from .layers import Layer
from .artist import artist_mutation,setp
from .geometry import Feature,FeatureCollection
from .styles import style_dict,dash_pattern
from .colors import NoNorm


def _colors(values):
    if values is None:return None
    values=(values,) if isinstance(values,str) else tuple(values)
    if not values or any(not isinstance(v,str) or not v.strip() for v in values):
        raise ValueError('Contour colors require a color string or nonempty sequence of strings')
    return values


def _widths(values):
    values=(values,) if isinstance(values,Real) else tuple(values)
    if not values:raise ValueError('linewidths must not be empty')
    return tuple(float(style_dict(linewidth=v)['linewidth']) for v in values)


def _linestyles(values):
    if isinstance(values,str):values=(values,)
    else:
        values=tuple(values)
        if values and all(isinstance(v,Real) for v in values):values=(values,)
    if not values:raise ValueError('linestyles must not be empty')
    return tuple(style_dict(linestyle=value)['linestyle'] for value in values)


class ContourSet(Layer):
    """Fixed contour paths; colors, per-level widths/styles and labels are editable.

    Geographic geometry/levels are frozen. Recompute a field by making a new
    contour, as with Axes.contour; set_array edits scalar colors, not topology.
    """
    def __post_init__(self):
        super().__post_init__()
        self.labelTexts=[]
        self.options['feature_levels']=tuple(self.levels.index(f.properties['level']) for f in self.data)

    @property
    def levels(self):return tuple(self.options['levels'])

    @property
    def cvalues(self):
        return self.get_array() if self._array is not None else list(self.options.get('initial_cvalues',self.levels))

    def _prepare_array(self,values):
        if values is None:return None
        values=[None if v is None else float(v) for v in values]
        if len(values)!=len(self.levels):raise ValueError('Contour color values must match the number of levels')
        return values

    @property
    def allsegs(self):
        return [[[[x,y] for x,y in feature.geometry.coordinates]
                 for feature in self.data if feature.properties['level']==level]
                for level in self.levels]

    def _line_geometry(self):raise TypeError('Contour paths are fixed; create a new contour for different data')

    @artist_mutation
    def set(self,**kwargs):
        options=dict(kwargs);updates={}
        for names,key,prepare in (
            (('color','colors','edgecolor','edgecolors','c','ec'),'contour_colors',_colors),
            (('linewidth','linewidths','lw'),'contour_widths',_widths),
            (('linestyle','linestyles','ls'),'contour_linestyles',_linestyles)):
            present=[name for name in names if name in options]
            if len(present)>1:raise ValueError(f'Use only one of {names}')
            if present:updates[key]=prepare(options.pop(present[0]))
        prepared=self._prepare_set(options)
        self.options.update(updates)
        self._apply_set(prepared)
        self._sync_labels()
        return self

    def _effective(self,key,fallback):
        values=self.options.get(key) or (fallback,)
        return [values[i%len(values)] for i in range(len(self.levels))]

    def get_linewidth(self):return self._effective('contour_widths',self.style.get('linewidth',1))
    get_linewidths=get_linewidth
    def set_linewidths(self,values):return self.set(linewidths=values)
    def get_linestyle(self):return self._effective('contour_linestyles',self.style.get('linestyle','-'))
    get_linestyles=get_linestyle
    def set_linestyles(self,values):return self.set(linestyles=values)
    def get_color(self):return [self._level_color(i) for i in range(len(self.levels))]
    get_edgecolor=get_color
    get_edgecolors=get_color
    def set_edgecolors(self,values):return self.set(edgecolors=values)

    def properties(self):
        props=super().properties()
        props.update(linewidth=self.get_linewidth(),linewidths=self.get_linewidths(),
                     linestyle=self.get_linestyle(),linestyles=self.get_linestyles(),
                     color=self.get_color(),edgecolor=self.get_edgecolor(),edgecolors=self.get_edgecolors())
        return props

    def _level_color(self,index):
        colors=self.options.get('contour_colors')
        if colors:return colors[index%len(colors)]
        return self._mapped_color(index)

    def _mapped_color(self,index):
        value=(self._array if self._array is not None else self.options.get('initial_cvalues',self.levels))[index]
        if isinstance(self.norm,NoNorm):
            return self.cmap.bad if value is None or not math.isfinite(value) else self.cmap(int(value))
        return self.to_color(value)

    def _feature_style(self,index,feature,style=None):
        level_index=self.options['feature_levels'][index]
        style=dict(self.style if style is None else style)
        colors=self.options.get('contour_colors')
        style['color']=colors[level_index%len(colors)] if colors else self._mapped_color(level_index)
        for key,option in (('linewidth','contour_widths'),('linestyle','contour_linestyles')):
            values=self.options.get(option)
            if values:style[key]=values[level_index%len(values)]
        return style

    def _sync_labels(self):
        for label in tuple(getattr(self,'labelTexts',())):
            if label._follow_contour_color:
                color=self._level_color(self.levels.index(label.options['contour_level']))
                if label.style.get('color')!=color:
                    label.style['color']=color;label._changed()

    def changed(self):
        self._sync_labels()
        super().changed()

    def clabel(self,levels=None,**kwargs):
        if self.axes is None:raise ValueError('Contour is detached from its axes')
        return self.axes.clabel(self,levels,**kwargs)

    def remove(self):
        for label in tuple(self.labelTexts):label.remove()
        super().remove()


class ContourLabel(Layer):
    """Editable text handle retaining own projected line-label placement."""
    def __post_init__(self):
        super().__post_init__()
        self._contour_ref=lambda:None
        self._follow_contour_color=False

    def _unsupported_properties(self):return super()._unsupported_properties()-{'text'}
    def get_text(self):return str(self.data[0].properties[self.options['field']])
    def set_text(self,value):return self.set(text=value)
    def get_inline(self):return self.options.get('inline',True)
    def set_inline(self,value):return self.set(inline=value)
    def get_inline_spacing(self):return self.options.get('inline_spacing',5.)
    def set_inline_spacing(self,value):return self.set(inline_spacing=value)

    @artist_mutation
    def set(self,**kwargs):
        options=dict(kwargs);data=self.data
        if 'text' in options:
            feature=self.data[0];props=dict(feature.properties)
            props[self.options['field']]=str(options.pop('text'))
            data=FeatureCollection((Feature(feature.geometry,props,feature.id),))
        settings={key:options.pop(key) for key in ('inline','inline_spacing') if key in options}
        _inline_settings(settings)
        prepared=self._prepare_set(options)
        self.data=data
        self.options.update(settings)
        if 'color' in options or 'c' in options:self._follow_contour_color=False
        self._apply_set(prepared)
        return self

    def remove(self):
        source=self._contour_ref()
        if source is not None:source.labelTexts[:]=[label for label in source.labelTexts if label is not self]
        self._contour_ref=lambda:None
        self._follow_contour_color=False
        super().remove()


class ContourLabels(list):
    """List of label handles; group helpers preserve Azimlib's earlier shorthand."""
    def set(self,**kwargs):setp(self,**kwargs);return self
    def set_visible(self,value):return self.set(visible=value)
    def get_visible(self):return any(label.get_visible() for label in self)
    def remove(self):
        for label in tuple(self):label.remove()


def make_labels(axes,contour,levels,fmt,kwargs):
    if not isinstance(contour,ContourSet) or contour.axes is not axes:
        raise ValueError('clabel requires a contour attached to these axes')
    levels=contour.levels if levels is None else tuple(float(v) for v in levels)
    if any(v not in contour.levels for v in levels):raise ValueError('Label levels must belong to the contour')
    options=dict(kwargs)
    settings=dict(inline=options.pop('inline',True),inline_spacing=options.pop('inline_spacing',5.))
    _inline_settings(settings)
    if settings['inline']:options.setdefault('offsets',((0,0),))
    colors=_colors(options.pop('colors',None))
    if colors is not None and ('color' in options or 'c' in options):raise ValueError('Use colors or color, not both')
    from .axes import MapAxes
    validator=MapAxes(None,(0,0,1,1))
    prototype=validator.labels(FeatureCollection(),color=colors[0] if colors else contour._level_color(0),**options) if not ('color' in options or 'c' in options) else validator.labels(FeatureCollection(),**options)
    created=[]
    for feature_index,feature in enumerate(contour.data):
        value=feature.properties['level']
        if value not in levels:continue
        text=(fmt.get(value,'%g'%value) if isinstance(fmt,dict) else
              fmt.format_ticks([value])[0] if hasattr(fmt,'format_ticks') else
              fmt(value) if callable(fmt) else fmt%value)
        index=contour.levels.index(value)
        color=colors[levels.index(value)%len(colors)] if colors else contour._level_color(index)
        styles=dict(prototype.style)
        if not ('color' in options or 'c' in options):styles['color']=color
        data=FeatureCollection((Feature(feature.geometry,{'name':str(text)}),))
        label=ContourLabel('labels',data,styles,dict(prototype.options,contour_level=value,
            contour_feature=feature_index,**settings))
        label._contour_ref=weakref.ref(contour)
        label._follow_contour_color=colors is None and not ('color' in options or 'c' in options)
        created.append(label)
    for label in created:
        label._axes=axes;label._bind_parent(axes);axes.layers.append(label)
    contour.labelTexts.extend(created)
    if created:axes._changed()
    return ContourLabels(contour.labelTexts)


def _inline_settings(options):
    if 'inline' in options and not isinstance(options['inline'],bool):raise TypeError('inline must be a bool')
    if 'inline_spacing' in options:
        spacing=float(options['inline_spacing'])
        if not math.isfinite(spacing) or spacing<0:raise ValueError('inline_spacing must be finite and nonnegative')
        options['inline_spacing']=spacing
