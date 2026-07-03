# -*- coding: utf-8 -*-
"""图书信息表模型 — 扩展字段：publisher, publish_year, cover_image, location"""

from datetime import datetime
from extensions import db


class Book(db.Model):
    """图书信息表"""
    __tablename__ = 'book'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='图书ID')
    title = db.Column(db.String(255), nullable=False, comment='书名')
    author = db.Column(db.String(255), nullable=False, comment='作者')
    isbn = db.Column(db.String(50), unique=True, nullable=False, comment='ISBN编号')
    publisher = db.Column(db.String(255), comment='出版社')
    publish_year = db.Column(db.Integer, comment='出版年份')
    stock = db.Column(db.Integer, nullable=False, default=0, comment='库存数量')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False,
                            comment='分类ID')
    cover_image = db.Column(db.String(500), comment='封面图片路径')
    location = db.Column(db.String(100), comment='馆藏位置(如"A区3排")')
    description = db.Column(db.Text, comment='图书简介')
    is_deleted = db.Column(db.Boolean, default=False, comment='逻辑删除')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='入库时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now,
                            comment='更新时间')

    borrows = db.relationship('Borrow', backref='book', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author,
            'isbn': self.isbn,
            'publisher': self.publisher or '',
            'publish_year': self.publish_year or '',
            'stock': self.stock,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else '',
            'cover_image': self.cover_image or '',
            'location': self.location or '',
            'description': self.description or '',
            'is_deleted': self.is_deleted,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M') if self.create_time else '',
        }
