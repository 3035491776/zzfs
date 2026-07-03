# -*- coding: utf-8 -*-
"""图书荐购 API — 学生/教师提交收录请求，管理员审核"""

from flask import Blueprint, request, g
from models.book_request import BookRequest
from models.user import User
from extensions import db
from config import Config
from utils.response import success, error, paginate as paginate_resp
from utils.jwt_utils import login_required, admin_required
from services.notification_service import create_notification

book_request_bp = Blueprint('book_request', __name__)


# ================================================================
# 提交荐购请求
# ================================================================
@book_request_bp.route('', methods=['POST'])
@login_required
def submit_request():
    """提交图书荐购

    Request Body:
        title: 书名 (必填)
        author: 作者
        publisher: 出版社
        isbn: ISBN (选填)
        reason: 荐购理由
    """
    if g.current_user['role'] == 'admin':
        return error('管理员无需荐购，可直接添加图书')

    data = request.get_json(silent=True) or {}
    title = data.get('title', '').strip()
    author = data.get('author', '').strip()
    publisher = data.get('publisher', '').strip()
    isbn = data.get('isbn', '').strip()
    reason = data.get('reason', '').strip()

    if not title:
        return error('书名不能为空')

    if not reason:
        return error('请填写荐购理由')

    req = BookRequest(
        user_id=g.current_user['user_id'],
        title=title,
        author=author or None,
        publisher=publisher or None,
        isbn=isbn or None,
        reason=reason,
        status='pending',
    )
    db.session.add(req)
    db.session.commit()

    return success({'request': req.to_dict()}, '荐购请求已提交，感谢您的推荐！')


# ================================================================
# 我的荐购列表
# ================================================================
@book_request_bp.route('/my', methods=['GET'])
@login_required
def my_requests():
    """我的荐购列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '').strip()

    query = BookRequest.query.filter_by(user_id=g.current_user['user_id'])
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(BookRequest.create_time.desc()).paginate(
        page=page, per_page=Config.PAGE_SIZE, error_out=False
    )

    return success(paginate_resp(pagination, [r.to_dict() for r in pagination.items]))


# ================================================================
# 所有荐购列表（管理员）
# ================================================================
@book_request_bp.route('', methods=['GET'])
@admin_required
def all_requests():
    """所有荐购列表（管理员）"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '').strip()

    query = BookRequest.query
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(BookRequest.create_time.desc()).paginate(
        page=page, per_page=Config.PAGE_SIZE, error_out=False
    )

    return success(paginate_resp(pagination, [r.to_dict() for r in pagination.items]))


# ================================================================
# 采纳荐购（管理员）
# ================================================================
@book_request_bp.route('/<int:req_id>/approve', methods=['PUT'])
@admin_required
def approve_request(req_id):
    """采纳荐购"""
    req = BookRequest.query.get(req_id)
    if not req:
        return error('荐购记录不存在', code=404)
    if req.status != 'pending':
        return error('该请求已处理过')

    data = request.get_json(silent=True) or {}
    comment = data.get('comment', '').strip()

    req.status = 'approved'
    req.review_admin_id = g.current_user['user_id']
    req.review_comment = comment or '已采纳，将尽快采购入库'
    db.session.commit()

    # 通知申请人
    create_notification(
        user_id=req.user_id,
        title='🎉 您的图书荐购已被采纳',
        content=f'感谢您的推荐！您推荐的《{req.title}》已被采纳，我们将尽快采购入库。您的参与让图书馆变得更好，请继续为我们推荐好书！',
        n_type='system',
    )

    return success(message=f'已采纳《{req.title}》的荐购请求')


# ================================================================
# 驳回荐购（管理员）
# ================================================================
@book_request_bp.route('/<int:req_id>/reject', methods=['PUT'])
@admin_required
def reject_request(req_id):
    """驳回荐购"""
    req = BookRequest.query.get(req_id)
    if not req:
        return error('荐购记录不存在', code=404)
    if req.status != 'pending':
        return error('该请求已处理过')

    data = request.get_json(silent=True) or {}
    comment = data.get('comment', '').strip()

    req.status = 'rejected'
    req.review_admin_id = g.current_user['user_id']
    req.review_comment = comment or '暂不收录'
    db.session.commit()

    # 通知申请人
    create_notification(
        user_id=req.user_id,
        title='荐购结果通知',
        content=f'感谢您的推荐！您推荐的《{req.title}》经评估暂未被采纳。{comment}不过您的热心参与我们非常感激，欢迎继续推荐其他好书！',
        n_type='system',
    )

    return success(message=f'已驳回《{req.title}》的荐购请求')
