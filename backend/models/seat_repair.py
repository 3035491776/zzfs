# -*- coding: utf-8 -*-
"""自习室座位报修表模型 — NEW
学生/教师提交座位损坏报修，管理员审核维修
"""

from datetime import datetime
from extensions import db


class SeatRepair(db.Model):
    """座位报修表"""
    __tablename__ = 'seat_repair'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='报修ID')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='报修人ID')
    seat_id = db.Column(db.Integer, db.ForeignKey('seat.id'), nullable=False, comment='座位ID')
    description = db.Column(db.Text, nullable=False, comment='故障描述')
    status = db.Column(db.String(20), nullable=False, default='pending',
                       comment='状态: pending=待处理, fixing=维修中, resolved=已修复, rejected=已驳回')
    review_admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='审核管理员ID')
    review_comment = db.Column(db.Text, comment='处理意见')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='报修时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

    # 关系
    reporter = db.relationship('User', foreign_keys=[user_id], backref='seat_repairs')
    seat = db.relationship('Seat', foreign_keys=[seat_id], backref='repairs')
    review_admin = db.relationship('User', foreign_keys=[review_admin_id])

    STATUS_MAP = {
        'pending': '待处理',
        'fixing': '维修中',
        'resolved': '已修复',
        'rejected': '已驳回',
    }

    def status_text(self):
        return self.STATUS_MAP.get(self.status, self.status)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'reporter_name': self.reporter.real_name if self.reporter else '',
            'seat_id': self.seat_id,
            'seat_number': self.seat.seat_number if self.seat else '',
            'room_name': self.seat.room_name if self.seat else '',
            'description': self.description,
            'status': self.status,
            'status_text': self.status_text(),
            'review_comment': self.review_comment or '',
            'review_admin_name': self.review_admin.real_name if self.review_admin else '',
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M') if self.create_time else '',
        }
