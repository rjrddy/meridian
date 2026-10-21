# Single-operator authentication

Context: run creation and replay expose control-plane operations even in a demo.
Options: public anonymous controls, external OAuth, local password plus server-side sessions.
Decision: environment-provided password, salted scrypt verification, random expiring server sessions, HttpOnly SameSite strict cookie and session-bound CSRF proof for writes and WebSockets. Do not put credentials in URL strings. Bound login/write/client maps, session count and viewer count.
Tradeoffs: no password recovery, roles, persistent sessions or distributed rate limiter. TLS and Secure cookies are required on hosted deployments. Restart logs everyone out. This is a demonstrator rather than an enterprise identity provider.
