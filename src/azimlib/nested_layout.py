"""Own hierarchical track allocation measured against composed decorations."""
import warnings
from .gridspec import grid_ancestors,_track_edges
from .layout_engine import item_bounds,position_figure_labels,figure_label_space,reset_bar_clearance,reserve_bar_clearance


class _CannotFit(Exception):pass


def solve(figure,axes,root,rect,pad,wpad,hpad,*,automatic_labels=False):
    """Fit one root hierarchy; retain every prior position on any failure."""
    def failed(reason):
        warnings.warn('Azimlib layout could not fit decorations: '+reason+'. Previous positions were retained.',UserWarning,stacklevel=3)
        return False
    W,H=(v*100 for v in figure.figsize)
    rect=list(rect)
    for i,key in enumerate(('left','bottom','right','top')):
        value=root._params[key]
        if value is not None:rect[i]=(max if i<2 else min)(rect[i],value)
    if rect[0]>=rect[2] or rect[1]>=rect[3]:return failed('grid margins and layout rect do not intersect')
    px,py=pad if isinstance(pad,tuple) else (pad,pad)
    outer=(rect[0]*W+px,(1-rect[3])*H+py,(rect[2]-rect[0])*W-2*px,(rect[3]-rect[1])*H-2*py)
    members={};children={};direct={}
    for ax in axes:
        grid=ax.get_gridspec();direct.setdefault(grid,[]).append(ax)
        for ancestor in reversed(grid_ancestors(grid)):
            members.setdefault(ancestor,None);children.setdefault(ancestor,[])
            if ancestor is not root:
                parent=ancestor._subplot_spec.get_gridspec()
                if ancestor not in children[parent]:children[parent].append(ancestor)
    margins={g:([0.]*g.ncols,[0.]*g.ncols,[0.]*g.nrows,[0.]*g.nrows) for g in members}
    originals={ax:ax.position for ax in figure.axes};pars=dict(figure.subplotpars)
    original_labels=position_figure_labels(figure,pad,automatic_labels)
    original_bars=reset_bar_clearance(figure)
    allocations={};label_space=(0.,0.,0.);success=False

    def allocation(grid,box):
        x,y,w,h=box;L,R,T,B=margins[grid]
        left=x+L[0];right=x+w-R[-1];top=y+T[0];bottom=y+h-B[-1]
        hg=max([wpad]+[R[c]+L[c+1]+wpad for c in range(grid.ncols-1)])
        vg=max([hpad]+[B[r]+T[r+1]+hpad for r in range(grid.nrows-1)])
        for name,count,total in (('wspace',grid.ncols,right-left),('hspace',grid.nrows,bottom-top)):
            space=grid._params[name]
            if space is not None:
                gap=space*total/(count+space*(count-1))
                if name=='wspace':hg=max(hg,gap)
                else:vg=max(vg,gap)
        if right-left<=(grid.ncols-1)*hg or bottom-top<=(grid.nrows-1)*vg:raise _CannotFit
        xs,xe=_track_edges(left,right-left,grid.get_width_ratios(),hg)
        ys,ye=_track_edges(top,bottom-top,grid.get_height_ratios(),vg)
        allocations[grid]=(left,right,top,bottom,hg,vg)
        def slot(spec):
            r,c=spec.rowspan,spec.colspan
            return xs[c.start],ys[r.start],xe[c.stop-1]-xs[c.start],ye[r.stop-1]-ys[r.start]
        for ax in direct.get(grid,()):
            sx,sy,sw,sh=slot(ax.get_subplotspec())
            if min(sw,sh)<30:raise _CannotFit
            ax.position=(sx/W,1-(sy+sh)/H,sw/W,sh/H)
        for child in children[grid]:allocation(child,slot(child._subplot_spec))

    def install():
        x,y,w,h=outer
        el,et,eb=label_space
        allocation(root,(x+el,y+et,w-el,h-et-eb))

    def ancestor_selection(ax,grid):
        spec=ax.get_subplotspec()
        while spec.get_gridspec() is not grid:spec=spec.get_gridspec()._subplot_spec
        return spec

    try:
        # Aspect-constrained descendants can consume their blank vertical
        # slack gradually before text reservations reach a fixed point.
        for iteration in range(32):
            install();scene=figure._compose_scene(measure_layout=True);delta=0.
            delta=reserve_bar_clearance(scene,axes,wpad,hpad)
            for owners,start,end,slot in scene._layout_groups:
                owners=[a for a in owners if a in axes]
                if not owners:continue
                box=item_bounds(scene,start,end)
                if box is None:continue
                chains=[grid_ancestors(a.get_gridspec()) for a in owners]
                common=next(g for g in chains[0] if all(g in chain for chain in chains[1:]))
                specs=[ancestor_selection(a,common) for a in owners]
                indices=(min(s.colspan.start for s in specs),max(s.colspan.stop-1 for s in specs),
                         min(s.rowspan.start for s in specs),max(s.rowspan.stop-1 for s in specs))
                sx,sy,sw,sh=slot;x,y,w,h=box
                fx,fy=scene._layout_scales.get(owners[0],(1,1)) if len(owners)==1 else (1,1)
                extents=((sx-x)/fx,(x+w-sx-sw)/fx,(sy-y)/fy,(y+h-sy-sh)/fy)
                for side,index,extra in zip(margins[common],indices,extents):
                    value=max(side[index],extra);delta=max(delta,value-side[index]);side[index]=value
            try:new_space=figure_label_space(figure,scene,pad,automatic_labels)
            except ValueError as error:return failed(str(error))
            delta=max(delta,max(abs(a-b) for a,b in zip(new_space,label_space)))
            label_space=new_space
            if delta<.1:break
        else:return failed('nested layout did not converge within thirty-two measurements')
        install()
        left,right,top,bottom,hg,vg=allocations[root]
        cw=(right-left-(root.ncols-1)*hg)/root.ncols;ch=(bottom-top-(root.nrows-1)*vg)/root.nrows
        figure.subplotpars.update(left=left/W,right=right/W,top=1-top/H,bottom=1-bottom/H,wspace=hg/cw,hspace=vg/ch)
        success=True
        return True
    except _CannotFit:return failed('insufficient nested axes area; enlarge figsize or reduce text/padding')
    except ValueError as error:
        if str(error)=='Figure is too small for its titles, subplots, and color bars':return failed('insufficient nested map area after colorbar allocation')
        raise
    finally:
        if not success:
            for ax,position in originals.items():ax.position=position
            for artist,position in original_labels.items():artist._position=position
            for bar,clearance in original_bars:bar._layout_clearance=clearance
            figure.subplotpars.update(pars)
