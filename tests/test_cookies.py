import uuid
import pytest
import hashlib
from http_session.cookie import SignedCookieManager
from http_session.session import Session
from unittest.mock import patch
from itsdangerous.exc import SignatureExpired
from freezegun import freeze_time


def uuid_generator(count = 0):
    while True:
        yield uuid.UUID(int=count)
        count += 1


def mock_uuid(generator):
    def uuid_patch():
        return next(generator)
    return uuid_patch


def test_manager_basics(store):
    manager = SignedCookieManager(store, secret='mysecret')
    assert manager.session_factory is Session
    assert manager.TTL == 300
    assert manager.cookie_name == "sid"

    manager = SignedCookieManager(store, secret='mysecret', TTL=500)
    assert manager.TTL == 500

    manager = SignedCookieManager(store, secret='mysecret', TTL=None)
    SignedCookieManager(store, secret='mysecret', TTL=None)
    assert manager.TTL is None


def test_manager_digest(store):
    manager = SignedCookieManager(store, secret='mysecret', digest='sha256')
    assert manager._signer.digest_method is hashlib.sha256

    with pytest.raises(KeyError):
        SignedCookieManager(
            store, secret='mysecret', digest='john')


def test_manager_salt(store):
    manager = SignedCookieManager(store, secret='mysecret')
    assert manager._signer.salt is not None
    assert len(manager._signer.salt) == 16


@patch('uuid.uuid4', mock_uuid(uuid_generator()))
def test_manager_generate_id(store):
    manager = SignedCookieManager(store, secret='mysecret')
    assert manager.generate_id() == '00000000-0000-0000-0000-000000000000'
    assert manager.generate_id() == '00000000-0000-0000-0000-000000000001'


@patch('uuid.uuid4', mock_uuid(uuid_generator()))
def test_get_session(store):
    manager = SignedCookieManager(store, secret='mysecret')
    session = manager.get_session(None)  # this should create a new session
    assert isinstance(session, Session)
    assert session.sid == '00000000-0000-0000-0000-000000000000'
    assert session.new is True
    assert session.data == {}


@patch('uuid.uuid4', mock_uuid(uuid_generator()))
def test_get_session(store):
    manager = SignedCookieManager(store, secret='mysecret')
    session = manager.get_session(None)  # this should create a new session
    assert isinstance(session, Session)
    assert session.sid == '00000000-0000-0000-0000-000000000000'
    assert session.new is True
    assert session.data == {}


def test_id_signature(store):
    manager = SignedCookieManager(store, secret='mysecret')
    assert manager.TTL == 300

    with freeze_time('2021-10-29 19:00:00'):
        ssid = manager.sign_id('test')
        assert manager.verify_id(ssid)

    with freeze_time('2021-10-29 19:04:00'):
        assert manager.verify_id(ssid)

    with freeze_time('2021-10-29 19:05:01'):
        with pytest.raises(SignatureExpired):
            manager.verify_id(ssid)


def test_create_cookie_with_expiration(store):
    manager = SignedCookieManager(store, secret='mysecret', salt="pepper")
    with freeze_time('2021-10-29 19:00:00'):
        cookie = manager.cookie('test')
    assert cookie == (
        'sid=test.YXxEsA.O7ZKiljgyFx7xSSUgR69oZCbcf8; '
        'Expires=Fri, 29 Oct 2021 19:05:00 GMT; '
        'Domain=localhost; Path=/; '
        'Secure; SameSite=Lax'
    )

    with freeze_time('2021-10-29 19:02:00'):
        assert manager.get_id(cookie) == 'test'

    with freeze_time('2021-10-29 19:06:00'):
        assert manager.get_id(cookie) is None

    with pytest.raises(ValueError) as exc:
        cookie = manager.cookie('test', secure=False, samesite='None')
    assert str(exc.value) == "SameSite `None` requires a secure context."

    manager = SignedCookieManager(
        store, secret='mysecret', salt="pepper", TTL=600)
    with freeze_time('2021-10-29 23:59:00'):
        cookie = manager.cookie('test', samesite='None')
    assert cookie == (
        'sid=test.YXyKxA.DEUCVRD9agn_9TlJKYvr4twBl1s; '
        'Expires=Sat, 30 Oct 2021 00:09:00 GMT; '
        'Domain=localhost; Path=/; '
        'Secure; SameSite=None'
    )

    with freeze_time('2021-10-30 00:02:00'):
        assert manager.get_id(cookie) == 'test'

    with freeze_time('2021-10-30 00:16:00'):
        assert manager.get_id(cookie) is None

    with pytest.raises(ValueError) as exc:
        manager.cookie('test'*1500)
    assert str(exc.value) == "The Cookie is over 4093 bytes."


def test_create_session_cookie(store):
    manager = SignedCookieManager(
        store, secret='mysecret', salt="pepper", TTL=None)
    with freeze_time('2021-10-29 19:00:00'):
        cookie = manager.cookie('test')
    assert cookie == (
        'sid=test.YXxEsA.O7ZKiljgyFx7xSSUgR69oZCbcf8; '
        'Domain=localhost; Path=/; Secure; SameSite=Lax'
    )
    assert manager.get_id(cookie) == 'test'

    with pytest.raises(ValueError) as exc:
        cookie = manager.cookie('test', secure=False, samesite='None')
    assert str(exc.value) == "SameSite `None` requires a secure context."

    manager = SignedCookieManager(
        store, secret='mysecret', salt="pepper", TTL=None)
    with freeze_time('2021-10-29 23:59:00'):
        cookie = manager.cookie('test', samesite='None')
    assert cookie == (
        'sid=test.YXyKxA.DEUCVRD9agn_9TlJKYvr4twBl1s; '
        'Domain=localhost; Path=/; Secure; SameSite=None'
    )

    with pytest.raises(ValueError) as exc:
        manager.cookie('test'*1500)
    assert str(exc.value) == "The Cookie is over 4093 bytes."
