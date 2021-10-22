roughrider.session
******************

``roughrider.session`` is the foundation of a session management system.
The provided prototypes allow implementations using a wide array of
backends.

`roughrider.session` provides three prototypes that are interconnected.

The "store" prototyped in `roughrider.session.prototypes.Store`
represents a store handling sessions. This store knows how to
retrieve, persist, clear or create sessions, using their SID.

The "session" prototyped in
`roughrider.session.prototypes.Session` represents the session iself.
It is discriminated by its sid and is able to set and get key/value
pairs and track the modifications and accesses.

The "manager" oversees the store and session,
in order to interface them with the browser. It is mainly used as a
SID policy and middleware. A functional implementation is
provided in `roughrider.session.cookie.SignedCookieManager`
using cookies to keep track of the sid and expiration.
