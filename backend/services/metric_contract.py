# -*- coding: utf-8 -*-
"""Shared V2 metric result contract and period helpers."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional


CALCULATION_VERSION = 'metrics-v1.0.0'
BUSINESS_TIMEZONE = 'Asia/Shanghai'
METRIC_CODES = frozenset(f'METRIC-{number:02d}' for number in range(1, 7))
QUALITY_STATUSES = frozenset({'EXACT', 'BEST_EFFORT', 'UNAVAILABLE'})
PERIOD_TYPES = frozenset({'DAY', 'MONTH'})


@dataclass(frozen=True)
class MetricResult:
    metric_code: str
    period_type: str
    period_start: datetime
    period_end: datetime
    temporal_type: str
    as_of_time: Optional[datetime]
    scope_type: str
    scope_key: str
    dimension_type: str
    dimension_key: str
    value_decimal: Optional[Decimal]
    unit: str
    rank: Optional[int]
    dimension_payload: Optional[Dict[str, Any]]
    quality_status: str
    quality_reason: Optional[str]
    coverage_ratio: Optional[Decimal]

    @property
    def identity(self):
        return (
            self.metric_code,
            self.period_type,
            self.period_start,
            self.period_end,
            self.scope_type,
            self.scope_key,
            self.dimension_type,
            self.dimension_key,
        )


def canonical_period(period_type, value):
    """Return the canonical half-open [S, E) DAY or MONTH period."""
    normalized = (period_type or '').upper()
    if normalized not in PERIOD_TYPES:
        raise ValueError('period_type must be DAY or MONTH')

    if isinstance(value, datetime):
        value = value.date()
    if not isinstance(value, date):
        raise ValueError('period value must be a date or datetime')

    if normalized == 'DAY':
        start = datetime.combine(value, time.min)
        return start, start + timedelta(days=1)

    start = datetime(value.year, value.month, 1)
    if value.month == 12:
        end = datetime(value.year + 1, 1, 1)
    else:
        end = datetime(value.year, value.month + 1, 1)
    return start, end


def enumerate_periods(period_type, first_value, last_value):
    """Return inclusive DAY/MONTH periods from first_value through last_value."""
    first_start, _ = canonical_period(period_type, first_value)
    last_start, _ = canonical_period(period_type, last_value)
    if last_start < first_start:
        raise ValueError('end period must not be before start period')

    periods = []
    cursor = first_start
    while cursor <= last_start:
        start, end = canonical_period(period_type, cursor)
        periods.append((start, end))
        cursor = end
    return periods
