"""
The session prototype provides a base implementation of an
HTTP Session based  Mapping type.

The session object assumes that the data is presented as a mapping
and handles it accordingly.
"""
from http_session.session import Session


def test_session_creation(store):
    """The `new` flag is set to mark the session has a brand new : it does
    not exist in store. Since it's a new session, it's marked as dirty to
    be persisted through the 'modified' attribute.

    `_data` is lazily loaded hence not using the accessor should yield
    a None value.
    """
    session = Session('a sid', store, new=True)
    assert session.accessed is False
    assert session.modified is False
    assert session._data is None

    assert session.data == {}
    assert session._data is not None
    assert session.accessed is True

    # No session yet as we didn't persist
    assert list(store) == []

    # Persisting and checks
    session.save()
    session.persist()
    assert list(store) == ['a sid']


def test_session_attribution(store):
    session = Session('a sid', store, new=True)
    session.persist()

    assert session.data == {}
    assert session.modified is False

    session['my var'] = 12
    assert session.modified is True

    assert session.data == {'my var': 12}
    assert list(session) == list(session.keys()) == ['my var']
    assert list(session.values()) == [12]
    assert session.get('my var') == 12
    assert session.get('unknown') is None
    assert session.get('unknown', ...) is ...


def test_session_persistence(store):
    # we created a new session
    session = Session('a sid', store, new=True)
    session.persist(force=True)

    # we continue an existing session
    # Accessing directly the data doesn't trigger the flag value setting
    session = Session('a sid', store)
    session.data['my var'] = 12
    assert session.modified is False

    # A persistence without a force flag, when not mofidied
    # will just trigged a 'touch' update
    session.persist()
    store.touch.assert_called_once_with('a sid')
    store.touch.reset_mock()
    assert store.get('a sid') == {}

    # A forced persistence will do an overriding write
    session.persist(force=True)
    assert store.get('a sid') == {'my var': 12}

    # Another way to do it is to mark it for save
    session = Session('a sid', store)
    session.data['other var'] = 42
    assert session.modified is False

    session.save()
    assert session.modified is True

    session.persist()
    assert store.get('a sid') == {'other var': 42, 'my var': 12}


def test_session_clear(store):
    session = Session('a sid', store, new=True)
    session['my var'] = 12
    session.persist()
    assert store.get('a sid') == {'my var': 12}

    session.clear()
    assert session.data == {}
    assert session.modified is True
    session.persist()
    assert store.get('a sid') == {}
