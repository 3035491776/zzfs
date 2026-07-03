# -*- coding: utf-8 -*-
"""通知推送服务"""

from models.notification import Notification
from models.user import User
from extensions import db


def create_notification(user_id, title, content, n_type='system'):
    """给单个用户创建通知"""
    notification = Notification(
        user_id=user_id,
        title=title,
        content=content,
        type=n_type,
        is_read=False,
    )
    db.session.add(notification)
    db.session.commit()
    return notification


def broadcast_notification(title, content, target_role=None):
    """向指定角色（或全部非管理员）广播通知

    Args:
        title: 通知标题
        content: 通知内容
        target_role: None=所有非管理员, 'student'=仅学生, 'teacher'=仅教师

    Returns:
        int: 发送数量
    """
    query = User.query.filter(User.role != 'admin')
    if target_role:
        query = query.filter_by(role=target_role)

    users = query.all()
    count = 0
    for u in users:
        create_notification(
            user_id=u.id,
            title=title,
            content=content,
            n_type='system',
        )
        count += 1
    return count


def notify_overdue(borrow):
    """发送逾期提醒"""
    create_notification(
        user_id=borrow.user_id,
        title='图书逾期提醒',
        content=f'您借阅的《{borrow.book.title}》已逾期，请尽快归还',
        n_type='overdue',
    )


def notify_due_soon(borrow):
    """发送即将到期提醒（到期前3天）"""
    create_notification(
        user_id=borrow.user_id,
        title='图书即将到期',
        content=f'您借阅的《{borrow.book.title}》将于 {borrow.due_time.strftime("%Y-%m-%d")} 到期',
        n_type='borrow',
    )
