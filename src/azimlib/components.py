"""Independently editable text, spine and axis components."""
from dataclasses import dataclass
import math
from .styles import style_dict,text_style,normalize_aliases,validate_text_properties
from .config import rcParams
from .artist import Artist,artist_mutation

class LayoutArtist(Artist):
    """Compatibility name for the common Artist protocol."""


def _detach_texts(texts):
    """Discard text handles without retaining their former owner."""
    for text in texts or ():
        text._owner=None
        text._bind_parent(None)

class TextProperties:
    """Shared editable font and alignment vocabulary for own text handles."""
    def set_horizontalalignment(self,value):return self.set(ha=value)
    def get_horizontalalignment(self):return self.style.get('ha','left')
    def set_verticalalignment(self,value):return self.set(va=value)
    def get_verticalalignment(self):return self.style.get('va','baseline')
    set_ha=set_horizontalalignment;get_ha=get_horizontalalignment
    set_va=set_verticalalignment;get_va=get_verticalalignment
    def set_fontfamily(self,value):return self.set(fontfamily=value)
    def get_fontfamily(self):return self.style.get('fontfamily',rcParams['font.family'])
    def set_fontstyle(self,value):return self.set(fontstyle=value)
    def get_fontstyle(self):return self.style.get('fontstyle','normal')
    def set_size(self,value):return self.set(fontsize=value)
    def get_size(self):return self.get_fontsize()
    def set_weight(self,value):return self.set(fontweight=value)
    def get_weight(self):return self.get_fontweight()
    def get_rotation(self):return float(self.style.get('rotation',0))%360
    def set_rotation_mode(self,value):return self.set(rotation_mode=value)
    def get_rotation_mode(self):return self.style.get('rotation_mode','default')

class TextArtist(TextProperties,LayoutArtist):
    def __init__(self,text='',_owner=None,_slot=None,**style):
        Artist.__init__(self,_owner)
        self._in_layout=bool(style.pop('in_layout',True))
        self.text=str(text)
        self.visible=True
        self._owner=_owner;self._slot=_slot
        self.style={'fontfamily':rcParams['font.family'],'color':rcParams['text.color'],**style_dict(style)}
        validate_text_properties(self.style)
        text_style(self.style)
    def __iter__(self):return iter((self.text,self.style))
    def __getitem__(self,index):return (self.text,self.style)[index]
    def __bool__(self):return self.visible
    @artist_mutation
    def set_visible(self,value):self.visible=bool(value)
    def get_visible(self):return self.visible
    def remove(self):
        if self._owner is not None and self._slot is None and not getattr(self._owner,'_is_figure',False):
            raise NotImplementedError('This text belongs to a component; use set_visible(False)')
        self.set_visible(False)
        if self._owner is not None:
            if self._slot and getattr(self._owner,self._slot,None) is self:
                setattr(self._owner,self._slot,None)
            elif self._slot is None and getattr(self._owner,'_is_figure',False):
                self._owner._texts[:]=[entry for entry in self._owner._texts if entry[2] is not self]
        self._owner=None
        self._bind_parent(None)
    @artist_mutation
    def set_text(self,value):self.text=str(value);return self
    def get_text(self):return self.text
    @artist_mutation
    def set(self,**kwargs):
        options=dict(kwargs)
        controls={key:options.pop(key) for key in ('in_layout','visible','text') if key in options}
        clear_alpha='alpha' in options and options['alpha'] is None
        if clear_alpha:options.pop('alpha')
        updates=style_dict(options)
        validate_text_properties(updates)
        text_style(dict(self.style,**updates))
        if 'in_layout' in controls:self.set_in_layout(controls['in_layout'])
        if 'visible' in controls:self.set_visible(controls['visible'])
        if 'text' in controls:self.set_text(controls['text'])
        if clear_alpha:self.style.pop('alpha',None)
        self.style.update(updates);return self
    def set_color(self,value):return self.set(color=value)
    def get_color(self):return self.style.get('color','black')
    def set_fontsize(self,value):return self.set(fontsize=value)
    def get_fontsize(self):return self.style.get('fontsize',10)
    def set_fontweight(self,value):return self.set(fontweight=value)
    def get_fontweight(self):return self.style.get('fontweight','normal')
    def set_rotation(self,value):return self.set(rotation=value)
    def get_rotation(self):return float(self.style.get('rotation',0))%360
    def set_alpha(self,value):return self.set(alpha=value)
    def get_alpha(self):return self.style.get('alpha')

@dataclass
class Spine(LayoutArtist):
    visible: bool=True
    color: str='black'
    linewidth: float=.8
    def __post_init__(self):Artist.__init__(self)
    @artist_mutation
    def set(self,**kwargs):
        kwargs=normalize_aliases(kwargs)
        unknown=set(kwargs)-{'color','edgecolor','linewidth','visible','in_layout'}
        if unknown:raise AttributeError(f'Unsupported spine properties: {sorted(unknown)}')
        if 'color' in kwargs and 'edgecolor' in kwargs:raise ValueError('Use color or edgecolor, not both')
        updates=style_dict({key:kwargs[key] for key in ('color','edgecolor','linewidth') if key in kwargs})
        if 'color' in updates or 'edgecolor' in updates:self.color=updates.get('color',updates.get('edgecolor'))
        if 'linewidth' in updates:self.linewidth=updates['linewidth']
        if 'visible' in kwargs:self.visible=bool(kwargs['visible'])
        if 'in_layout' in kwargs:self._in_layout=bool(kwargs['in_layout'])
        return self
    def get_color(self):return self.color
    get_edgecolor=get_color
    def get_linewidth(self):return self.linewidth
    @artist_mutation
    def set_visible(self,value):self.visible=bool(value)
    def get_visible(self):return self.visible
    @artist_mutation
    def set_color(self,value):self.color=value
    set_edgecolor=set_color
    @artist_mutation
    def set_linewidth(self,value):self.linewidth=style_dict(linewidth=value)['linewidth']

class AxisComponents(LayoutArtist):
    @artist_mutation
    def ticklabel_format(self,*,axis='both',style=None,scilimits=None,useOffset=None,useLocale=None,useMathText=None):
        """Configure ScalarFormatter on the requested major axes atomically."""
        from .ticker import configure_scalar_axes
        configure_scalar_axes(self,axis=axis,style=style,scilimits=scilimits,
                              useOffset=useOffset,useLocale=useLocale,useMathText=useMathText)

    def _init_components(self):
        self._initializing_components=True
        self._labelpad={name:rcParams['axes.labelpad'] for name in ('x','y')}
        self.spines={side:Spine(color=rcParams['axes.edgecolor'],linewidth=rcParams['axes.linewidth']) for side in ('left','right','top','bottom')}
        for spine in self.spines.values():spine._bind_parent(self)
        self._ticks={'x':None,'y':None}
        self._tick_labels={'x':None,'y':None}
        self._minor_ticks={'x':None,'y':None}
        self._minor_tick_labels={'x':None,'y':None}
        from .axis import Axis
        self.xaxis=Axis(self,'x');self.yaxis=Axis(self,'y')
        self._tick_params={axis:dict(direction='out',length=3.5,width=.8,color=rcParams['axes.edgecolor'],
            labelcolor=rcParams['text.color'],labelsize=rcParams[axis+'tick.labelsize'],pad=3.5,rotation=0,rotation_mode='default',
            bottom=True,top=False,left=True,right=False,
            labelbottom=True,labeltop=False,labelleft=True,labelright=False) for axis in ('x','y')}
        self._minor_tick_params={axis:{**self._tick_params[axis],
            'length':rcParams[axis+'tick.minor.size'],'width':rcParams[axis+'tick.minor.width'],
            'pad':rcParams[axis+'tick.minor.pad']} for axis in ('x','y')}
        from .ticker import AutoMinorLocator
        for axis in ('x','y'):
            if rcParams[axis+'tick.minor.visible']:getattr(self,axis+'axis').set_minor_locator(AutoMinorLocator())
        self._initializing_components=False

    def _set_ticks(self,axis,ticks,labels=None,*,minor=False,**kwargs):
        bar=getattr(self,'_colorbar_artist',None)
        if bar is not None:return bar._tickaxis.set_xticks(ticks,labels,minor=minor,**kwargs)
        values=tuple(float(value) for value in ticks)
        bound=180 if axis=='x' else 90
        if any(not math.isfinite(v) or abs(v)>bound for v in values):raise ValueError('Ticks must be finite geographic coordinates')
        if labels is not None:
            labels=tuple(str(value) for value in labels)
            if len(labels)!=len(values):raise ValueError('ticks and labels must have the same length')
        elif kwargs:raise ValueError('Text options require explicit labels')
        style=style_dict(kwargs)
        validate_text_properties(style)
        from .ticker import FixedLocator,FixedFormatter
        controller=getattr(self,axis+'axis')
        (controller.set_minor_locator if minor else controller.set_major_locator)(FixedLocator(values))
        if labels is not None:(controller.set_minor_formatter if minor else controller.set_major_formatter)(FixedFormatter(labels))
        ticks_store=self._minor_ticks if minor else self._ticks
        labels_store=self._minor_tick_labels if minor else self._tick_labels
        ticks_store[axis]=values
        settings=(self._minor_tick_params if minor else self._tick_params)[axis]
        defaults=dict(color=settings['labelcolor'],fontsize=settings['labelsize'],rotation=settings['rotation'],rotation_mode=settings['rotation_mode'])
        labels_store[axis]=[TextArtist(value,_owner=self,**{**defaults,**style}) for value in labels] if labels is not None else None
        if values:
            low,high=self.get_xlim() if axis=='x' else self.get_ylim()
            (self.set_xlim if axis=='x' else self.set_ylim)(min(low,min(values)),max(high,max(values)))
        return labels_store[axis] or []

    def set_xticks(self,ticks,labels=None,*,minor=False,**kwargs):return self._set_ticks('x',ticks,labels,minor=minor,**kwargs)
    def set_yticks(self,ticks,labels=None,*,minor=False,**kwargs):return self._set_ticks('y',ticks,labels,minor=minor,**kwargs)
    def get_xticks(self,*,minor=False):return self._get_ticks('x',minor=minor)
    def get_yticks(self,*,minor=False):return self._get_ticks('y',minor=minor)
    def get_xaxis(self):return self.xaxis
    def get_yaxis(self):return self.yaxis
    def _get_ticks(self,axis,*,minor=False):
        bar=getattr(self,'_colorbar_artist',None)
        if bar is not None:return bar.get_ticks(minor=minor)
        from .render_map import axis_tick_values
        scene=self.figure.to_scene()
        index=self.figure.axes.index(self) if self in self.figure.axes else -1
        meta=next((m for m in scene.maps if m.get('axes_index')==index),None)
        pixels=meta['box'][2 if axis=='x' else 3]*100/self.figure.dpi if meta else self.position[2 if axis=='x' else 3]*self.figure.figsize[0 if axis=='x' else 1]*100
        return tuple(axis_tick_values(self,axis,pixels,minor=minor))

    def minorticks_on(self):
        """Enable automatic minor ticks without enabling any grid."""
        bar=getattr(self,'_colorbar_artist',None)
        if bar is not None:return bar.minorticks_on()
        from .ticker import AutoMinorLocator
        for axis in (self.xaxis,self.yaxis):axis.set_minor_locator(AutoMinorLocator())
    def minorticks_off(self):
        bar=getattr(self,'_colorbar_artist',None)
        if bar is not None:return bar.minorticks_off()
        from .ticker import NullLocator
        for axis in (self.xaxis,self.yaxis):axis.set_minor_locator(NullLocator())

    @artist_mutation
    def tick_params(self,axis='both',which='major',**kwargs):
        bar=getattr(self,'_colorbar_artist',None)
        if bar is not None:return bar._tickaxis.tick_params(axis,which,**kwargs)
        if axis not in ('x','y','both') or which not in ('major','minor','both'):
            raise ValueError('axis: x/y/both; which: major/minor/both')
        if 'colors' in kwargs:
            value=kwargs.pop('colors');kwargs.setdefault('color',value);kwargs.setdefault('labelcolor',value)
        if 'labelrotation' in kwargs:kwargs['rotation']=kwargs.pop('labelrotation')
        if 'labelrotation_mode' in kwargs:kwargs['rotation_mode']=kwargs.pop('labelrotation_mode')
        if 'rotation_mode' in kwargs:
            kwargs['rotation_mode']=style_dict({'rotation_mode':kwargs['rotation_mode']})['rotation_mode']
        unknown=set(kwargs)-set(self._tick_params['x'])
        if unknown:raise TypeError(f'Unsupported tick options: {sorted(unknown)}')
        if kwargs.get('direction','out') not in ('in','out','inout'):raise ValueError('direction: in/out/inout')
        for key in ('length','width','labelsize','pad','rotation'):
            if key in kwargs:
                kwargs[key]=float(kwargs[key])
                if not math.isfinite(kwargs[key]) or key!='rotation' and kwargs[key]<0 or key=='labelsize' and kwargs[key]==0:
                    raise ValueError(f'Invalid tick {key}')
        for kind in ('major','minor') if which=='both' else (which,):
            params=self._minor_tick_params if kind=='minor' else self._tick_params
            labels=self._minor_tick_labels if kind=='minor' else self._tick_labels
            for name in ('x','y') if axis=='both' else (axis,):
                params[name].update(kwargs)
                changes={target:kwargs[source] for source,target in (('labelcolor','color'),('labelsize','fontsize'),('rotation','rotation'),('rotation_mode','rotation_mode')) if source in kwargs}
                for label in labels[name] or []:label.set(**changes)
                if kind=='major':
                    offset=getattr(self,name+'axis').get_offset_text()
                    offset.set(**{key:value for key,value in changes.items() if key in ('color','fontsize')})

    @artist_mutation
    def set_axis_off(self):self._frame=False
    @artist_mutation
    def set_axis_on(self):self._frame=True

    def _label_outer_axis(self,name,remove_inner_ticks=False):
        spec=self.get_subplotspec()
        if spec is None:return
        sides=(('top',spec.is_first_row()),('bottom',spec.is_last_row())) if name=='x' else (
            ('left',spec.is_first_col()),('right',spec.is_last_col()))
        for side,outer in sides:
            if outer:continue
            options={'label'+side:False}
            if remove_inner_ticks:options[side]=False
            self.tick_params(axis=name,which='both',**options)
            if side==('bottom' if name=='x' else 'left'):
                (self.set_xlabel if name=='x' else self.set_ylabel)('')

    @artist_mutation
    def label_outer(self,remove_inner_ticks=False):
        """Hide inner labels; optionally hide ticks, using the local SubplotSpec."""
        for name in ('x','y'):self._label_outer_axis(name,remove_inner_ticks)

class MapComponent(dict,LayoutArtist):
    """Owned cartographic artist with familiar visibility and removal methods."""
    def __init__(self,*,axes=None,slot=None,**options):
        Artist.__init__(self,axes)
        self._in_layout=bool(options.pop('in_layout',True))
        visible=bool(options.pop('visible',True))
        super().__init__(visible=visible,**options)
        self.axes=axes;self.slot=slot
    def __bool__(self):return self.get_visible()
    @artist_mutation
    def set_visible(self,value):
        self['visible']=bool(value)
        self._changed()
    def get_visible(self):return self.get('visible',True)
    def remove(self):
        self.set_visible(False)
        if self.axes and self.slot and getattr(self.axes,self.slot,None) is self:
            setattr(self.axes,self.slot,None)
        self._bind_parent(None)
        self.axes=None

class OrientationIndicator(MapComponent):
    """Editable north arrow or compass rose; each has an independent Axes slot."""
    def __init__(self,*,axes,slot,loc,size,color,compass=False):
        options=self._validate_options(dict(loc=loc,size=size,color=color,visible=True))
        super().__init__(axes=axes,slot=slot,compass=bool(compass),
                         **{k:v for k,v in options.items() if k!='visible'})

    @staticmethod
    def _validate_options(options):
        from .axes import _validate_loc
        _validate_loc(options['loc'])
        size=float(options['size'])
        if not math.isfinite(size) or size<=0:raise ValueError('size must be finite and positive')
        style_dict(color=options['color'])
        return dict(options,size=size,visible=bool(options['visible']))

    @artist_mutation
    def set(self,**kwargs):
        kwargs=dict(kwargs);layout=kwargs.pop('in_layout',None)
        unknown=set(kwargs)-{'loc','size','color','visible'}
        if unknown:raise TypeError(f'Unsupported orientation properties: {sorted(unknown)}')
        options=self._validate_options(dict(self,**kwargs))
        if layout is not None:self.set_in_layout(layout)
        self.update(options)
        return self

    def get_angle(self):
        from .render_map import orientation_angle,_anchor
        from .typography import POINT
        vp=self.axes._transform_viewport();size=self['size']*POINT;pad=13*POINT
        x,y=_anchor(vp.box,self['loc'],size+2*pad,size+2*pad,pad=10)
        return math.degrees(orientation_angle(vp,x+size/2+pad,y+size/2+pad))

    def get_loc(self):return self['loc']
    def set_loc(self,value):return self.set(loc=value)
    def get_size(self):return self['size']
    def set_size(self,value):return self.set(size=value)
    def get_color(self):return self['color']
    def set_color(self,value):return self.set(color=value)

class Legend(MapComponent):
    """Legend configuration returned by Axes.legend; handles retain live styles."""
    def __init__(self,**options):
        from .legend_layout import validate_options
        axes=options.pop('axes',None);slot=options.pop('slot',None)
        in_layout=options.pop('in_layout',True)
        super().__init__(axes=axes,slot=slot,**validate_options(options))
        self.set_in_layout(in_layout)
        self._text_defaults={'color':rcParams['text.color'],'fontfamily':rcParams['font.family']}
        self.title_artist=TextArtist(self['title'] or '',_owner=self,fontsize=self['title_fontsize'],ha='center',va='top')
        self._texts=[];self._source_labels=None;self._last_box=None;self._last_loc=None
        self._symbol_visibility={id(layer):getattr(layer,'get_visible',lambda:True)() for entry in
            (self['handles'] if self['handles'] is not None else self.axes.layers)
            for layer in (entry if isinstance(entry,tuple) else (entry,))}
    def _sync_texts(self,labels):
        if labels!=self._source_labels:
            for text in self._texts:text._bind_parent(None)
            self._texts=[TextArtist(label,_owner=self,fontsize=self['fontsize'],va='center',**self._text_defaults) for label in labels]
            self._source_labels=list(labels)
        return self._texts
    def get_texts(self):
        from .legend_layout import entries
        return self._sync_texts([label for label,_ in entries(self)])
    def get_title(self):return self.title_artist
    @artist_mutation
    def set_title(self,text,**kwargs):
        with self.title_artist._mutation():
            self.title_artist.set(text=text,**kwargs)
            self['title']=str(text);self['title_fontsize']=self.title_artist.get_fontsize();self._changed()
        return self
    @artist_mutation
    def set(self,**kwargs):
        from .legend_layout import validate_options
        layout=kwargs.pop('in_layout',None)
        if set(kwargs)-set(self):raise TypeError('Unknown legend property')
        options=validate_options(dict(self,**kwargs))
        if layout is not None:self.set_in_layout(layout)
        self.update(options)
        if 'title' in kwargs:self.title_artist.set_text(kwargs['title'] or '')
        if 'title_fontsize' in kwargs:self.title_artist.set_fontsize(kwargs['title_fontsize'])
        if 'fontsize' in kwargs:
            for text in self._texts:text.set_fontsize(kwargs['fontsize'])
        self._changed();return self
    def set_loc(self,value):return self.set(loc=value)
    def set_ncols(self,value):return self.set(ncols=value)
    def set_bbox_to_anchor(self,value,transform=None):return self.set(bbox_to_anchor=value,**({'bbox_transform':transform} if transform else {}))
    def get_frame_on(self):return self['frameon']
    def set_frame_on(self,value):return self.set(frameon=bool(value))
    def get_frame(self):
        if not hasattr(self,'_frame_artist'):self._frame_artist=LegendFrame(self)
        return self._frame_artist
    def get_children(self):return [self.title_artist,*self.get_texts(),self.get_frame()]

class LegendFrame(LayoutArtist):
    def __init__(self,legend):
        Artist.__init__(self,legend)
        self.legend=legend
    @artist_mutation
    def set(self,**kwargs):
        kwargs=normalize_aliases(kwargs)
        mapping={'facecolor':'facecolor','edgecolor':'edgecolor','linewidth':'linewidth','alpha':'framealpha','visible':'frameon'}
        unknown=set(kwargs)-set(mapping)-{'in_layout'}
        if unknown:raise AttributeError(f'Unsupported legend frame properties: {sorted(unknown)}')
        updates={mapping[key]:value for key,value in kwargs.items() if key in mapping}
        # Validate the whole delegated edit before changing its owner or frame.
        from .legend_layout import validate_options
        validate_options(dict(self.legend,**updates))
        self.legend.set(**updates)
        if 'in_layout' in kwargs:self._in_layout=bool(kwargs['in_layout'])
        return self
    def get_facecolor(self):return self.legend['facecolor']
    def get_edgecolor(self):return self.legend['edgecolor']
    def get_linewidth(self):return self.legend['linewidth']
    def get_alpha(self):return self.legend['framealpha']
    @artist_mutation
    def set_facecolor(self,value):return self.legend.set(facecolor=value)
    @artist_mutation
    def set_edgecolor(self,value):return self.legend.set(edgecolor=value)
    @artist_mutation
    def set_linewidth(self,value):return self.legend.set(linewidth=value)
    @artist_mutation
    def set_alpha(self,value):return self.legend.set(framealpha=value)
    @artist_mutation
    def set_visible(self,value):return self.legend.set_frame_on(value)
    def get_visible(self):return self.legend.get_frame_on()

class ScaleBar(MapComponent):
    """Editable local distance; graduations adapt without reducing font size.

    Lengths use the selected unit. Crowded labels reduce to endpoints, then a
    single total/unit caption; geographic distance is never stretched to fit.
    """
    def __init__(self,*,axes=None,slot=None,**options):
        layout=options.pop('in_layout',True)
        super().__init__(axes=axes,slot=slot,in_layout=layout,**self._validate_options(options))

    @staticmethod
    def _validate_options(options):
        options=dict(options)
        from .axes import _validate_loc
        _validate_loc(options['loc'])
        if options['units'] not in ('m','km','mi'):raise ValueError('units must be km, m, or mi')
        length=options['length']
        if length is not None:
            length=float(length)
            if not math.isfinite(length) or length<=0:raise ValueError('Scale bar length must be finite and positive')
            options['length']=length
        alpha=float(options['framealpha'])
        if not math.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('framealpha must lie in [0,1]')
        options['framealpha']=alpha
        options.update(style_dict({key:options[key] for key in ('fontsize','color','facecolor','edgecolor')}))
        options['frameon']=bool(options['frameon'])
        if 'visible' in options:options['visible']=bool(options['visible'])
        return options

    @artist_mutation
    def set(self,**kwargs):
        layout=kwargs.pop('in_layout',None)
        unknown=set(kwargs)-set(self)
        if unknown:raise TypeError(f'Unsupported scale properties: {sorted(unknown)}')
        options=self._validate_options(dict(self,**kwargs))
        if layout is not None:self.set_in_layout(layout)
        self.update(options)
        self._changed()
        return self
    def set_length(self,value):return self.set(length=value)
    def get_length(self):return self['length']
    def set_units(self,value):return self.set(units=value)
    def get_units(self):return self['units']
    def set_loc(self,value):return self.set(loc=value)
    def get_loc(self):return self['loc']
    def set_fontsize(self,value):return self.set(fontsize=value)
    def get_fontsize(self):return self['fontsize']
    def set_color(self,value):return self.set(color=value)
    def get_color(self):return self['color']
    def set_facecolor(self,value):return self.set(facecolor=value)
    def set_edgecolor(self,value):return self.set(edgecolor=value)
    def set_frame_on(self,value):return self.set(frameon=bool(value))
    def get_frame_on(self):return self['frameon']
