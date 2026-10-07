"""UTC numeric dates and calendar-aware tickers; no implicit lon/lat conversion."""
import datetime as dt
import math
from .ticker import Locator,Formatter
UTC=dt.timezone.utc
EPOCH=dt.datetime(1970,1,1,tzinfo=UTC)
def date2num(value):
    if isinstance(value,(list,tuple)):return [date2num(v) for v in value]
    if isinstance(value,dt.date) and not isinstance(value,dt.datetime):value=dt.datetime.combine(value,dt.time(),UTC)
    if not isinstance(value,dt.datetime):raise TypeError('Require datetime or date')
    if value.tzinfo is None:value=value.replace(tzinfo=UTC)
    return (value.astimezone(UTC)-EPOCH).total_seconds()/86400
def num2date(value,tz=UTC):
    if isinstance(value,(list,tuple)):return [num2date(v,tz) for v in value]
    value=float(value)
    if not math.isfinite(value):raise ValueError('Date number must be finite')
    return (EPOCH+dt.timedelta(days=value)).astimezone(tz)
class DateFormatter(Formatter):
    def __init__(self,fmt='%Y-%m-%d',tz=UTC):self.fmt,self.tz=fmt,tz
    def __call__(self,value,pos=None):return num2date(value,self.tz).strftime(self.fmt)
class DayLocator(Locator):
    def __init__(self,interval=1):
        if not isinstance(interval,int) or interval<1:raise ValueError('interval must be a positive integer')
        self.interval=interval
    def tick_values(self,vmin,vmax):
        low,high=sorted((float(vmin),float(vmax)))
        if not all(math.isfinite(v) for v in (low,high)):raise ValueError('Date bounds must be finite')
        a=math.ceil(low/self.interval);b=math.floor(high/self.interval)
        if b-a+1>self.MAXTICKS:raise ValueError('Invalid/excessive date range')
        return tuple(i*self.interval for i in range(a,b+1))
class MonthLocator(Locator):
    def __init__(self,interval=1):
        if not isinstance(interval,int) or interval<1:raise ValueError('interval must be a positive integer')
        self.interval=interval
    def tick_values(self,vmin,vmax):
        low,high=sorted((float(vmin),float(vmax)));start=num2date(low);stop=num2date(high)
        a=start.year*12+start.month-1;b=stop.year*12+stop.month-1
        if (b-a)//self.interval+1>self.MAXTICKS:raise ValueError('Excessive calendar range')
        out=[]
        for i in range(a,b+1):
            if i%self.interval:continue
            year,month=divmod(i,12);value=date2num(dt.datetime(year,month+1,1,tzinfo=UTC))
            if low<=value<=high:out.append(value)
        return tuple(out)
class AutoDateLocator(Locator):
    def __init__(self,maxticks=9):
        if not isinstance(maxticks,int) or maxticks<2:raise ValueError('maxticks must be at least two')
        self.maxticks=maxticks
    def tick_values(self,vmin,vmax):
        low,high=sorted((float(vmin),float(vmax)))
        if not all(math.isfinite(v) for v in (low,high)):raise ValueError('Date bounds must be finite')
        span=high-low
        if span>90:return MonthLocator(max(1,math.ceil(span/(30*(self.maxticks-1))))).tick_values(low,high)
        if span>2:return DayLocator(max(1,math.ceil(span/(self.maxticks-1)))).tick_values(low,high)
        step=next((n/86400 for n in (1,5,15,60,300,900,3600,10800,21600,43200) if n/86400>=span/(self.maxticks-1)),1.)
        return tuple(i*step for i in range(math.ceil(low/step),math.floor(high/step)+1))
