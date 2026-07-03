# -*- coding: utf-8 -*-
"""门禁记录表模型 — NEW（预留人脸功能）"""

from datetime import datetime
from extensions import db


class AccessLog(db.Model):
    """门禁记录表"""
    __tablename__ = 'access_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='记录ID')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='用户ID')
    access_type = db.Column(db.String(20), comment='通行方式: face/card/code')
    direction = db.Column(db.String(10), comment='方向: in/out')
    access_time = db.Column(db.DateTime, default=datetime.now, comment='通行时间')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.real_name if self.user else '',
            'access_type': self.access_type or '',
            'direction': self.direction or '',
            'access_time': self.access_time.strftime('%Y-%m-%d %H:%M:%S') if self.access_time else '',
        }
