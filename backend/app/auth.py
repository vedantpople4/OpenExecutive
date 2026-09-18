"""Supabase token verification and this backend's own session cookie.

Two credentials, deliberately of two different kinds:

  * Supabase issues the access token the browser holds. It is a JWT signed with
    the project's ES256 private key. This process only ever sees the public half
    (via JWKS), so it can verify a token and can never mint one.
  * This backend issues its own cookie in exchange. It is an itsdangerous signed
    value, not a JWT. Keeping it out of JWT-land means this process contains no
    symmetric JWT verification path at all -- there is nothing for the classic
    alg=HS256 confusion attack against the Supabase token to land in, because a
    forged HS256 token has no verifier here even in principle.

Nothing in this module logs a token, a cookie value, or a decoded claim set.
"""

from __future__ import annotations

import jwt
from fastapi import HTTPException, Request, Response
from itsdangerous import BadSignature, URLSafeTimedSerializer
from jwt import PyJWKClient

from app.config import get_settings

# The only algorithms this process will verify, checked before any key is
# fetched. Supabase is on asymmetric signing keys, so a token arriving as HS256
# is an attack rather than an old client, and gets no key lookup at all.
ALLOWED_ALGORITHMS = ["ES256"]

# What Supabase stamps on a token for a signed-in (non-anonymous) user.
EXPECTED_AUDIENCE = "authenticated"

# Longer than Supabase's one-hour access token, so a single missed refresh or a
# deliberation that streams for many minutes does not 401 mid-flight. Short
# enough that a stolen cookie dies within the working day -- which is the only
# bound there is, since nothing revokes an issued cookie yet.
SESSION_TTL_SECONDS = 8 * 60 * 60

_settings = get_settings()

# Module-level so the fetched JWKS is cached across requests rather than
# re-fetched per login. Constructing it performs no network call; the first
# get_signing_key_from_jwt does.
jwk_client = PyJWKClient(_settings.supabase_jwks_url, cache_keys=True)

# Salted so this signer's output can never be replayed against a different
# itsdangerous signer that happens to share the secret.
_serializer = URLSafeTimedSerializer(_settings.session_secret, salt="openexec.session")


def verify_supabase_jwt(token: str) -> dict:
    """Verify a Supabase access token against the project's published JWKS.

    Raises a jwt exception on any failure. Callers map that to a 401 with a
    fixed message; no part of the token reaches the response or the logs.
    """
    header = jwt.get_unverified_header(token)
    if header.get("alg") not in ALLOWED_ALGORITHMS:
        raise jwt.InvalidAlgorithmError("token algorithm is not accepted")

    signing_key = jwk_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=ALLOWED_ALGORITHMS,
        audience=EXPECTED_AUDIENCE,
        options={"require": ["exp", "sub"]},
    )


def set_session_cookie(response: Response, user_id: str) -> None:
    """Issue the backend's session cookie. The one place these flags are set."""
    response.set_cookie(
        key=get_settings().session_cookie_name,
        value=_serializer.dumps(user_id),
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=True,
        samesite="strict",
        path="/",
    )


def get_current_user(request: Request) -> str:
    """FastAPI dependency resolving the signed-in user id from the cookie.

    Not attached to any route yet; it lands with the routes it protects.
    """
    raw = request.cookies.get(get_settings().session_cookie_name)
    if raw is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        # max_age here, not just the cookie's: a client controls what it sends
        # back, so the server-side age check is the one that binds.
        user_id: str = _serializer.loads(raw, max_age=SESSION_TTL_SECONDS)
    except BadSignature as exc:
        raise HTTPException(status_code=401, detail="Not authenticated") from exc
    return user_id


def verify_origin(request: Request) -> None:
    """CSRF guard for cookie-authenticated, state-changing routes.

    Not attached to any route yet; it lands with the routes it protects.

    A missing Origin is rejected along with a mismatched one. Browsers send the
    header on every cross-origin fetch and on every same-origin non-GET, so its
    absence means the request did not come from a page this backend serves.
    """
    origin = request.headers.get("origin")
    if origin is None or origin not in get_settings().cors_origins:
        raise HTTPException(status_code=403, detail="Origin not allowed")
