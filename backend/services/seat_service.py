# -*- coding: utf-8 -*-
"""自习室座位业务逻辑 — 冲突检测、状态管理"""

from datetime import datetime, date, time
from models.reservation import Reservation
from models.seat import Seat
from extensions import db


def check_time_conflict(seat_id, reserve_date, start_time, end_time, exclude_id=None):
    """检查时段冲突

    Args:
        seat_id: 座位ID
        reserve_date: 预约日期 (date 对象)
        start_time: 开始时间 (time 对象)
        end_time: 结束时间 (time 对象)
        exclude_id: 排除的预约ID (编辑时排除自身)

    Returns:
        bool: True=有冲突, False=无冲突
    """
    query = Reservation.query.filter(
        Reservation.seat_id == seat_id,
        Reservation.date == reserve_date,
        Reservation.status.in_(['reserved', 'checked_in']),
    )

    if exclude_id:
        query = query.filter(Reservation.id != exclude_id)

    existing = query.all()

    for r in existing:
        # 时间重叠检测
        if start_time < r.end_time and end_time > r.start_time:
            return True

    return False


def get_available_slots(seat_id, reserve_date):
    """获取某座位某天的可用时段

    自习室开放时间: 08:00-22:00
    每1小时为一个时段

    Returns:
        list: 可用时段列表 [{'start': '08:00', 'end': '09:00', 'available': True}, ...]
    """
    slots = []
    hour = 8  # 8:00 开始
    while hour < 22:  # 22:00 结束
        start = time(hour, 0)
        end = time(hour + 1, 0)

        conflict = Reservation.query.filter(
            Reservation.seat_id == seat_id,
            Reservation.date == reserve_date,
            Reservation.status.in_(['reserved', 'checked_in']),
            Reservation.start_time < end,
            Reservation.end_time > start,
        ).first()

        slots.append({
            'start': start.strftime('%H:%M'),
            'end': end.strftime('%H:%M'),
            'available': conflict is None,
        })
        hour += 1

    return slots


def auto_release_expired():
    """定时任务：自动释放超时预约"""
    now = datetime.now()

    # 1. 结束时间已过的预约 → completed
    overdue_reservations = Reservation.query.filter(
        Reservation.status.in_(['reserved', 'checked_in']),
        Reservation.date == date.today(),
        Reservation.end_time <= now.time(),
    ).all()
    for r in overdue_reservations:
        r.status = 'completed'

    # 2. 预约未签到超30分钟 → no_show
    from config import Config
    no_show_cutoff = now.time()
    # 简化：检查start_time + 30分钟后仍未签到的reserved状态
    no_show_list = Reservation.query.filter(
        Reservation.status == 'reserved',
        Reservation.date == date.today(),
        Reservation.start_time <= now.time(),
    ).all()
    for r in no_show_list:
        # 计算时间差
        start_dt = datetime.combine(r.date, r.start_time)
        if (now - start_dt).total_seconds() > Config.SEAT_CHECKIN_MINUTES * 60:
            r.status = 'no_show'
            # 释放座位
            seat = Seat.query.get(r.seat_id)
            if seat and seat.status == 'occupied':
                seat.status = 'available'

    db.session.commit()
    return len(overdue_reservations) + len(no_show_list)
