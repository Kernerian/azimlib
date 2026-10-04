"""Own display-path cutting beneath labels without changing geographic sources."""
import math
from .line_labels import clip_segment
from .typography import text_bounds


def label_cuts(axes,planned):
    """Only visible, placed inline labels cut their own connected contour path."""
    cuts={}
    for label in axes.layers:
        if not label.visible or not getattr(label,'get_inline',lambda:False)():continue
        source=label._contour_ref()
        if source is None or source.axes is not axes:continue
        item=planned.get((id(label),0))
        if item is None or item.style.get('opacity',1)==0:continue
        x,y,w,h=text_bounds(item.text,item.style)
        # clabel spacing is in display pixels at the Figure's DPI. Rendering
        # happens in logical 100-DPI units before the scene-wide conversion.
        gap=label.get_inline_spacing()*100/(axes.figure.dpi if axes.figure else 100)
        key=(id(source),label.options['contour_feature'])
        cuts.setdefault(key,[]).append((item.position,item.style.get('rotation',0),
                                        (x-gap,y,w+2*gap,h)))
    return cuts


def _interval(a,b,cut):
    center,angle,box=cut
    radians=math.radians(angle);c,s=math.cos(radians),math.sin(radians)
    def local(p):
        dx,dy=p[0]-center[0],p[1]-center[1]
        return c*dx+s*dy,-s*dx+c*dy
    aa,bb=local(a),local(b);dx,dy=bb[0]-aa[0],bb[1]-aa[1]
    length=dx*dx+dy*dy
    if length==0:return None
    clipped=clip_segment(aa,bb,box)
    if clipped is None:return None
    values=[((p[0]-aa[0])*dx+(p[1]-aa[1])*dy)/length for p in clipped]
    lo,hi=max(0.,min(values)),min(1.,max(values))
    return (lo,hi) if hi-lo>1e-12 else None


def cut_path(points,cuts):
    """Subtract rotated label rectangles from a polyline; return fresh parts."""
    if not cuts:return [points]
    result=[];current=[]
    for a,b in zip(points,points[1:]):
        keep=[(0.,1.)]
        for cut in cuts:
            interval=_interval(a,b,cut)
            if interval is None:continue
            lo,hi=interval;next_keep=[]
            for left,right in keep:
                if hi<=left or lo>=right:next_keep.append((left,right));continue
                if lo>left:next_keep.append((left,lo))
                if hi<right:next_keep.append((hi,right))
            keep=next_keep
        for lo,hi in keep:
            if hi-lo<=1e-12:continue
            start=(a[0]+lo*(b[0]-a[0]),a[1]+lo*(b[1]-a[1]))
            end=(a[0]+hi*(b[0]-a[0]),a[1]+hi*(b[1]-a[1]))
            if current and math.dist(current[-1],start)>1e-7:
                if len(current)>1:result.append(current)
                current=[]
            if not current:current.append(start)
            if math.dist(current[-1],end)>1e-12:current.append(end)
        if not keep or keep[-1][1]<1-1e-12:
            if len(current)>1:result.append(current)
            current=[]
    if len(current)>1:result.append(current)
    return result
