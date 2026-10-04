"""Own figure registry and pyplot current-figure/current-axes selection."""
import operator
import warnings
from .figure import Figure
from .axes import MapAxes
from .gridspec import SubplotSpec,GridSpecFromSubplotSpec
from .projections import get_projection

_figures=[]


def _number(value):
    try:return operator.index(value)
    except TypeError:raise TypeError('Figure identifier must be an integer, label or managed Figure') from None


def _find(num):
    if isinstance(num,Figure):return num if num in _figures else None
    if isinstance(num,str):return next((f for f in _figures if f.get_label()==num),None)
    number=_number(num)
    return next((f for f in _figures if f.number==number),None)


def figure(num=None,*,figsize=None,dpi=None,facecolor=None,layout=None,clear=False):
    """Create/reactivate an own figure by number, label or managed Figure."""
    found=None if num is None else _find(num)
    if isinstance(num,Figure) and found is None:raise ValueError('Figure is not managed by pyplot')
    if found is not None:
        if any(v is not None for v in (figsize,dpi,facecolor,layout)):
            warnings.warn('Ignoring specified arguments because figure already exists.',UserWarning,stacklevel=2)
        _figures.remove(found);_figures.append(found)
        if clear:found.clear()
        return found
    number=max([0,*get_fignums()])+1 if num is None or isinstance(num,str) else _number(num)
    fig=Figure(figsize=figsize,dpi=dpi,facecolor=facecolor,layout=layout)
    fig.number=number
    if isinstance(num,str):fig.set_label(num)
    _figures.append(fig)
    return fig


def subplots(nrows=1,ncols=1,*,projection='equirectangular',figsize=None,dpi=None,
             facecolor=None,squeeze=True,projection_kw=None,subplot_kw=None,layout=None,
             gridspec_kw=None,width_ratios=None,height_ratios=None,num=None,clear=False,sharex=False,sharey=False):
    existing=set(_figures)
    fig=figure(num,figsize=figsize,dpi=dpi,facecolor=facecolor,layout=layout,clear=clear)
    try:
        axes=fig.subplots(nrows,ncols,projection=projection,projection_kw=projection_kw,squeeze=squeeze,
                          subplot_kw=subplot_kw,gridspec_kw=gridspec_kw,width_ratios=width_ratios,height_ratios=height_ratios,sharex=sharex,sharey=sharey)
    except Exception:
        if fig not in existing:close(fig)
        raise
    return fig,axes


def subplot_mosaic(mosaic,*,projection='equirectangular',projection_kw=None,
                   figsize=None,dpi=None,facecolor=None,layout=None,num=None,clear=False,
                   subplot_kw=None,per_subplot_kw=None,gridspec_kw=None,
                   width_ratios=None,height_ratios=None,empty_sentinel='.',sharex=False,sharey=False):
    """Return (figure, dict of named axes) for a rectangular or nested mosaic."""
    existing=set(_figures)
    fig=figure(num,figsize=figsize,dpi=dpi,facecolor=facecolor,layout=layout,clear=clear)
    try:
        axes=fig.subplot_mosaic(mosaic,projection=projection,projection_kw=projection_kw,
                                subplot_kw=subplot_kw,per_subplot_kw=per_subplot_kw,gridspec_kw=gridspec_kw,
                                width_ratios=width_ratios,height_ratios=height_ratios,empty_sentinel=empty_sentinel,sharex=sharex,sharey=sharey)
    except Exception:
        if fig not in existing:close(fig)
        raise
    return fig,axes


def get_fignums():return sorted(f.number for f in _figures)
def get_figlabels():return [f.get_label() for f in sorted(_figures,key=lambda f:f.number)]
def fignum_exists(num):return _find(num) is not None
def gcf():return _figures[-1] if _figures else figure()
def gca():return gcf().gca()


def sca(ax):
    """Select an axes and its managed figure without reordering Figure.axes."""
    if not isinstance(ax,MapAxes) or ax.figure not in _figures or ax not in ax.figure.axes:
        raise ValueError('Axes must belong to a managed figure')
    figure(ax.figure);ax.figure.sca(ax)


def subplot(*args,**kwargs):
    """Select/reuse a subplot; explicit projection options can create another."""
    if set(kwargs)-{'projection','projection_kw','sharex','sharey'}:raise TypeError('Unsupported subplot option')
    for name in ('sharex','sharey'):
        if kwargs.get(name) is not None and not isinstance(kwargs[name],MapAxes):raise TypeError('Sharing requires a MapAxes')
    fig=gcf()
    spec=args[0] if len(args)==1 and isinstance(args[0],SubplotSpec) else None
    if spec is not None:
        geometry=spec.get_geometry()
        if spec.get_gridspec().figure not in (None,fig):raise ValueError('GridSpec belongs to another figure')
    else:
        if not args:rows,cols,index=1,1,1
        elif len(args)==1 and isinstance(args[0],int) and 100<=args[0]<=999:rows,cols,index=map(int,str(args[0]))
        elif len(args)==3:rows,cols,index=args
        else:raise ValueError('Use subplot(spec), subplot(111) or subplot(rows,cols,index)')
        if any(not isinstance(v,int) or v<1 for v in (rows,cols)):raise ValueError('Invalid subplot grid')
        endpoints=index if isinstance(index,tuple) else (index,index)
        if len(endpoints)!=2 or any(not isinstance(v,int) or not 1<=v<=rows*cols for v in endpoints) or endpoints[0]>endpoints[1]:raise ValueError('Invalid subplot index or span')
        geometry=(rows,cols,endpoints[0]-1,endpoints[1]-1)
    projection=get_projection(kwargs.get('projection','equirectangular'),**(kwargs.get('projection_kw') or {}))
    for ax in fig.axes:
        owned=ax.get_subplotspec()
        if spec is None and owned is not None and isinstance(owned.get_gridspec(),GridSpecFromSubplotSpec):continue
        projection_matches=not any(k in kwargs for k in ('projection','projection_kw')) or ax.projection==projection
        sharing_matches=all(name not in kwargs or getattr(ax,'_'+name) is kwargs[name] for name in ('sharex','sharey'))
        if owned is not None and owned.get_geometry()==geometry and (spec is None or owned==spec) and projection_matches and sharing_matches:
            fig.sca(ax);return ax
    return fig.add_subplot(*args,projection=projection,**{k:kwargs[k] for k in ('sharex','sharey') if k in kwargs})


def savefig(path,**kwargs):return gcf().save(path,**kwargs)
def clf():return gcf().clear()
def cla():return gca().clear()


def show(*,block=True,backend='tk',open_browser=True):
    """Show own viewers; desktop event loop blocks only when requested."""
    result=tuple(fig.show(backend=backend,block=False,open_browser=open_browser) for fig in tuple(_figures))
    if backend=='tk' and block:
        from .backends.tk import mainloop
        mainloop()
    return result


def close(fig=None):
    """Close current, numbered/named/explicit figure, or 'all', without creation."""
    if fig is None:targets=_figures[-1:] if _figures else []
    elif isinstance(fig,str) and fig=='all':targets=list(_figures)
    elif isinstance(fig,Figure):targets=[fig]
    else:
        target=_find(fig);targets=[] if target is None else [target]
    for target in targets:
        if target in _figures:_figures.remove(target)
        target._closed=True
        viewer=getattr(target,'_viewer',None)
        if viewer and not viewer.closed:viewer.close()
