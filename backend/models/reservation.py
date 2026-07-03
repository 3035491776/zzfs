# -*- coding: utf-8 -*-
"""自习室预约表模型 — NEW"""

from datetime import datetime
from extensions import db


class Reservation(db.Model):
    """自习室预约表"""
    __tablename__ = 'reservation'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='预约ID')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='预约人ID')
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'), nullable=False, comment='座位ID')
    date = db.Column(db.Date, nullable=False, comment='预约日期')
    start_time = db.Column(db.Time, nullable=False, comment='开始时间')
    end_time = db.Column(db.Time, nullable=False, comment='结束时间')
    status = db.Column(db.String(20), nullable=False, default='reserved',
                       comment='状态: reserved/checked_in/completed/cancelled/no_show')
    checkin_time = db.Column(db.DateTime, comment='签到时间')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='预约时间')

    STATUS_MAP = {
        'reserved': '已预约',
        'checked_in': '已签到',
        'completed': '已完成',
        'cancelled': '已取消',
        'no_show': '未签到',
    }

    def status_text(self):
        return self.STATUS_MAP.get(self.status, self.status)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.real_name if self.user else '',
            'seat_id': self.seat_id,
            'seat_number': self.seat.seat_number if self.seat else '',
            'room_name': self.seat.room_name if self.seat else '',
            'floor': self.seat.floor if self.seat else 0,
            'date': self.date.strftime('%Y-%m-%d') if self.date else '',
            'start_time': self.start_time.strftime('%H:%M') if self.start_time else '',
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else '',
            'status': self.status,
            'status_text': self.status_text(),
            'checkin_time': self.checkin_time.strftime('%Y-%m-%d %H:%M') if self.checkin_time else '',
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M') if self.create_time else '',
        }
