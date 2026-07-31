from ..database import get_db
from fastapi import Header
from typing import Optional


def get_session_id(x_session_id: Optional[str] = Header(default=None)) -> Optional[str]:
    """
    从请求头 X-Session-Id 中读取前端生成的会话标识。
    前端在 client.ts 里已经统一携带这个头，这里负责接收。
    没有携带时返回 None，不强制要求（兼容旧客户端/直接调用API的场景）。
    """
    return x_session_id

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from ..database.models import User


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """
    验证当前请求的登录令牌，返回对应的用户对象。
    验证失败（没带令牌/令牌无效）直接抛401，中断请求。
    用法：在需要登录才能访问的接口里加一个参数
        current_user: User = Depends(get_current_user)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录或令牌缺失")

    token = authorization[len("Bearer "):]
    from ..services.auth_service import AuthService
    user = AuthService(db).get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")

    return user