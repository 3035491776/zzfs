# -*- coding: utf-8 -*-
"""短信记录表模型 — NEW"""

from datetime import datetime
from extensions import db


class SmsLog(db.Model):
    """短信记录表"""
    __tablename__ = 'sms_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='记录ID')
    phone = db.Column(db.String(20), comment='手机号')
    code = db.Column(db.String(10), comment='验证码')
    type = db.Column(db.String(30), comment='类型: login/register/reset')
    is_used = db.Column(db.Boolean, default=False, comment='是否已使用')
    expire_time = db.Column(db.DateTime, comment='过期时间')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='发送时间')

    def is_expired(self):
        """判断是否过期"""
        if self.expire_time:
            return datetime.now() > self.expire_time
        return True

    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone or '',
            'code': self.code or '',
            'type': self.type or '',
            'is_used': self.is_used,
            'expire_time': self.expire_time.strftime('%Y-%m-%d %H:%M:%S') if self.expire_time else '',
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else '',
        }
