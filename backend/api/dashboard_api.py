# -*- coding: utf-8 -*-
"""数据大屏 API — 核心指标 + 图表数据"""

from datetime import datetime, timedelta
from flask import Blueprint, request
from models.book import Book
from models.category import Category
from models.borrow import Borrow, update_overdue_borrows
from models.user import User
from models.seat import Seat
from models.reservation import Reservation
from extensions import db
from utils.response import success
from utils.jwt_utils import login_required, admin_required

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/stats', methods=['GET'])
@login_required
def stats():
    """核心指标汇总"""
    update_overdue_borrows()

    total_books = Book.query.filter_by(is_deleted=False).count()
    total_stock = db.session.query(db.func.sum(Book.stock)).filter(
        Book.is_deleted == False).scalar() or 0
    total_borrowed = Borrow.query.filter(
        Borrow.status.in_(['borrowed', 'overdue'])).count()
    total_overdue = Borrow.query.filter_by(status='overdue').count()
    total_students = User.query.filter_by(role='student').count()
    total_teachers = User.query.filter_by(role='teacher').count()
    available_seats = Seat.query.filter_by(status='available').count()
    today_reservations = Reservation.query.filter_by(
        date=datetime.now().date()).count()

    return success({
        'total_books': total_books,
        'total_stock': total_stock,
        'total_borrowed': total_borrowed,
        'total_overdue': total_overdue,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'available_seats': available_seats,
        'today_reservations': today_reservations,
    })


@dashboard_bp.route('/borrow-trend', methods=['GET'])
@admin_required
def borrow_trend():
    """借阅趋势 — 按月份统计（最近12个月）"""
    now = datetime.now()
    trend = []

    for i in range(11, -1, -1):
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1

        count = Borrow.query.filter(
            db.extract('year', Borrow.borrow_time) == year,
            db.extract('month', Borrow.borrow_time) == month,
            Borrow.status.in_(['borrowed', 'returned', 'overdue']),
        ).count()

        trend.append({
            'month': f'{year}-{month:02d}',
            'count': count,
        })

    return success({'trend': trend})


@dashboard_bp.route('/category-chart', methods=['GET'])
@admin_required
def category_chart():
    """分类借阅占比"""
    categories = Category.query.filter_by(is_deleted=False).all()
    chart_data = []

    for cat in categories:
        count = Borrow.query.join(Book).filter(
            Book.category_id == cat.id
        ).count()
        if count > 0:
            chart_data.append({
                'name': cat.name,
                'value': count,
            })

    return success({'chart': chart_data})


@dashboard_bp.route('/popular-books', methods=['GET'])
@admin_required
def popular_books():
    """热门图书 TOP10 — 按借阅次数"""
    top = db.session.query(
        Book.id, Book.title, Book.author,
        db.func.count(Borrow.id).label('borrow_count')
    ).join(Borrow, Book.id == Borrow.book_id).filter(
        Book.is_deleted == False
    ).group_by(Book.id).order_by(
        db.func.count(Borrow.id).desc()
    ).limit(10).all()

    return success({
        'list': [{
            'book_id': b.id,
            'title': b.title,
            'author': b.author,
            'borrow_count': b.borrow_count,
        } for b in top],
    })


@dashboard_bp.route('/seat-usage', methods=['GET'])
@admin_required
def seat_usage():
    """座位使用率"""
    total = Seat.query.count()
    available = Seat.query.filter_by(status='available').count()
    occupied = Seat.query.filter_by(status='occupied').count()
    maintenance = Seat.query.filter_by(status='maintenance').count()

    usage_rate = round((occupied / total * 100), 1) if total > 0 else 0

    return success({
        'total': total,
        'available': available,
        'occupied': occupied,
        'maintenance': maintenance,
        'usage_rate': usage_rate,
    })


@dashboard_bp.route('/user-activity', methods=['GET'])
@admin_required
def user_activity():
    """用户活跃度"""
    active_borrowers = db.session.query(
        db.func.count(db.func.distinct(Borrow.user_id))
    ).filter(
        Borrow.create_time >= datetime.now() - timedelta(days=30)
    ).scalar() or 0

    return success({
        'active_borrowers_30d': active_borrowers,
        'total_users': User.query.count(),
    })
