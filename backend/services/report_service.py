# -*- coding: utf-8 -*-
"""月度报告统计服务。

只负责从现有数据库表聚合真实月度运营数据，不生成 AI 内容，不做导出。
"""

from calendar import monthrange
from collections import Counter
from datetime import date, datetime, time

from extensions import db
from models.book import Book
from models.book_request import BookRequest
from models.borrow import Borrow, update_overdue_borrows
from models.category import Category
from models.reservation import Reservation
from models.seat import Seat
from models.user import User


BORROW_VALID_STATUSES = ('borrowed', 'returned', 'overdue')
RESERVATION_VALID_STATUSES = ('reserved', 'checked_in', 'completed', 'no_show')


def parse_month(month_text):
    """解析 YYYY-MM，返回当月起止边界。"""
    try:
        year, month = map(int, month_text.split('-'))
        if month < 1 or month > 12:
            raise ValueError
    except (AttributeError, TypeError, ValueError):
        raise ValueError('month 参数格式应为 YYYY-MM')

    start_date = date(year, month, 1)
    end_date = date(year, month, monthrange(year, month)[1])
    start_at = datetime.combine(start_date, time.min)
    end_at = datetime.combine(end_date, time.max)
    return start_date, end_date, start_at, end_at


def _borrow_base_query(start_at, end_at):
    return Borrow.query.filter(
        Borrow.borrow_time >= start_at,
        Borrow.borrow_time <= end_at,
        Borrow.status.in_(BORROW_VALID_STATUSES),
    )


def _reservation_base_query(start_date, end_date):
    return Reservation.query.filter(
        Reservation.date >= start_date,
        Reservation.date <= end_date,
        Reservation.status.in_(RESERVATION_VALID_STATUSES),
    )


def _book_request_base_query(start_at, end_at):
    return BookRequest.query.filter(
        BookRequest.create_time >= start_at,
        BookRequest.create_time <= end_at,
    )


def _count_distinct_activity_users(start_at, end_at, start_date, end_date):
    user_ids = set()

    borrow_rows = db.session.query(Borrow.user_id).filter(
        Borrow.borrow_time >= start_at,
        Borrow.borrow_time <= end_at,
        Borrow.status.in_(BORROW_VALID_STATUSES),
    ).distinct().all()
    user_ids.update(row.user_id for row in borrow_rows if row.user_id)

    reservation_rows = db.session.query(Reservation.user_id).filter(
        Reservation.date >= start_date,
        Reservation.date <= end_date,
        Reservation.status.in_(RESERVATION_VALID_STATUSES),
    ).distinct().all()
    user_ids.update(row.user_id for row in reservation_rows if row.user_id)

    request_rows = db.session.query(BookRequest.user_id).filter(
        BookRequest.create_time >= start_at,
        BookRequest.create_time <= end_at,
    ).distinct().all()
    user_ids.update(row.user_id for row in request_rows if row.user_id)

    return user_ids


def _build_core_stats(start_at, end_at, start_date, end_date):
    borrow_count = _borrow_base_query(start_at, end_at).count()
    active_user_ids = _count_distinct_activity_users(start_at, end_at, start_date, end_date)
    reservation_count = _reservation_base_query(start_date, end_date).count()
    overdue_count = Borrow.query.filter(
        Borrow.due_time >= start_at,
        Borrow.due_time <= end_at,
        Borrow.status == 'overdue',
    ).count()
    book_request_count = _book_request_base_query(start_at, end_at).count()

    return {
        'borrow_count': borrow_count,
        'active_user_count': len(active_user_ids),
        'reservation_count': reservation_count,
        'overdue_count': overdue_count,
        'book_request_count': book_request_count,
    }


def _build_book_analysis(start_at, end_at):
    popular_rows = db.session.query(
        Book.id,
        Book.title,
        Book.author,
        Book.stock,
        Category.name.label('category_name'),
        db.func.count(Borrow.id).label('borrow_count'),
    ).join(Borrow, Book.id == Borrow.book_id).join(Category, Book.category_id == Category.id).filter(
        Book.is_deleted == False,
        Borrow.borrow_time >= start_at,
        Borrow.borrow_time <= end_at,
        Borrow.status.in_(BORROW_VALID_STATUSES),
    ).group_by(
        Book.id,
        Book.title,
        Book.author,
        Book.stock,
        Category.name,
    ).order_by(
        db.func.count(Borrow.id).desc(),
        Book.stock.asc(),
    ).limit(10).all()

    popular_books = [{
        'book_id': row.id,
        'title': row.title,
        'author': row.author,
        'category': row.category_name or '未分类',
        'borrow_count': int(row.borrow_count or 0),
        'stock': row.stock or 0,
    } for row in popular_rows]

    category_rows = db.session.query(
        Category.id,
        Category.name,
        db.func.count(Borrow.id).label('borrow_count'),
    ).join(Book, Book.category_id == Category.id).join(Borrow, Borrow.book_id == Book.id).filter(
        Category.is_deleted == False,
        Book.is_deleted == False,
        Borrow.borrow_time >= start_at,
        Borrow.borrow_time <= end_at,
        Borrow.status.in_(BORROW_VALID_STATUSES),
    ).group_by(Category.id, Category.name).order_by(
        db.func.count(Borrow.id).desc(),
    ).all()

    categories = [{
        'category_id': row.id,
        'name': row.name,
        'value': int(row.borrow_count or 0),
    } for row in category_rows]

    stock_risk_books = []
    for book in popular_books:
        if book['borrow_count'] >= 3 and book['stock'] <= 3:
            stock_risk_books.append({
                'book_id': book['book_id'],
                'title': book['title'],
                'stock': book['stock'],
                'borrow_count': book['borrow_count'],
                'reason': f"借阅 {book['borrow_count']} 次，当前库存 {book['stock']} 本",
            })

    return {
        'popular_books': popular_books,
        'categories': categories,
        'stock_risk_books': stock_risk_books[:5],
    }


def _format_hour_slot(start_time):
    if not start_time:
        return '未知时段'
    hour = start_time.hour
    return f'{hour:02d}:00 - {min(hour + 2, 24):02d}:00'


def _build_seat_analysis(start_date, end_date):
    reservations = _reservation_base_query(start_date, end_date).all()

    seat_counter = Counter()
    room_counter = Counter()
    hour_counter = Counter()
    power_counter = Counter({'with_power': 0, 'without_power': 0})

    for reservation in reservations:
        seat = reservation.seat
        if seat:
            seat_counter[(seat.id, seat.seat_number)] += 1
            room_counter[seat.room_name or '未命名自习室'] += 1
            power_counter['with_power' if seat.has_power else 'without_power'] += 1
        hour_counter[_format_hour_slot(reservation.start_time)] += 1

    total_power = power_counter['with_power'] + power_counter['without_power']
    with_power_ratio = round(power_counter['with_power'] / total_power * 100, 1) if total_power else 0
    without_power_ratio = round(power_counter['without_power'] / total_power * 100, 1) if total_power else 0

    return {
        'popular_seats': [{
            'seat_id': seat_id,
            'seat_number': seat_number,
            'reservation_count': count,
        } for (seat_id, seat_number), count in seat_counter.most_common(5)],
        'popular_rooms': [{
            'room_name': room_name,
            'reservation_count': count,
        } for room_name, count in room_counter.most_common(5)],
        'peak_hours': [{
            'label': label,
            'reservation_count': count,
        } for label, count in hour_counter.most_common(8)],
        'feature_preference': {
            'with_power_count': power_counter['with_power'],
            'without_power_count': power_counter['without_power'],
            'with_power_ratio': with_power_ratio,
            'without_power_ratio': without_power_ratio,
        },
    }


def _build_user_behavior(start_at, end_at, start_date, end_date):
    active_user_ids = _count_distinct_activity_users(start_at, end_at, start_date, end_date)
    student_count = 0
    teacher_count = 0

    if active_user_ids:
        role_rows = db.session.query(User.role, db.func.count(User.id)).filter(
            User.id.in_(active_user_ids),
            User.role.in_(('student', 'teacher')),
        ).group_by(User.role).all()
        role_map = {role: count for role, count in role_rows}
        student_count = int(role_map.get('student', 0) or 0)
        teacher_count = int(role_map.get('teacher', 0) or 0)

    total_active = student_count + teacher_count
    renew_count = db.session.query(db.func.sum(Borrow.renew_count)).filter(
        Borrow.borrow_time >= start_at,
        Borrow.borrow_time <= end_at,
        Borrow.status.in_(BORROW_VALID_STATUSES),
    ).scalar() or 0
    book_request_count = _book_request_base_query(start_at, end_at).count()
    overdue_count = Borrow.query.filter(
        Borrow.due_time >= start_at,
        Borrow.due_time <= end_at,
        Borrow.status == 'overdue',
    ).count()

    return {
        'role_distribution': [
            {
                'role': 'student',
                'name': '学生',
                'count': student_count,
                'ratio': round(student_count / total_active * 100, 1) if total_active else 0,
            },
            {
                'role': 'teacher',
                'name': '教师',
                'count': teacher_count,
                'ratio': round(teacher_count / total_active * 100, 1) if total_active else 0,
            },
        ],
        'renew_count': int(renew_count),
        'book_request_count': book_request_count,
        'overdue_count': overdue_count,
    }


def get_monthly_report(month_text):
    """获取指定月份的真实月度统计报告。"""
    start_date, end_date, start_at, end_at = parse_month(month_text)

    update_overdue_borrows()

    return {
        'month': month_text,
        'range': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
        },
        'data_source': 'database',
        'is_mock': False,
        'core_stats': _build_core_stats(start_at, end_at, start_date, end_date),
        'book_analysis': _build_book_analysis(start_at, end_at),
        'seat_analysis': _build_seat_analysis(start_date, end_date),
        'user_behavior': _build_user_behavior(start_at, end_at, start_date, end_date),
    }
