"""Own font-aware layout for weighted/nested tracks and disjoint root regions.

Measurement uses export primitives. Fixed edge obstacles reserve strips;
compressed layout compacts complete unspanned fixed-aspect grids.
"""
from __future__ import annotations
import math
import warnings
from .scene import Text, Path, Circle, Rect
from .typography import POINT
from .config import rcParams
from .gridspec import _track_edges


def primitive_bounds(item):
    """Visible bounds (x, y, width, height), respecting primitive clipping."""
    stroke=item.style.get('stroke_width',0)/2 if item.style.get('stroke') else 0
    if isinstance(item,Text):
        from .label_layout import text_box
        box=text_box(item.x,item.y,item.text,item.style,padding=0)
    elif isinstance(item,Path):
        points=[p for part in item.paths for p in part]
        if not points:return None
        x0=min(p[0] for p in points);x1=max(p[0] for p in points)
        y0=min(p[1] for p in points);y1=max(p[1] for p in points)
        box=(x0-stroke,y0-stroke,x1-x0+2*stroke,y1-y0+2*stroke)
    elif isinstance(item,Circle):
        r=item.r+stroke;box=(item.x-r,item.y-r,2*r,2*r)
    else:
        box=(item.x-stroke,item.y-stroke,item.width+2*stroke,item.height+2*stroke)
    if item.clip is not None:
        x,y,w,h=box;cx,cy,cw,ch=item.clip
        left=max(x,cx);top=max(y,cy);right=min(x+w,cx+cw);bottom=min(y+h,cy+ch)
        if right<left or bottom<top:return None
        box=(left,top,right-left,bottom-top)
    return box


def union_bounds(boxes):
    boxes=[b for b in boxes if b is not None]
    if not boxes:return None
    left=min(b[0] for b in boxes);top=min(b[1] for b in boxes)
    return left,top,max(b[0]+b[2] for b in boxes)-left,max(b[1]+b[3] for b in boxes)-top


def item_bounds(scene,start=0,end=None):
    end=len(scene.items) if end is None else end
    boxes=[primitive_bounds(item) for i,item in enumerate(scene.items[start:end],start)
           if i not in scene._layout_excluded]
    for a,b,box,clip in scene._text_blocks:
        if not (start<=a and b<=end) or not any(i not in scene._layout_excluded for i in range(a,b)):continue
        if clip is not None:
            x,y,w,h=box;cx,cy,cw,ch=clip
            left=max(x,cx);top=max(y,cy);right=min(x+w,cx+cw);bottom=min(y+h,cy+ch)
            if right<left or bottom<top:continue
            box=(left,top,right-left,bottom-top)
        boxes.append(box)
    return union_bounds(boxes)


def reset_bar_clearance(figure):
    """Borrow automatic inner padding without changing public bar.pad/cax."""
    bars=[*figure._colorbars,*[ax._colorbar for ax in figure.axes if ax._colorbar]]
    originals=[(bar,getattr(bar,'_layout_clearance',0)) for bar in bars]
    for bar in bars:bar._layout_clearance=0.
    return originals


def reserve_bar_clearance(scene,axes,wpad,hpad):
    """Keep parent decorations out of automatic colorbars' measured bounds.

    Outer grid margins alone cannot see a title crossing into the portion of
    its own slot stolen by a shared bar. Explicit cax/in_layout=False remain
    manual. The public fractional pad is a lower bound, never rewritten.
    """
    occupied={i for _,start,end in scene._layout_bars for i in range(start,end)}
    delta=0.
    for bar,start,end in scene._layout_bars:
        if bar.cax is not None or not bar.get_in_layout():continue
        parents=[ax for ax in bar.parents if ax in axes]
        if not parents:continue
        decor=union_bounds(primitive_bounds(scene.items[i])
            for owners,a,b,slot in scene._layout_groups if len(owners)==1 and owners[0] in parents
            for i in range(a,b) if i not in occupied and i not in scene._layout_excluded)
        bbox=item_bounds(scene,start,end)
        if decor is None or bbox is None:continue
        x,y,w,h=decor;bx,by,bw,bh=bbox
        gap={'right':bx-x-w,'left':x-bx-bw,'bottom':by-y-h,'top':y-by-bh}[bar['location']]
        needed=(wpad if bar.orientation=='vertical' else hpad)-gap
        if needed>.05:
            bar._layout_clearance+=needed
            delta=max(delta,needed)
    return delta


def position_figure_labels(figure,pad,automatic):
    """Borrow label positions; only constrained's automatic edge moves them."""
    originals={a:a.get_position() for a in figure._figure_labels()}
    if automatic:
        px,py=pad if isinstance(pad,tuple) else (pad,pad)
        W,H=(v*100 for v in figure.figsize)
        for slot,value,axis in (('_suptitle',1-py/H,1),('_supxlabel',py/H,1),('_supylabel',px/W,0)):
            artist=getattr(figure,slot)
            if artist is not None and artist.get_visible() and artist.get_in_layout() and artist._autopos:
                position=list(artist.get_position());position[axis]=value;artist._position=tuple(position)
    return originals


def figure_label_space(figure,scene,pad,automatic):
    """Extra left/top/bottom reservations, beyond the ordinary outer padding."""
    px,py=pad if isinstance(pad,tuple) else (pad,pad)
    W,H=(v*100 for v in figure.figsize)
    extra=[]
    for slot,index,limit,gap in (('_supylabel',2,H,px),('_suptitle',3,W,py),('_supxlabel',3,W,py)):
        artist=getattr(figure,slot);box=getattr(scene,'_layout'+slot)
        if artist is None or box is None or automatic and not artist._autopos:
            extra.append(0.);continue
        length=box[3] if index==2 else box[2]
        if length>limit:raise ValueError(slot[1:]+(' is taller' if index==2 else ' is wider')+' than the figure')
        extra.append(box[index]+gap)
    return tuple(extra)


class LayoutEngine:
    """Base for independently implemented layout engines."""
    adjust_compatible=True
    def get(self):return dict(self._params)
    def execute(self,figure):raise NotImplementedError


class PlaceHolderLayoutEngine(LayoutEngine):
    """Stop automatic adjustment while retaining the prior engine's policy."""
    def __init__(self,adjust_compatible=True):
        self.adjust_compatible=bool(adjust_compatible);self._params={}
    def execute(self,figure):return True


class TightLayoutEngine(LayoutEngine):
    """Font-size fraction padding; recompute at every draw when installed."""
    def __init__(self,*,pad=1.08,w_pad=None,h_pad=None,rect=(0,0,1,1)):
        self._params={};self.set(pad=pad,w_pad=w_pad,h_pad=h_pad,rect=rect)
    def set(self,**kwargs):
        values=dict(self._params,**kwargs)
        if set(values)-{'pad','w_pad','h_pad','rect'}:raise TypeError('Unknown tight layout parameter')
        for key in ('pad','w_pad','h_pad'):
            if values[key] is not None and (not math.isfinite(float(values[key])) or values[key]<0):
                raise ValueError('Layout padding must be finite and non-negative')
        rect=tuple(float(v) for v in (values['rect'] or (0,0,1,1)))
        if len(rect)!=4 or not all(math.isfinite(v) for v in rect) or not (0<=rect[0]<rect[2]<=1 and 0<=rect[1]<rect[3]<=1):
            raise ValueError('rect must be (left, bottom, right, top) inside the figure')
        values['rect']=rect;self._params=values
        return self
    def execute(self,figure):
        p=self._params;font=rcParams['font.size']*POINT
        return _solve(figure,p['rect'],p['pad']*font,
                      (p['pad'] if p['w_pad'] is None else p['w_pad'])*font,
                      (p['pad'] if p['h_pad'] is None else p['h_pad'])*font)


class ConstrainedLayoutEngine(LayoutEngine):
    """Continuous GridSpec layout; edge/gap padding is specified in inches.

    rect follows Matplotlib's constrained layout (left,bottom,width,height).
    wspace/hspace add a fraction of the usable figure dimension between cells.
    """
    adjust_compatible=False
    def __init__(self,*,w_pad=3/72,h_pad=3/72,wspace=.02,hspace=.02,rect=(0,0,1,1)):
        self._params={};self.set(w_pad=w_pad,h_pad=h_pad,wspace=wspace,hspace=hspace,rect=rect)
    def set(self,**kwargs):
        values=dict(self._params,**kwargs)
        if set(values)-{'w_pad','h_pad','wspace','hspace','rect'}:raise TypeError('Unknown constrained layout parameter')
        for key in ('w_pad','h_pad','wspace','hspace'):
            if not math.isfinite(float(values[key])) or values[key]<0:raise ValueError('Layout spacing must be finite and non-negative')
        x,y,w,h=map(float,values['rect'])
        if not all(math.isfinite(v) for v in (x,y,w,h)) or min(x,y)<0 or min(w,h)<=0 or x+w>1 or y+h>1:
            raise ValueError('rect must be (left,bottom,width,height) inside the figure')
        values['rect']=(x,y,w,h);self._params=values
        return self
    def execute(self,figure):
        p=self._params;x,y,w,h=p['rect']
        axes=figure._subplot_axes()
        rows,cols=axes[0].get_subplotspec().get_topmost_subplotspec().get_gridspec().get_geometry() if axes else (1,1)
        return _solve(figure,(x,y,x+w,y+h),(p['w_pad']*100,p['h_pad']*100),
                      max(2*p['w_pad']*100,p['wspace']*w*figure.figsize[0]*100/max(1,cols-1)),
                      max(2*p['h_pad']*100,p['hspace']*h*figure.figsize[1]*100/max(1,rows-1)),automatic_labels=True)


def _solve_one(figure,rect,pad,wpad,hpad,*,automatic_labels=False):
    axes=figure._subplot_axes()
    def failed(reason):
        warnings.warn('Azimlib layout could not fit decorations: '+reason+'. Previous positions were retained.',UserWarning,stacklevel=3)
        return False
    if not axes:return failed('no compatible subplot grid')
    grid=axes[0].get_gridspec()
    from .gridspec import GridSpecFromSubplotSpec
    if any(isinstance(a.get_gridspec(),GridSpecFromSubplotSpec) for a in axes):
        roots=[a.get_subplotspec().get_topmost_subplotspec().get_gridspec() for a in axes]
        if any(root is not roots[0] for root in roots):return failed('mixed subplot grids are not supported')
        from .nested_layout import solve
        return solve(figure,axes,roots[0],rect,pad,wpad,hpad,automatic_labels=automatic_labels)
    if any(a.get_gridspec() is not grid for a in axes):
        return failed('mixed subplot grids are not supported')
    rows,cols=grid.get_geometry();W,H=(v*100 for v in figure.figsize)
    widths=grid.get_width_ratios();heights=grid.get_height_ratios()
    # Explicit grid margins bound the automatic solver's available rectangle.
    rect=list(rect)
    for i,key in enumerate(('left','bottom','right','top')):
        value=grid._params[key]
        if value is not None:rect[i]=(max if i<2 else min)(rect[i],value)
    if rect[0]>=rect[2] or rect[1]>=rect[3]:return failed('grid margins and layout rect do not intersect')
    px,py=pad if isinstance(pad,tuple) else (pad,pad)
    originals={ax:ax.position for ax in figure.axes};pars=dict(figure.subplotpars)
    original_labels=position_figure_labels(figure,pad,automatic_labels)
    original_bars=reset_bar_clearance(figure)
    # Each draw starts afresh, so changes to text/visibility can release space.
    left=rect[0]*W+px;right=rect[2]*W-px
    top=(1-rect[3])*H+py;bottom=(1-rect[1])*H-py
    hg,vg=wpad,hpad
    success=False
    def install_positions():
        xs,xe=_track_edges(left,right-left,widths,hg)
        ys,ye=_track_edges(top,bottom-top,heights,vg)
        for ax in axes:
            spec=ax.get_subplotspec();r,c=spec.rowspan,spec.colspan
            x,y=xs[c.start],ys[r.start];w=xe[c.stop-1]-x;h=ye[r.stop-1]-y
            if min(w,h)<30:return False
            ax.position=(x/W,1-(y+h)/H,w/W,h/H)
        return True
    try:
        # Monotone reservations avoid oscillation for equal-aspect map axes.
        L=[0.0]*cols;R=[0.0]*cols;T=[0.0]*rows;B=[0.0]*rows
        for iteration in range(16):
            if right-left<=(cols-1)*hg or bottom-top<=(rows-1)*vg or not install_positions():
                return failed('insufficient axes area; enlarge figsize or reduce text/padding')
            try:scene=figure._compose_scene(measure_layout=True)
            except ValueError as error:
                if str(error)=='Figure is too small for its titles, subplots, and color bars':
                    return failed('insufficient map area after colorbar allocation')
                raise
            clearance=reserve_bar_clearance(scene,axes,wpad,hpad)
            for owners,start,end,slot in scene._layout_groups:
                owners=[a for a in owners if a in axes]
                if not owners:continue
                box=item_bounds(scene,start,end)
                if box is None:continue
                r0=min(a.get_subplotspec().rowspan.start for a in owners)
                r1=max(a.get_subplotspec().rowspan.stop-1 for a in owners)
                c0=min(a.get_subplotspec().colspan.start for a in owners)
                c1=max(a.get_subplotspec().colspan.stop-1 for a in owners)
                sx,sy,sw,sh=slot;x,y,w,h=box
                fx,fy=scene._layout_scales.get(owners[0],(1,1)) if len(owners)==1 else (1,1)
                L[c0]=max(L[c0],(sx-x)/fx);R[c1]=max(R[c1],(x+w-sx-sw)/fx)
                T[r0]=max(T[r0],(sy-y)/fy);B[r1]=max(B[r1],(y+h-sy-sh)/fy)
            try:el,et,eb=figure_label_space(figure,scene,pad,automatic_labels)
            except ValueError as error:return failed(str(error))
            nleft=rect[0]*W+px+L[0]+el;nright=rect[2]*W-px-R[-1]
            ntop=(1-rect[3])*H+py+T[0]+et;nbottom=(1-rect[1])*H-py-B[-1]-eb
            nhg=max([wpad]+[R[c]+L[c+1]+wpad for c in range(cols-1)])
            nvg=max([hpad]+[B[r]+T[r+1]+hpad for r in range(rows-1)])
            # GridSpec spaces are fractions of average cell size. Decoration
            # clearance remains a lower bound when a smaller space is requested.
            if grid._params['wspace'] is not None:
                space=grid._params['wspace']
                nhg=max(nhg,space*(nright-nleft)/(cols+space*(cols-1)))
            if grid._params['hspace'] is not None:
                space=grid._params['hspace']
                nvg=max(nvg,space*(nbottom-ntop)/(rows+space*(rows-1)))
            error=max(clearance,max(abs(a-b) for a,b in zip((left,right,top,bottom,hg,vg),(nleft,nright,ntop,nbottom,nhg,nvg))))
            left,right,top,bottom,hg,vg=nleft,nright,ntop,nbottom,nhg,nvg
            if error<.1:success=True;break
        if not success:return failed('layout did not converge within sixteen measurements')
        # Install the final geometry, with no intermediate positions escaping.
        cw=(right-left-(cols-1)*hg)/cols;ch=(bottom-top-(rows-1)*vg)/rows
        if min(cw,ch)<=0 or not install_positions():
            success=False
            return failed('insufficient axes area')
        figure.subplotpars.update(left=left/W,right=right/W,top=1-top/H,bottom=1-bottom/H,wspace=hg/cw,hspace=vg/ch)
        return True
    finally:
        if not success:
            for ax,position in originals.items():ax.position=position
            for artist,position in original_labels.items():artist._position=position
            for bar,clearance in original_bars:bar._layout_clearance=clearance
            figure.subplotpars.update(pars)

class _RegionalFigure:
    def __init__(self,figure,axes):
        self._source,self._axes=figure,axes
        self.subplotpars=dict(figure.subplotpars)
        self._suptitle=self._supxlabel=self._supylabel=None
    def __getattr__(self,name):return getattr(self._source,name)
    def _subplot_axes(self,**kwargs):return self._axes
    def _figure_labels(self):return []
    def _compose_scene(self,**kwargs):
        scene=self._source._compose_scene(**kwargs)
        scene._layout_suptitle=scene._layout_supxlabel=scene._layout_supylabel=None
        return scene

def _obstacle_rect(figure,rect,pad,scene,*,include_labels=False):
    """Reserve edge strips for fixed free text/manual cax; interior objects stay manual."""
    W,H=(v*100 for v in figure.figsize);l,b,r,t=rect;px,py=pad if isinstance(pad,tuple) else (pad,pad)
    boxes=[item_bounds(scene,start,end) for artist,start,end in scene._layout_free if artist.get_in_layout()]
    boxes += [item_bounds(scene,start,end) for bar,start,end in scene._layout_bars if bar.cax is not None and bar.get_in_layout()]
    if include_labels:boxes += [box for box in (scene._layout_suptitle,scene._layout_supxlabel,scene._layout_supylabel) if box is not None]
    for box in boxes:
        if box is None:continue
        x,y,w,h=box;cx,cy=x+w/2,y+h/2
        if x+w<l*W or x>r*W or y+h<(1-t)*H or y>(1-b)*H:continue
        if cy<(1-t+.12*(t-b))*H:t=min(t,1-(y+h+py)/H)
        elif cy>(1-b-.12*(t-b))*H:b=max(b,1-(y-py)/H)
        elif cx<(l+.08*(r-l))*W:l=max(l,(x+w+px)/W)
        elif cx>(r-.08*(r-l))*W:r=min(r,(x-px)/W)
    return l,b,r,t

def _solve(figure,rect,pad,wpad,hpad,*,automatic_labels=False):
    from .gridspec import grid_ancestors
    axes=figure._subplot_axes();groups={}
    for ax in axes:groups.setdefault(grid_ancestors(ax.get_gridspec())[-1],[]).append(ax)
    fixed=bool(figure._texts) or any(bar.cax is not None and bar.get_in_layout() for bar in figure._colorbars)
    if len(groups)<=1 and not fixed:return _solve_one(figure,rect,pad,wpad,hpad,automatic_labels=automatic_labels)
    if len(groups)>1:
        regions=[]
        for grid in groups:
            p=grid.get_subplot_params(figure);region=getattr(grid,'_layout_region',(p.left,p.bottom,p.right-p.left,p.top-p.bottom))
            l,b,w,h=region;regions.append((l,b,l+w,b+h))
        if any(min(a[2],b[2])-max(a[0],b[0])>1e-8 and min(a[3],b[3])-max(a[1],b[1])>1e-8 for i,a in enumerate(regions) for b in regions[i+1:]):
            warnings.warn('mixed subplot grids require disjoint explicit regions; previous positions retained',UserWarning,stacklevel=3);return False
    try:scene=figure._compose_scene(measure_layout=True)
    except ValueError as error:
        if str(error)=='Figure is too small for its titles, subplots, and color bars':
            if len(groups)<=1:return _solve_one(figure,rect,pad,wpad,hpad,automatic_labels=automatic_labels)
            warnings.warn('Azimlib layout could not fit decorations: insufficient axes area. Previous positions retained.',UserWarning,stacklevel=3);return False
        raise
    if len(groups)<=1:
        # Preserve the legacy solve path if there are no new fixed obstacles.
        adjusted=_obstacle_rect(figure,rect,pad,scene) if scene._layout_free or any(bar.cax is not None for bar,_,_ in scene._layout_bars) else rect
        return _solve_one(figure,adjusted,pad,wpad,hpad,automatic_labels=automatic_labels)
    original={ax:ax.position for ax in figure.axes};original_labels={a:a.get_position() for a in figure._figure_labels()}
    original_bars=[(bar,getattr(bar,'_layout_clearance',0)) for bar,_,_ in scene._layout_bars]
    regions=[]
    for grid,members in groups.items():
        region=getattr(grid,'_layout_region',None)
        if region is None:
            p=grid.get_subplot_params(figure);region=(p.left,p.bottom,p.right-p.left,p.top-p.bottom)
        l,b,w,h=region;region=(max(rect[0],l),max(rect[1],b),min(rect[2],l+w),min(rect[3],b+h))
        regions.append((grid,members,region))
    for i,(_,_,a) in enumerate(regions):
        if a[0]>=a[2] or a[1]>=a[3] or any(min(a[2],b[2])-max(a[0],b[0])>1e-8 and min(a[3],b[3])-max(a[1],b[1])>1e-8 for _,_,b in regions[i+1:]):
            warnings.warn('Independent GridSpecs need disjoint explicit regions; previous positions retained',UserWarning,stacklevel=3);return False
    success=False
    try:
        for grid,members,region in regions:
            region=_obstacle_rect(figure,region,pad,scene,include_labels=True)
            if not _solve_one(_RegionalFigure(figure,members),region,pad,wpad,hpad,automatic_labels=False):return False
        success=True
        return True
    finally:
        # Failure is transactional across all roots.
        import sys
        if not success:
            for ax,p in original.items():ax.position=p
            for artist,p in original_labels.items():artist._position=p
            for bar,value in original_bars:bar._layout_clearance=value

class CompressedLayoutEngine(ConstrainedLayoutEngine):
    """Compact fixed-aspect slots in complete unspanned grids after measurement.

    Nested/spanning grids keep the constrained solution. Explicit add_axes and
    manual cax are never moved. Ratios remain inputs to the constrained solve.
    """
    def execute(self,figure):
        if not super().execute(figure):return False
        from .gridspec import grid_ancestors
        axes=figure._subplot_axes();scene=figure._compose_scene(measure_layout=True);groups={}
        for ax in axes:groups.setdefault(ax.get_gridspec(),[]).append(ax)
        W,H=(v*100 for v in figure.figsize)
        for grid,members in groups.items():
            rows,cols=grid.get_geometry()
            if len(grid_ancestors(grid))>1 or len(members)!=rows*cols or any(len(a.get_subplotspec().rowspan)!=1 or len(a.get_subplotspec().colspan)!=1 for a in members):continue
            boxes={a:next(m['box'] for m in scene.maps if m['axes_index']==figure.axes.index(a)) for a in members}
            widths=[max(boxes[a][2] for a in members if a.get_subplotspec().colspan.start==c) for c in range(cols)]
            heights=[max(boxes[a][3] for a in members if a.get_subplotspec().rowspan.start==r) for r in range(rows)]
            ext={a:item_bounds(scene,start,end) for owners,start,end,slot in scene._layout_groups if len(owners)==1 for a in owners if a in members}
            left=[0.]*cols;right=[0.]*cols;top=[0.]*rows;bottom=[0.]*rows
            for a in members:
                x,y,w,h=boxes[a];bx,by,bw,bh=ext[a];r=a.get_subplotspec().rowspan.start;c=a.get_subplotspec().colspan.start
                left[c]=max(left[c],x-bx);right[c]=max(right[c],bx+bw-x-w);top[r]=max(top[r],y-by);bottom[r]=max(bottom[r],by+bh-y-h)
            xg=[right[c]+left[c+1]+2*self._params['w_pad']*100 for c in range(cols-1)]
            yg=[bottom[r]+top[r+1]+2*self._params['h_pad']*100 for r in range(rows-1)]
            union=union_bounds(boxes.values());tw=sum(widths)+sum(xg);th=sum(heights)+sum(yg)
            if tw>union[2]+.1 or th>union[3]+.1:continue
            xs=[union[0]+(union[2]-tw)/2];ys=[union[1]+(union[3]-th)/2]
            for c in range(cols-1):xs.append(xs[-1]+widths[c]+xg[c])
            for r in range(rows-1):ys.append(ys[-1]+heights[r]+yg[r])
            for a in members:
                r=a.get_subplotspec().rowspan.start;c=a.get_subplotspec().colspan.start;x,y,w,h=boxes[a]
                a.position=((xs[c]+(widths[c]-w)/2)/W,1-(ys[r]+(heights[r]+h)/2)/H,w/W,h/H)
        return True
