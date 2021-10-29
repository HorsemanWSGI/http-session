import typing as t
from abc import ABC, abstractmethod


SessionData = t.Mapping[str, t.Any]


class Store(ABC):
    """Session store abstraction.
    """
    TTL: t.Optional[int] = None

    def touch(self, sid: str) -> t.NoReturn:
        """This method is similar to the `touch` unix command.
        It will update the timestamps, if that makes sense in the
        context of the session. Example of uses : file, cookie, jwt...
        """
        pass

    def flush_expired_sessions(self) -> t.NoReturn:
        """This method removes all the expired sessions.
        Implement if that makes sense in your store context.
        This method should be called as part of a scheduling,
        since it can be very costy.
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, sid: str) -> SessionData:
        raise NotImplementedError

    @abstractmethod
    def set(self, sid: str, session: SessionData):
        raise NotImplementedError

    @abstractmethod
    def clear(self, sid: str):
        raise NotImplementedError

    @abstractmethod
    def delete(self, sid: str):
        raise NotImplementedError
