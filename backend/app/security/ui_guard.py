"""
Lightweight UI guard for unprotected UI proxy routes.
Checks optional IP allowlist and optional role header.
In production, integrate with real auth/SSO.
"""

from fastapi import Request, HTTPException, status
from ..core.config import get_settings


async def ui_guard(request: Request):
    settings = get_settings()

    # IP allowlist: comma-separated CIDRs or IPs in env UI_IP_ALLOWLIST
    allowlist_raw = settings.ui_ip_allowlist
    if allowlist_raw:
        client_ip = request.client.host if request.client else None
        if not client_ip:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        allowed = False
        items = [i.strip() for i in allowlist_raw.split(',') if i.strip()]
        for item in items:
            if item == client_ip:
                allowed = True
                break
        if not allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="IP not allowed")

    # Optional role enforcement via header provided by reverse proxy/SSO
    required_roles = [r.strip() for r in settings.ui_required_roles.split(',') if r.strip()]
    if required_roles:
        roles_header = request.headers.get('X-User-Roles', '')
        user_roles = [r.strip() for r in roles_header.split(',') if r.strip()]
        if not any(r in user_roles for r in required_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")

    return True


