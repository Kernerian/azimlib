"""Own weak sharing groups for geographic limits and ticker controllers."""
from weakref import WeakSet

TICKER_FIELDS=('_locator','_formatter','locator_explicit','formatter_explicit',
               '_minor_locator','_minor_formatter','minor_locator_explicit','minor_formatter_explicit')


class SharedGroup:
    def __init__(self,owner):self.members=WeakSet([owner]);self.joined=False


class SharedAxesView:
    """Read-only membership view, matching the public Matplotlib queries."""
    def __init__(self,name):self.name=name
    def joined(self,a,b):
        group=getattr(a,'_shared_axes',{}).get(self.name)
        return group is not None and group.joined and b in group.members
    def get_siblings(self,ax):return list(ax._shared_axes[self.name].members)


def sharing_mode(value):
    if isinstance(value,bool):return 'all' if value else 'none'
    if isinstance(value,str) and value in ('all','none','row','col'):return value
    raise ValueError("sharex/sharey must be bool or 'all', 'none', 'row', 'col'")


def share(owner,other,name):
    from .axes import MapAxes
    if not isinstance(other,MapAxes):raise TypeError('Sharing requires a MapAxes')
    if owner._colorbar_artist is not None or other._colorbar_artist is not None:
        raise ValueError('Colorbar axes cannot share geographic coordinates')
    previous=getattr(owner,'_share'+name)
    if previous is not None and previous is not other:raise ValueError(name+'-axis is already shared')
    source=other._shared_axes[name];old=owner._shared_axes[name]
    source.joined=True
    for member in tuple(old.members):
        source.members.add(member);member._shared_axes[name]=source
    setattr(owner,'_share'+name,other)
    copy_tickers(owner,other,name)
    limits=other.get_xlim() if name=='x' else other.get_ylim()
    owner._set_interval(name,*limits,emit=False,auto=other._autoscale_on[name])


def copy_tickers(owner,other,name):
    from .components import _detach_texts
    target=getattr(owner,name+'axis');origin=getattr(other,name+'axis')
    for field in TICKER_FIELDS:setattr(target,field,getattr(origin,field))
    for store in ('_ticks','_tick_labels','_minor_ticks','_minor_tick_labels'):
        if 'labels' in store:_detach_texts(getattr(owner,store)[name])
        getattr(owner,store)[name]=None


def sync_tickers(owner,name,*,minor=False,locator=False):
    from .components import _detach_texts
    origin=getattr(owner,name+'axis');fields=('_minor_locator','minor_locator_explicit') if minor and locator else (
        '_locator','locator_explicit') if locator else ('_minor_formatter','minor_formatter_explicit') if minor else ('_formatter','formatter_explicit')
    stores=(('_minor_ticks','_minor_tick_labels') if minor else ('_ticks','_tick_labels')) if locator else (
        ('_minor_tick_labels',) if minor else ('_tick_labels',))
    for member in tuple(owner._shared_axes[name].members):
        if member is owner:continue
        target=getattr(member,name+'axis')
        for field in fields:setattr(target,field,getattr(origin,field))
        for store in stores:
            if 'labels' in store:_detach_texts(getattr(member,store)[name])
            getattr(member,store)[name]=None
        member._changed()


def detach(owner):
    for name,group in owner._shared_axes.items():
        group.members.discard(owner)
        remaining=list(group.members)
        if remaining:
            controller=getattr(remaining[0],name+'axis')
            for field in ('_locator','_formatter','_minor_locator','_minor_formatter'):
                # Only rebind helpers attached to the group being detached.
                helper=getattr(controller,field)
                if helper.axis is not None and helper.axis.owner is owner:helper.axis=controller
            for member in remaining:
                if getattr(member,'_share'+name) is owner:setattr(member,'_share'+name,remaining[0] if member is not remaining[0] else None)
        owner._shared_axes[name]=SharedGroup(owner)
        setattr(owner,'_share'+name,None)


def configure_grid(matrix,sharex,sharey):
    for name,mode in (('x',sharex),('y',sharey)):
        for row,axes in enumerate(matrix):
            for col,ax in enumerate(axes):
                target=matrix[0][0] if mode=='all' else matrix[row][0] if mode=='row' else matrix[0][col] if mode=='col' else ax
                if target is not ax:getattr(ax,'share'+name)(target)
                if mode in (('all','col') if name=='x' else ('all','row')):ax._label_outer_axis(name)
