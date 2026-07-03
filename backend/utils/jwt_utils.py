# -*- coding: utf-8 -*-
"""JWT 工具 — token 生成、验证、权限装饰器"""

from functools import wraps
from datetime import datetime, timedelta
import jwt
from flask import request, g, current_app
from utils.response import error

# JWT 算法
JWT_ALGORITHM = 'HS256'


def create_token(user_id, username, role):
    """生成 JWT token

    Args:
        user_id: 用户ID
        username: 用户名
        role: 角色 (admin/teacher/student)

    Returns:
        str: JWT token 字符串
    """
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=current_app.config.get('JWT_EXPIRATION_HOURS', 24)),
    }
    secret = current_app.config.get('JWT_SECRET_KEY', 'default-secret')
    token = jwt.encode(payload, secret, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token):
    """解析 JWT token

    Returns:
        dict or None: payload 字典，解析失败返回 None
    """
    try:
        secret = current_app.config.get('JWT_SECRET_KEY', 'default-secret')
        payload = jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ---- 权限装饰器 ----

def login_required(f):
    """登录拦截装饰器 — 解析 JWT token，注入 g.current_user"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # 从 Authorization header 获取 token
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]

        if not token:
            return error('请先登录', code=401)

        payload = decode_token(token)
        if payload is None:
            return error('登录已过期，请重新登录', code=401)

        # 注入全局用户信息
        g.current_user = {
            'user_id': payload['user_id'],
            'username': payload['username'],
            'role': payload['role'],
        }
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """管理员权限拦截装饰器"""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if g.current_user['role'] != 'admin':
            return error('权限不足，仅管理员可操作', code=403)
        return f(*args, **kwargs)
    return decorated


def teacher_required(f):
    """教师权限拦截装饰器"""
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if g.current_user['role'] not in ('admin', 'teacher'):
            return error('权限不足', code=403)
        return f(*args, **kwargs)
    return decorated
