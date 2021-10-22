http-session
************

``http_session`` is the foundation of a session management system.
The provided prototypes allow implementations using a wide array of
backends.

``http_session`` relies on three components:

The "store" prototyped in `http_session.meta.Store`
represents a store handling sessions. This store knows how to
retrieve, persist, clear or create sessions, using their SID.

The "session" implemented in `http_session.session.Session` represents
the session iself. It is discriminated by its sid and is able to set
and get key/value pairs and track the modifications and accesses.

The "manager" oversees the store and session, in order to interface
them with the browser. It is mainly used as a SID policy and middleware.
A functional implementation using secure cookies is provided in
`http_session.cookie.SignedCookieManager`.
