# -*- coding: utf-8 -*-
"""消息通知表模型 — NEW"""

from datetime import datetime
from extensions import db


class Notification(db.Model):
    """消息通知表"""
    __tablename__ = 'notification'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='通知ID')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='接收人ID')
    title = db.Column(db.String(200), comment='通知标题')
    content = db.Column(db.Text, comment='通知内容')
    type = db.Column(db.String(30), comment='类型: borrow/return/overdue/reservation/system')
    is_read = db.Column(db.Boolean, default=False, comment='是否已读')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='发送时间')

    TYPE_MAP = {
        'borrow': '借阅通知',
        'return': '归还通知',
        'overdue': '逾期提醒',
        'reservation': '预约通知',
        'system': '系统通知',
    }

    def type_text(self):
        return self.TYPE_MAP.get(self.type, self.type or '')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title or '',
            'content': self.content or '',
            'type': self.type or '',
            'type_text': self.type_text(),
            'is_read': self.is_read,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M') if self.create_time else '',
        }
