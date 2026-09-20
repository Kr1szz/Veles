import asyncio
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from aegis.config import settings
from aegis.models.database import User
from aegis.models.schemas import LoginRequest, TokenResponse
from aegis.core.rate_limiter import rate_limiter
from aegis.core.middleware import get_client_ip
from aegis.core.security import (
    verify_password_constant_time,
    create_access_token,
    decode_access_token,
    cookie_name
)
from aegis.services.storage import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])
security_scheme = HTTPBearer(auto_error=False)

LOGIN_THROTTLE_PER_MIN = 10


def _cookie_secure() -> bool:
    if settings.COOKIE_SECURE is not None:
        return settings.COOKIE_SECURE
    return settings.ENVIRONMENT.lower() == "production"


async def _throttle_login(request: Request) -> None:
    client_ip = get_client_ip(request)
    allowed, _count, retry_after = await rate_limiter.check_velocity(
        key=f"login:{client_ip}",
        limit=LOGIN_THROTTLE_PER_MIN,
        window_seconds=60
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts, retry later",
            headers={"Retry-After": f"{max(1, int(retry_after))}"}
        )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    session_cookie = cookie_name(_cookie_secure())
    token = credentials.credentials if credentials else request.cookies.get(session_cookie)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        payload = decode_access_token(token)
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token claims")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")

    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def require_role(allowed_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires role in {allowed_roles}"
            )
        return current_user
    return role_checker


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, response: Response, db: Session = Depends(get_db), body: LoginRequest = ...):
    await _throttle_login(request)

    user = db.query(User).filter(User.username == body.username).first()
    password_ok = verify_password_constant_time(body.password, user.hashed_password if user else None)
    if not user or not user.is_active or not password_ok:
        await asyncio.sleep(0.5)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=expires
    )

    secure = _cookie_secure()
    response.set_cookie(
        key=cookie_name(secure), value=token, httponly=True,
        secure=secure, samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, path="/"
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user.role,
        username=user.username,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(cookie_name(_cookie_secure()), path="/")


@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat()
    }
