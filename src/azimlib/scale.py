"""Numeric scale contracts, independent of map CRS and angular latitude."""
import math
from .transforms import Transform

class ScaleTransform(Transform):
    def __init__(self,scale,inverse=False):self.scale,self.inverse=scale,inverse
    def transform_point(self,p):
        from .transforms import _pair
        return tuple((self.scale.inverse if self.inverse else self.scale.forward)(v) for v in _pair(p))
    def inverted(self):return ScaleTransform(self.scale,not self.inverse)

class LinearScale:
    name='linear'
    def forward(self,value):
        value=float(value)
        if not math.isfinite(value):raise ValueError('Scale coordinates must be finite')
        return value
    inverse=forward
    def get_transform(self):return ScaleTransform(self)

class LogScale(LinearScale):
    name='log'
    def __init__(self,base=10):
        self.base=float(base)
        if not math.isfinite(self.base) or self.base<=1:raise ValueError('Log base must exceed one')
    def forward(self,value):
        value=super().forward(value)
        if value<=0:raise ValueError('Log coordinates must be positive')
        return math.log(value)/math.log(self.base)
    def inverse(self,value):return super().forward(self.base**super().forward(value))

class SymLogScale(LogScale):
    name='symlog'
    def __init__(self,base=10,linthresh=1):
        super().__init__(base);self.linthresh=float(linthresh)
        if not math.isfinite(self.linthresh) or self.linthresh<=0:raise ValueError('linthresh must be positive')
    def forward(self,value):
        value=LinearScale.forward(self,value);a=abs(value)/self.linthresh
        return math.copysign(a if a<=1 else 1+math.log(a)/math.log(self.base),value)
    def inverse(self,value):
        value=LinearScale.forward(self,value);a=abs(value)
        return math.copysign(self.linthresh*(a if a<=1 else self.base**(a-1)),value)

def scale_factory(name,**kwargs):
    if name=='linear':return LinearScale(**kwargs)
    if name=='log':return LogScale(**kwargs)
    if name=='symlog':return SymLogScale(**kwargs)
    raise ValueError('Unknown numeric scale')
