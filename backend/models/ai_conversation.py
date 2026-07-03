# -*- coding: utf-8 -*-
"""AI对话记录表模型 — NEW"""

from datetime import datetime
from extensions import db


class AiConversation(db.Model):
    """AI对话记录表"""
    __tablename__ = 'ai_conversation'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='对话ID')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='用户ID')
    role = db.Column(db.String(20), comment='角色: user/assistant')
    content = db.Column(db.Text, comment='对话内容')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='时间')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role': self.role or '',
            'content': self.content or '',
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else '',
        }
