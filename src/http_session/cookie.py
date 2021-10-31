import uuid
import secrets
import typing as t
import hashlib
import itsdangerous
from enum import Enum
from biscuits import parse, Cookie
from datetime import datetime, timedelta
from functools import wraps
from .meta import Store
from .session import Session, SessionFactory


HashAlgorithm = Enum(
    'Algorithm', {
        name: getattr(hashlib, name)
        for name in hashlib.algorithms_guaranteed
    }
)


class SameSite(Enum):
    lax = 'Lax'
    strict = 'Strict'
    none = 'None'


class SignedCookieManager:

    def __init__(self,
                 store: Store,
                 secret: str,
                 salt: t.Optional[str] = None,
                 digest: str = HashAlgorithm.sha1.name,
                 TTL: t.Optional[int] = 300,  # lifespan in seconds.
                 cookie_name: str = 'sid',
                 session_factory: SessionFactory = Session):
        self.store = store
        self.TTL = TTL
        self.cookie_name = cookie_name
        self.session_factory = session_factory
        if salt is None:
            salt = secrets.token_hex(8)
        self._signer = itsdangerous.TimestampSigner(
            secret, salt=salt,
            digest_method=HashAlgorithm[digest].value
        )

    def generate_id(self):
        return str(uuid.uuid4())

    def sign_id(self, sid: str) -> str:
        return str(self._signer.sign(sid), 'utf-8')

    def verify_id(self, sid: str) -> bool:
        if self.TTL:
            return self._signer.unsign(sid, max_age=self.TTL)
        return self._signer.unsign(sid)

    def get_session(self, cookie: t.Optional[str] = None) -> Session:
        if cookie is not None:
            sid = self.get_id(cookie)
            if sid is not None:
                return self.session_factory(sid, self.store, new=False)
        sid = self.generate_id()
        return self.session_factory(sid, self.store, new=True)

    def get_id(self, cookie: str):
        morsels = parse(cookie)
        signed_sid = morsels.get(self.cookie_name)
        if signed_sid is not None:
            try:
                sid = self.verify_id(signed_sid)
                return str(sid, 'utf-8')
            except itsdangerous.exc.SignatureExpired:
                # Session expired. We generate a new one.
                pass

    def cookie(self,
               sid: str,
               path: str = "/",
               domain: str = "localhost",
               secure: bool = True,
               samesite: SameSite = SameSite.lax,
               httponly: bool = False):
        """We enforce the expiration.
        """
        samesite = SameSite(samesite)
        if samesite is SameSite.none and not secure:
            raise ValueError('SameSite `None` requires a secure context.')

        if self.TTL:
            # Generate the expiration date using the TTL
            expires = datetime.now() + timedelta(seconds=self.TTL)
        else:
            expires = None

        # Create the cookie containing the ssid.
        cookie = Cookie(
            name=self.cookie_name,
            value=self.sign_id(sid),
            path=path,
            domain=domain,
            secure=secure,
            expires=expires,
            samesite=samesite.value,
            httponly=httponly,
        )

        value = str(cookie)

        # Check value
        if len(value) > 4093:  # 4096 - 3 bytes of overhead
            raise ValueError('The Cookie is over 4093 bytes.')

        return value

    def middleware(self, app,
                   environ_key: str = 'httpsession',
                   secure: bool = True,
                   samesite: SameSite = SameSite.lax,
                   httponly: bool = False):

        @wraps(app)
        def session_wrapper(environ, start_response):

            def session_start_response(status, headers, exc_info=None):
                # Write down the session
                # This relies on the good use of the `save` method.
                session = environ[environ_key]
                if session.modified or not session.new:
                    session.persist()
                    # Prepare the cookie
                    path = environ['SCRIPT_NAME'] or '/'
                    domain = environ['HTTP_HOST'].split(':', 1)[0]
                    cookie = self.cookie(
                        session.sid,
                        path,
                        domain,
                        secure=secure,
                        samesite=samesite,
                        httponly=httponly
                    )

                    # Write the cookie header
                    headers.append(('Set-Cookie', cookie))

                # Return normally
                return start_response(status, headers, exc_info)

            session = self.get_session(environ.get('HTTP_COOKIE'))
            environ[environ_key] = session
            return app(environ, session_start_response)

        return session_wrapper
