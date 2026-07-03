# -*- coding: utf-8 -*-
"""用户管理 API — 列表/个人信息/密码修改/状态管理"""

from flask import Blueprint, request, g
from models.user import User
from extensions import db
from config import Config
from utils.response import success, error, paginate as paginate_resp
from utils.jwt_utils import login_required, admin_required

user_bp = Blueprint('user', __name__)


@user_bp.route('', methods=['GET'])
@admin_required
def get_users():
    """用户列表 — 分页 + 搜索"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    role = request.args.get('role', '').strip()

    query = User.query
    if search:
        query = query.filter(
            db.or_(User.username.contains(search), User.real_name.contains(search))
        )
    if role:
        query = query.filter_by(role=role)

    pagination = query.order_by(User.id.desc()).paginate(
        page=page, per_page=Config.PAGE_SIZE, error_out=False
    )

    return success(paginate_resp(pagination, [u.to_dict() for u in pagination.items]))


@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """获取当前用户信息"""
    user = User.query.get(g.current_user['user_id'])
    if not user:
        return error('用户不存在', code=404)
    return success({'user': user.to_dict()})


@user_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """修改个人信息（手机号、邮箱等）"""
    user = User.query.get(g.current_user['user_id'])
    if not user:
        return error('用户不存在', code=404)

    data = request.get_json(silent=True) or {}
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()

    if phone:
        user.phone = phone
    if email:
        user.email = email

    db.session.commit()
    return success({'user': user.to_dict()}, '个人信息已更新')


@user_bp.route('/password', methods=['PUT'])
@login_required
def change_password():
    """修改密码"""
    user = User.query.get(g.current_user['user_id'])
    if not user:
        return error('用户不存在', code=404)

    data = request.get_json(silent=True) or {}
    old_pw = data.get('old_password', '').strip()
    new_pw = data.get('new_password', '').strip()

    if not user.check_password(old_pw):
        return error('原密码不正确')

    if len(new_pw) < 6 or len(new_pw) > 16:
        return error('新密码长度需为6~16位')
    if new_pw.isdigit():
        return error('密码不能为纯数字')
    if new_pw.isalpha():
        return error('密码不能为纯字母')

    user.set_password(new_pw)
    db.session.commit()
    return success(message='密码修改成功')


@user_bp.route('/<int:user_id>/status', methods=['PUT'])
@admin_required
def toggle_status(user_id):
    """启用/禁用用户"""
    user = User.query.get(user_id)
    if not user:
        return error('用户不存在', code=404)
    if user.role == 'admin':
        return error('不能操作管理员账号')

    user.status = 'disabled' if user.status == 'active' else 'active'
    db.session.commit()

    action = '冻结' if user.status == 'disabled' else '启用'
    return success(message=f'账号已{action}: {user.real_name}')


@user_bp.route('/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_password(user_id):
    """重置用户密码"""
    user = User.query.get(user_id)
    if not user:
        return error('用户不存在', code=404)
    if user.role == 'admin':
        return error('不能重置管理员密码')

    user.set_password('123456')
    db.session.commit()
    return success(message=f'用户 "{user.real_name}" 的密码已重置为 123456')
