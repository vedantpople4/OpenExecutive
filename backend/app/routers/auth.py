import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from jwt.exceptions import PyJWKClientConnectionError, PyJWKClientError
from pydantic import BaseModel

from app import auth

router = APIRouter()


class SessionRequest(BaseModel):
    access_token: str


def require_json_content_type(request: Request) -> None:
    """Closes the one cross-site shape that carries cookies without a preflight.

    An HTML form can only POST urlencoded, plain-text or multipart bodies, so
    demanding application/json means any cross-origin caller has to send a
    preflight first -- which CORSMiddleware answers against allow_origins.
    """
    media_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if media_type != "application/json":
        raise HTTPException(status_code=415, detail="Content-Type must be application/json")


@router.post("/auth/session", dependencies=[Depends(require_json_content_type)])
def create_session(payload: SessionRequest, response: Response) -> dict[str, bool]:
    """Exchange a verified Supabase access token for this backend's own cookie.

    The token arrives in the JSON body, never a query parameter: a query string
    is written to nginx's access log, a body is not. Nothing below logs the
    token, the claims, or the cookie, and the 401 detail is a fixed string so no
    part of a submitted token is echoed back to whoever submitted it.
    """
    try:
        claims = auth.verify_supabase_jwt(payload.access_token)
    except PyJWKClientConnectionError as exc:
        # Not a verification failure. A 401 here would sign every user out over
        # a Supabase JWKS outage rather than telling them to retry.
        raise HTTPException(status_code=503, detail="Key discovery unavailable") from exc
    except (jwt.PyJWTError, PyJWKClientError) as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    auth.set_session_cookie(response, user_id)
    return {"ok": True}
