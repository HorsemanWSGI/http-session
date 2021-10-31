import uuid
import pytest
from http_session.cookie import SignedCookieManager
from unittest.mock import patch
from freezegun import freeze_time
from webtest import TestApp as WebApp


def uuid_generator(count = 0):
    while True:
        yield uuid.UUID(int=count)
        count += 1


def mock_uuid(generator):
    def uuid_patch():
        return next(generator)
    return uuid_patch


def noop(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b"Hello World!\n"]


def app(environ, start_response):
    session = environ['httpsession']
    if 'test' not in session:
        session['test'] = 42
        session.save()
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [b"I set a new value!\n"]
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b"I did nothing!\n"]


def test_wsgi_middleware_nothing_happens(store):
    manager = SignedCookieManager(store, secret='mysecret', salt="pepper")
    wsgiapp = WebApp(manager.middleware(noop))
    response = wsgiapp.get('/')
    assert response.headers.get('Set-Cookie') is None

    cookie = (
        "sid=00000000-0000-0000-0000-000000000000"
        ".YXxEsA.X2CUHMwIkHhoI3mJG7DOyWaDAjs; "
        "Expires=Fri, 29 Oct 2021 19:05:00 GMT; "
        "Domain=localhost; Path=/; Secure; SameSite=Lax"
    )
    with freeze_time('2021-10-29 19:02:00'):
        response = wsgiapp.get('/', headers={'Cookie': cookie})
    assert response.headers.get('Set-Cookie') == (
        "sid=00000000-0000-0000-0000-000000000000"
        ".YXxFKA.F1O1sUOTE3sHHrjv3tcmrO6CZ9Y; "
        "Expires=Fri, 29 Oct 2021 19:07:00 GMT; "
        "Domain=localhost; Path=/; Secure; SameSite=Lax"
    )


@patch('uuid.uuid4', mock_uuid(uuid_generator()))
def test_wsgi_middleware_save(store):
    manager = SignedCookieManager(store, secret='mysecret', salt="pepper")
    wsgiapp = WebApp(manager.middleware(app))

    with freeze_time('2021-10-29 19:00:00'):
        response = wsgiapp.get('/')

    assert response.body == b'I set a new value!\n'
    cookie = response.headers.get('Set-Cookie')
    assert cookie == (
        "sid=00000000-0000-0000-0000-000000000000"
        ".YXxEsA.X2CUHMwIkHhoI3mJG7DOyWaDAjs; "
        "Expires=Fri, 29 Oct 2021 19:05:00 GMT; "
        "Domain=localhost; Path=/; Secure; SameSite=Lax"
    )

    with freeze_time('2021-10-29 19:02:00'):
        response = wsgiapp.get('/', headers={'Cookie': cookie})

    assert response.body == b'I did nothing!\n'
    assert response.headers.get('Set-Cookie') == (
        "sid=00000000-0000-0000-0000-000000000000"
        ".YXxFKA.F1O1sUOTE3sHHrjv3tcmrO6CZ9Y; "
        "Expires=Fri, 29 Oct 2021 19:07:00 GMT; "
        "Domain=localhost; Path=/; Secure; SameSite=Lax"
    )

    with freeze_time('2021-10-29 19:10:00'):
        response = wsgiapp.get('/', headers={'Cookie': cookie})
    assert response.headers.get('Set-Cookie') == (
        "sid=00000000-0000-0000-0000-000000000001"
        ".YXxHCA.NXZRXgDkqBo3Tny1HyliOiQ53kM; "
        "Expires=Fri, 29 Oct 2021 19:15:00 GMT; "
        "Domain=localhost; Path=/; Secure; SameSite=Lax"
    )


@patch('uuid.uuid4', mock_uuid(uuid_generator()))
def test_wsgi_middleware_parameters(store):
    manager = SignedCookieManager(store, secret='mysecret', salt="pepper")
    wsgiapp = WebApp(manager.middleware(
        app, samesite='None', httponly=True))

    with freeze_time('2021-10-29 19:00:00'):
        response = wsgiapp.get('/')

    assert response.body == b'I set a new value!\n'
    cookie = response.headers.get('Set-Cookie')
    assert cookie == (
        "sid=00000000-0000-0000-0000-000000000000"
        ".YXxEsA.X2CUHMwIkHhoI3mJG7DOyWaDAjs; "
        "Expires=Fri, 29 Oct 2021 19:05:00 GMT; "
        "Domain=localhost; Path=/; Secure; HttpOnly; SameSite=None"
    )
