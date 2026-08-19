# -*- coding: utf-8 -*-
"""借阅管理 API — 申请/审批/归还/续借/查询"""

from datetime import datetime, timedelta
from flask import Blueprint, request, g
from models.borrow import Borrow, update_overdue_borrows
from models.book import Book
from models.user import User
from extensions import db
from config import Config
from utils.response import success, error, paginate as paginate_resp
from utils.jwt_utils import login_required, admin_required
from services.notification_service import create_notification
from services.borrow_renewal_service import (
    RenewalPersistenceError,
    RenewalRuleError,
    renew_borrow_record,
)

borrow_bp = Blueprint('borrow', __name__)


# ================================================================
# 借阅列表（管理员查看全部，学生/老师只看自己的）
# ================================================================
@borrow_bp.route('', methods=['GET'])
@login_required
def get_borrows():
    """借阅列表 — 分页 + 筛选

    Query Params:
        page: 页码
        status: 状态筛选
        scope: 范围 (all=管理员全部, my=本人)
    """
    update_overdue_borrows()

    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '').strip()
    scope = request.args.get('scope', 'my').strip()

    query = Borrow.query

    # 非管理员只能看自己的
    if g.current_user['role'] != 'admin' or scope == 'my':
        query = query.filter_by(user_id=g.current_user['user_id'])

    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(Borrow.create_time.desc()).paginate(
        page=page, per_page=Config.PAGE_SIZE, error_out=False
    )

    return success(paginate_resp(pagination, [b.to_dict() for b in pagination.items]))


# ================================================================
# 我的借阅记录
# ================================================================
@borrow_bp.route('/my', methods=['GET'])
@login_required
def my_borrows():
    """我的借阅记录 — 含各状态统计"""
    update_overdue_borrows()

    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '').strip()
    user_id = g.current_user['user_id']

    query = Borrow.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(Borrow.create_time.desc()).paginate(
        page=page, per_page=Config.PAGE_SIZE, error_out=False
    )

    # 各状态统计
    counts = {
        'pending': Borrow.query.filter_by(user_id=user_id, status='pending').count(),
        'borrowed': Borrow.query.filter_by(user_id=user_id, status='borrowed').count(),
        'overdue': Borrow.query.filter_by(user_id=user_id, status='overdue').count(),
        'returned': Borrow.query.filter_by(user_id=user_id, status='returned').count(),
        'rejected': Borrow.query.filter_by(user_id=user_id, status='rejected').count(),
    }

    return success({
        **paginate_resp(pagination, [b.to_dict() for b in pagination.items]),
        'counts': counts,
    })


# ================================================================
# 提交借阅申请
# ================================================================
@borrow_bp.route('', methods=['POST'])
@login_required
def apply_borrow():
    """提交借阅申请

    Request Body:
        book_id: 图书ID
    """
    if g.current_user['role'] == 'admin':
        return error('管理员无法借阅图书')

    data = request.get_json(silent=True) or {}
    book_id = int(data.get('book_id', 0))
    user_id = g.current_user['user_id']

    book = Book.query.get(book_id)
    if not book or book.is_deleted:
        return error('图书不存在或已下架', code=404)

    # 库存校验
    if book.stock <= 0:
        return error('该图书暂无库存')

    # 最大借阅数量
    active_count = Borrow.query.filter(
        Borrow.user_id == user_id,
        Borrow.status.in_(['pending', 'borrowed', 'overdue'])
    ).count()
    if active_count >= Config.MAX_BORROW_BOOKS:
        return error(f'您当前有 {active_count} 本在途借阅，已达上限 {Config.MAX_BORROW_BOOKS} 本')

    # 重复借阅校验
    exist = Borrow.query.filter(
        Borrow.user_id == user_id,
        Borrow.book_id == book_id,
        Borrow.status.in_(['pending', 'borrowed', 'overdue'])
    ).first()
    if exist:
        return error(f'您已对《{book.title}》有在途借阅记录，请勿重复申请')

    borrow = Borrow(user_id=user_id, book_id=book_id, status='pending')
    db.session.add(borrow)
    db.session.commit()

    return success({'borrow': borrow.to_dict()}, f'《{book.title}》借阅申请已提交，等待管理员审核')


# ================================================================
# 审批通过借阅
# ================================================================
@borrow_bp.route('/<int:borrow_id>/approve', methods=['PUT'])
@admin_required
def approve_borrow(borrow_id):
    """审批通过借阅申请"""
    borrow = Borrow.query.get(borrow_id)
    if not borrow:
        return error('借阅记录不存在', code=404)
    if borrow.status != 'pending':
        return error('该申请已处理过')

    book = Book.query.get(borrow.book_id)
    if book.stock <= 0:
        return error('图书库存不足，无法借出')

    # 通过：扣库存 + 记录时间
    book.stock -= 1
    borrow.status = 'borrowed'
    borrow.borrow_time = datetime.now()
    borrow.due_time = datetime.now() + timedelta(days=Config.BORROW_DAYS)
    borrow.review_admin_id = g.current_user['user_id']
    db.session.commit()

    # 发送通知
    create_notification(
        user_id=borrow.user_id,
        title='借阅申请已通过',
        content=f'您借阅的《{book.title}》已通过审核，到期日：{borrow.due_time.strftime("%Y-%m-%d")}',
        n_type='borrow',
    )

    return success({
        'borrow': borrow.to_dict(),
        'due_time': borrow.due_time.strftime('%Y-%m-%d'),
    }, '借阅申请已通过')


# ================================================================
# 驳回借阅申请
# ================================================================
@borrow_bp.route('/<int:borrow_id>/reject', methods=['PUT'])
@admin_required
def reject_borrow(borrow_id):
    """驳回借阅申请"""
    borrow = Borrow.query.get(borrow_id)
    if not borrow:
        return error('借阅记录不存在', code=404)
    if borrow.status != 'pending':
        return error('该申请已处理过')

    borrow.status = 'rejected'
    borrow.review_admin_id = g.current_user['user_id']
    db.session.commit()

    create_notification(
        user_id=borrow.user_id,
        title='借阅申请已驳回',
        content=f'您对《{borrow.book.title}》的借阅申请已被驳回',
        n_type='borrow',
    )

    return success(message='借阅申请已驳回')


# ================================================================
# 确认归还
# ================================================================
@borrow_bp.route('/<int:borrow_id>/return', methods=['PUT'])
@admin_required
def return_borrow(borrow_id):
    """确认归还"""
    borrow = Borrow.query.get(borrow_id)
    if not borrow:
        return error('借阅记录不存在', code=404)
    if borrow.status not in ('borrowed', 'overdue'):
        return error('该记录不处于在借/逾期状态')

    book = Book.query.get(borrow.book_id)
    book.stock += 1
    borrow.status = 'returned'
    borrow.return_time = datetime.now()
    borrow.review_admin_id = g.current_user['user_id']
    db.session.commit()

    create_notification(
        user_id=borrow.user_id,
        title='图书已归还',
        content=f'《{book.title}》已确认归还',
        n_type='return',
    )

    return success(message=f'《{book.title}》已确认归还')


# ================================================================
# 续借
# ================================================================
@borrow_bp.route('/<int:borrow_id>/renew', methods=['PUT'])
@login_required
def renew_borrow(borrow_id):
    """续借（仅本人可操作）"""
    try:
        result = renew_borrow_record(
            borrow_id,
            g.current_user['user_id'],
            max_renew_count=Config.MAX_RENEW_COUNT,
            borrow_days=Config.BORROW_DAYS,
        )
    except RenewalRuleError as exc:
        return error(str(exc), code=exc.status_code)
    except RenewalPersistenceError:
        return error('续借失败，请稍后重试', code=500)

    borrow = result.borrow

    return success({
        'borrow': borrow.to_dict(),
        'new_due_time': borrow.due_time.strftime('%Y-%m-%d'),
    }, f'续借成功，新到期日：{borrow.due_time.strftime("%Y-%m-%d")}')
