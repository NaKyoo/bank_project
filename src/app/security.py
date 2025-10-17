from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.db import get_session
from sqlmodel import Session
from app.models.user import User

# Simple bearer scheme
bearer_scheme = HTTPBearer()

# JWT config (in-memory secret for dev)
SECRET_KEY = "replace-me-with-secure-secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def create_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
    now = datetime.now(tz=timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub": str(user.user_id),
        "email": user.email,
        # exp must be a numeric timestamp for PyJWT to validate correctly
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), session: Session = Depends(get_session)) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = session.get(User, int(sub))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
