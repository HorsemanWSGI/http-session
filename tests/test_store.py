"""
The store prototype is a class abstraction. It is meant to be
subclassed as the inner workings can't be generic as they heavily depend
on the backend.
"""

import pytest
from http_session.meta import Store


def test_store_instance():

    with pytest.raises(TypeError) as exc:
        Store()

    assert str(exc.value) == (
        "Can't instantiate abstract class Store with abstract "
        "methods clear, delete, get, set"
    )
