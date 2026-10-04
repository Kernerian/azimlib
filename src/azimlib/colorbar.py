"""Editable colorbar artist sharing its mappable's live normalization."""
import math
from .components import MapComponent,TextArtist,Spine
from .styles import style_dict
from .colors import BoundaryNorm
from .cm import ScalarMappable
from .artist import artist_mutation

class ColorbarAxes:
    """Colorbar text/tick facade; not a geographic MapAxes."""
    def __init__(self,bar):
        self.bar=bar
        from .axis import Axis
        self.xaxis=Axis(self,'x');self.yaxis=Axis(self,'y')
        self.settings=dict(labelsize=10,labelcolor='black',color='black',length=3.5,width=.8,pad=3.5,direction='out',rotation=0,rotation_mode='default')
        from .config import rcParams
        prefix='ytick.minor.' if bar.orientation=='vertical' else 'xtick.minor.'
        self.minor_settings={**self.settings,'length':rcParams[prefix+'size'],
                             'width':rcParams[prefix+'width'],'pad':rcParams[prefix+'pad']}
    def tick_params(self,axis='both',which='major',**kwargs):
        if axis not in ('x','y','both') or which not in ('major','minor','both'):raise ValueError('axis: x/y/both; which: major/minor/both')
        if 'colors' in kwargs:
            color=kwargs.pop('colors');kwargs.update(color=color,labelcolor=color)
        if 'labelrotation' in kwargs:kwargs['rotation']=kwargs.pop('labelrotation')
        if 'labelrotation_mode' in kwargs:kwargs['rotation_mode']=kwargs.pop('labelrotation_mode')
        if 'rotation' in kwargs:kwargs['rotation']=style_dict({'rotation':kwargs['rotation']})['rotation']
        if 'rotation_mode' in kwargs:kwargs['rotation_mode']=style_dict({'rotation_mode':kwargs['rotation_mode']})['rotation_mode']
        if set(kwargs)-set(self.settings):raise TypeError('Unsupported colorbar tick option')
        if kwargs.get('direction','out') not in ('in','out','inout'):raise ValueError('Invalid tick direction')
        for key in ('labelsize','length','width','pad'):
            if key in kwargs:
                kwargs[key]=float(kwargs[key])
                if not math.isfinite(kwargs[key]) or kwargs[key]<0 or key=='labelsize' and kwargs[key]==0:raise ValueError('Invalid tick size')
        changes={target:kwargs[source] for source,target in (('labelsize','fontsize'),('labelcolor','color'),('rotation','rotation'),('rotation_mode','rotation_mode')) if source in kwargs}
        if axis!='both' and axis!=self.bar._long_axis.name:return
        for kind in ('major','minor') if which=='both' else (which,):
            (self.minor_settings if kind=='minor' else self.settings).update(kwargs)
            for artist in (self.bar._minor_ticklabels if kind=='minor' else self.bar._ticklabels) or []:artist.set(**changes)
            if kind=='major':self.bar._long_axis.get_offset_text().set(**changes)
        self.bar._changed()
    def set_ylabel(self,text,**kwargs):return self.bar.set_label(text,**kwargs)
    def set_xlabel(self,text,**kwargs):return self.bar.set_label(text,**kwargs)
    def set_visible(self,value):self.bar.set_visible(value)
    def get_visible(self):return self.bar.get_visible()
    def set_xticks(self,ticks,labels=None,*,minor=False,**kwargs):
        self.bar.set_ticks(ticks,labels=labels,minor=minor,**kwargs)
        return (self.bar._minor_ticklabels if minor else self.bar._ticklabels) or []
    def set_yticks(self,ticks,labels=None,*,minor=False,**kwargs):return self.set_xticks(ticks,labels,minor=minor,**kwargs)
    def get_xticks(self,*,minor=False):return self.bar.get_ticks(minor=minor)
    def get_yticks(self,*,minor=False):return self.bar.get_ticks(minor=minor)
    def minorticks_on(self):return self.bar.minorticks_on()
    def minorticks_off(self):return self.bar.minorticks_off()
    def get_xaxis(self):return self.xaxis
    def get_yaxis(self):return self.yaxis
    def ticklabel_format(self,**kwargs):
        from .ticker import configure_scalar_axes
        kwargs.setdefault('axis',self.bar._long_axis.name)
        configure_scalar_axes(self,**kwargs)

class Colorbar(MapComponent):
    def __init__(self,axes,mappable,*,orientation=None,location=None,label=None,
                 fraction=.15,shrink=1,aspect=20,pad=None,ticks=None,format=None,
                 extend='neither',extendfrac=.05,spacing='uniform',drawedges=False,alpha=1):
        if location is None:location='bottom' if orientation=='horizontal' else 'right'
        if location not in ('left','right','top','bottom'):raise ValueError('Invalid colorbar location')
        orientation=orientation or ('horizontal' if location in ('top','bottom') else 'vertical')
        options=dict(orientation=orientation,location=location,fraction=fraction,shrink=shrink,aspect=aspect,
                     pad={'left':.10,'right':.05,'top':.05,'bottom':.15}[location] if pad is None else pad,extend=extend,extendfrac=extendfrac,
                     spacing=spacing,drawedges=drawedges,alpha=alpha)
        self._validate(options)
        if not isinstance(mappable,ScalarMappable):raise TypeError('colorbar needs an Azimlib ScalarMappable')
        self._prepare_mappable(mappable)
        super().__init__(axes=axes,slot='_colorbar',layer=mappable,label=label,**options)
        # Initialize internal tickers without requesting a draw before the
        # caller has registered this component in its Axes/Figure.
        self._bind_parent(None)
        self.mappable=mappable;self._norm=mappable.norm
        self._mappable_cid=mappable.callbacks.connect('changed',self.update_normal)
        self._tickaxis=ColorbarAxes(self);self.ax=self._tickaxis;self.outline=Spine(linewidth=.8)
        self.parents=(axes,);self.cax=None;self._figure=axes.figure
        self.outline._bind_parent(self)
        self.label_artist=TextArtist(label or '',_owner=self,fontsize=10)
        self.labelpad=4;self.label_loc='center'
        self._ticks=None;self._ticklabels=None;self._minor_ticks=None;self._minor_ticklabels=None
        self._reset_tickers();self.formatter=format
        if ticks is not None:self.set_ticks(ticks)
        self._bind_parent(axes)
    @staticmethod
    def _prepare_mappable(mappable):
        from .layers import Layer
        if isinstance(mappable,Layer) and not mappable.norm.scaled() and mappable.get_array() is None:
            raise ValueError('Colorbar needs numeric data or explicit normalization limits')
        if mappable.norm.scaled():return
        mappable.autoscale_None()
        if mappable.norm.scaled():return
        from .colors import LogNorm,TwoSlopeNorm
        norm=mappable.norm
        low,high=(1.,10.) if isinstance(norm,LogNorm) else (norm.vcenter-1,norm.vcenter+1) if isinstance(norm,TwoSlopeNorm) else (0.,1.)
        norm._set_limits(low,high)
    @staticmethod
    def _validate(o):
        if o['orientation'] not in ('vertical','horizontal'):raise ValueError('orientation must be vertical or horizontal')
        if o['location'] not in ('right','left','top','bottom') or (o['orientation']=='vertical')!=(o['location'] in ('right','left')):raise ValueError('Location incompatible with orientation')
        for name in ('fraction','shrink','aspect','pad','extendfrac','alpha'):
            if not math.isfinite(float(o[name])) or float(o[name])<0:raise ValueError(f'Invalid {name}')
        if not 0<o['fraction']<1 or not 0<o['shrink']<=1 or o['aspect']<=0 or o['fraction']+o['pad']>=.8 or o['alpha']>1:raise ValueError('Invalid colorbar size or alpha')
        if o['extend'] not in ('neither','min','max','both'):raise ValueError('Invalid extend')
        if o['spacing'] not in ('uniform','proportional'):raise ValueError('Invalid spacing')
    def get_children(self):return [self.label_artist,self.outline,self._tickaxis.xaxis.offsetText,self._tickaxis.yaxis.offsetText,*(self._ticklabels or []),*(self._minor_ticklabels or [])]
    @property
    def norm(self):return self.mappable.norm
    @property
    def cmap(self):return self.mappable.cmap
    @property
    def orientation(self):return self['orientation']
    @property
    def boundaries(self):
        return self.mappable.levels if getattr(self.mappable,'options',{}).get('contour') else self.norm.boundaries if isinstance(self.norm,BoundaryNorm) else None
    @property
    def values(self):
        return tuple(self.mappable.cvalues) if getattr(self.mappable,'options',{}).get('contour') else None
    @property
    def vmin(self):return self._view_interval()[0]
    @property
    def vmax(self):return self._view_interval()[1]
    def _view_interval(self):
        if getattr(self.mappable,'options',{}).get('contour'):
            lo,hi=self.mappable.levels[0],self.mappable.levels[-1]
            return (lo,hi) if lo!=hi else (lo-.5,hi+.5)
        return self.mappable.get_clim()
    @property
    def _long_axis(self):return self._tickaxis.yaxis if self.orientation=='vertical' else self._tickaxis.xaxis
    def _reset_tickers(self):
        from .components import _detach_texts
        _detach_texts(self._ticklabels);_detach_texts(self._minor_ticklabels)
        self._ticks=self._ticklabels=None
        from .ticker import AutoLocator,AutoMinorLocator,LogLocator,FixedLocator,ScalarFormatter,NullLocator,NullFormatter
        from .colors import LogNorm
        from .config import rcParams
        for axis in (self._tickaxis.xaxis,self._tickaxis.yaxis):
            locator=NullLocator() if axis is not self._long_axis else FixedLocator(self.mappable.levels) if getattr(self.mappable,'options',{}).get('contour') else FixedLocator(self.norm.boundaries) if isinstance(self.norm,BoundaryNorm) else LogLocator() if isinstance(self.norm,LogNorm) else AutoLocator()
            locator.set_axis(axis);axis._locator=locator;axis.locator_explicit=False
            formatter=ScalarFormatter() if axis is self._long_axis else NullFormatter()
            formatter.set_axis(axis);axis._formatter=formatter;axis.formatter_explicit=False
            minor=LogLocator(subs=tuple(range(2,10))) if axis is self._long_axis and isinstance(self.norm,LogNorm) else AutoMinorLocator() if axis is self._long_axis and rcParams[axis.name+'tick.minor.visible'] else NullLocator()
            minor.set_axis(axis);axis._minor_locator=minor;axis.minor_locator_explicit=False
            fmt=NullFormatter();fmt.set_axis(axis);axis._minor_formatter=fmt;axis.minor_formatter_explicit=False
        self._minor_ticks=self._minor_ticklabels=None
    def _sync_tickers(self):
        self._prepare_mappable(self.mappable)
        if self.mappable.norm is not self._norm:
            self._norm=self.mappable.norm;self._reset_tickers()
    @property
    def locator(self):return self._long_axis.get_major_locator()
    @locator.setter
    def locator(self,value):self._long_axis.set_major_locator(value)
    @property
    def formatter(self):return self._long_axis.get_major_formatter()
    @property
    def minorlocator(self):return self._long_axis.get_minor_locator()
    @minorlocator.setter
    def minorlocator(self,value):self._long_axis.set_minor_locator(value)
    @property
    def minorformatter(self):return self._long_axis.get_minor_formatter()
    @minorformatter.setter
    def minorformatter(self,value):self._long_axis.set_minor_formatter(value)
    @formatter.setter
    def formatter(self,value):
        from .ticker import Formatter,ScalarFormatter,FormatStrFormatter,StrMethodFormatter,FuncFormatter
        if value is None:value=ScalarFormatter()
        elif isinstance(value,str):
            spec=value
            value=StrMethodFormatter(spec) if '{' in spec else FormatStrFormatter(spec) if '%' in spec else FuncFormatter(lambda x,pos:format(x,spec))
        elif not isinstance(value,Formatter) and callable(value):
            func=value;value=FuncFormatter(lambda x,pos:func(x))
        self._long_axis.set_major_formatter(value)
    def update_ticks(self):self._changed()
    def set(self,**kwargs):
        layout=kwargs.pop('in_layout',None)
        if set(kwargs)-set(self):raise TypeError('Unknown colorbar property')
        options=dict(self,**kwargs);self._validate(options)
        if layout is not None:self.set_in_layout(layout)
        oldaxis=self._long_axis;self.update(options);newaxis=self._long_axis
        if oldaxis is not newaxis:
            oldaxis.offsetText,newaxis.offsetText=newaxis.offsetText,oldaxis.offsetText
            from .ticker import NullLocator,NullFormatter
            for name,flag,factory in (('_locator','locator_explicit',NullLocator),('_formatter','formatter_explicit',NullFormatter),
                                      ('_minor_locator','minor_locator_explicit',NullLocator),('_minor_formatter','minor_formatter_explicit',NullFormatter)):
                value=getattr(oldaxis,name);value.axis=newaxis;setattr(newaxis,name,value);setattr(newaxis,flag,getattr(oldaxis,flag))
                replacement=factory();replacement.set_axis(oldaxis);setattr(oldaxis,name,replacement);setattr(oldaxis,flag,False)
        if 'label' in kwargs:self.label_artist.set_text(kwargs['label'] or '')
        self._changed();return self
    @artist_mutation
    def set_label(self,text,*,labelpad=None,loc=None,**kwargs):
        if labelpad is not None:
            if not math.isfinite(labelpad):raise ValueError('labelpad must be finite')
        if loc is not None:
            if loc not in (('bottom','center','top') if self.orientation=='vertical' else ('left','center','right')):raise ValueError('Invalid label location')
        with self.label_artist._mutation():
            self.label_artist.set(text=text,**kwargs)
            if labelpad is not None:self.labelpad=float(labelpad)
            if loc is not None:self.label_loc=loc
            self['label']=str(text);self._changed()
        return self.label_artist
    def set_alpha(self,value):return self.set(alpha=value)
    def set_ticks(self,ticks,labels=None,*,minor=False,**kwargs):
        values=tuple(float(v) for v in ticks)
        if any(not math.isfinite(v) for v in values):raise ValueError('Ticks must be finite')
        if labels is not None and len(labels)!=len(values):raise ValueError('Ticks and labels must match')
        if labels is None and kwargs:raise ValueError('Text options require labels')
        style_dict(kwargs)
        from .ticker import FixedLocator,FixedFormatter
        if minor:
            self.minorlocator=FixedLocator(values)
            if labels is not None:self.minorformatter=FixedFormatter(labels)
            self._minor_ticks=values;self._minor_ticklabels=None if labels is None else [TextArtist(v,_owner=self,**kwargs) for v in labels]
        else:
            self.locator=FixedLocator(values)
            if labels is not None:self.formatter=FixedFormatter(labels)
            self._ticks=values;self._ticklabels=None if labels is None else [TextArtist(v,_owner=self,**kwargs) for v in labels]
        self._changed()
    def get_ticks(self,*,minor=False):
        self._sync_tickers()
        if minor:return self._long_axis.get_minorticklocs()
        if self._long_axis.locator_explicit:return self.locator()
        if self._ticks is not None:return self._ticks
        if getattr(self.mappable,'options',{}).get('contour'):return self.mappable.levels
        if isinstance(self.norm,BoundaryNorm):return self.norm.boundaries
        lo,hi=self.mappable.get_clim()
        if lo==hi:return (lo,)
        from .colors import LogNorm
        if isinstance(self.norm,LogNorm):return tuple(10.**i for i in range(math.ceil(math.log10(lo)),math.floor(math.log10(hi))+1)) or (lo,hi)
        target=(hi-lo)/9;power=10**math.floor(math.log10(target))
        step=next(v*power for v in (1,2,2.5,5,10) if v*power>=target)
        return tuple(i*step for i in range(math.ceil(lo/step),math.floor(hi/step)+1))
    def set_ticklabels(self,labels,*,minor=False,**kwargs):self.set_ticks(self.get_ticks(minor=minor),labels=labels,minor=minor,**kwargs)
    def minorticks_on(self):
        """Enable subdivisions on the long axis; the short axis remains empty."""
        from .ticker import AutoMinorLocator,LogLocator
        from .colors import LogNorm
        self.minorlocator=LogLocator(subs=tuple(range(2,10))) if isinstance(self.norm,LogNorm) else AutoMinorLocator()
    def minorticks_off(self):
        from .ticker import NullLocator
        self.minorlocator=NullLocator()
    def update_normal(self,mappable):
        if not isinstance(mappable,ScalarMappable):raise TypeError('Expected ScalarMappable')
        self._prepare_mappable(mappable)
        if mappable is not self.mappable:
            self.mappable.callbacks.disconnect(self._mappable_cid)
            self._mappable_cid=mappable.callbacks.connect('changed',self.update_normal)
        changed=mappable.norm is not self._norm
        self.mappable=mappable;self._norm=mappable.norm;self['layer']=mappable
        if changed:self._reset_tickers()
        self._changed()
    def remove(self):
        figure=self._figure
        self.mappable.callbacks.disconnect(self._mappable_cid)
        super().remove()
        if figure:figure._colorbars[:]=[bar for bar in figure._colorbars if bar is not self]
        if self.cax is not None and figure is not None:
            self.cax._colorbar_artist=None
            if self.cax in figure.axes:figure.axes.remove(self.cax)
            figure._forget_axes(self.cax)
            self.cax.visible=False
            self.cax._bind_parent(None)
        self.axes=None;self._figure=None
