"""GUI-independent view history and geographic navigation calculations."""
from __future__ import annotations
import math


class Navigation:
    def __init__(self,figure):
        self.figure=figure
        self.history=[self.snapshot()]
        self._autoscale_history=[self._autoscale_snapshot()]
        self.index=0

    def snapshot(self):
        return tuple(None if ax._colorbar_artist is not None else ax.get_extent() for ax in self.figure.axes)

    def _autoscale_snapshot(self):
        return tuple(None if ax._colorbar_artist is not None else (ax.get_autoscalex_on(),ax.get_autoscaley_on()) for ax in self.figure.axes)

    def _apply(self,index):
        with self.figure._mutation():
            for ax,extent,flags in zip(self.figure.axes,self.history[index],self._autoscale_history[index]):
                if extent is not None and ax._colorbar_artist is None:
                    # A snapshot may contain emit=False edits and local auto flags.
                    # Restore each view without propagating it over later entries.
                    with ax._mutation():
                        w,e,s,n=extent
                        ax.set_xlim(w,e,emit=False,auto=flags[0])
                        ax.set_ylim(s,n,emit=False,auto=flags[1])
            for ax,extent in zip(self.figure.axes,self.history[index]):
                if extent is not None and ax._colorbar_artist is None:
                    for name in ('x','y'):ax.callbacks.process(name+'lim_changed',ax)

    def push(self):
        current=self.snapshot()
        flags=self._autoscale_snapshot()
        if current!=self.history[self.index] or flags!=self._autoscale_history[self.index]:
            self.history=self.history[:self.index+1]+[current]
            self._autoscale_history=self._autoscale_history[:self.index+1]+[flags]
            self.index+=1

    def restore(self,index):
        if not 0<=index<len(self.history):
            return False
        self.index=index
        self._apply(index)
        return True

    def home(self):
        self._apply(0)
        self.push()

    def back(self):
        return self.restore(self.index-1)

    def forward(self):
        return self.restore(self.index+1)


def bounded_extent(west,east,south,north):
    """Translate windows back into geographic domain without reversing axes."""
    width=max(1e-6,min(360,east-west))
    height=max(1e-6,min(179.8,north-south))
    west=max(-180,min(180-width,west))
    south=max(-89.9,min(89.9-height,south))
    return west,west+width,south,south+height


def viewport_from_metadata(projection,meta):
    from .viewport import Viewport
    viewport=object.__new__(Viewport)
    viewport.projection=projection
    for key in ('extent','box','scale','ox','oy','projected_bounds'):
        setattr(viewport,key,meta[key])
    return viewport


def _pan_delta(dx,dy,constraint):
    """Constrain a Cartesian drag; callers convert Tk's downward Y first."""
    if constraint=='x':return dx,0.
    if constraint=='y':return 0.,dy
    if constraint=='control':
        value=dx if abs(dx)>abs(dy) else dy
        return value,value
    if constraint=='shift':
        if abs(dx)*2<abs(dy):return 0.,dy
        if abs(dy)*2<abs(dx):return dx,0.
        length=max(abs(dx),abs(dy))
        return math.copysign(length,dx),math.copysign(length,dy)
    return dx,dy


def drag_extent(ax,viewport,start,end,*,mode='pan',button=1,constraint=None,initial_extent=None):
    """Compute geographic limits from a drag in screen pixels.

    Projected corner sampling handles cylindrical and regional conic views.
    A singularity or invisible orthographic region returns None safely.
    """
    x,y,w,h=viewport.box
    dx,dy=end[0]-start[0],end[1]-start[1]
    original=tuple(initial_extent) if initial_extent is not None else ax.get_extent()
    if mode=='pan' and button==1:
        dx,up=_pan_delta(dx,-dy,constraint)
        dy=-up
        if dx==dy==0:return original
        corners=[(x-dx,y-dy),(x+w-dx,y-dy),(x-dx,y+h-dy),(x+w-dx,y+h-dy)]
    elif mode=='pan':
        # Equal geographic aspect uses one scale in both projected axes.
        # Normalize the drag by the frozen map dimensions, then scale its
        # display bounds around the initial cursor before applying the inverse.
        sx,sy=_pan_delta(-dx/w,dy/h,constraint)
        exponent=(sx+sy)/2
        if exponent==0:return original
        if not math.isfinite(exponent) or abs(exponent)>300:return None
        span=10.**exponent
        cx,cy=start
        corners=[(cx+(px-cx)*span,cy+(py-cy)*span)
                 for px,py in ((x,y),(x+w,y),(x,y+h),(x+w,y+h))]
    else:
        x0,x1=sorted((max(x,min(x+w,start[0])),max(x,min(x+w,end[0]))))
        y0,y1=sorted((max(y,min(y+h,start[1])),max(y,min(y+h,end[1]))))
        if constraint=='x':y0,y1=y,y+h
        if constraint=='y':x0,x1=x,x+w
        if x1-x0<5 or y1-y0<5:return None
        if button==3:
            center=viewport.inverse((x0+x1)/2,(y0+y1)/2)
            return zoom_extent(ax,min((x1-x0)/w,(y1-y0)/h),center)
        corners=[(x0,y0),(x1,y0),(x0,y1),(x1,y1)]
    points=[viewport.inverse(*p) for p in corners]
    if any(p is None for p in points):
        # Globe corners are outside the projection disk; a center derivative
        # still gives a well-defined geographic translation for regional pans.
        if mode=='pan' and button==1:
            a,b=viewport.inverse(*start),viewport.inverse(*end)
            if a and b:
                west,east,south,north=original
                dl,dp=a[0]-b[0],a[1]-b[1]
                return bounded_extent(west+dl,east+dl,south+dp,north+dp)
        return None
    west,east=min(p[0] for p in points),max(p[0] for p in points)
    south,north=min(p[1] for p in points),max(p[1] for p in points)
    return bounded_extent(west,east,south,north)


def zoom_extent(ax,factor,center=None):
    if not math.isfinite(float(factor)) or factor<=0:
        raise ValueError('Zoom factor must be positive and finite')
    west,east,south,north=ax.get_extent()
    cx,cy=center or ((west+east)/2,(south+north)/2)
    return bounded_extent(cx+(west-cx)/factor,cx+(east-cx)/factor,
                          cy+(south-cy)/factor,cy+(north-cy)/factor)
