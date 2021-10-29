import typing as t
from .meta import Store, SessionData


class Session(t.Mapping[str, t.Any]):
    """ HTTP session implementation.
    This is an abstraction on top of a simple dict.
    It has flags to track modifications and access.
    Persistence should be handled and called exclusively
    in and through this abstraction.
    """
    _data: t.Optional[SessionData] = None  # Lazy loading

    def __init__(self, sid: str, store: Store, new: bool = False):
        self.sid = sid
        self.store = store
        self.new = new  # boolean : this is a new session.
        self._modified = False

    def __getitem__(self, key: str):
        return self.data[key]

    def __setitem__(self, key: str, value: t.Any):
        self.data[key] = value
        self._modified = True

    def __delitem__(self, key: str):
        self.data.__delitem__(key)
        self._modified = True

    def __repr__(self):
        return self.data.__repr__()

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __contains__(self, key: str):
        return key in self.data

    def has_key(self, key: str):
        return key in self.data

    def get(self, key: str, default: t.Any = None):
        return self.data.get(key, default)

    @property
    def data(self) -> SessionData:
        if self._data is None:
            if self.new:
                self._data = {}
            else:
                # an empty data is returned if it's expired.
                self._data = self.store.get(self.sid) or {}
        return self._data

    @property
    def accessed(self) -> bool:
        return self._data is not None

    @property
    def modified(self) -> bool:
        return self._modified

    def save(self) -> t.NoReturn:
        """Mark as dirty to allow persistence.
        This is dramatically important to use that method to mark
        the session to be written. If this method is not called,
        only new sessions or forced persistence will be taken into
        consideration.
        """
        self._modified = True

    def persist(self, force: bool = False) -> t.NoReturn:
        if force or (not force and self._modified):
            self.store.set(self.sid, self.data)
            self._modified = False
        elif self.accessed and not self.new:
            # We are alive, please keep us that way.
            self.store.touch(self.sid)

    def clear(self) -> t.NoReturn:
        self.data.clear()
        self._modified = True


SessionFactory = t.Callable[[str, Store, bool], Session]
