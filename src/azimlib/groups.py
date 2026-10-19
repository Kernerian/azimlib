"""Owned Layer groups: flat render list, explicit hierarchy, no duplicate Artists."""
from collections.abc import MutableMapping
from .artist import Artist,artist_mutation
from .geometry import _number
from .styles import style_dict


class _GroupStyle(MutableMapping):
    """Local properties override nearest-group defaults; data never enter styles."""
    def __init__(self,layer,local):self.layer,self.local=layer,dict(local)
    def _values(self):
        group=getattr(self.layer,'_group',None)
        return dict(group.effective_style() if group else {},**self.local)
    def __getitem__(self,key):return self._values()[key]
    def __iter__(self):return iter(self._values())
    def __len__(self):return len(self._values())
    def __setitem__(self,key,value):self.local[key]=value
    def __delitem__(self,key):del self.local[key]
    def __contains__(self,key):return key in self._values()
    def pop(self,key,*default):return self.local.pop(key,*default)


class ArtistGroup(Artist):
    """A hierarchy of Layers owned by exactly one existing 2D MapAxes.

    Child visibility is ANDed with ancestors. Zorder offsets add. Group styles
    are defaults (nearest group wins, then local Artist properties). Group
    clipping can force the existing Axes rectangle, never an arbitrary path.
    Picking continues to report the leaf Artist, not an ambiguous duplicate.
    """
    def __init__(self,axes,*,name='',parent=None,style=None,zorder=0,visible=True,clip_on=True):
        from .axes import MapAxes
        if not isinstance(axes,MapAxes) or getattr(axes,'_terrain3d',False) or axes._colorbar_artist is not None:
            raise TypeError('Groups require a live 2D geographic MapAxes')
        if axes.get_figure() is None:raise ValueError('Axes is detached')
        if not isinstance(name,str):raise TypeError('Group name must be a string')
        if parent is not None and (not isinstance(parent,ArtistGroup) or parent.axes is not axes):raise ValueError('Parent belongs to another Axes')
        self._axes=axes;self._children=[];self._group=None;self.name=name
        self._style=self._validated_style(style or {});self._zorder=_number(zorder,'zorder')
        self._visible=bool(visible);self._clip_on=bool(clip_on)
        Artist.__init__(self,axes)
        axes._groups.append(self)
        if parent is not None:parent.add(self)
        self._changed()

    @property
    def axes(self):return self._axes
    def get_body(self):return self.axes.get_body() if self.axes else None
    def _changed(self):
        # Existing label/cache keys depend on leaf change serials. Group edits
        # must invalidate those keys too, without replacing geometry or handles.
        for child in tuple(getattr(self,'_children',())):child._changed()
        super()._changed()
    def get_children(self):return list(self._children)
    def get_visible(self):return self._visible and (self._group is None or self._group.get_visible())
    def get_local_visible(self):return self._visible
    def get_zorder(self):return self._zorder+(self._group.get_zorder() if self._group else 0)
    def get_clip_on(self):return self._clip_on or bool(self._group and self._group.get_clip_on())
    def effective_style(self):return dict(self._group.effective_style() if self._group else {},**self._style)

    @staticmethod
    def _validated_style(value):
        parsed=style_dict(dict(value))
        allowed={'color','facecolor','edgecolor','alpha','linewidth','linestyle','marker','markersize',
                 'markerfacecolor','markeredgecolor','markeredgewidth','hatch'}
        if set(parsed)-allowed:raise ValueError('Group styles are visual defaults only; unsupported keys: '+str(sorted(set(parsed)-allowed)))
        return parsed

    def _require_live(self):
        if self._axes is None:raise ValueError('Group is detached')

    @artist_mutation
    def add(self,artist):
        from .layers import Layer
        self._require_live()
        if not isinstance(artist,(Layer,ArtistGroup)):raise TypeError('Group children must be Layers or groups')
        if artist.axes is not self.axes:raise ValueError('Group and child must belong to the same Axes; instantiate per viewport')
        node=self
        while node is not None:
            if node is artist:raise ValueError('Group cycles are forbidden')
            node=node._group
        if getattr(artist,'_group',None) is not None:raise ValueError('Artist already has a group; remove it explicitly before reparenting')
        if isinstance(artist,Layer) and not isinstance(artist.style,_GroupStyle):artist.style=_GroupStyle(artist,artist.style)
        artist._group=self;self._children.append(artist)
        # Stale propagates through the group, while Layer.axes remains stable.
        artist._bind_parent(self);artist._changed()
        return artist

    @artist_mutation
    def discard(self,artist):
        self._require_live()
        if not any(a is artist for a in self._children):raise ValueError('Artist is not a direct child')
        self._children[:]=[a for a in self._children if a is not artist]
        artist._group=None;artist._bind_parent(self.axes)
        if hasattr(artist,'style') and isinstance(artist.style,_GroupStyle):artist.style=dict(artist.style.local)
        artist._changed();return artist

    def _forget(self,artist):
        self._children[:]=[a for a in self._children if a is not artist]
        artist._group=None
        if hasattr(artist,'style') and isinstance(artist.style,_GroupStyle):artist.style=dict(artist.style.local)
        self._changed()

    @artist_mutation
    def set_visible(self,value):self._require_live();self._visible=bool(value)
    @artist_mutation
    def set_zorder(self,value):self._require_live();self._zorder=_number(value,'zorder offset')
    @artist_mutation
    def set_clip_on(self,value):self._require_live();self._clip_on=bool(value)
    @artist_mutation
    def set_style(self,**values):
        self._require_live();self._style=self._validated_style(values)

    def set_transform(self,transform):
        raise NotImplementedError('Phase A groups do not transform descendant coordinates; edit leaf Artists explicitly')

    def set_picker(self,picker):
        raise NotImplementedError('Phase A picking targets leaf Artists; aggregate group picking is not implemented')

    def remove(self):
        if self._axes is None:return
        axes=self._axes
        for child in tuple(self._children):child.remove()
        if self._group is not None:self._group._forget(self)
        axes._groups[:]=[g for g in axes._groups if g is not self]
        self._changed();self._axes=None;self._bind_parent(None)

    def instantiate(self,axes):
        """Fresh visual instances over immutable geometry; no shared callbacks."""
        from .layers import Layer
        self._require_live()
        if axes.get_context()!=self.axes.get_context():raise ValueError('Cannot instantiate data in another Body/coordinate context')
        def validate(group):
            for child in group._children:
                if isinstance(child,ArtistGroup):validate(child)
                elif (type(child) is not Layer or child.kind!='geometry' or getattr(child,'_transform',None) is not None
                      or set(child.options)-{'feature_style','fit'} or child.options.get('feature_style') is not None):
                    raise NotImplementedError('Phase A cloning supports plain immutable geometry Layers without transforms/options')
        validate(self)
        def clone(group,parent=None):
            result=ArtistGroup(axes,name=group.name,parent=parent,style=group._style,zorder=group._zorder,
                               visible=group._visible,clip_on=group._clip_on)
            for child in group._children:
                if isinstance(child,ArtistGroup):clone(child,result)
                else:
                    local=dict(child.style.local) if isinstance(child.style,_GroupStyle) else dict(child.style)
                    new=Layer('geometry',child.data,local,dict(child.options),visible=child.get_local_visible())
                    new._body_context=child.get_context()
                    axes.add_collection(new,autolim=False);result.add(new)
            return result
        return clone(self)
