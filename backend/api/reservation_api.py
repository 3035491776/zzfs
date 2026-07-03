# -*- coding: utf-8 -*-
"""自习室预约 API — 预约/签到/取消/查询"""

from datetime import datetime, date, time, timedelta
from flask import Blueprint, request, g
from models.reservation import Reservation
from models.seat import Seat
from extensions import db
from config import Config
from utils.response import success, error, paginate as paginate_resp
from utils.jwt_utils import login_required, admin_required
from services.seat_service import check_time_conflict, get_available_slots
from services.notification_service import create_notification

reservation_bp = Blueprint('reservation', __name__)


# ================================================================
# 查看座位可用时段
# ================================================================
@reservation_bp.route('/seats/<int:seat_id>/slots', methods=['GET'])
@login_required
def get_seat_slots(seat_id):
    """获取某座位的可用时段

    Query Params:
        date: 日期 (YYYY-MM-DD)，默认今天
    """
    seat = Seat.query.get(seat_id)
    if not seat:
        return error('座位不存在', code=404)

    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        reserve_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return error('日期格式错误，请使用 YYYY-MM-DD')

    slots = get_available_slots(seat_id, reserve_date)
    return success({
        'seat': seat.to_dict(),
        'date': date_str,
        'slots': slots,
    })


# ================================================================
# 预约座位
# ================================================================
@reservation_bp.route('/seats/<int:seat_id>/reserve', methods=['POST'])
@login_required
def reserve_seat(seat_id):
    """预约座位

    Request Body:
        date: 日期 (YYYY-MM-DD)
        start_time: 开始时间 (HH:MM)
        end_time: 结束时间 (HH:MM)
    """
    if g.current_user['role'] == 'admin':
        return error('管理员无法预约座位')

    seat = Seat.query.get(seat_id)
    if not seat:
        return error('座位不存在', code=404)
    if seat.status != 'available':
        return error(f'座位当前状态: {seat.status_text()}，无法预约')

    data = request.get_json(silent=True) or {}
    date_str = data.get('date', '')
    start_str = data.get('start_time', '')
    end_str = data.get('end_time', '')

    if not all([date_str, start_str, end_str]):
        return error('日期和时段为必填项')

    try:
        reserve_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_str, '%H:%M').time()
        end_time = datetime.strptime(end_str, '%H:%M').time()
    except ValueError:
        return error('日期或时间格式错误')

    # 日期校验
    today = date.today()
    max_date = today + timedelta(days=Config.SEAT_RESERVE_DAYS)
    if reserve_date < today:
        return error('不能预约过去的日期')
    if reserve_date > max_date:
        return error(f'只能预约 {Config.SEAT_RESERVE_DAYS} 天内的座位')

    # 时间校验
    if start_time >= end_time:
        return error('开始时间必须早于结束时间')
    if start_time < time(8, 0) or end_time > time(22, 0):
        return error('自习室开放时间为 08:00-22:00')

    # 冲突检测
    if check_time_conflict(seat_id, reserve_date, start_time, end_time):
        return error('该时段已被预约，请选择其他时段')

    # 检查用户本月 no_show 次数
    month_start = date(today.year, today.month, 1)
    no_show_count = Reservation.query.filter(
        Reservation.user_id == g.current_user['user_id'],
        Reservation.status == 'no_show',
        Reservation.create_time >= month_start,
    ).count()
    if no_show_count >= Config.SEAT_NO_SHOW_LIMIT:
        return error(f'本月未签到次数已达 {no_show_count} 次，已被限制预约')

    reservation = Reservation(
        user_id=g.current_user['user_id'],
        seat_id=seat_id,
        date=reserve_date,
        start_time=start_time,
        end_time=end_time,
        status='reserved',
    )
    db.session.add(reservation)

    # 更新座位状态
    seat.status = 'occupied'
    db.session.commit()

    create_notification(
        user_id=g.current_user['user_id'],
        title='自习室预约成功',
        content=f'座位 {seat.seat_number}（{seat.room_name}）预约成功：{date_str} {start_str}-{end_str}',
        n_type='reservation',
    )

    return success({
        'reservation': reservation.to_dict(),
    }, f'座位 {seat.seat_number} 预约成功')


# ================================================================
# 签到
# ================================================================
@reservation_bp.route('/reservations/<int:res_id>/checkin', methods=['POST'])
@login_required
def checkin(res_id):
    """签到"""
    reservation = Reservation.query.get(res_id)
    if not reservation:
        return error('预约记录不存在', code=404)
    if reservation.user_id != g.current_user['user_id']:
        return error('不是您的预约', code=403)
    if reservation.status != 'reserved':
        return error(f'当前状态: {reservation.status_text()}，无法签到')

    now = datetime.now()

    # 检查是否迟到
    start_dt = datetime.combine(reservation.date, reservation.start_time)
    if now - start_dt > timedelta(minutes=Config.SEAT_CHECKIN_MINUTES):
        reservation.status = 'no_show'
        seat = Seat.query.get(reservation.seat_id)
        if seat:
            seat.status = 'available'
        db.session.commit()
        return error(f'已超过签到时间（迟到 {Config.SEAT_CHECKIN_MINUTES} 分钟），标记为未签到')

    reservation.status = 'checked_in'
    reservation.checkin_time = now
    db.session.commit()

    return success({
        'reservation': reservation.to_dict(),
    }, '签到成功')


# ================================================================
# 取消预约
# ================================================================
@reservation_bp.route('/reservations/<int:res_id>/cancel', methods=['POST'])
@login_required
def cancel_reservation(res_id):
    """取消预约"""
    reservation = Reservation.query.get(res_id)
    if not reservation:
        return error('预约记录不存在', code=404)
    if reservation.user_id != g.current_user['user_id']:
        return error('不是您的预约', code=403)
    if reservation.status == 'cancelled':
        return error('该预约已取消')

    reservation.status = 'cancelled'

    # 释放座位
    seat = Seat.query.get(reservation.seat_id)
    if seat and seat.status == 'occupied':
        # 检查是否还有该座位的其他有效预约
        active_count = Reservation.query.filter(
            Reservation.seat_id == seat.id,
            Reservation.status == 'checked_in',
            Reservation.date == date.today(),
        ).count()
        if active_count == 0:
            seat.status = 'available'

    db.session.commit()

    return success(message='预约已取消')


# ================================================================
# 我的预约列表
# ================================================================
@reservation_bp.route('/reservations/my', methods=['GET'])
@login_required
def my_reservations():
    """我的预约列表"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '').strip()

    query = Reservation.query.filter_by(user_id=g.current_user['user_id'])
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(Reservation.create_time.desc()).paginate(
        page=page, per_page=Config.PAGE_SIZE, error_out=False
    )

    return success(paginate_resp(pagination, [r.to_dict() for r in pagination.items]))


# ================================================================
# 所有预约（管理员）
# ================================================================
@reservation_bp.route('/reservations', methods=['GET'])
@admin_required
def all_reservations():
    """所有预约列表（管理员）"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '').strip()

    query = Reservation.query
    if status:
        query = query.filter_by(status=status)

    pagination = query.order_by(Reservation.create_time.desc()).paginate(
        page=page, per_page=Config.PAGE_SIZE, error_out=False
    )

    return success(paginate_resp(pagination, [r.to_dict() for r in pagination.items]))
