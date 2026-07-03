# -*- coding: utf-8 -*-
"""管理员待处理事项统计 API"""

from flask import Blueprint
from models.book_request import BookRequest
from models.seat_repair import SeatRepair
from utils.response import success
from utils.jwt_utils import admin_required

admin_counts_bp = Blueprint('admin_counts', __name__)


@admin_counts_bp.route('/counts', methods=['GET'])
@admin_required
def pending_counts():
    """获取管理员待处理事项数量"""
    pending_requests = BookRequest.query.filter_by(status='pending').count()
    pending_repairs = SeatRepair.query.filter_by(status='pending').count()
    fixing_repairs = SeatRepair.query.filter_by(status='fixing').count()

    return success({
        'pending_book_requests': pending_requests,
        'pending_seat_repairs': pending_repairs,
        'fixing_seat_repairs': fixing_repairs,
    })
