# -*- coding: utf-8 -*-
"""系统广播通知 API — 管理员向全体用户发送通知"""

from flask import Blueprint, request, g
from utils.response import success, error
from utils.jwt_utils import admin_required
from services.notification_service import broadcast_notification

broadcast_bp = Blueprint('broadcast', __name__)


@broadcast_bp.route('', methods=['POST'])
@admin_required
def send_broadcast():
    """发送广播通知

    Request Body:
        title: 通知标题
        content: 通知内容
        target: 发送对象 (all=全部 / student=仅学生 / teacher=仅教师)
    """
    data = request.get_json(silent=True) or {}
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    target = data.get('target', 'all').strip()

    if not title:
        return error('请输入通知标题')
    if not content:
        return error('请输入通知内容')

    if target == 'all':
        target_role = None
        target_name = '全体师生'
    elif target == 'student':
        target_role = 'student'
        target_name = '全体学生'
    elif target == 'teacher':
        target_role = 'teacher'
        target_name = '全体教师'
    else:
        return error('无效的发送对象')

    count = broadcast_notification(title, content, target_role)

    return success({
        'count': count,
        'target': target_name,
    }, f'已向 {target_name}（{count} 人）发送通知')
