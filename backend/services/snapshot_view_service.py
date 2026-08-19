# -*- coding: utf-8 -*-
"""Compatibility views that expose immutable snapshots to existing APIs."""

from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import inspect as sqlalchemy_inspect

from extensions import db
from models.metric_job_run import MetricJobRun
from models.metric_snapshot import MetricSnapshot
from services.metric_contract import CALCULATION_VERSION, canonical_period
from services.metric_pipeline_service import (
    get_current_snapshot_set,
    get_latest_snapshot_set,
    snapshot_payload,
)


REQUIRED_SNAPSHOT_TABLES = ('metric_snapshot', 'metric_job_run')


def snapshot_schema_available():
    """Return whether the current database can serve V2 metric snapshots."""
    inspector = sqlalchemy_inspect(db.engine)
    return all(inspector.has_table(table_name) for table_name in REQUIRED_SNAPSHOT_TABLES)


def _single(snapshots, metric_code):
    return next(
        (snapshot for snapshot in snapshots if snapshot.metric_code == metric_code),
        None,
    )


def _number(snapshot, default=0):
    if snapshot is None or snapshot.metric_value is None:
        return default
    return int(snapshot.metric_value)


def _metadata(current):
    job = current.job_run
    return {
        'source': 'snapshot',
        'calculation_version': job.calculation_version,
        'generated_time': job.finish_time.isoformat() if job.finish_time else None,
        'job_run_id': job.id,
        'period_type': job.period_type,
    }


def dashboard_snapshot_stats():
    if not snapshot_schema_available():
        return None
    current = get_latest_snapshot_set('DAY')
    if current is None:
        return None
    snapshots = current.snapshots
    utilization = _single(snapshots, 'METRIC-06')
    data = {
        'total_stock': _number(_single(snapshots, 'METRIC-01')),
        'total_borrowed': _number(_single(snapshots, 'METRIC-02')),
        'total_overdue': _number(_single(snapshots, 'METRIC-03')),
        'active_user_count': _number(_single(snapshots, 'METRIC-04')),
        'seat_utilization_rate': (
            float(utilization.metric_value * Decimal(100))
            if utilization is not None and utilization.metric_value is not None else None
        ),
        'period_start': snapshots[0].period_start.isoformat(),
        'period_end': snapshots[0].period_end.isoformat(),
        'quality': {
            snapshot.metric_code: {
                'status': snapshot.quality_status,
                'reason': snapshot.quality_reason,
                'coverage_ratio': (
                    float(snapshot.coverage_ratio)
                    if snapshot.coverage_ratio is not None else None
                ),
            }
            for snapshot in snapshots
            if snapshot.metric_code != 'METRIC-05'
        },
    }
    data.update(_metadata(current))
    return data


def latest_popular_books(limit=10):
    if not snapshot_schema_available():
        return None
    current = get_latest_snapshot_set('MONTH')
    if current is None:
        return None
    books = []
    for snapshot in current.snapshots:
        if snapshot.metric_code != 'METRIC-05':
            continue
        payload = snapshot_payload(snapshot) or {}
        books.append({
            'book_id': payload.get('book_id'),
            'title': payload.get('title') or '',
            'author': payload.get('author') or '',
            'borrow_count': int(snapshot.metric_value or 0),
            'rank': snapshot.rank_value,
        })
    books.sort(key=lambda item: (item['rank'] or 0, item['book_id'] or 0))
    return {'list': books[:limit], **_metadata(current)}


def latest_category_chart():
    if not snapshot_schema_available():
        return None
    current = get_latest_snapshot_set('MONTH')
    if current is None:
        return None
    counts = defaultdict(int)
    for snapshot in current.snapshots:
        if snapshot.metric_code != 'METRIC-05':
            continue
        payload = snapshot_payload(snapshot) or {}
        counts[payload.get('category_name') or '未分类'] += int(snapshot.metric_value or 0)
    chart = [
        {'name': name, 'value': value}
        for name, value in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    return {'chart': chart, **_metadata(current)}


def monthly_borrow_trend(limit=12):
    if not snapshot_schema_available():
        return None
    periods = db.session.query(
        MetricSnapshot.period_start,
        MetricSnapshot.period_end,
    ).join(
        MetricJobRun, MetricJobRun.id == MetricSnapshot.job_run_id
    ).filter(
        MetricSnapshot.metric_code == 'METRIC-02',
        MetricSnapshot.period_type == 'MONTH',
        MetricSnapshot.calculation_version == CALCULATION_VERSION,
        MetricJobRun.status == 'SUCCESS',
    ).distinct().order_by(MetricSnapshot.period_start.desc()).limit(limit).all()
    trend = []
    job_ids = []
    generated_times = []
    for period_start, period_end in reversed(periods):
        current = get_current_snapshot_set('MONTH', period_start, period_end)
        if current is None:
            continue
        metric = _single(current.snapshots, 'METRIC-02')
        if metric is None:
            continue
        trend.append({
            'month': period_start.strftime('%Y-%m'),
            'count': int(metric.metric_value or 0),
        })
        job_ids.append(current.job_run.id)
        if current.job_run.finish_time:
            generated_times.append(current.job_run.finish_time)
    if not trend:
        return None
    return {
        'trend': trend,
        'source': 'snapshot',
        'calculation_version': CALCULATION_VERSION,
        'generated_time': max(generated_times).isoformat() if generated_times else None,
        'job_run_ids': job_ids,
    }


def build_monthly_snapshot_report(month_text):
    try:
        month_date = datetime.strptime(month_text, '%Y-%m').date()
    except (TypeError, ValueError) as exc:
        raise ValueError('month 参数格式应为 YYYY-MM') from exc
    if not snapshot_schema_available():
        return None
    start, end = canonical_period('MONTH', month_date)
    current = get_current_snapshot_set('MONTH', start, end)
    if current is None:
        return None

    snapshots = current.snapshots
    metrics = {code: _single(snapshots, code) for code in (
        'METRIC-01', 'METRIC-02', 'METRIC-03', 'METRIC-04', 'METRIC-06'
    )}
    end_date = end.date() - timedelta(days=1)
    core_stats = {
        'borrow_count': _number(metrics['METRIC-02']),
        'active_user_count': _number(metrics['METRIC-04']),
        'overdue_count': _number(metrics['METRIC-03']),
        'total_collection_copies': _number(metrics['METRIC-01']),
        'reservation_count': None,
        'book_request_count': None,
    }

    popular_books = []
    category_counts = defaultdict(int)
    for snapshot in snapshots:
        if snapshot.metric_code != 'METRIC-05':
            continue
        payload = snapshot_payload(snapshot) or {}
        book_id = payload.get('book_id')
        count = int(snapshot.metric_value or 0)
        category_name = payload.get('category_name') or '未分类'
        popular_books.append({
            'book_id': book_id,
            'title': payload.get('title') or '',
            'author': payload.get('author') or '',
            'category': category_name,
            'borrow_count': count,
            'stock': None,
            'rank': snapshot.rank_value,
        })
        category_counts[category_name] += count
    popular_books.sort(key=lambda item: (item['rank'] or 0, item['book_id'] or 0))
    book_analysis = {
        'popular_books': popular_books[:10],
        'categories': [
            {'name': name, 'value': value}
            for name, value in sorted(
                category_counts.items(), key=lambda item: (-item[1], item[0])
            )
        ],
        'stock_risk_books': [],
    }

    utilization = metrics['METRIC-06']
    seat_analysis = {
        'popular_seats': [],
        'popular_rooms': [],
        'peak_hours': [],
        'feature_preference': {
            'with_power_count': None,
            'without_power_count': None,
            'with_power_ratio': None,
            'without_power_ratio': None,
        },
        'utilization': {
            'ratio': (
                float(utilization.metric_value)
                if utilization and utilization.metric_value is not None else None
            ),
            'percent': (
                float(utilization.metric_value * Decimal(100))
                if utilization and utilization.metric_value is not None else None
            ),
            'quality_status': utilization.quality_status if utilization else 'UNAVAILABLE',
            'quality_reason': utilization.quality_reason if utilization else 'SNAPSHOT_MISSING',
            'coverage_ratio': (
                float(utilization.coverage_ratio)
                if utilization and utilization.coverage_ratio is not None else None
            ),
            'details': snapshot_payload(utilization) if utilization else None,
        },
    }

    user_behavior = {
        'role_distribution': [],
        'active_user_count': _number(metrics['METRIC-04']),
        'renew_count': None,
        'book_request_count': None,
        'overdue_count': _number(metrics['METRIC-03']),
    }

    report = {
        'month': month_text,
        'range': {'start': start.date().isoformat(), 'end': end_date.isoformat()},
        'data_source': 'snapshot',
        'source': 'snapshot',
        'supplemental_source': 'unavailable_in_metrics_v1',
        'is_mock': False,
        'core_stats': core_stats,
        'book_analysis': book_analysis,
        'seat_analysis': seat_analysis,
        'user_behavior': user_behavior,
        'quality': {
            code: {
                'status': snapshot.quality_status,
                'reason': snapshot.quality_reason,
                'coverage_ratio': (
                    float(snapshot.coverage_ratio)
                    if snapshot.coverage_ratio is not None else None
                ),
            }
            for code, snapshot in metrics.items() if snapshot is not None
        },
    }
    report.update(_metadata(current))
    return report
