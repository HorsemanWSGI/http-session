import typing as t
from abc import ABC, abstractmethod


class Store(ABC):
    """Session store abstraction.
    """
    def new(self):
        return {}

    def touch(self, sid):
        """This method is similar to the `touch` unix command.
        It will update the timestamps, if that makes sense in the
        context of the session. Example of uses : file, cookie, jwt...
        """
        pass

    def flush_expired_sessions(self):
        """This method removes all the expired sessions.
        Implement if that makes sense in your store context.
        This method should be called as part of a scheduling,
        since it can be very costy.
        """
        raise NotImplementedError

    @abstractmethod
    def __iter__(self):
        """Iterates the session ids if that makes sense in the context
        of the session management.
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, sid):
        raise NotImplementedError

    @abstractmethod
    def set(self, sid, session):
        raise NotImplementedError

    @abstractmethod
    def clear(self, sid):
        raise NotImplementedError

    @abstractmethod
    def delete(self, sid):
        raise NotImplementedError


class Session(t.Mapping[str, t.Any]):
    """ HTTP session dict prototype.
    This is an abstraction on top of a simple dict.
    It has flags to track modifications and access.
    Persistence should be handled and called exclusively
    in and through this abstraction.
    """
    def __init__(self, sid, store, new=False):
        self.sid = sid
        self.store = store
        self.new = new  # boolean : this is a new session.
        self._modified = new or False
        self._data = None  # Lazy loading

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value
        self._modified = True

    def __delitem__(self, key):
        self.data.__delitem__(key)
        self._modified = True

    def __repr__(self):
        return self.data.__repr__()

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __contains__(self, key):
        return key in self.data

    def has_key(self, key):
        return key in self.data

    def get(self, key, default=None):
        return self.data.get(key, default)

    @property
    def data(self):
        if self._data is None:
            if self.new:
                self._data = self.store.new()
            else:
                self._data = self.store.get(self.sid)
        return self._data

    @property
    def accessed(self):
        return self._data is not None

    @property
    def modified(self):
        return self._modified

    def save(self):
        """Mark as dirty to allow persistence.
        This is dramatically important to use that method to mark
        the session to be written. If this method is not called,
        only new sessions or forced persistence will be taken into
        consideration.
        """
        self._modified = True

    def persist(self, force=False):
        if force or (not force and self._modified):
            self.store.set(self.sid, self.data)
            self._modified = False
        elif self.accessed:
            # We are alive, please keep us that way.
            self.store.touch(self.sid)

    def clear(self):
        self.data.clear()
        self._modified = True
