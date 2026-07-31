"""
认证服务 —— 注册、登录、会话令牌验证
"""
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta, timezone

from ..database.models import User, UserSession
from ..utils.helpers import hash_password, verify_password, generate_session_token

# 令牌有效期：7 天。超过这个时间未重新登录，旧 token 自动失效，
# 需要重新输入用户名密码——避免"登录一次永久有效"这种长期暴露的风险。
SESSION_TTL = timedelta(days=7)


def _naive_utc_now() -> datetime:
    """返回不带时区信息的当前 UTC 时间。

    SQLite 的 DATETIME 列不保留时区信息：写入 aware datetime 时 SQLAlchemy
    会静默丢弃 tzinfo，读出来的自然也是 naive；这里统一生成/比较 naive UTC
    时间，避免 aware/naive 混比时抛 TypeError，同时不用已被标记弃用的
    datetime.utcnow()。
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, username: str, password: str) -> tuple[User, str]:
        """注册新用户，成功后直接颁发会话令牌（注册即登录）"""
        existing = self.db.query(User).filter(User.username == username).first()
        if existing:
            raise ValueError("用户名已被注册")

        user = User(username=username, password_hash=hash_password(password))
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        token = self._create_session(user.id)
        return user, token

    def login(self, username: str, password: str) -> tuple[User, str]:
        """登录，验证用户名密码，成功后颁发新的会话令牌"""
        user = self.db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.password_hash):
            raise ValueError("用户名或密码错误")

        token = self._create_session(user.id)
        return user, token

    def logout(self, token: str) -> None:
        """退出登录，删除对应的会话记录"""
        self.db.query(UserSession).filter(UserSession.token == token).delete()
        self.db.commit()

    def get_user_by_token(self, token: str) -> Optional[User]:
        """根据令牌反查用户，用于验证"这个请求是谁发的"；令牌过期视为无效并顺手清理"""
        session = self.db.query(UserSession).filter(UserSession.token == token).first()
        if not session:
            return None

        # SQLite 的 DATETIME 列不保留时区信息，读出来的 expires_at 是 naive datetime；
        # 这里统一用 naive UTC 时间比较，避免 aware/naive 混比抛 TypeError。
        if session.expires_at is not None and session.expires_at < _naive_utc_now():
            self.db.delete(session)
            self.db.commit()
            return None

        return self.db.query(User).filter(User.id == session.user_id).first()

    def _create_session(self, user_id: str) -> str:
        token = generate_session_token()
        session = UserSession(
            token=token,
            user_id=user_id,
            expires_at=_naive_utc_now() + SESSION_TTL,
        )
        self.db.add(session)
        self.db.commit()
        return token