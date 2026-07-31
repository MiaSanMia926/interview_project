"""
认证接口 —— 注册、登录、退出登录
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from ...database import get_db
from ...schemas.user import RegisterRequest, LoginRequest, AuthResponse
from ...services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """注册新账号，成功后直接返回会话令牌（注册即登录，无需再手动登录一次）"""
    service = AuthService(db)
    try:
        user, token = service.register(data.username, data.password)
        return AuthResponse(token=token, user_id=user.id, username=user.username)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """登录，验证用户名密码，成功后返回新的会话令牌"""
    service = AuthService(db)
    try:
        user, token = service.login(data.username, data.password)
        return AuthResponse(token=token, user_id=user.id, username=user.username)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout", status_code=204)
def logout(authorization: Optional[str] = Header(default=None), db: Session = Depends(get_db)):
    """退出登录，使当前令牌失效"""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[len("Bearer "):]
        AuthService(db).logout(token)
    return None