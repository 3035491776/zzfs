# -*- coding: utf-8 -*-
"""Read-only Python implementation of the sealed METRIC-01 through METRIC-06."""

from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from extensions import db
from models.book import Book
from models.book_request import BookRequest
from models.borrow import Borrow
from models.borrow_due_change import BorrowDueChange
from models.category import Category
from models.metric_job_run import MetricJobRun
from models.reservation import Reservation
from models.seat_capacity_snapshot import SeatCapacitySnapshot
from models.user import User
from services.metric_contract import MetricResult, PERIOD_TYPES


BORROW_VALID_STATUSES = ('borrowed', 'returned', 'overdue')
RESERVATION_VALID_STATUSES = ('reserved', 'checked_in', 'completed', 'no_show')
DUE_CHANGE_TRACKING_START = datetime(2026, 8, 19, 0, 0, 0)
SERVICE_START = time(8, 0)
SERVICE_END = time(22, 0)
SIX_DECIMALS = Decimal('0.000001')


def _six_decimals(value):
    return value.quantize(SIX_DECIMALS, rounding=ROUND_HALF_UP)


def _base_result(metric_code, period_type, start, end, **overrides):
    values = {
        'metric_code': metric_code,
        'period_type': period_type,
        'period_start': start,
        'period_end': end,
        'temporal_type': 'INTERVAL',
        'as_of_time': None,
        'scope_type': 'ALL',
        'scope_key': 'ALL',
        'dimension_type': 'ALL',
        'dimension_key': 'ALL',
        'value_decimal': Decimal(0),
        'unit': 'COUNT',
        'rank': None,
        'dimension_payload': None,
        'quality_status': 'EXACT',
        'quality_reason': None,
        'coverage_ratio': None,
    }
    values.update(overrides)
    return MetricResult(**values)


def _metric_01(period_type, start, end, generated_time):
    available = db.session.query(db.func.coalesce(db.func.sum(Book.stock), 0)).filter(
        Book.is_deleted.is_(False)
    ).scalar() or 0
    borrowed = db.session.query(db.func.count(Borrow.id)).join(
        Book, Book.id == Borrow.book_id
    ).filter(
        Book.is_deleted.is_(False),
        Borrow.status.in_(('borrowed', 'overdue')),
    ).scalar() or 0
    return _base_result(
        'METRIC-01', period_type, start, end,
        temporal_type='POINT',
        as_of_time=generated_time,
        value_decimal=Decimal(int(available) + int(borrowed)),
        unit='COPY',
        quality_status='BEST_EFFORT',
        quality_reason='CURRENT_INVENTORY_USED_WITHOUT_HISTORICAL_STOCK_FACTS',
    )


def _borrow_fact_query(start, end):
    return Borrow.query.filter(
        Borrow.borrow_time >= start,
        Borrow.borrow_time < end,
        Borrow.status.in_(BORROW_VALID_STATUSES),
    )


def _metric_02(period_type, start, end):
    return _base_result(
        'METRIC-02', period_type, start, end,
        value_decimal=Decimal(_borrow_fact_query(start, end).count()),
    )


def _due_time_at(borrow, changes, boundary):
    before = [change for change in changes if change.change_time < boundary]
    if before:
        return max(before, key=lambda item: (item.change_time, item.change_sequence)).new_due_time
    after = [change for change in changes if change.change_time >= boundary]
    if after:
        return min(after, key=lambda item: (item.change_time, item.change_sequence)).old_due_time
    return borrow.due_time


def _metric_03(period_type, start, end):
    borrows = Borrow.query.filter(
        Borrow.borrow_time.isnot(None),
        Borrow.borrow_time < end,
        Borrow.due_time.isnot(None),
    ).all()
    borrow_ids = [borrow.id for borrow in borrows]
    changes_by_borrow = defaultdict(list)
    if borrow_ids:
        changes = BorrowDueChange.query.filter(
            BorrowDueChange.borrow_id.in_(borrow_ids)
        ).order_by(
            BorrowDueChange.borrow_id,
            BorrowDueChange.change_time,
            BorrowDueChange.change_sequence,
        ).all()
        for change in changes:
            changes_by_borrow[change.borrow_id].append(change)

    overdue = 0
    for borrow in borrows:
        due_time = _due_time_at(borrow, changes_by_borrow[borrow.id], end)
        if due_time is None or due_time >= end:
            continue
        if borrow.return_time is None or borrow.return_time >= end:
            overdue += 1

    exact = end > DUE_CHANGE_TRACKING_START
    return _base_result(
        'METRIC-03', period_type, start, end,
        temporal_type='POINT',
        as_of_time=end,
        value_decimal=Decimal(overdue),
        quality_status='EXACT' if exact else 'BEST_EFFORT',
        quality_reason=None if exact else 'PERIOD_PRECEDES_DUE_CHANGE_TRACKING',
    )


def _metric_04(period_type, start, end):
    user_ids = set()
    user_ids.update(
        user_id for (user_id,) in db.session.query(Borrow.user_id).filter(
            Borrow.borrow_time >= start,
            Borrow.borrow_time < end,
            Borrow.status.in_(BORROW_VALID_STATUSES),
        ).distinct().all()
        if user_id is not None
    )
    user_ids.update(
        user_id for (user_id,) in db.session.query(Reservation.user_id).filter(
            Reservation.date >= start.date(),
            Reservation.date < end.date(),
            Reservation.status.in_(RESERVATION_VALID_STATUSES),
        ).distinct().all()
        if user_id is not None
    )
    user_ids.update(
        user_id for (user_id,) in db.session.query(BookRequest.user_id).filter(
            BookRequest.create_time >= start,
            BookRequest.create_time < end,
        ).distinct().all()
        if user_id is not None
    )
    count = 0
    if user_ids:
        count = User.query.filter(
            User.id.in_(user_ids),
            User.role.in_(('student', 'teacher')),
        ).count()
    return _base_result(
        'METRIC-04', period_type, start, end,
        value_decimal=Decimal(count),
    )


def _metric_05(period_type, start, end):
    rows = db.session.query(
        Book.id.label('book_id'),
        Book.title,
        Book.author,
        Book.category_id,
        Category.name.label('category_name'),
        db.func.count(Borrow.id).label('borrow_count'),
    ).join(
        Borrow, Borrow.book_id == Book.id
    ).outerjoin(
        Category, Category.id == Book.category_id
    ).filter(
        Borrow.borrow_time >= start,
        Borrow.borrow_time < end,
        Borrow.status.in_(BORROW_VALID_STATUSES),
    ).group_by(
        Book.id,
        Book.title,
        Book.author,
        Book.category_id,
        Category.name,
    ).order_by(
        db.func.count(Borrow.id).desc(),
        Book.id.asc(),
    ).all()

    results = []
    previous_count = None
    dense_rank = 0
    for row in rows:
        count = int(row.borrow_count or 0)
        if count != previous_count:
            dense_rank += 1
            previous_count = count
        results.append(_base_result(
            'METRIC-05', period_type, start, end,
            dimension_type='BOOK',
            dimension_key=str(row.book_id),
            value_decimal=Decimal(count),
            rank=dense_rank,
            dimension_payload={
                'book_id': row.book_id,
                'title': row.title,
                'author': row.author,
                'category_id': row.category_id,
                'category_name': row.category_name,
            },
        ))
    return results


def _reservation_minutes_by_date(start, end):
    minutes = defaultdict(int)
    reservations = Reservation.query.filter(
        Reservation.date >= start.date(),
        Reservation.date < end.date(),
        Reservation.status.in_(RESERVATION_VALID_STATUSES),
    ).all()
    for reservation in reservations:
        service_start = datetime.combine(reservation.date, SERVICE_START)
        service_end = datetime.combine(reservation.date, SERVICE_END)
        reservation_start = datetime.combine(reservation.date, reservation.start_time)
        reservation_end = datetime.combine(reservation.date, reservation.end_time)
        clipped_start = max(service_start, reservation_start)
        clipped_end = min(service_end, reservation_end)
        if clipped_end > clipped_start:
            minutes[reservation.date] += int((clipped_end - clipped_start).total_seconds() // 60)
    return minutes


def _current_capacity(capacity_date):
    return db.session.query(SeatCapacitySnapshot).join(
        MetricJobRun, MetricJobRun.id == SeatCapacitySnapshot.job_run_id
    ).filter(
        SeatCapacitySnapshot.capacity_date == capacity_date,
        MetricJobRun.status == 'SUCCESS',
        MetricJobRun.snapshot_row_count == 1,
    ).order_by(
        MetricJobRun.finish_time.desc(),
        MetricJobRun.id.desc(),
        SeatCapacitySnapshot.id.desc(),
    ).first()


def _period_dates(start, end):
    cursor = start.date()
    dates = []
    while cursor < end.date():
        dates.append(cursor)
        cursor += timedelta(days=1)
    return dates


def _metric_06(period_type, start, end):
    reservation_minutes = _reservation_minutes_by_date(start, end)
    dates = _period_dates(start, end)
    covered_dates = []
    unavailable_reasons = []
    denominator = 0
    numerator = 0
    for capacity_date in dates:
        capacity = _current_capacity(capacity_date)
        if capacity is None or capacity.quality_status != 'EXACT':
            unavailable_reasons.append(
                capacity.quality_reason if capacity is not None else 'CAPACITY_SNAPSHOT_MISSING'
            )
            continue
        covered_dates.append(capacity_date)
        denominator += int(capacity.capacity_minutes or 0)
        numerator += reservation_minutes.get(capacity_date, 0)

    total_days = len(dates)
    coverage = (
        _six_decimals(Decimal(len(covered_dates)) / Decimal(total_days))
        if total_days else Decimal(0)
    )
    if denominator <= 0:
        return _base_result(
            'METRIC-06', period_type, start, end,
            value_decimal=None,
            unit='RATIO',
            quality_status='UNAVAILABLE',
            quality_reason=(unavailable_reasons[0] if unavailable_reasons else 'ZERO_CAPACITY'),
            coverage_ratio=coverage,
        )

    ratio = _six_decimals(Decimal(numerator) / Decimal(denominator))
    if len(covered_dates) == total_days:
        quality_status = 'EXACT'
        quality_reason = None
    else:
        quality_status = 'BEST_EFFORT'
        quality_reason = f'CAPACITY_COVERAGE_{len(covered_dates)}_OF_{total_days}_DAYS'
    return _base_result(
        'METRIC-06', period_type, start, end,
        value_decimal=ratio,
        unit='RATIO',
        quality_status=quality_status,
        quality_reason=quality_reason,
        coverage_ratio=coverage,
        dimension_payload={
            'reservation_minutes': numerator,
            'capacity_minutes': denominator,
            'covered_days': len(covered_dates),
            'total_days': total_days,
        },
    )


def compute_metrics(period_type, period_start, period_end, now_provider=datetime.now):
    """Compute one canonical period and return only MetricResult objects."""
    normalized = (period_type or '').upper()
    if normalized not in PERIOD_TYPES:
        raise ValueError('period_type must be DAY or MONTH')
    if not isinstance(period_start, datetime) or not isinstance(period_end, datetime):
        raise ValueError('period boundaries must be datetime values')
    if period_start >= period_end:
        raise ValueError('period_start must be before period_end')

    generated_time = now_provider().replace(microsecond=0)
    results = [
        _metric_01(normalized, period_start, period_end, generated_time),
        _metric_02(normalized, period_start, period_end),
        _metric_03(normalized, period_start, period_end),
        _metric_04(normalized, period_start, period_end),
    ]
    results.extend(_metric_05(normalized, period_start, period_end))
    results.append(_metric_06(normalized, period_start, period_end))
    return results
