"""
HMAC-based API authentication for agents and internal services.

Expected headers:
 - X-API-Key: public key identifier
 - X-Timestamp: unix epoch seconds
 - X-Signature: hex HMAC-SHA256 over (method + "\n" + path + "\n" + timestamp + "\n" + body)

For Phase 1, we support a single shared secret from settings. In Phase 2+,
map API keys to per-agent secrets stored in DB/KV.
"""

import hmac
import hashlib
import time
from fastapi import Depends, HTTPException, Request, status
from ..core.config import get_settings


def _constant_time_compare(a: str, b: str) -> bool:
    try:
        return hmac.compare_digest(a, b)
    except Exception:
        return False


async def verify_request(request: Request):
    settings = get_settings()

    # Allow unauthenticated in development if disabled
    if not settings.enable_hmac_auth:
        return True

    api_key = request.headers.get("X-API-Key", "")
    timestamp = request.headers.get("X-Timestamp", "")
    signature = request.headers.get("X-Signature", "")

    if not api_key or not timestamp or not signature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing auth headers")

    # Basic replay protection
    try:
        ts = int(timestamp)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid timestamp")

    now = int(time.time())
    if abs(now - ts) > settings.hmac_auth_ttl_seconds:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Stale request")

    # Phase 1: single shared secret
    if api_key != settings.hmac_api_key_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    body_bytes = await request.body()
    body = body_bytes.decode("utf-8") if body_bytes else ""
    method = request.method.upper()
    path = request.url.path

    payload = f"{method}\n{path}\n{timestamp}\n{body}"
    expected_sig = hmac.new(
        key=settings.hmac_api_secret.encode("utf-8"),
        msg=payload.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not _constant_time_compare(signature, expected_sig):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")

    return True


