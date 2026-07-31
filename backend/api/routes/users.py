from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database import get_db
from ...database.models import User
from ...schemas.user import UserResponse, UserProfile
from ...services.user_service import UserService
from ..deps import get_current_user

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user


@router.get("/{user_id}/profile", response_model=UserProfile)
def get_user_profile(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取用户画像 —— 只能查看自己的画像"""
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看他人的用户画像")
    service = UserService(db)
    profile = service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="用户不存在")
    return profile