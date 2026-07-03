# -*- coding: utf-8 -*-
"""图书荐购/收录请求表模型 — NEW
学生/教师提交希望图书馆收录的图书，管理员审核采纳/驳回
"""

from datetime import datetime
from extensions import db


class BookRequest(db.Model):
    """图书荐购表"""
    __tablename__ = 'book_request'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='请求ID')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, comment='申请人ID')
    title = db.Column(db.String(255), nullable=False, comment='书名')
    author = db.Column(db.String(255), comment='作者')
    publisher = db.Column(db.String(255), comment='出版社')
    isbn = db.Column(db.String(50), comment='ISBN（选填）')
    reason = db.Column(db.Text, comment='荐购理由')
    status = db.Column(db.String(20), nullable=False, default='pending',
                       comment='状态: pending=待审核, approved=已采纳, rejected=已驳回')
    review_admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='审核管理员ID')
    review_comment = db.Column(db.Text, comment='审核意见')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='提交时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now,
                            comment='更新时间')

    # 关系
    applicant = db.relationship('User', foreign_keys=[user_id], backref='book_requests')
    review_admin = db.relationship('User', foreign_keys=[review_admin_id])

    STATUS_MAP = {
        'pending': '待审核',
        'approved': '已采纳',
        'rejected': '已驳回',
    }

    def status_text(self):
        return self.STATUS_MAP.get(self.status, self.status)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'applicant_name': self.applicant.real_name if self.applicant else '',
            'title': self.title,
            'author': self.author or '',
            'publisher': self.publisher or '',
            'isbn': self.isbn or '',
            'reason': self.reason or '',
            'status': self.status,
            'status_text': self.status_text(),
            'review_comment': self.review_comment or '',
            'review_admin_name': self.review_admin.real_name if self.review_admin else '',
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M') if self.create_time else '',
        }
