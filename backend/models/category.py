# -*- coding: utf-8 -*-
"""图书分类表模型"""

from datetime import datetime
from extensions import db


class Category(db.Model):
    """图书分类表"""
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='分类ID')
    name = db.Column(db.String(100), unique=True, nullable=False, comment='分类名称')
    is_deleted = db.Column(db.Boolean, default=False, comment='逻辑删除')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now,
                            comment='更新时间')

    books = db.relationship('Book', backref='category', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_deleted': self.is_deleted,
            'book_count': self.books.filter_by(is_deleted=False).count(),
        }
