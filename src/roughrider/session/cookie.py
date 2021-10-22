import typing as t
import itsdangerous
from biscuits import parse, Cookie
from datetime import datetime, timedelta
from functools import wraps
from uuid import uuid4
from roughrider.session.prototypes import Session, Store


class SignedCookieManager:

    def __init__(self, store: Store, secret: str, cookie_name: str = 'sid'):
        self.store = store
        self.delta: int = store.delta  # lifespan delta in seconds.
        self.cookie_name = cookie_name
        self._signer = itsdangerous.TimestampSigner(secret)

    def generate_id(self):
        return str(uuid4())

    def refresh_id(self, sid: str):
        return str(self._signer.sign(sid), 'utf-8')

    def verify_id(self, sid: str) -> bool:
        return self._signer.unsign(sid, max_age=self.delta)

    def get_session(self, cookie) -> Session:
        """Override to change the session baseclass, if needed.
        """
        new, sid = self.get_id(cookie)
        return Session(sid, self.store, new=new)

    def get_id(self, cookie):
        if cookie is not None:
            morsels = parse(cookie)
            signed_sid = morsels.get(self.cookie_name)
            if signed_sid is not None:
                try:
                    sid = self.verify_id(signed_sid)
                    return False, str(sid, 'utf-8')
                except itsdangerous.exc.SignatureExpired:
                    # Session expired. We generate a new one.
                    pass
        return True, self.generate_id()

    def cookie(self, sid: str, path: str = "/", domain: str = "localhost"):
        """We enforce the expiration.
        """
        # Refresh the signature on the sid.
        ssid = self.refresh_id(sid)

        # Generate the expiration date using the delta
        expires = datetime.now() + timedelta(seconds=self.delta)

        # Create the cookie containing the ssid.
        cookie = Cookie(
            name=self.cookie_name, value=ssid, path=path,
            domain=domain, expires=expires)

        value = str(cookie)

        # Check value
        if len(value) > 4093:  # 4096 - 3 bytes of overhead
            raise ValueError('The Cookie is over 4093 bytes.')

        return value

    def middleware(self, app, environ_key: str = 'httpsession'):

        @wraps(app)
        def session_wrapper(environ, start_response):

            def session_start_response(status, headers, exc_info=None):
                # Write down the session
                # This relies on the good use of the `save` method.
                session = environ[environ_key]
                session.persist()

                # Prepare the cookie
                path = environ['SCRIPT_NAME'] or '/'
                domain = environ['HTTP_HOST'].split(':', 1)[0]
                cookie = self.cookie(session.sid, path, domain)

                # Write the cookie header
                headers.append(('Set-Cookie', cookie))

                # Return normally
                return start_response(status, headers, exc_info)

            session = self.get_session(environ.get('HTTP_COOKIE'))
            environ[self.environ_key] = session
            return app(environ, session_start_response)

        return session_wrapper
