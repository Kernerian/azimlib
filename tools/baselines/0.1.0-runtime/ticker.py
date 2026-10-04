"""Own tick placement and formatting objects with familiar plotting contracts.

Coordinates remain geographic degrees. LogLocator is useful on colorbars;
it does not make a geographic axis logarithmic.
"""
import math

def _finite(values):
    result=tuple(float(v) for v in values)
    if any(not math.isfinite(v) for v in result):raise ValueError('Values must be finite')
    return result

class TickHelper:
    axis=None
    def set_axis(self,axis):
        if self.axis is not None and self.axis is not axis:
            old=self.axis;group=getattr(getattr(old,'owner',None),'_shared_axes',{}).get(getattr(old,'name',None))
            if getattr(old,'name',None)!=getattr(axis,'name',None) or group is None or not group.joined or getattr(axis,'owner',None) not in group.members:
                raise ValueError('Use a separate ticker object for each independent axis')
        self.axis=axis

class Locator(TickHelper):
    MAXTICKS=1500
    def __call__(self):
        if self.axis is None:raise RuntimeError('Locator is not attached to an axis; use tick_values')
        return self.tick_values(*self.axis.get_view_interval())
    def tick_values(self,vmin,vmax):raise NotImplementedError
    def raise_if_exceeds(self,locs):
        if len(locs)>self.MAXTICKS:raise ValueError('Locator creates too many ticks')
        return tuple(locs)

class FixedLocator(Locator):
    def __init__(self,locs):self.locs=_finite(locs);self.raise_if_exceeds(self.locs)
    def tick_values(self,vmin,vmax):return self.locs

class NullLocator(Locator):
    def tick_values(self,vmin,vmax):return ()

class MultipleLocator(Locator):
    def __init__(self,base=1.,offset=0.):self.set_params(base=base,offset=offset)
    def set_params(self,*,base=None,offset=None):
        base=getattr(self,'base',1.) if base is None else float(base)
        offset=getattr(self,'offset',0.) if offset is None else float(offset)
        if not math.isfinite(base) or base<=0 or not math.isfinite(offset):raise ValueError('base must be positive and offset finite')
        self.base,self.offset=base,offset
    def tick_values(self,vmin,vmax):
        low,high=sorted(_finite((vmin,vmax)))
        start=math.floor((low-self.offset)/self.base+1e-12)
        stop=math.ceil((high-self.offset)/self.base-1e-12)
        if abs(low-(self.offset+start*self.base))<self.base*1e-10:start-=1
        if abs(high-(self.offset+stop*self.base))<self.base*1e-10:stop+=1
        if stop-start+1>self.MAXTICKS:raise ValueError('Locator creates too many ticks')
        return tuple(self.offset+i*self.base for i in range(start,stop+1))

class MaxNLocator(Locator):
    """Choose a decimal step for at most nbins intervals, including outer ticks."""
    def __init__(self,nbins=10,*,steps=None,integer=False,prune=None):
        self.set_params(nbins=nbins,steps=(1,1.5,2,2.5,3,4,5,6,8,10) if steps is None else steps,integer=integer,prune=prune)
    def set_params(self,**kwargs):
        allowed={'nbins','steps','integer','prune'}
        if set(kwargs)-allowed:raise TypeError('Unsupported locator parameter')
        values=dict(nbins=getattr(self,'nbins',10),steps=getattr(self,'steps',(1,2,5,10)),integer=getattr(self,'integer',False),prune=getattr(self,'prune',None))
        values.update(kwargs)
        if values['nbins']!='auto' and (not isinstance(values['nbins'],int) or isinstance(values['nbins'],bool) or values['nbins']<1):raise ValueError('nbins must be a positive integer or auto')
        steps=_finite(values['steps'])
        if not steps or any(a>=b for a,b in zip(steps,steps[1:])) or steps[0]<1 or steps[-1]>10:raise ValueError('steps must increase within [1,10]')
        if values['prune'] not in (None,'lower','upper','both'):raise ValueError('Invalid prune')
        self.nbins=values['nbins'];self.steps=tuple(sorted(set((1.,*steps,10.))))
        self.integer=bool(values['integer']);self.prune=values['prune']
    def tick_values(self,vmin,vmax):
        low,high=sorted(_finite((vmin,vmax)))
        if low==high:
            delta=abs(low)*.001 or .001;low-=delta;high+=delta
        nbins=max(2,min(9,self.axis.get_tick_space())) if self.nbins=='auto' and self.axis is not None else 9 if self.nbins=='auto' else self.nbins
        if nbins>self.MAXTICKS:raise ValueError('Locator creates too many ticks')
        target=(high-low)/nbins;power=10.**math.floor(math.log10(target))
        step=next(s*power for s in self.steps if s*power>=target*(1-1e-12))
        if self.integer and high-low>=1:step=max(1.,math.ceil(step))
        first=math.floor(low/step+1e-10);last=math.ceil(high/step-1e-10)
        if last-first+1>self.MAXTICKS:raise ValueError('Locator creates too many ticks')
        ticks=tuple(0. if abs(i*step)<step*1e-10 else i*step for i in range(first,last+1))
        if self.prune in ('lower','both'):ticks=ticks[1:]
        if self.prune in ('upper','both'):ticks=ticks[:-1]
        return ticks

class AutoLocator(MaxNLocator):
    def __init__(self):super().__init__('auto',steps=(1,2,2.5,5,10))

class AutoMinorLocator(Locator):
    """Subdivide evenly spaced major ticks on a linear axis; n is intervals."""
    def __init__(self,n=None):
        if n is not None and n!='auto' and (not isinstance(n,int) or isinstance(n,bool) or n<1):raise ValueError('n must be a positive integer, auto, or None')
        self.ndivs=n
    def __call__(self):
        if self.axis is None:raise RuntimeError('AutoMinorLocator needs an axis')
        if self.axis.get_scale()=='log':
            import warnings
            warnings.warn('AutoMinorLocator does not work on logarithmic scales',UserWarning,stacklevel=2)
            return ()
        major=sorted(set(self.axis.get_majorticklocs()))
        if len(major)<2:return ()
        step=major[1]-major[0]
        n=self.ndivs
        if n is None:
            from .config import rcParams
            n=rcParams[self.axis.name+'tick.minor.ndivs']
        if n=='auto':
            mantissa=step/10.**math.floor(math.log10(step))
            n=5 if any(math.isclose(mantissa,v,rel_tol=1e-5) for v in (1,2.5,5,10)) else 4
        spacing=step/n;low,high=sorted(self.axis.get_view_interval());origin=major[0]
        first=round((low-origin)/spacing);last=round((high-origin)/spacing)
        if last-first+1>self.MAXTICKS:raise ValueError('Locator creates too many ticks')
        return self.raise_if_exceeds(tuple(origin+i*spacing for i in range(first,last+1)))
    def tick_values(self,vmin,vmax):raise NotImplementedError('AutoMinorLocator needs major ticks from an axis')

class LogLocator(Locator):
    def __init__(self,base=10.,subs=(1.,)):
        self.base=float(base);self.subs=_finite(subs)
        if not math.isfinite(self.base) or self.base<=1 or not self.subs or min(self.subs)<=0:raise ValueError('Invalid logarithmic locator')
    def tick_values(self,vmin,vmax):
        low,high=sorted(_finite((vmin,vmax)))
        if low<=0:raise ValueError('LogLocator needs positive limits')
        low_exp=math.log10(low)/math.log10(self.base);high_exp=math.log10(high)/math.log10(self.base)
        is_minor=len(self.subs)>1 or self.subs[0]!=1
        first=math.ceil(low_exp)-1 if is_minor else math.floor(low_exp)-1
        last=math.floor(high_exp) if is_minor else math.ceil(high_exp)+1
        if (last-first+1)*len(self.subs)>self.MAXTICKS:raise ValueError('Locator creates too many ticks')
        return self.raise_if_exceeds(sorted(set(s*self.base**i for i in range(first,last+1) for s in self.subs)))

class Formatter(TickHelper):
    locs=()
    def __call__(self,x,pos=None):raise NotImplementedError
    def set_locs(self,locs):self.locs=_finite(locs)
    def format_ticks(self,values):
        self.set_locs(values);return [str(self(x,i)) for i,x in enumerate(values)]
    def format_data(self,value):return str(self(value))
    def format_data_short(self,value):return self.format_data(value)
    def get_offset(self):return ''
    @staticmethod
    def fix_minus(text):
        from .config import rcParams
        return str(text).replace('-','−') if rcParams['axes.unicode_minus'] else str(text)

class ScalarFormatter(Formatter):
    """Common precision, decimal scientific scaling and an additive offset.

    All calculations and text are our own. TeX/MathText typesetting is not
    implemented; locale formatting uses Python's current numeric locale.
    """
    def __init__(self,useOffset=None,useMathText=None,useLocale=None,*,usetex=None):
        from .config import rcParams
        self.locs=();self.offset=0.;self.orderOfMagnitude=0;self._digits=0
        self._scientific=True;self._powerlimits=tuple(rcParams['axes.formatter.limits'])
        self._offset_threshold=rcParams['axes.formatter.offset_threshold']
        self.set_useMathText(rcParams['axes.formatter.use_mathtext'] if useMathText is None else useMathText)
        self.set_usetex(False if usetex is None else usetex)
        self.set_useLocale(rcParams['axes.formatter.use_locale'] if useLocale is None else useLocale)
        self.set_useOffset(rcParams['axes.formatter.useoffset'] if useOffset is None else useOffset)
    def _changed(self):
        if self.axis is not None:
            self.axis.formatter_explicit=True
            if hasattr(self.axis,'_sync_shared'):self.axis._sync_shared()
            self.axis._changed()
    def set_useOffset(self,value):
        if isinstance(value,bool):automatic=value;offset=0.
        else:
            offset=float(value);automatic=False
            if not math.isfinite(offset):raise ValueError('Offset must be finite')
        self._useOffset=automatic;self.offset=offset;self._changed()
    def get_useOffset(self):return self._useOffset
    def set_scientific(self,value):self._scientific=bool(value);self._changed()
    def set_powerlimits(self,lims):
        values=tuple(lims)
        if len(values)!=2 or any(not isinstance(v,int) or isinstance(v,bool) for v in values):raise ValueError('Power limits must contain two integer exponents')
        if any(abs(v)>300 for v in values):raise ValueError('Power limits must lie within [-300,300]')
        self._powerlimits=values;self._changed()
    def set_useLocale(self,value):self._useLocale=bool(value);self._changed()
    def get_useLocale(self):return self._useLocale
    def set_useMathText(self,value):
        if value:raise NotImplementedError('Azimlib does not yet typeset MathText; use plain scientific notation')
        self._useMathText=False;self._changed()
    def get_useMathText(self):return self._useMathText
    def set_usetex(self,value):
        if value:raise NotImplementedError('Azimlib does not use a TeX renderer')
        self._usetex=False;self._changed()
    def get_usetex(self):return self._usetex
    def _number(self,value,spec):
        text=format(value,spec)
        if self._useLocale:
            import locale
            text=locale.format_string('%'+spec,value,grouping=True)
        return self.fix_minus(text)
    def set_locs(self,locs):
        self.locs=_finite(locs);self.orderOfMagnitude=0;self._digits=0
        if self._useOffset:self.offset=0.
        if not self.locs:return
        low,high=sorted(self.axis.get_view_interval()) if self.axis is not None else (min(self.locs),max(self.locs))
        visible=[v for v in self.locs if low<=v<=high]
        if self._useOffset and len(set(visible))>1 and not min(visible)<=0<=max(visible):
            a,b=sorted((abs(min(visible)),abs(max(visible))))
            exponent=math.ceil(math.log10(b))
            while exponent>-300 and math.floor(a/10.**exponent)==math.floor(b/10.**exponent):exponent-=1
            quantum=10.**(exponent+1)
            if (b-a)/quantum<=.01:
                exponent=math.ceil(math.log10(b))
                while exponent>-300 and math.floor(b/10.**exponent)-math.floor(a/10.**exponent)<=1:exponent-=1
                quantum=10.**(exponent+1)
            prefix=math.floor(b/quantum)
            if prefix>=10**(self._offset_threshold-1):self.offset=math.copysign(prefix*quantum,min(visible))
        if self._scientific:
            lower,upper=self._powerlimits
            if lower==upper!=0:self.orderOfMagnitude=lower
            elif visible:
                magnitude=high-low if self.offset else max(abs(v) for v in visible)
                exponent=math.floor(math.log10(magnitude)) if magnitude else 0
                if exponent<=lower or exponent>=upper:self.orderOfMagnitude=exponent
        scaled=[(v-self.offset)/10.**self.orderOfMagnitude for v in self.locs]
        endpoints=scaled if len(scaled)>1 else scaled+[(v-self.offset)/10.**self.orderOfMagnitude for v in (low,high)]
        span=max(endpoints)-min(endpoints) or max(map(abs,endpoints)) or 1.
        exponent=math.floor(math.log10(span));tolerance=1e-3*10.**exponent
        for digits in range(max(0,3-exponent)+1):
            if all(abs(v-round(v,digits))<tolerance for v in scaled):
                self._digits=digits;break
        else:self._digits=max(0,3-exponent)
    def __call__(self,x,pos=None):
        x=float(x)
        if not math.isfinite(x):raise ValueError('Tick must be finite')
        if not self.locs:return self._number(x,'g')
        value=(x-self.offset)/10.**self.orderOfMagnitude
        if abs(value)<1e-8:value=0.
        return self._number(value,f'.{self._digits}f')
    def format_data(self,value):
        value=float(value)
        if not math.isfinite(value):raise ValueError('Value must be finite')
        if not value:return '0'
        exponent=math.floor(math.log10(abs(value)));mantissa=round(value/10.**exponent,10)
        return self._number(mantissa,'.10g')+(self.fix_minus(f'e{exponent}') if exponent else '')
    def format_data_short(self,value):return self._number(float(value),'.12g')
    def get_offset(self):
        if not self.locs:return ''
        scale=self.fix_minus(f'1e{self.orderOfMagnitude}') if self.orderOfMagnitude else ''
        shift=('+' if self.offset>0 else '')+self.format_data(self.offset) if self.offset else ''
        return scale+shift

class EngFormatter(Formatter):
    """SI prefixes for quantities such as distances and population counts."""
    ENG_PREFIXES=dict(zip(range(-30,31,3),('q','r','y','z','a','f','p','n','µ','m','','k','M','G','T','P','E','Z','Y','R','Q')))
    def __init__(self,unit='',places=None,sep=' ',*,usetex=None,useMathText=None,useOffset=False):
        if usetex or useMathText:raise NotImplementedError('Engineering labels currently use plain text')
        if useOffset:raise NotImplementedError('Engineering offsets are not yet supported; use ScalarFormatter')
        if places is not None and (not isinstance(places,int) or isinstance(places,bool) or places<0 or places>30):raise ValueError('places must be a nonnegative integer up to 30, or None')
        self.unit=str(unit);self.places=places;self.sep=str(sep)
    def format_eng(self,value):
        value=float(value)
        if not math.isfinite(value):raise ValueError('Value must be finite')
        exponent=max(-30,min(30,3*math.floor(math.log10(abs(value))/3))) if value else 0
        mantissa=value/10.**exponent;spec='g' if self.places is None else f'.{self.places}f'
        if abs(float(format(mantissa,spec)))>=1000 and exponent<30:mantissa/=1000;exponent+=3
        suffix=self.ENG_PREFIXES[exponent]
        return self.fix_minus(format(mantissa,spec))+self.sep+suffix
    def __call__(self,x,pos=None):
        text=self.format_eng(x)+self.unit
        return text[:-len(self.sep)] if self.sep and not self.unit and text.endswith(self.sep) else text

class NullFormatter(Formatter):
    def __call__(self,x,pos=None):return ''

class FixedFormatter(Formatter):
    def __init__(self,seq):self.seq=tuple(str(v) for v in seq)
    def __call__(self,x,pos=None):return self.seq[pos] if pos is not None and 0<=pos<len(self.seq) else ''

class FuncFormatter(Formatter):
    def __init__(self,func):
        if not callable(func):raise TypeError('Formatter needs a callable (value, position)')
        self.func=func
    def __call__(self,x,pos=None):return str(self.func(x,pos))

class FormatStrFormatter(Formatter):
    def __init__(self,fmt):self.fmt=str(fmt)
    def __call__(self,x,pos=None):return self.fmt%x

class StrMethodFormatter(Formatter):
    def __init__(self,fmt):self.fmt=str(fmt)
    def __call__(self,x,pos=None):return self.fmt.format(x=x,pos=pos)

class _DegreeFormatter(Formatter):
    def __init__(self,*,direction_label=True,degree_symbol='°',number_format='g',dms=False,
                 zero_direction_label=False,dateline_direction_label=False):
        self.direction_label=bool(direction_label);self.degree_symbol=str(degree_symbol)
        self.number_format=str(number_format);format(1.,self.number_format)
        self.dms=bool(dms);self.zero_direction_label=bool(zero_direction_label)
        self.dateline_direction_label=bool(dateline_direction_label)
    def __call__(self,x,pos=None):
        x=float(x)
        if not math.isfinite(x):raise ValueError('Coordinate must be finite')
        suffix=self.negative if math.copysign(1.,x)<0 else self.positive
        if x==0 and not self.zero_direction_label:suffix=''
        if self.bound==180 and abs(x)==180 and not self.dateline_direction_label:suffix=''
        value=abs(x) if self.direction_label else x
        if self.dms:
            seconds=round(abs(value)*3600,3);degrees=int(seconds//3600)
            minutes=int((seconds-degrees*3600)//60);seconds=seconds-degrees*3600-minutes*60
            text=f'{degrees}{self.degree_symbol}'
            if minutes or seconds:text+=f'{minutes}′'
            if seconds:text+=f'{seconds:g}″'
            if value<0:text='−'+text
        else:text=self.fix_minus(format(value,self.number_format))+self.degree_symbol
        return text+(suffix if self.direction_label else '')

class LongitudeFormatter(_DegreeFormatter):
    """Longitude labels with E/W, optionally degrees/minutes/seconds."""
    negative='W';positive='E';bound=180

class LatitudeFormatter(_DegreeFormatter):
    """Latitude labels with N/S, optionally degrees/minutes/seconds."""
    negative='S';positive='N';bound=90

def as_formatter(value):
    if isinstance(value,Formatter):return value
    if isinstance(value,str):return StrMethodFormatter(value)
    if callable(value):return FuncFormatter(value)
    raise TypeError('Expected Formatter, format string or callable (value, position)')

def configure_scalar_axes(owner,*,axis='both',style=None,scilimits=None,useOffset=None,useLocale=None,useMathText=None):
    """Validate all targets and options before touching any live formatter."""
    if axis not in ('x','y','both'):raise ValueError('axis must be x, y or both')
    if style is not None and style not in ('sci','scientific','plain'):raise ValueError('style must be sci, scientific or plain')
    targets=[getattr(owner,name+'axis')._target() for name in ('x','y') if axis in ('both',name)]
    formatters=[target.get_major_formatter() for target in targets]
    if any(not isinstance(fmt,ScalarFormatter) for fmt in formatters):raise AttributeError('ticklabel_format only works with ScalarFormatter')
    options={method:value for method,value in (('set_powerlimits',scilimits),('set_useOffset',useOffset),('set_useLocale',useLocale),('set_useMathText',useMathText)) if value is not None}
    if style is not None:options['set_scientific']=style!='plain'
    candidate=ScalarFormatter()
    for method,value in options.items():getattr(candidate,method)(value)
    for target,fmt in zip(targets,formatters):
        attached=fmt.axis;fmt.axis=None
        try:
            for method,value in options.items():getattr(fmt,method)(value)
        finally:fmt.axis=attached
        target.formatter_explicit=True
        target._sync_shared()
    bar=getattr(owner,'bar',None)
    if bar is not None:bar._changed()
    elif hasattr(owner,'_changed'):owner._changed()
