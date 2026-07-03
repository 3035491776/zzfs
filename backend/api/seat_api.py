# -*- coding: utf-8 -*-
"""自习室座位管理 API"""

from flask import Blueprint, request
from models.seat import Seat
from extensions import db
from config import Config
from utils.response import success, error, paginate as paginate_resp
from utils.jwt_utils import login_required, admin_required

seat_bp = Blueprint('seat', __name__)


@seat_bp.route('', methods=['GET'])
@login_required
def get_seats():
    """座位列表 — 按楼层、房间筛选

    Query Params:
        floor: 楼层筛选
        room_name: 自习室名称
        status: 状态筛选
    """
    floor = request.args.get('floor', 0, type=int)
    room_name = request.args.get('room_name', '').strip()
    status = request.args.get('status', '').strip()

    query = Seat.query
    if floor > 0:
        query = query.filter_by(floor=floor)
    if room_name:
        query = query.filter(Seat.room_name.contains(room_name))
    if status:
        query = query.filter_by(status=status)

    seats = query.order_by(Seat.floor.asc(), Seat.room_name.asc(), Seat.seat_number.asc()).all()

    # 按楼层分组
    floors = {}
    for s in seats:
        f = f'F{s.floor}'
        if f not in floors:
            floors[f] = []
        floors[f].append(s.to_dict())

    return success({
        'list': [s.to_dict() for s in seats],
        'floors': floors,
        'rooms': list(set(s.room_name for s in seats)),
        'total': len(seats),
    })


@seat_bp.route('/<int:seat_id>', methods=['GET'])
@login_required
def get_seat(seat_id):
    """获取座位详情"""
    seat = Seat.query.get(seat_id)
    if not seat:
        return error('座位不存在', code=404)
    return success({'seat': seat.to_dict()})


@seat_bp.route('', methods=['POST'])
@admin_required
def add_seat():
    """新增座位"""
    data = request.get_json(silent=True) or {}
    seat_number = data.get('seat_number', '').strip()
    room_name = data.get('room_name', '').strip()
    floor = int(data.get('floor', 1))
    has_power = data.get('has_power', True)
    description = data.get('description', '').strip()

    if not seat_number or not room_name:
        return error('座位编号和自习室名称为必填项')

    if Seat.query.filter_by(seat_number=seat_number).first():
        return error(f'座位编号 "{seat_number}" 已存在')

    seat = Seat(
        seat_number=seat_number,
        room_name=room_name,
        floor=floor,
        has_power=has_power,
        description=description,
    )
    db.session.add(seat)
    db.session.commit()

    return success({'seat': seat.to_dict()}, f'座位 {seat_number} 已添加')


@seat_bp.route('/<int:seat_id>', methods=['PUT'])
@admin_required
def update_seat(seat_id):
    """编辑座位信息"""
    seat = Seat.query.get(seat_id)
    if not seat:
        return error('座位不存在', code=404)

    data = request.get_json(silent=True) or {}
    seat_number = data.get('seat_number', '').strip()
    room_name = data.get('room_name', '').strip()
    floor = data.get('floor', None)
    has_power = data.get('has_power', None)
    status = data.get('status', '').strip()
    description = data.get('description', '').strip()

    if seat_number and seat_number != seat.seat_number:
        if Seat.query.filter_by(seat_number=seat_number).first():
            return error(f'座位编号 "{seat_number}" 已存在')
        seat.seat_number = seat_number
    if room_name:
        seat.room_name = room_name
    if floor is not None:
        seat.floor = int(floor)
    if has_power is not None:
        seat.has_power = has_power
    if status and status in ('available', 'occupied', 'maintenance'):
        seat.status = status
    if description:
        seat.description = description

    db.session.commit()
    return success({'seat': seat.to_dict()}, '座位信息已更新')


@seat_bp.route('/<int:seat_id>', methods=['DELETE'])
@admin_required
def delete_seat(seat_id):
    """删除座位"""
    seat = Seat.query.get(seat_id)
    if not seat:
        return error('座位不存在', code=404)

    db.session.delete(seat)
    db.session.commit()
    return success(message=f'座位 {seat.seat_number} 已删除')
