# -*- coding: utf-8 -*-
"""消息通知 API"""

from flask import Blueprint, request, g
from models.notification import Notification
from extensions import db
from config import Config
from utils.response import success, error, paginate as paginate_resp
from utils.jwt_utils import login_required

notification_bp = Blueprint('notification', __name__)


@notification_bp.route('', methods=['GET'])
@login_required
def get_notifications():
    """我的通知列表 — 分页"""
    page = request.args.get('page', 1, type=int)
    n_type = request.args.get('type', '').strip()

    query = Notification.query.filter_by(user_id=g.current_user['user_id'])
    if n_type:
        query = query.filter_by(type=n_type)

    pagination = query.order_by(Notification.create_time.desc()).paginate(
        page=page, per_page=Config.PAGE_SIZE, error_out=False
    )

    return success(paginate_resp(pagination, [n.to_dict() for n in pagination.items]))


@notification_bp.route('/unread-count', methods=['GET'])
@login_required
def unread_count():
    """获取未读通知数量"""
    count = Notification.query.filter_by(
        user_id=g.current_user['user_id'],
        is_read=False,
    ).count()
    return success({'count': count})


@notification_bp.route('/<int:notif_id>/read', methods=['PUT'])
@login_required
def mark_read(notif_id):
    """标记通知为已读"""
    notification = Notification.query.get(notif_id)
    if not notification:
        return error('通知不存在', code=404)
    if notification.user_id != g.current_user['user_id']:
        return error('无权操作', code=403)

    notification.is_read = True
    db.session.commit()
    return success(message='已标记为已读')


@notification_bp.route('/read-all', methods=['PUT'])
@login_required
def mark_all_read():
    """全部标记为已读"""
    Notification.query.filter_by(
        user_id=g.current_user['user_id'],
        is_read=False,
    ).update({'is_read': True})
    db.session.commit()
    return success(message='全部已标记为已读')
