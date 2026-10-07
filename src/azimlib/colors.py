"""Original scalar mapping implementation with separately credited color tables."""
import math
from numbers import Real
from functools import lru_cache
from pathlib import Path
import json
from .styles import PALETTES,sample_color
from .callbacks import CallbackRegistry

class Normalize:
    def __init__(self,vmin=None,vmax=None,clip=False):
        self.callbacks=CallbackRegistry(('changed',))
        self._vmin=self._limit(vmin);self._vmax=self._limit(vmax);self._clip=bool(clip)
        self._validate()
    @staticmethod
    def _limit(value):
        value=None if value is None else float(value)
        if value is not None and not math.isfinite(value):raise ValueError('Limits must be finite')
        return value
    @property
    def vmin(self):return self._vmin
    @vmin.setter
    def vmin(self,value):
        value=self._limit(value)
        if value!=self._vmin:self._vmin=value;self._changed()
    @property
    def vmax(self):return self._vmax
    @vmax.setter
    def vmax(self,value):
        value=self._limit(value)
        if value!=self._vmax:self._vmax=value;self._changed()
    @property
    def clip(self):return self._clip
    @clip.setter
    def clip(self,value):
        value=bool(value)
        if value!=self._clip:self._clip=value;self._changed()
    def _changed(self):self.callbacks.process('changed')
    def scaled(self):return self.vmin is not None and self.vmax is not None
    def _set_limits(self,low,high,*,force=False):
        """Commit an interval before notifying listeners (also for set_clim)."""
        low,high=self._limit(low),self._limit(high)
        if low is not None and high is not None and low>high:raise ValueError('vmin must not exceed vmax')
        changed=(low,high)!=(self._vmin,self._vmax)
        self._vmin,self._vmax=low,high
        if changed or force:self._changed()
    def _validate(self):
        for v in (self.vmin,self.vmax):
            if v is not None and not math.isfinite(v):raise ValueError('Limits must be finite')
        if self.vmin is not None and self.vmax is not None and self.vmin>self.vmax:raise ValueError('vmin must not exceed vmax')
    def autoscale_None(self,values):
        valid=[float(v) for v in values if v is not None and math.isfinite(float(v))]
        if not valid:return
        low=self.vmin if self.vmin is not None else min(valid)
        high=self.vmax if self.vmax is not None else max(valid)
        self._set_limits(low,high)
    def autoscale(self,values):
        with self.callbacks.blocked():
            self._vmin=self._vmax=None
            self.autoscale_None(values)
        self._changed()
    def __call__(self,value,clip=None):
        if value is None:return None
        if not isinstance(value,Real):
            value=list(value);self.autoscale_None(value)
            return [self(v,clip=clip) for v in value]
        if not math.isfinite(value):return None
        self.autoscale_None([value]);self._validate()
        t=(value-self.vmin)/(self.vmax-self.vmin) if self.vmax!=self.vmin else 0.
        return max(0.,min(1.,t)) if (self.clip if clip is None else clip) else t
    def inverse(self,value):
        if self.vmin is None or self.vmax is None:raise ValueError('Normalizer has not been scaled')
        return self.vmin+value*(self.vmax-self.vmin)

class NoNorm(Normalize):
    """Identity mapping for explicit colormap indices; finite scalars/lists."""
    def __call__(self,value,clip=None):
        if value is None:return None
        if not isinstance(value,Real):return [self(v,clip=clip) for v in value]
        return value if math.isfinite(value) else None
    def inverse(self,value):return value


class LogNorm(Normalize):
    def autoscale_None(self,values):
        super().autoscale_None([v for v in values if v is not None and math.isfinite(float(v)) and float(v)>0])
    def __call__(self,value,clip=None):
        if value is None:return None
        if not isinstance(value,Real):
            value=list(value);self.autoscale_None(value);return [self(v,clip=clip) for v in value]
        if not math.isfinite(value) or value<=0:return None
        self.autoscale_None([value]);self._validate()
        if self.vmin<=0 or self.vmax<=0:raise ValueError('LogNorm needs positive limits')
        t=math.log(value/self.vmin)/math.log(self.vmax/self.vmin) if self.vmin!=self.vmax else 0.
        return max(0.,min(1.,t)) if (self.clip if clip is None else clip) else t
    def inverse(self,value):return self.vmin*(self.vmax/self.vmin)**value

class TwoSlopeNorm(Normalize):
    def __init__(self,vcenter,vmin=None,vmax=None):
        self._vcenter=self._limit(vcenter)
        if self._vcenter is None:raise ValueError('vcenter must be finite')
        super().__init__(vmin,vmax)
    @property
    def vcenter(self):return self._vcenter
    @vcenter.setter
    def vcenter(self,value):
        value=self._limit(value)
        if value is None:raise ValueError('vcenter must be finite')
        if value!=self._vcenter:self._vcenter=value;self._changed()
    def autoscale_None(self,values):
        before=(self.vmin,self.vmax)
        with self.callbacks.blocked():
            super().autoscale_None(values)
            if self.scaled():
                low,high=self.vmin,self.vmax
                if low>=self.vcenter:low=self.vcenter-(high-self.vcenter)
                if high<=self.vcenter:high=self.vcenter+(self.vcenter-low)
                self._set_limits(low,high)
        if before!=(self.vmin,self.vmax):self._changed()
    def __call__(self,value,clip=None):
        if value is None:return None
        if not isinstance(value,Real):
            value=list(value);self.autoscale_None(value);return [self(v,clip=clip) for v in value]
        if not math.isfinite(value):return None
        self.autoscale_None([value]);self._validate()
        if not self.vmin<self.vcenter<self.vmax:raise ValueError('Require vmin < vcenter < vmax')
        if value<self.vmin:return -math.inf
        if value>self.vmax:return math.inf
        return .5*(value-self.vmin)/(self.vcenter-self.vmin) if value<=self.vcenter else .5+.5*(value-self.vcenter)/(self.vmax-self.vcenter)
    def inverse(self,value):
        return self.vmin+2*value*(self.vcenter-self.vmin) if value<=.5 else self.vcenter+2*(value-.5)*(self.vmax-self.vcenter)

class BoundaryNorm(Normalize):
    def __init__(self,boundaries,ncolors=None,clip=False):
        self.boundaries=tuple(float(v) for v in boundaries)
        if len(self.boundaries)<2 or any(not math.isfinite(v) for v in self.boundaries) or any(a>=b for a,b in zip(self.boundaries,self.boundaries[1:])):raise ValueError('Boundaries must be finite and strictly increasing')
        self.ncolors=len(self.boundaries)-1 if ncolors is None else ncolors
        if not isinstance(self.ncolors,int) or isinstance(self.ncolors,bool) or self.ncolors<1:raise ValueError('ncolors must be a positive integer')
        if self.ncolors<len(self.boundaries)-1:raise ValueError('Not enough colors for intervals')
        super().__init__(self.boundaries[0],self.boundaries[-1],clip)
    def __call__(self,value,clip=None):
        if value is None:return None
        if not isinstance(value,Real):return [self(v,clip=clip) for v in value]
        if not math.isfinite(value):return None
        index=sum(value>=v for v in self.boundaries)-1;regions=len(self.boundaries)-1
        if index<0:return 0 if (self.clip if clip is None else clip) else -1
        if index>=regions:return self.ncolors-1 if (self.clip if clip is None else clip) else self.ncolors
        return int(index*(self.ncolors-1)/(regions-1)) if regions>1 else (self.ncolors-1)//2
    def inverse(self,value):raise ValueError('BoundaryNorm has no unique inverse')

class Colormap:
    def __init__(self,name='viridis',colors=None):
        self.name=name;self.colors=tuple(colors or PALETTES.get(name,()))
        if len(self.colors)<2:raise ValueError(f'Unknown or invalid colormap: {name}')
        self.bad='#00000000';self.under=self.colors[0];self.over=self.colors[-1]
    def __call__(self,value):
        if value is None or math.isnan(value):return self.bad
        if value<0:return self.under
        if value>1:return self.over
        return sample_color(self.colors,value)
    def reversed(self,name=None):return Colormap(name or self.name+'_r',self.colors[::-1])
    def set_bad(self,color):self.bad=color
    def set_under(self,color):self.under=color
    def set_over(self,color):self.over=color

class ListedColormap(Colormap):
    def __init__(self,colors,name='from_list'):
        colors=tuple(colors)
        # A single category is useful for a monochromatic contour/colorbar.
        super().__init__(name,colors if len(colors)!=1 else colors*2)
        self.colors=colors;self.N=len(colors)
    def __call__(self,value):
        if value is None:return self.bad
        if isinstance(value,int):
            return self.under if value<0 else self.over if value>=self.N else self.colors[value]
        if math.isnan(value):return self.bad
        if value<0:return self.under
        if value>1:return self.over
        return self.colors[min(self.N-1,int(value*self.N))]
    def reversed(self,name=None):return ListedColormap(self.colors[::-1],name or self.name+'_r')

@lru_cache(maxsize=1)
def _tables():return json.loads((Path(__file__).with_name('data')/'colormaps.json').read_text(encoding='utf-8'))['tables']

def get_cmap(value='viridis'):
    if isinstance(value,Colormap):return value
    if isinstance(value,str):
        if value in _tables():return ListedColormap(_tables()[value],value)
        return get_cmap(value[:-2]).reversed() if value.endswith('_r') else Colormap(value)
    return Colormap('custom',value)

def to_rgba(color,alpha=None):
    """Dependency-free basic CSS/hex or normalized RGB(A) conversion.

    Accept #RGB/#RGBA/#RRGGBB/#RRGGBBAA and the basic HTML color names.
    alpha overrides source alpha; 'none' always stays fully transparent.
    """
    if isinstance(color,str):
        names={'black':'000000','white':'ffffff','red':'ff0000','green':'008000',
               'blue':'0000ff','yellow':'ffff00','cyan':'00ffff','aqua':'00ffff',
               'magenta':'ff00ff','fuchsia':'ff00ff','gray':'808080','grey':'808080',
               'silver':'c0c0c0','maroon':'800000','olive':'808000','lime':'00ff00',
               'teal':'008080','navy':'000080','purple':'800080','orange':'ffa500'}
        color=color.lower().strip()
        if color=='none':return (0.,0.,0.,0.)
        value=names.get(color,color.removeprefix('#'))
        if len(value) in (3,4):value=''.join(v*2 for v in value)
        if len(value) not in (6,8):raise ValueError('Use a basic HTML color or hexadecimal RGB(A)')
        try:values=tuple(int(value[i:i+2],16)/255 for i in range(0,len(value),2))
        except ValueError as exc:raise ValueError('Invalid hexadecimal color') from exc
    else:values=tuple(float(v) for v in color)
    if len(values) not in (3,4) or any(not math.isfinite(v) or not 0<=v<=1 for v in values):raise ValueError('RGBA requires normalized channels')
    result=values[:3]+(values[3] if len(values)==4 else 1.,)
    if alpha is not None:
        alpha=float(alpha)
        if not math.isfinite(alpha) or not 0<=alpha<=1:raise ValueError('alpha must be in [0,1]')
        result=result[:3]+(alpha,)
    return result
