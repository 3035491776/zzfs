# -*- coding: utf-8 -*-
"""认证接口 — 多方式登录、注册、登出"""

from flask import Blueprint, request, session, current_app
from utils.response import success, error
from utils.jwt_utils import create_token, login_required
from utils.sms_utils import send_sms, generate_sms_code
from models.user import User
from models.sms_log import SmsLog
from extensions import db
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)


# ================================================================
# 密码登录
# ================================================================
@auth_bp.route('/login', methods=['POST'])
def login():
    """密码登录

    Request Body:
        username: 用户名
        password: 密码
        captcha: 验证码 (可选)

    Response:
        { code: 200, data: { token, user } }
    """
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    captcha = data.get('captcha', '').strip()

    # 非空校验
    if not username or not password:
        return error('请输入用户名和密码')

    # 查询用户
    user = User.query.filter_by(username=username).first()
    if not user:
        return error('账号不存在')

    # 校验密码
    if not user.check_password(password):
        return error('密码错误')

    # 校验账号状态
    if user.status == 'disabled':
        return error('账号已被冻结，请联系管理员', code=403)

    # 生成 JWT
    token = create_token(user.id, user.username, user.role)

    return success({
        'token': token,
        'user': user.to_dict(),
    }, '登录成功')



# ================================================================
# 短信验证码登录
# ================================================================
@auth_bp.route('/login/sms', methods=['POST'])
def login_sms():
    """短信验证码登录

    Request Body:
        phone: 手机号
        code: 短信验证码
    """
    data = request.get_json(silent=True) or {}
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()

    if not phone or not code:
        return error('请输入手机号和验证码')

    # 按手机号查用户
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return error('手机号未注册')

    if user.status == 'disabled':
        return error('账号已被冻结', code=403)

    # 校验短信验证码
    sms_log = SmsLog.query.filter_by(phone=phone, code=code, is_used=False).order_by(
        SmsLog.create_time.desc()).first()
    if not sms_log:
        return error('验证码错误')
    if sms_log.is_expired():
        return error('验证码已过期')

    # 标记验证码已使用
    sms_log.is_used = True
    db.session.commit()

    token = create_token(user.id, user.username, user.role)

    return success({
        'token': token,
        'user': user.to_dict(),
    }, '登录成功')


# ================================================================
# 发送短信验证码
# ================================================================
@auth_bp.route('/sms/send', methods=['POST'])
def sms_send():
    """发送短信验证码

    Request Body:
        phone: 手机号
    """
    data = request.get_json(silent=True) or {}
    phone = data.get('phone', '').strip()

    if not phone:
        return error('请输入手机号')

    if len(phone) != 11 or not phone.isdigit():
        return error('请输入正确的手机号')

    # 生成验证码
    code = generate_sms_code()

    # 保存到数据库
    sms_log = SmsLog(
        phone=phone,
        code=code,
        type='login',
        expire_time=datetime.now() + timedelta(seconds=current_app.config.get('CAPTCHA_EXPIRE_SECONDS', 300)),
    )
    db.session.add(sms_log)
    db.session.commit()

    # 发送短信
    result = send_sms(phone, code)

    return success({
        'phone': phone,
        'expire_seconds': current_app.config.get('CAPTCHA_EXPIRE_SECONDS', 300),
    }, result['message'] if result['success'] else '短信发送失败')


# ================================================================
# 用户注册
# ================================================================
@auth_bp.route('/register', methods=['POST'])
def register():
    """学生/教师注册

    Request Body:
        username: 用户名
        password: 密码
        real_name: 真实姓名
        role: 角色 (student/teacher，默认student)
        phone: 手机号 (可选)
        email: 邮箱 (可选)
    """
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    real_name = data.get('real_name', '').strip()
    role = data.get('role', 'student').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()

    # 后端校验
    if not username or not password or not real_name:
        return error('用户名、密码、真实姓名为必填项')

    if role not in ('student', 'teacher'):
        return error('无效的角色类型')

    # 用户名唯一性
    if User.query.filter_by(username=username).first():
        return error('用户名已存在，请更换')

    # 密码复杂度
    if len(password) < 6 or len(password) > 16:
        return error('密码长度需为6~16位')
    if password.isdigit():
        return error('密码不能为纯数字')
    if password.isalpha():
        return error('密码不能为纯字母')

    # 创建用户
    user = User(
        username=username,
        real_name=real_name,
        role=role,
        status='active',
        phone=phone or None,
        email=email or None,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return success({
        'user': user.to_dict(),
    }, '注册成功')


# ================================================================
# 退出登录
# ================================================================
@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """退出登录 (客户端删除 token)"""
    return success(message='已安全退出')


# ================================================================
# 获取当前用户信息
# ================================================================
@auth_bp.route('/me', methods=['GET'])
@login_required
def get_me():
    """获取当前登录用户信息"""
    from flask import g
    user = User.query.get(g.current_user['user_id'])
    if not user:
        return error('用户不存在', code=404)
    return success({'user': user.to_dict()})
