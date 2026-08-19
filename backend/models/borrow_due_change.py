# -*- coding: utf-8 -*-
"""借阅到期时间真实变更历史模型。"""

from datetime import datetime

from extensions import db


class BorrowDueChange(db.Model):
    """记录 Phase 1 启用后的真实 due_time 变更。"""

    __tablename__ = 'borrow_due_change'
    __table_args__ = (
        db.UniqueConstraint(
            'borrow_id', 'change_sequence', name='uq_borrow_due_change_borrow_sequence'
        ),
        db.Index('ix_borrow_due_change_borrow_time', 'borrow_id', 'change_time'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci',
        },
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='到期时间变更ID')
    borrow_id = db.Column(
        db.Integer,
        db.ForeignKey('borrow.id', ondelete='RESTRICT'),
        nullable=False,
        comment='借阅记录ID',
    )
    change_sequence = db.Column(db.Integer, nullable=False, comment='借阅内变更序号')
    change_type = db.Column(db.String(20), nullable=False, comment='变更类型')
    old_due_time = db.Column(db.DateTime, nullable=False, comment='变更前到期时间')
    new_due_time = db.Column(db.DateTime, nullable=False, comment='变更后到期时间')
    change_time = db.Column(
        db.DateTime, nullable=False, default=datetime.now, comment='实际变更时间'
    )
    operator_user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='SET NULL'),
        nullable=True,
        comment='操作用户ID',
    )
