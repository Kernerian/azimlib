"""Owned editable artists, change notifications and draw invalidation.

No plotting framework is imported. Geographic layers keep their existing
handles; this protocol supplies their common lifecycle.
"""
from contextlib import contextmanager
from functools import wraps
from .callbacks import CallbackRegistry

_interactive = False


def isinteractive():
    return _interactive


class _InteractiveContext:
    def __init__(self, previous):
        self.previous = previous
    def __enter__(self):
        return self
    def __exit__(self, *args):
        global _interactive
        _interactive = self.previous


def ion():
    global _interactive
    context = _InteractiveContext(_interactive)
    _interactive = True
    return context


def ioff():
    global _interactive
    context = _InteractiveContext(_interactive)
    _interactive = False
    return context


def artist_mutation(method):
    """Coalesce nested setters on one artist; failed edits do not notify."""
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        with self._mutation():
            result = method(self, *args, **kwargs)
            self._changed()
        return result
    return wrapped


class Artist:
    def __init__(self, parent=None):
        self._artist_parent = parent
        self._stale = True
        self.stale_callback = None
        self._artist_callbacks = CallbackRegistry(('pchanged',))
        self._mutation_depth = 0
        self._mutation_pending = False

    def _ensure_artist(self):
        if not hasattr(self, '_artist_callbacks'):
            Artist.__init__(self)

    def _bind_parent(self, parent):
        self._ensure_artist()
        self._artist_parent = parent

    def get_figure(self, root=False):
        node = self
        seen = set()
        while node is not None and id(node) not in seen:
            seen.add(id(node))
            if getattr(node, '_is_figure', False):
                return node
            node = getattr(node, '_artist_parent', None)
        return None

    @property
    def stale(self):
        return getattr(self, '_stale', True)

    @stale.setter
    def stale(self, value):
        self._ensure_artist()
        self._stale = bool(value)
        if not value:
            return
        parent = self._artist_parent
        if parent is not None:
            parent.stale = True
        elif getattr(self, '_is_figure', False) and isinteractive() and not getattr(self, '_composing', False):
            canvas = getattr(self, 'canvas', None)
            if canvas is not None:
                canvas.draw_idle()
        if self.stale_callback is not None:
            self.stale_callback(self, True)

    def add_callback(self, func):
        self._ensure_artist()
        return self._artist_callbacks.connect('pchanged', func)

    def remove_callback(self, oid):
        self._ensure_artist()
        self._artist_callbacks.disconnect(oid)

    def pchanged(self):
        self._ensure_artist()
        self._artist_callbacks.process('pchanged', self)

    def _changed(self):
        self._ensure_artist()
        if self._mutation_depth:
            self._mutation_pending = True
            return
        # Invalidate first so a callback observes the committed dirty figure.
        self.stale = True
        self.pchanged()

    @contextmanager
    def _mutation(self):
        self._ensure_artist()
        outer = self._mutation_depth == 0
        previous = self._mutation_pending
        self._mutation_depth += 1
        try:
            yield
        except BaseException:
            self._mutation_pending = previous
            raise
        finally:
            self._mutation_depth -= 1
            if outer and self._mutation_pending:
                self._mutation_pending = False
                self._changed()

    def get_picker(self):return getattr(self,'_picker',None)
    @artist_mutation
    def set_picker(self,value):
        import math
        if value is not None and not callable(value) and not isinstance(value,bool):
            value=float(value)
            if not math.isfinite(value) or value<0:raise ValueError('picker radius must be finite nonnegative pixels')
        self._picker=value
    def get_pickradius(self):return getattr(self,'_pickradius',5.)
    @artist_mutation
    def set_pickradius(self,value):
        import math
        value=float(value)
        if not math.isfinite(value) or value<0:raise ValueError('pickradius must be finite nonnegative pixels')
        self._pickradius=value
    def contains(self,mouseevent):
        from .picking import contains
        return contains(self,mouseevent)
    def pick(self,mouseevent):
        from .picking import pick
        return pick(mouseevent.canvas,mouseevent,only=self)

    def get_clip_on(self):return getattr(self,'_clip_on',True)
    @artist_mutation
    def set_clip_on(self,value):self._clip_on=bool(value)

    def get_transform(self):
        from .transforms import IdentityTransform
        explicit=getattr(self,'_transform',None)
        if explicit is not None:return explicit
        axes=getattr(self,'axes',None)
        if axes is not None:
            options=getattr(self,'options',{})
            return axes.transAxes if options.get('transform')=='axes' else axes.transData
        return IdentityTransform()

    @artist_mutation
    def set_transform(self,transform):
        from .transforms import Transform
        if not isinstance(transform,Transform):raise TypeError('Require an Azimlib Transform')
        figure=self.get_figure(root=True)
        if figure is not None and any(owner is not figure for owner in transform.owners()):raise ValueError('Transform belongs to another figure')
        self._transform=transform

    def set_in_layout(self, value):
        self._in_layout = bool(value)
        self._changed()

    def get_in_layout(self):
        return getattr(self, '_in_layout', True)

    def get_children(self):
        return []

    def findobj(self, match=None, include_self=True):
        if match is not None and not isinstance(match, type) and not callable(match):
            raise TypeError('match must be an Artist type or a predicate')
        predicate = (lambda a: True) if match is None else (lambda a: isinstance(a, match)) if isinstance(match, type) else match
        result, seen = [], set()
        def visit(artist, include):
            if id(artist) in seen:
                return
            seen.add(id(artist))
            for child in artist.get_children():
                visit(child, True)
            if include and predicate(artist):
                result.append(artist)
        visit(self, include_self)
        return result

    def properties(self):
        # Only editable properties: avoid executing getters that compose maps.
        result = {}
        for name in dir(type(self)):
            if name.startswith('get_') and callable(getattr(self, name)):
                key = name[4:]
                if callable(getattr(self, 'set_' + key, None)):
                    # A Layer supports different properties for lines/text.
                    if key in self._unsupported_properties():continue
                    result[key] = getattr(self, name)()
        result.update(getattr(self, 'style', {}))
        return result

    def _unsupported_properties(self):
        return set()

    def set(self, **kwargs):
        setters = []
        for name, value in kwargs.items():
            setter = getattr(self, 'set_' + name, None)
            if not callable(setter):
                raise AttributeError(f'{type(self).__name__} has no property {name!r}')
            setters.append((setter, value))
        with self._mutation():
            for setter, value in setters:
                setter(value)
        return self

    def update(self, props):
        return self.set(**props)


def _artists(value):
    if isinstance(value, Artist):
        yield value
    else:
        for item in value:
            yield from _artists(item)


def setp(artists, *args, **kwargs):
    """Set properties on an artist or nested sequence of artists."""
    if len(args) % 2:
        raise ValueError('Positional properties require name/value pairs')
    props = dict(zip(args[::2], args[1::2]))
    props.update(kwargs)
    for artist in _artists(artists):
        artist.set(**props)


def getp(artist, property=None):
    if property is None:
        return artist.properties()
    getter = getattr(artist, 'get_' + property, None)
    if callable(getter):
        return getter()
    # Preserve a family's actual get_size (e.g. orientation), resolving a
    # style alias only when that spelling has no dedicated getter.
    from .styles import _ALIASES
    property=_ALIASES.get(property,property)
    getter=getattr(artist,'get_'+property,None)
    if callable(getter):return getter()
    props = artist.properties()
    if property not in props:
        raise AttributeError(f'Unknown property {property!r}')
    return props[property]
