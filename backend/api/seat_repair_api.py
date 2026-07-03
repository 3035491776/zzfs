# -*- coding: utf-8 -*-
"""座位报修 API — 学生/教师报修，管理员审核维修"""

from flask import Blueprint, request, g
from models.seat_repair import SeatRepair
from models.seat import Seat
from extensions import db
from config import Config
from utils.response import success, error, paginate as paginate_resp
from utils.jwt_utils import login_required, admin_required
from services.notification_service import create_notification

seat_repair_bp = Blueprint('seat_repair', __name__)


@seat_repair_bp.route('', methods=['POST'])
@login_required
def submit_repair():
    """提交座位报修"""
    if g.current_user['role'] == 'admin':
        return error('管理员无需报修，可直接修改座位状态')

    data = request.get_json(silent=True) or {}
    seat_id = int(data.get('seat_id', 0))
    description = data.get('description', '').strip()

    if not seat_id:
        return error('请选择要报修的座位')
    if not description:
        return error('请描述故障情况')

    seat = Seat.query.get(seat_id)
    if not seat:
        return error('座位不存在', code=404)

    # 检查是否有未处理的报修
    existing = SeatRepair.query.filter_by(seat_id=seat_id, status='pending').first()
    if existing:
        return error('该座位已有未处理的报修，请耐心等待')

    repair = SeatRepair(
        user_id=g.current_user['user_id'],
        seat_id=seat_id,
        description=description,
        status='pending',
    )
    db.session.add(repair)
    db.session.commit()

    return success({'repair': repair.to_dict()}, '报修已提交，我们会尽快处理')


@seat_repair_bp.route('/my', methods=['GET'])
@login_required
def my_repairs():
    """我的报修列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '').strip()

    query = SeatRepair.query.filter_by(user_id=g.current_user['user_id'])
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(SeatRepair.create_time.desc()).paginate(
        page=page, per_page=Config.PAGE_SIZE, error_out=False
    )
    return success(paginate_resp(pagination, [r.to_dict() for r in pagination.items]))


@seat_repair_bp.route('', methods=['GET'])
@admin_required
def all_repairs():
    """所有报修列表（管理员）"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '').strip()

    query = SeatRepair.query
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(SeatRepair.create_time.desc()).paginate(
        page=page, per_page=Config.PAGE_SIZE, error_out=False
    )
    return success(paginate_resp(pagination, [r.to_dict() for r in pagination.items]))


@seat_repair_bp.route('/<int:repair_id>/fix', methods=['PUT'])
@admin_required
def mark_fixing(repair_id):
    """标记为维修中"""
    repair = SeatRepair.query.get(repair_id)
    if not repair:
        return error('报修记录不存在', code=404)
    if repair.status != 'pending':
        return error('该报修已处理过')

    repair.status = 'fixing'
    repair.review_admin_id = g.current_user['user_id']
    # 座位标记为维护中
    seat = Seat.query.get(repair.seat_id)
    if seat:
        seat.status = 'maintenance'
    db.session.commit()

    create_notification(
        user_id=repair.user_id,
        title='🔧 您的报修正在处理中',
        content=f'感谢您的报修！座位 {repair.seat.seat_number}（{repair.seat.room_name}）已安排维修人员处理，我们会尽快修复。感谢您为改善图书馆环境做出的贡献！',
        n_type='system',
    )
    return success(message=f'座位 {repair.seat.seat_number} 已标记为维修中')


@seat_repair_bp.route('/<int:repair_id>/resolve', methods=['PUT'])
@admin_required
def resolve_repair(repair_id):
    """标记为已修复"""
    repair = SeatRepair.query.get(repair_id)
    if not repair:
        return error('报修记录不存在', code=404)

    data = request.get_json(silent=True) or {}
    comment = data.get('comment', '').strip()

    repair.status = 'resolved'
    repair.review_admin_id = g.current_user['user_id']
    repair.review_comment = comment or '已修复'

    # 恢复座位状态
    seat = Seat.query.get(repair.seat_id)
    if seat:
        seat.status = 'available'
    db.session.commit()

    create_notification(
        user_id=repair.user_id,
        title='🔧 您报修的座位已修复完毕',
        content=f'感谢您的反馈！座位 {repair.seat.seat_number}（{repair.seat.room_name}）已修复，现在可以正常预约使用了。您的报修让自习环境更加舒适，谢谢您！',
        n_type='system',
    )
    return success(message=f'座位 {repair.seat.seat_number} 已修复')


@seat_repair_bp.route('/<int:repair_id>/reject', methods=['PUT'])
@admin_required
def reject_repair(repair_id):
    """驳回报修"""
    repair = SeatRepair.query.get(repair_id)
    if not repair:
        return error('报修记录不存在', code=404)

    data = request.get_json(silent=True) or {}
    comment = data.get('comment', '').strip()

    repair.status = 'rejected'
    repair.review_admin_id = g.current_user['user_id']
    repair.review_comment = comment or '经检查无需维修'
    db.session.commit()

    create_notification(
        user_id=repair.user_id,
        title='报修反馈通知',
        content=f'感谢您的细心反馈！关于座位 {repair.seat.seat_number} 的报修，经管理员检查：{comment}。虽然这次没有维修，但我们非常感激您对图书馆的关心！',
        n_type='system',
    )
    return success(message='报修已驳回')
