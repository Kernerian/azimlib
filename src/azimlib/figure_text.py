"""Owned text in Figure fractions, independent of projection and backends."""
import math
from .components import TextArtist
from .artist import artist_mutation
from .styles import style_dict,text_style,validate_text_properties


def _position(value):
    value=tuple(float(v) for v in value)
    if len(value)!=2 or not all(math.isfinite(v) for v in value):
        raise ValueError('Text position must be two finite Figure fractions')
    return value


def _options(options):
    options=dict(options)
    for key in ('fontsize','size'):
        if key in options and isinstance(options[key],str):options[key]=label_fontsize(options[key])
    if options.get('rotation') in ('vertical','horizontal'):
        options['rotation']=90 if options['rotation']=='vertical' else 0
    mode=options.pop('rotation_mode',None)
    if mode is not None and mode not in ('default','anchor','xtick','ytick'):
        raise ValueError('Figure text rotation_mode must be default, anchor, xtick or ytick')
    return options,mode


class FigureTextArtist(TextArtist):
    """Editable Figure text; positioned in fractions with y pointing up."""
    def __init__(self,x,y,text='',**kwargs):
        position=_position((x,y));kwargs,mode=_options(kwargs)
        super().__init__(text,**kwargs)
        text_style(self.style)
        self._position=position;self._rotation_mode=mode or 'default';self._autopos=False

    def get_position(self):return self._position
    def get_x(self):return self._position[0]
    def get_y(self):return self._position[1]
    def set_position(self,value):return self.set(position=value)
    def set_x(self,value):return self.set(x=value)
    def set_y(self,value):return self.set(y=value)
    def set_rotation_mode(self,value):return self.set(rotation_mode=value)
    def get_rotation_mode(self):return self._rotation_mode
    def set_horizontalalignment(self,value):return self.set(ha=value)
    def get_horizontalalignment(self):return self.style.get('ha','left')
    def set_verticalalignment(self,value):return self.set(va=value)
    def get_verticalalignment(self):return self.style.get('va','baseline')
    set_ha=set_horizontalalignment;get_ha=get_horizontalalignment
    set_va=set_verticalalignment;get_va=get_verticalalignment

    @artist_mutation
    def set(self,**kwargs):
        options,mode=_options(kwargs)
        if 'rotation_mode' in kwargs and kwargs['rotation_mode'] is None:mode='default'
        position=_position(options.pop('position',self._position))
        position=_position((options.pop('x',position[0]),options.pop('y',position[1])))
        # Validate style/alignment before changing position or any controls.
        raw={k:v for k,v in options.items() if k not in ('text','visible','in_layout')}
        if raw.get('alpha',1) is None:raw.pop('alpha')
        updates=style_dict(raw)
        validate_text_properties(updates)
        text_style(dict(self.style,**updates))
        self._position=position
        if mode is not None:self._rotation_mode=mode
        return super().set(**options)

    def _scene_text(self,width,height):
        x,y=self._position;x*=width;y=(1-y)*height
        style=text_style(self.style)
        style['rotation_mode']=self._rotation_mode
        return x,y,style


def label_fontsize(value):
    """Resolve Figure rc font sizes relative to the configured base font."""
    from .config import rcParams
    factors={'xx-small':.579,'x-small':.694,'small':.833,'medium':1.,
             'large':1.2,'x-large':1.44,'xx-large':1.728,'larger':1.2,'smaller':.833}
    return rcParams['font.size']*factors[value] if isinstance(value,str) and value in factors else float(value)
