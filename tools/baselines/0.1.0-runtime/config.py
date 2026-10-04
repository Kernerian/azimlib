"""Validated plotting defaults, independent of any plotting framework."""
from collections import UserDict
from contextlib import contextmanager
from copy import deepcopy
import math
from .cycles import cycler,prepare_cycle,AZIM10

DEFAULTS={
    'figure.figsize':(6.4,4.8),'figure.dpi':100,'figure.facecolor':'white',
    'figure.titlesize':'large','figure.titleweight':'normal',
    'figure.labelsize':'large','figure.labelweight':'normal',
    'axes.facecolor':'white','axes.edgecolor':'black','axes.linewidth':.8,
    'axes.grid':False,'axes.axisbelow':'line',
    'axes.xmargin':.05,'axes.ymargin':.05,
    'axes.titlesize':12,'axes.labelsize':10,'axes.labelcolor':'black','axes.labelpad':4.,
    'axes.titlelocation':'center','axes.titlepad':6.,
    'axes.prop_cycle':cycler(color=AZIM10),
    'axes.unicode_minus':True,'axes.formatter.useoffset':True,
    'axes.formatter.limits':(-5,6),'axes.formatter.offset_threshold':4,
    'axes.formatter.use_locale':False,'axes.formatter.use_mathtext':False,
    'font.family':'DejaVu Sans','font.size':10,'text.color':'black',
    'lines.linewidth':1.5,'lines.markersize':6,
    'grid.color':'#b0b0b0','grid.linewidth':.8,'grid.linestyle':'-','grid.alpha':1,
    'xtick.labelsize':10,'ytick.labelsize':10,'legend.fontsize':10,'legend.loc':'best',
    'legend.facecolor':'inherit','legend.edgecolor':'#cccccc','legend.framealpha':.8,
    **{axis+'tick.minor.'+key:value for axis in ('x','y') for key,value in
       (('visible',False),('size',2.),('width',.6),('pad',3.4),('ndivs','auto'))},
    'axes.grid.which':'major','axes.grid.axis':'both',
    'keymap.home':['h','r','home'],'keymap.back':['left','c','backspace','MouseButton.BACK'],
    'keymap.forward':['right','v','MouseButton.FORWARD'],'keymap.pan':['p'],'keymap.zoom':['o'],
    'keymap.save':['s','ctrl+s'],'keymap.fullscreen':['f','ctrl+f'],
    'keymap.quit':['ctrl+w','cmd+w','q'],'keymap.grid':['g'],'keymap.grid_minor':['G'],
}

class RcParams(UserDict):
    def __setitem__(self,key,value):
        if key not in DEFAULTS:raise KeyError(f'Unsupported rcParam: {key}')
        reference=DEFAULTS[key]
        if key=='axes.prop_cycle':value=prepare_cycle(value)
        elif key.startswith('keymap.'):
            if isinstance(value,str):value=[item.strip() for item in value.split(',') if item.strip()]
            else:
                try:value=list(value)
                except TypeError as exc:raise ValueError(f'{key} requires a list of key strings') from exc
            if any(not isinstance(item,str) for item in value):raise ValueError(f'{key} requires key strings')
        elif key in ('axes.grid','axes.unicode_minus','axes.formatter.useoffset','axes.formatter.use_locale','axes.formatter.use_mathtext') or key.endswith('.minor.visible'):
            if not isinstance(value,bool):raise ValueError(f'{key} requires a boolean')
            if key=='axes.formatter.use_mathtext' and value:raise NotImplementedError('MathText typesetting is not yet supported')
        elif key=='axes.formatter.limits':
            value=tuple(value)
            if len(value)!=2 or any(not isinstance(v,int) or isinstance(v,bool) or abs(v)>300 for v in value):raise ValueError('Formatter limits require two integer exponents within [-300,300]')
        elif key=='axes.formatter.offset_threshold':
            if not isinstance(value,int) or isinstance(value,bool) or value<1:raise ValueError('Offset threshold requires a positive integer')
        elif key.endswith('.minor.ndivs'):
            if value!='auto' and (not isinstance(value,int) or isinstance(value,bool) or value<1):raise ValueError('minor.ndivs requires auto or a positive integer')
        elif key in ('axes.grid.which','axes.grid.axis'):
            if value not in (('major','minor','both') if key.endswith('which') else ('x','y','both')):raise ValueError(f'Invalid {key}')
        elif key in ('axes.xmargin','axes.ymargin'):
            value=float(value)
            if not math.isfinite(value) or value<=-.5:raise ValueError('Margin must be finite and greater than -0.5')
        elif key=='axes.axisbelow':
            if value is not True and value is not False and value!='line':raise ValueError("axes.axisbelow: True, False, or 'line'")
        elif key in ('figure.titlesize','figure.labelsize'):
            if isinstance(value,str) and value in ('xx-small','x-small','small','medium','large','x-large','xx-large','larger','smaller'):pass
            else:
                value=float(value)
                if not math.isfinite(value) or value<=0:raise ValueError(f'{key} must be a positive font size')
        elif key=='legend.loc':
            from .legend_layout import canonical_loc
            value=canonical_loc(value)
        elif key=='axes.titlelocation':
            if value not in ('left','center','right'):raise ValueError('axes.titlelocation: left, center or right')
        elif key in ('axes.titlepad','axes.labelpad'):
            value=float(value)
            if not math.isfinite(value):raise ValueError(f'{key} must be finite')
        elif isinstance(reference,(int,float)):
            value=float(value)
            if not math.isfinite(value) or value<0:raise ValueError(f'{key} must be finite and nonnegative')
            if (key.endswith('size') and not key.endswith('.minor.size') or key=='figure.dpi') and value==0:raise ValueError(f'{key} must be positive')
            if key in ('grid.alpha','legend.framealpha') and value>1:raise ValueError(f'{key} must lie in [0,1]')
        elif key=='figure.figsize':
            value=tuple(float(v) for v in value)
            if len(value)!=2 or any(not math.isfinite(v) or v<=0 for v in value):raise ValueError('Invalid figure.figsize')
        elif not isinstance(value,str):raise TypeError(f'{key} requires a string')
        self.data[key]=value
    def update(self,other=(),**kwargs):
        validated=RcParams.__new__(RcParams);validated.data={}
        for key,value in dict(other,**kwargs).items():validated[key]=value
        self.data.update(validated.data)

rcParams=RcParams(DEFAULTS)

def rcdefaults():rcParams.update(deepcopy(DEFAULTS))

def rc(group,**kwargs):
    groups=(group,) if isinstance(group,str) else tuple(group)
    rcParams.update({f'{g}.{key}':value for g in groups for key,value in kwargs.items()})

@contextmanager
def rc_context(rc=None):
    previous=deepcopy(rcParams.data)
    try:
        if rc is not None:rcParams.update(rc)
        yield
    finally:
        rcParams.data=previous
