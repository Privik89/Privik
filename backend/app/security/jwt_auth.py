"""
JWT-based auth with simple RBAC for admin routes.
"""

from fastapi import Request, HTTPException, status
import jwt
from ..core.config import get_settings


async def verify_jwt_admin(request: Request):
    settings = get_settings()
    if not settings.enable_jwt_auth:
        # Allow if disabled
        return True
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = auth.split(' ', 1)[1]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=['HS256'])
        roles = payload.get('roles', [])
        if settings.jwt_admin_role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return True
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


