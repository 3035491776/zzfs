# -*- coding: utf-8 -*-
"""图书分类管理 API — CRUD"""

from flask import Blueprint, request
from models.category import Category
from models.book import Book
from extensions import db
from config import Config
from utils.response import success, error, paginate as paginate_resp
from utils.jwt_utils import login_required, admin_required

category_bp = Blueprint('category', __name__)


@category_bp.route('', methods=['GET'])
@login_required
def get_categories():
    """获取分类列表（所有分类，不分页）"""
    search = request.args.get('search', '').strip()
    query = Category.query.filter_by(is_deleted=False)

    if search:
        query = query.filter(Category.name.contains(search))

    categories = query.order_by(Category.id.asc()).all()
    return success({'list': [c.to_dict() for c in categories]})


@category_bp.route('', methods=['POST'])
@admin_required
def add_category():
    """新增分类"""
    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()

    if not name:
        return error('分类名称不能为空')

    if Category.query.filter_by(name=name, is_deleted=False).first():
        return error(f'分类 "{name}" 已存在')

    cat = Category(name=name)
    db.session.add(cat)
    db.session.commit()

    return success({'category': cat.to_dict()}, f'分类 "{name}" 已添加')


@category_bp.route('/<int:cat_id>', methods=['PUT'])
@admin_required
def update_category(cat_id):
    """编辑分类名称"""
    cat = Category.query.get(cat_id)
    if not cat:
        return error('分类不存在', code=404)

    data = request.get_json(silent=True) or {}
    name = data.get('name', '').strip()

    if not name:
        return error('分类名称不能为空')

    exist = Category.query.filter(
        Category.name == name, Category.id != cat_id, Category.is_deleted == False
    ).first()
    if exist:
        return error(f'分类 "{name}" 已存在')

    cat.name = name
    cat.update_time = db.func.now()
    db.session.commit()

    return success({'category': cat.to_dict()}, f'分类已更新为 "{name}"')


@category_bp.route('/<int:cat_id>', methods=['DELETE'])
@admin_required
def delete_category(cat_id):
    """逻辑删除分类（已绑定图书的分类不可删除）"""
    cat = Category.query.get(cat_id)
    if not cat:
        return error('分类不存在', code=404)

    book_count = Book.query.filter_by(category_id=cat.id, is_deleted=False).count()
    if book_count > 0:
        return error(f'分类 "{cat.name}" 下仍有 {book_count} 本在架图书，无法删除')

    cat.is_deleted = True
    db.session.commit()

    return success(message=f'分类 "{cat.name}" 已删除')
