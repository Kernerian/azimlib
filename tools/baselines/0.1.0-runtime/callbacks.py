"""Small, independent signal registry; bound methods do not retain owners."""
from contextlib import contextmanager
import inspect
import weakref


class CallbackRegistry:
    def __init__(self, signals=None):
        self.signals = None if signals is None else frozenset(signals)
        self._callbacks = {}
        self._next_id = 0
        self._blocked = []

    def _check(self, signal):
        if self.signals is not None and signal not in self.signals:
            raise ValueError(f'Unknown signal {signal!r}')

    def connect(self, signal, callback):
        self._check(signal)
        if not callable(callback):
            raise TypeError('callback must be callable')
        for cid, (name, ref, weak) in tuple(self._callbacks.items()):
            target = ref() if weak else ref
            if target is None:
                self.disconnect(cid)
            elif name == signal and target == callback:
                return cid
        self._next_id += 1
        cid = self._next_id
        weak = inspect.ismethod(callback) and callback.__self__ is not None
        ref = weakref.WeakMethod(callback, lambda ref: self.disconnect(cid)) if weak else callback
        self._callbacks[cid] = signal, ref, weak
        return cid

    def disconnect(self, cid):
        self._callbacks.pop(cid, None)

    def process(self, signal, *args, **kwargs):
        self._check(signal)
        if any(value is None or value == signal for value in self._blocked):
            return
        # A snapshot allows callbacks to connect/disconnect while dispatching.
        for cid, (name, ref, weak) in tuple(self._callbacks.items()):
            if name != signal or cid not in self._callbacks:
                continue
            callback = ref() if weak else ref
            if callback is not None:
                callback(*args, **kwargs)

    @contextmanager
    def blocked(self, *, signal=None):
        if signal is not None:
            self._check(signal)
        self._blocked.append(signal)
        try:
            yield
        finally:
            self._blocked.pop()
