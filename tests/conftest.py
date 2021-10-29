import pytest
from copy import deepcopy
from http_session.meta import Store
from unittest.mock import Mock


class MemoryStore(Store):

    def __init__(self, TTL=None):
        self._store = {}
        self.touch = Mock()
        self.TTL = TTL

    def __iter__(self):
        return iter(self._store.keys())

    def get(self, sid):
        """We return a copy, to avoid mutability by reference.
        """
        data = self._store.get(sid)
        if data is not None:
            return deepcopy(data)
        return data

    def set(self, sid, session):
        self._store[sid] = session

    def clear(self, sid):
        if sid in self._store:
            self._store[sid].clear()

    def delete(self, sid):
        del self._store[sid]


@pytest.fixture(scope="function")
def store():
    return MemoryStore()
