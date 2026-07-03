# -*- coding: utf-8 -*-
"""图书管理 API — CRUD + 分页 + 多条件检索"""

from flask import Blueprint, request
from models.book import Book
from models.category import Category
from extensions import db
from config import Config
from utils.response import success, error, paginate as paginate_resp
from utils.jwt_utils import login_required, admin_required
from services.notification_service import broadcast_notification
from sqlalchemy import or_

book_bp = Blueprint('book', __name__)


@book_bp.route('', methods=['GET'])
@login_required
def get_books():
    """图书列表 — 分页 + 多条件检索

    Query Params:
        page: 页码 (默认1)
        search: 书名/作者 关键词搜索
        category_id: 分类筛选
        sort: 排序字段 (默认 create_time)
    """
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', 0, type=int)

    query = Book.query.filter_by(is_deleted=False)

    if search:
        query = query.filter(
            or_(Book.title.contains(search), Book.author.contains(search), Book.isbn.contains(search))
        )
    if category_id > 0:
        query = query.filter(Book.category_id == category_id)

    pagination = query.order_by(Book.id.desc()).paginate(
        page=page, per_page=Config.PAGE_SIZE, error_out=False
    )

    return success(paginate_resp(pagination, [b.to_dict() for b in pagination.items]))


@book_bp.route('/<int:book_id>', methods=['GET'])
@login_required
def get_book(book_id):
    """获取图书详情"""
    book = Book.query.get(book_id)
    if not book or book.is_deleted:
        return error('图书不存在或已下架', code=404)

    return success({'book': book.to_dict()})


@book_bp.route('', methods=['POST'])
@admin_required
def add_book():
    """新增图书"""
    data = request.get_json(silent=True) or {}
    title = data.get('title', '').strip()
    author = data.get('author', '').strip()
    isbn = data.get('isbn', '').strip()
    publisher = data.get('publisher', '').strip()
    publish_year_raw = data.get('publish_year', None)
    publish_year = int(publish_year_raw) if publish_year_raw else None
    stock = int(data.get('stock', 0))
    category_id = int(data.get('category_id', 0))
    location = data.get('location', '').strip()
    description = data.get('description', '').strip()

    if not all([title, author, isbn, category_id]):
        return error('书名、作者、ISBN、分类为必填项')

    if Book.query.filter_by(isbn=isbn).first():
        return error(f'ISBN "{isbn}" 已被占用')

    if stock < 0:
        return error('库存数量不能为负数')

    book = Book(
        title=title, author=author, isbn=isbn,
        publisher=publisher, publish_year=publish_year,
        stock=stock, category_id=category_id,
        location=location, description=description,
    )
    db.session.add(book)
    db.session.commit()

    # 通知所有学生和教师
    broadcast_notification(
        title='📚 新书上架通知',
        content=f'图书馆新到《{title}》（{author}著），ISBN: {isbn}，馆藏位置: {location or "待定"}，库存 {stock} 册。欢迎前来借阅！',
    )

    return success({'book': book.to_dict()}, f'《{title}》已成功入库，已通知全体读者')


@book_bp.route('/<int:book_id>', methods=['PUT'])
@admin_required
def update_book(book_id):
    """编辑图书信息"""
    book = Book.query.get(book_id)
    if not book:
        return error('图书不存在', code=404)

    data = request.get_json(silent=True) or {}
    title = data.get('title', '').strip()
    author = data.get('author', '').strip()
    isbn = data.get('isbn', '').strip()
    publisher = data.get('publisher', '').strip()
    publish_year_raw = data.get('publish_year', None)
    publish_year = int(publish_year_raw) if publish_year_raw else None
    stock = int(data.get('stock', 0))
    category_id = int(data.get('category_id', 0))
    location = data.get('location', '').strip()
    description = data.get('description', '').strip()

    # ISBN 唯一性校验
    exist = Book.query.filter(Book.isbn == isbn, Book.id != book_id).first()
    if exist:
        return error(f'ISBN "{isbn}" 已被其他图书占用')

    if stock < 0:
        return error('库存数量不能为负数')

    book.title = title or book.title
    book.author = author or book.author
    book.isbn = isbn or book.isbn
    book.publisher = publisher or book.publisher
    book.publish_year = publish_year or book.publish_year
    book.stock = stock
    book.category_id = category_id or book.category_id
    book.location = location or book.location
    book.description = description or book.description

    db.session.commit()

    return success({'book': book.to_dict()}, f'《{book.title}》信息已更新')


@book_bp.route('/<int:book_id>', methods=['DELETE'])
@admin_required
def delete_book(book_id):
    """图书下架（逻辑删除）"""
    book = Book.query.get(book_id)
    if not book:
        return error('图书不存在', code=404)

    book.is_deleted = True
    db.session.commit()

    return success(message=f'《{book.title}》已下架')
