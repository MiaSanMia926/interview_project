import json
from typing import List, Optional

def parse_json_field(value: Optional[str], default=None):
    """解析JSON字段"""
    if value is None:
        return default if default is not None else []
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default if default is not None else []

def to_json_field(value) -> str:
    """转换为JSON字段"""
    return json.dumps(value, ensure_ascii=False)

import bcrypt


def hash_password(plain_password: str) -> str:
    """把明文密码转换成不可逆的哈希值，用于存入数据库"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """验证登录时用户输入的密码是否和数据库里存的哈希值匹配"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def generate_session_token() -> str:
    """生成一个随机、不可预测的登录会话令牌"""
    import secrets
    return secrets.token_hex(32)  # 64个字符的随机十六进制字符串