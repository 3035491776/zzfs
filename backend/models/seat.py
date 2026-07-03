# -*- coding: utf-8 -*-
"""自习室座位表模型 — NEW"""

from extensions import db


class Seat(db.Model):
    """自习室座位表"""
    __tablename__ = 'seat'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='座位ID')
    seat_number = db.Column(db.String(20), unique=True, nullable=False, comment='座位编号')
    room_name = db.Column(db.String(50), comment='自习室名称')
    floor = db.Column(db.Integer, comment='楼层')
    status = db.Column(db.String(20), nullable=False, default='available',
                       comment='状态: available/occupied/maintenance')
    has_power = db.Column(db.Boolean, default=True, comment='是否有电源')
    description = db.Column(db.String(200), comment='座位描述')

    reservations = db.relationship('Reservation', backref='seat', lazy='dynamic')

    STATUS_MAP = {
        'available': '可用',
        'occupied': '已占用',
        'maintenance': '维护中',
    }

    def status_text(self):
        return self.STATUS_MAP.get(self.status, self.status)

    def to_dict(self):
        return {
            'id': self.id,
            'seat_number': self.seat_number,
            'room_name': self.room_name or '',
            'floor': self.floor or 0,
            'status': self.status,
            'status_text': self.status_text(),
            'has_power': self.has_power,
            'description': self.description or '',
        }
