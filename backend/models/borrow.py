# -*- coding: utf-8 -*-
"""借阅记录表模型 — 扩展字段：renew_count"""

from datetime import datetime
from extensions import db


class Borrow(db.Model):
    """借阅记录表"""
    __tablename__ = 'borrow'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='借阅记录ID')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False,
                        comment='借阅学生ID')
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False,
                        comment='借阅图书ID')
    status = db.Column(db.String(20), nullable=False, default='pending',
                       comment='状态: pending=待审核, borrowed=在借, returned=已归还, rejected=已驳回, overdue=逾期')
    borrow_time = db.Column(db.DateTime, comment='借阅时间(审核通过时)')
    due_time = db.Column(db.DateTime, comment='到期时间')
    return_time = db.Column(db.DateTime, comment='实际归还时间')
    review_admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), comment='审核管理员ID')
    renew_count = db.Column(db.Integer, default=0, comment='续借次数')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='申请创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now,
                            comment='更新时间')

    # 审核管理员关系
    review_admin = db.relationship('User', foreign_keys=[review_admin_id])

    STATUS_MAP = {
        'pending': '待审核',
        'borrowed': '在借',
        'returned': '已归还',
        'rejected': '已驳回',
        'overdue': '逾期',
    }

    def status_text(self):
        return self.STATUS_MAP.get(self.status, self.status)

    def is_overdue(self):
        """判断是否逾期"""
        if self.status in ('borrowed', 'overdue') and self.due_time:
            return datetime.now() > self.due_time
        return False

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'student_name': self.student.real_name if self.student else '',
            'student_username': self.student.username if self.student else '',
            'book_id': self.book_id,
            'book_title': self.book.title if self.book else '',
            'book_author': self.book.author if self.book else '',
            'book_isbn': self.book.isbn if self.book else '',
            'status': self.status,
            'status_text': self.status_text(),
            'borrow_time': self.borrow_time.strftime('%Y-%m-%d %H:%M') if self.borrow_time else '',
            'due_time': self.due_time.strftime('%Y-%m-%d') if self.due_time else '',
            'return_time': self.return_time.strftime('%Y-%m-%d %H:%M') if self.return_time else '',
            'renew_count': self.renew_count,
            'review_admin_name': self.review_admin.real_name if self.review_admin else '',
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M') if self.create_time else '',
        }


def update_overdue_borrows():
    """自动更新逾期记录"""
    now = datetime.now()
    overdue_list = Borrow.query.filter(
        Borrow.status == 'borrowed',
        Borrow.due_time < now
    ).all()
    for b in overdue_list:
        b.status = 'overdue'
    if overdue_list:
        db.session.commit()
    return len(overdue_list)
