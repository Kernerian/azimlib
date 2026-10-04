"""Own geographic text and annotation handles with validated coordinate edits."""
import math
from .layers import Layer
from .components import TextProperties
from .artist import artist_mutation
from .styles import text_style


def coordinate_pair(value,geographic=False):
    if isinstance(value,(str,bytes,dict)):raise ValueError('Position must be a finite coordinate pair')
    try:result=tuple(float(v) for v in value)
    except (TypeError,ValueError) as exc:raise ValueError('Position must be a finite coordinate pair') from exc
    if len(result)!=2 or not all(math.isfinite(v) for v in result):raise ValueError('Position must be a finite coordinate pair')
    if geographic:
        from .geometry import position
        position(result)
    return result


ANNOTATION_COORDS=('data','axes','axes fraction','offset pixels','offset points')


class MapText(TextProperties,Layer):
    """Position is lon/lat degrees or Axes fractions according to transform."""
    def __post_init__(self):
        super().__post_init__();text_style(self.style)
    def get_position(self):return tuple(self.data[:2])
    def set_position(self,value):return self.set(position=value)
    def get_x(self):return self.get_position()[0]
    def get_y(self):return self.get_position()[1]
    def set_x(self,value):return self.set(x=value)
    def set_y(self,value):return self.set(y=value)

    @artist_mutation
    def set(self,**kwargs):
        options=dict(kwargs)
        pair=options.pop('position',self.get_position())
        pair=coordinate_pair(pair)
        pair=coordinate_pair((options.pop('x',pair[0]),options.pop('y',pair[1])),self.options['transform']=='data')
        value=str(options.pop('text',self.get_text()))
        prepared=self._prepare_set(options)
        text_style(dict(self.style,**prepared[0]))
        self.data=(*pair,value);self._apply_set(prepared)
        return self


class Annotation(TextProperties,Layer):
    """Text position (xyann) is distinct from the geographic arrow target xy."""
    def __post_init__(self):
        super().__post_init__();text_style(self.style)
    def get_position(self):return self.data[1]
    def set_position(self,value):return self.set(position=value)
    def get_x(self):return self.get_position()[0]
    def get_y(self):return self.get_position()[1]
    def set_x(self,value):return self.set(x=value)
    def set_y(self,value):return self.set(y=value)
    @property
    def xy(self):return self.data[0]
    @xy.setter
    def xy(self,value):self.set(xy=value)
    @property
    def xyann(self):return self.get_position()
    @xyann.setter
    def xyann(self,value):self.set(position=value)
    def get_anncoords(self):return self.options['textcoords']
    def set_anncoords(self,value):return self.set(anncoords=value)

    @artist_mutation
    def set(self,**kwargs):
        options=dict(kwargs)
        coords=options.pop('anncoords',self.get_anncoords())
        if coords not in ANNOTATION_COORDS:raise ValueError('Unsupported annotation coordinates')
        target=coordinate_pair(options.pop('xy',self.xy),True)
        pair=coordinate_pair(options.pop('position',self.get_position()))
        pair=coordinate_pair((options.pop('x',pair[0]),options.pop('y',pair[1])),coords=='data')
        value=str(options.pop('text',self.get_text()))
        prepared=self._prepare_set(options)
        text_style(dict(self.style,**prepared[0]))
        self.data=(target,pair,value);self.options['textcoords']=coords;self._apply_set(prepared)
        return self
