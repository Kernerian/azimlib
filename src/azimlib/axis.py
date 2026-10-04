"""Major/minor tick controllers shared by geographic axes and colorbars."""
from .ticker import AutoLocator,ScalarFormatter,Locator,FixedFormatter,FixedLocator,NullLocator,NullFormatter,as_formatter
import warnings

class Axis:
    def __init__(self,owner,name):
        self.owner=owner;self.name=name;self._pixels=None
        self._locator=AutoLocator();self._locator.set_axis(self)
        self._formatter=ScalarFormatter();self._formatter.set_axis(self)
        self.locator_explicit=False;self.formatter_explicit=False
        self._minor_locator=NullLocator();self._minor_locator.set_axis(self)
        self._minor_formatter=NullFormatter();self._minor_formatter.set_axis(self)
        self.minor_locator_explicit=False;self.minor_formatter_explicit=False
        self.remove_overlapping_locs=True
        from .components import TextArtist
        from .config import rcParams
        parent=getattr(owner,'bar',owner)
        self.offsetText=TextArtist('',_owner=parent,fontsize=rcParams[name+'tick.labelsize'])
    def _target(self):
        bar=getattr(self.owner,'_colorbar_artist',None)
        return getattr(bar._tickaxis,self.name+'axis') if bar is not None else self
    def _bar(self):return getattr(self.owner,'bar',None)
    def _detach_labels(self,minor=False):
        from .components import _detach_texts
        bar=self._bar()
        labels=(getattr(bar,'_minor_ticklabels' if minor else '_ticklabels') if bar is not None else
                getattr(self.owner,'_minor_tick_labels' if minor else '_tick_labels')[self.name])
        _detach_texts(labels)
    def _changed(self):
        bar=self._bar()
        if bar is not None:bar._changed()
        elif hasattr(self.owner,'_changed'):self.owner._changed()
    def _sync_shared(self,*,minor=False,locator=False):
        if self._bar() is None and hasattr(self.owner,'_shared_axes') and not getattr(self.owner,'_initializing_components',False):
            from .shared_axes import sync_tickers
            sync_tickers(self.owner,self.name,minor=minor,locator=locator)
    def get_view_interval(self):
        target=self._target()
        if target is not self:return target.get_view_interval()
        bar=self._bar()
        return bar._view_interval() if bar is not None else self.owner.get_xlim() if self.name=='x' else self.owner.get_ylim()
    def get_tick_space(self):
        pixels=self._pixels or 500
        group=getattr(self.owner,'_shared_axes',{}).get(self.name)
        if group is not None and len(group.members)>1 and self.owner.figure is not None:
            # Shared automatic tickers use their owning axes' nominal map area,
            # independent of composition order or old per-render pixel caches.
            from .viewport import Viewport
            ax=self.owner;fig=ax.figure
            width=ax.position[2]*fig.figsize[0]*100;height=ax.position[3]*fig.figsize[1]*100
            vp=Viewport(ax.projection,ax._get_extent(),(0,0,width,height))
            a,b,c,d=vp.projected_bounds
            pixels=((c-a) if self.name=='x' else (d-b))*vp.scale
        return max(2,int(pixels/(65 if self.name=='x' else 42)))
    def get_scale(self):
        target=self._target()
        if target is not self:return target.get_scale()
        from .colors import LogNorm
        bar=self._bar()
        return 'log' if bar is not None and isinstance(bar.norm,LogNorm) else 'linear'
    def get_major_locator(self):
        target=self._target();bar=target._bar()
        if bar is not None:bar._sync_tickers()
        return target._locator
    def set_major_locator(self,locator):
        target=self._target()
        if target is not self:return target.set_major_locator(locator)
        if not isinstance(locator,Locator):raise TypeError('Expected an Azimlib Locator')
        bar=self._bar()
        if bar is not None and self is not bar._long_axis:raise ValueError('Only the colorbar long axis supports tick editing')
        if bar is not None:bar._sync_tickers()
        locator.set_axis(self);self._locator=locator;self.locator_explicit=True
        self._detach_labels()
        if bar is not None:bar._ticks=bar._ticklabels=None
        else:self.owner._ticks[self.name]=self.owner._tick_labels[self.name]=None
        self._sync_shared(locator=True)
        self._changed()
    def get_major_formatter(self):
        target=self._target();bar=target._bar()
        if bar is not None:bar._sync_tickers()
        return target._formatter
    def set_major_formatter(self,formatter):
        target=self._target()
        if target is not self:return target.set_major_formatter(formatter)
        formatter=as_formatter(formatter)
        bar=self._bar()
        if bar is not None and self is not bar._long_axis:raise ValueError('Only the colorbar long axis supports tick editing')
        if bar is not None:bar._sync_tickers()
        if isinstance(formatter,FixedFormatter) and not isinstance(self._locator,FixedLocator):warnings.warn('FixedFormatter should be used with FixedLocator',UserWarning,stacklevel=2)
        formatter.set_axis(self);self._formatter=formatter;self.formatter_explicit=True
        self._detach_labels()
        if bar is not None:bar._ticklabels=None
        else:self.owner._tick_labels[self.name]=None
        self._sync_shared()
        self._changed()
    def get_majorticklocs(self):
        target=self._target()
        if target is not self:return target.get_majorticklocs()
        bar=self._bar()
        if bar is not None:return bar.get_ticks() if self is bar._long_axis else self._locator()
        if self._pixels is None and getattr(self.owner,'figure',None):return self.owner._get_ticks(self.name)
        from .render_map import axis_tick_values
        return axis_tick_values(self.owner,self.name,self._pixels or 500)
    def get_minor_locator(self):
        target=self._target();bar=target._bar()
        if bar is not None:bar._sync_tickers()
        return target._minor_locator
    def set_minor_locator(self,locator):
        target=self._target()
        if target is not self:return target.set_minor_locator(locator)
        if not isinstance(locator,Locator):raise TypeError('Expected an Azimlib Locator')
        bar=self._bar()
        if bar is not None and self is not bar._long_axis:raise ValueError('Only the colorbar long axis supports tick editing')
        if bar is not None:bar._sync_tickers()
        locator.set_axis(self);self._minor_locator=locator;self.minor_locator_explicit=True
        self._detach_labels(minor=True)
        if bar is not None:bar._minor_ticks=bar._minor_ticklabels=None
        else:self.owner._minor_ticks[self.name]=self.owner._minor_tick_labels[self.name]=None
        self._sync_shared(minor=True,locator=True)
        self._changed()
    def get_minor_formatter(self):
        target=self._target();bar=target._bar()
        if bar is not None:bar._sync_tickers()
        return target._minor_formatter
    def set_minor_formatter(self,formatter):
        target=self._target()
        if target is not self:return target.set_minor_formatter(formatter)
        formatter=as_formatter(formatter);bar=self._bar()
        if bar is not None and self is not bar._long_axis:raise ValueError('Only the colorbar long axis supports tick editing')
        if bar is not None:bar._sync_tickers()
        if isinstance(formatter,FixedFormatter) and not isinstance(self._minor_locator,FixedLocator):warnings.warn('FixedFormatter should be used with FixedLocator',UserWarning,stacklevel=2)
        formatter.set_axis(self);self._minor_formatter=formatter;self.minor_formatter_explicit=True
        self._detach_labels(minor=True)
        if bar is not None:bar._minor_ticklabels=None
        else:self.owner._minor_tick_labels[self.name]=None
        self._sync_shared(minor=True)
        self._changed()
    def get_minorticklocs(self):
        target=self._target()
        if target is not self:return target.get_minorticklocs()
        minor=tuple(self.get_minor_locator()())
        if not minor:return ()
        if not self.remove_overlapping_locs:return tuple(minor)
        import math
        transform=math.log10 if self.get_scale()=='log' else float
        low,high=self.get_view_interval();tolerance=abs(transform(high)-transform(low))*1e-5
        major=[transform(v) for v in self.get_majorticklocs() if self.get_scale()!='log' or v>0]
        return tuple(v for v in minor if (self.get_scale()!='log' or v>0) and not any(abs(transform(v)-m)<=tolerance for m in major))
    def set_ticks(self,ticks,labels=None,*,minor=False,**kwargs):
        return self.owner.set_xticks(ticks,labels,minor=minor,**kwargs) if self.name=='x' else self.owner.set_yticks(ticks,labels,minor=minor,**kwargs)
    def set_tick_params(self,**kwargs):return self.owner.tick_params(axis=self.name,**kwargs)
    def get_offset_text(self):return self._target().offsetText
    def _export_ticks(self,degrees=False,*,minor=False):
        """Small portable subset; never serialize or execute Python callbacks."""
        from . import ticker as t
        locator=self._minor_locator if minor else self._locator
        formatter=self._minor_formatter if minor else self._formatter
        if type(locator) is t.MultipleLocator:loc=dict(kind='multiple',base=locator.base,offset=locator.offset)
        elif type(locator) is t.FixedLocator:loc=dict(kind='fixed',values=locator.locs)
        elif type(locator) is t.NullLocator:loc=dict(kind='fixed',values=[])
        elif type(locator) is t.AutoLocator:loc=dict(kind='auto')
        elif type(locator) is t.AutoMinorLocator:
            from .config import rcParams
            loc=dict(kind='auto_minor',ndivs=locator.ndivs if locator.ndivs is not None else rcParams[self.name+'tick.minor.ndivs'])
        else:return None
        if degrees and not minor and not self.formatter_explicit:formatter=t.LongitudeFormatter(dateline_direction_label=True) if self.name=='x' else t.LatitudeFormatter()
        if type(formatter) in (t.LongitudeFormatter,t.LatitudeFormatter):
            import re
            if formatter.number_format!='g' and not re.fullmatch(r'\.\d+[feg]',formatter.number_format):return None
            if formatter.number_format!='g' and int(formatter.number_format[1:-1])>20:return None
            fmt=dict(kind='longitude' if type(formatter) is t.LongitudeFormatter else 'latitude',
                     **{key:getattr(formatter,key) for key in ('direction_label','degree_symbol','number_format','dms','zero_direction_label','dateline_direction_label')})
        elif type(formatter) is t.ScalarFormatter:
            if formatter.get_offset() or formatter.get_useLocale():return None
            from .config import rcParams
            fmt=dict(kind='scalar',precision=formatter._digits,unicode_minus=rcParams['axes.unicode_minus'])
        elif type(formatter) is t.NullFormatter:fmt=dict(kind='null')
        elif type(formatter) is t.FixedFormatter:
            labels=getattr(self.owner,'_minor_tick_labels' if minor else '_tick_labels',{}).get(self.name)
            fmt=dict(kind='fixed',labels=[a.text if a.visible else '' for a in labels] if labels is not None else formatter.seq)
        else:return None
        from .typography import _export_metrics
        from .styles import text_style
        characters='0123456789.eE+-−°′″ NSEW'+''.join(fmt.get('labels',[]))
        return dict(locator=loc,formatter=fmt,metrics=_export_metrics(characters,text_style({})))
