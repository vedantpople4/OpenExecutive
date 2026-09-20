"""No real Supabase project is reachable from a test process, so these tests
sign tokens with a locally-generated EC keypair and monkeypatch the module's
PyJWKClient to hand back its public half -- verify_supabase_jwt never learns
the difference, since it only ever sees a key object with the right curve."""

from __future__ import annotations

import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app import auth
from app.main import app

client = TestClient(app)

_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())
_PUBLIC_KEY = _PRIVATE_KEY.public_key()


def _sign(claims: dict, *, alg: str = "ES256", key=None) -> str:
    return jwt.encode(claims, key or _PRIVATE_KEY, algorithm=alg)


def _valid_claims(**overrides) -> dict:
    claims = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    claims.update(overrides)
    return claims


@pytest.fixture(autouse=True)
def _stub_jwks(monkeypatch):
    class _Key:
        key = _PUBLIC_KEY

    monkeypatch.setattr(auth.jwk_client, "get_signing_key_from_jwt", lambda token: _Key())


def test_verify_supabase_jwt_accepts_a_validly_signed_token():
    token = _sign(_valid_claims())
    claims = auth.verify_supabase_jwt(token)
    assert claims["sub"] == "11111111-1111-1111-1111-111111111111"


def test_verify_supabase_jwt_rejects_expired_token():
    token = _sign(_valid_claims(exp=int(time.time()) - 60))
    with pytest.raises(jwt.ExpiredSignatureError):
        auth.verify_supabase_jwt(token)


def test_verify_supabase_jwt_rejects_wrong_audience():
    token = _sign(_valid_claims(aud="some-other-project"))
    with pytest.raises(jwt.InvalidAudienceError):
        auth.verify_supabase_jwt(token)


def test_verify_supabase_jwt_rejects_hs256_even_with_a_guessed_secret():
    """The alg-confusion attack this design exists to close: a token signed
    HS256 using the ES256 public key (PEM bytes) as the HMAC secret must not
    verify. PyJWT's own encode() refuses to sign HS256 with a PEM-shaped key
    (it has the same guard), so the forged token is built by hand here --
    an attacker forging this wouldn't go through PyJWT's guard either, and
    the defense under test is verify_supabase_jwt's own alg check, which
    runs before any key, guessed or real, is ever consulted."""
    import base64
    import hashlib
    import hmac
    import json

    from cryptography.hazmat.primitives import serialization

    public_pem = _PUBLIC_KEY.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    def _b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps(_valid_claims()).encode())
    signing_input = f"{header}.{payload}".encode()
    signature = _b64url(hmac.new(public_pem, signing_input, hashlib.sha256).digest())
    token = f"{header}.{payload}.{signature}"

    with pytest.raises(jwt.InvalidAlgorithmError):
        auth.verify_supabase_jwt(token)


def test_verify_origin_accepts_a_configured_origin():
    from fastapi import Request

    scope = {
        "type": "http",
        "headers": [(b"origin", b"http://localhost:5173")],
    }
    auth.verify_origin(Request(scope))


def test_verify_origin_rejects_missing_origin():
    from fastapi import HTTPException, Request

    scope = {"type": "http", "headers": []}
    with pytest.raises(HTTPException) as exc_info:
        auth.verify_origin(Request(scope))
    assert exc_info.value.status_code == 403


def test_verify_origin_rejects_mismatched_origin():
    from fastapi import HTTPException, Request

    scope = {
        "type": "http",
        "headers": [(b"origin", b"https://evil.example")],
    }
    with pytest.raises(HTTPException) as exc_info:
        auth.verify_origin(Request(scope))
    assert exc_info.value.status_code == 403


def test_create_session_sets_a_locked_down_cookie():
    token = _sign(_valid_claims())
    response = client.post(
        "/auth/session",
        json={"access_token": token},
    )
    assert response.status_code == 200
    set_cookie = response.headers["set-cookie"]
    assert "oe_session=" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Secure" in set_cookie
    assert "samesite=strict" in set_cookie.lower()
    assert "11111111-1111-1111-1111-111111111111" not in set_cookie


def test_create_session_rejects_an_invalid_token():
    response = client.post("/auth/session", json={"access_token": "not-a-jwt"})
    assert response.status_code == 401
    assert "not-a-jwt" not in response.text


def test_create_session_rejects_non_json_content_type():
    response = client.post(
        "/auth/session",
        content="access_token=whatever",
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 415


def test_get_current_user_round_trips_through_the_cookie():
    from fastapi import Response

    response = Response()
    auth.set_session_cookie(response, "22222222-2222-2222-2222-222222222222")
    raw_cookie = response.headers["set-cookie"].split("oe_session=", 1)[1].split(";", 1)[0]

    from fastapi import Request

    scope = {
        "type": "http",
        "headers": [(b"cookie", f"oe_session={raw_cookie}".encode())],
    }
    assert (
        auth.get_current_user(Request(scope))
        == "22222222-2222-2222-2222-222222222222"
    )


def test_get_current_user_rejects_missing_cookie():
    from fastapi import HTTPException, Request

    scope = {"type": "http", "headers": []}
    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user(Request(scope))
    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_a_tampered_cookie():
    from fastapi import HTTPException, Request

    scope = {
        "type": "http",
        "headers": [(b"cookie", b"oe_session=tampered.garbage.value")],
    }
    with pytest.raises(HTTPException) as exc_info:
        auth.get_current_user(Request(scope))
    assert exc_info.value.status_code == 401
