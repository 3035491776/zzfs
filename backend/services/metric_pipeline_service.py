# -*- coding: utf-8 -*-
"""Validation, immutable publication, job execution and current snapshot queries."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from extensions import db
from models.metric_job_run import MetricJobRun
from models.metric_snapshot import MetricSnapshot
from services.metric_contract import (
    BUSINESS_TIMEZONE,
    CALCULATION_VERSION,
    METRIC_CODES,
    PERIOD_TYPES,
    QUALITY_STATUSES,
    MetricResult,
    canonical_period,
)
from services.metrics_aggregator import compute_metrics


JOB_NAME = 'metric_aggregation'
ENGINE = 'PYTHON'


class MetricValidationError(ValueError):
    pass


class MetricJobRequestError(ValueError):
    pass


class MetricJobExecutionError(RuntimeError):
    def __init__(self, message, job_run_id=None):
        super().__init__(message)
        self.job_run_id = job_run_id


class DatabaseWriteNotAllowed(MetricJobRequestError):
    pass


@dataclass(frozen=True)
class MetricJobOutcome:
    job_run_id: int
    run_key: str
    status: str
    snapshot_row_count: int
    result_checksum: str
    reused: bool = False


@dataclass(frozen=True)
class CurrentSnapshotSet:
    job_run: MetricJobRun
    snapshots: tuple


def _decimal_text(value):
    if value is None:
        return None
    return format(value.normalize(), 'f') if value != 0 else '0'


def _canonical_result(result):
    return {
        'metric_code': result.metric_code,
        'period_type': result.period_type,
        'period_start': result.period_start.isoformat(timespec='seconds'),
        'period_end': result.period_end.isoformat(timespec='seconds'),
        'temporal_type': result.temporal_type,
        'as_of_time': (
            result.as_of_time.isoformat(timespec='seconds')
            if result.as_of_time else None
        ),
        'scope_type': result.scope_type,
        'scope_key': result.scope_key,
        'dimension_type': result.dimension_type,
        'dimension_key': result.dimension_key,
        'value_decimal': _decimal_text(result.value_decimal),
        'unit': result.unit,
        'rank': result.rank,
        'dimension_payload': result.dimension_payload,
        'quality_status': result.quality_status,
        'quality_reason': result.quality_reason,
        'coverage_ratio': _decimal_text(result.coverage_ratio),
    }


def calculate_result_checksum(results):
    normalized = sorted(
        (_canonical_result(result) for result in results),
        key=lambda item: (
            item['period_start'], item['period_end'], item['metric_code'],
            item['scope_type'], item['scope_key'], item['dimension_type'],
            item['dimension_key'],
        ),
    )
    payload = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def _checksum_for_snapshots(snapshots):
    results = [
        MetricResult(
            metric_code=snapshot.metric_code,
            period_type=snapshot.period_type,
            period_start=snapshot.period_start,
            period_end=snapshot.period_end,
            temporal_type=snapshot.temporal_type,
            as_of_time=snapshot.as_of_time,
            scope_type=snapshot.scope_type,
            scope_key=snapshot.scope_key,
            dimension_type=snapshot.dimension_type,
            dimension_key=snapshot.dimension_key,
            value_decimal=snapshot.metric_value,
            unit=snapshot.unit,
            rank=snapshot.rank_value,
            dimension_payload=(
                json.loads(snapshot.dimension_payload)
                if snapshot.dimension_payload else None
            ),
            quality_status=snapshot.quality_status,
            quality_reason=snapshot.quality_reason,
            coverage_ratio=snapshot.coverage_ratio,
        )
        for snapshot in snapshots
    ]
    return calculate_result_checksum(results)


def _validate_decimal(value, name, allow_none=False):
    if value is None and allow_none:
        return
    if not isinstance(value, Decimal):
        raise MetricValidationError(f'{name} must be Decimal')
    if not value.is_finite():
        raise MetricValidationError(f'{name} must be finite')
    sign, digits, exponent = value.as_tuple()
    del sign
    fractional_digits = max(-exponent, 0)
    integer_digits = max(len(digits) + exponent, 0)
    if fractional_digits > 6 or integer_digits > 14:
        raise MetricValidationError(f'{name} exceeds supported precision')


def validate_metric_results(results, expected_periods, calculation_version):
    if calculation_version != CALCULATION_VERSION:
        raise MetricValidationError('calculation_version does not match sealed bundle')
    if not results:
        raise MetricValidationError('metric result set must not be empty')

    expected = set(expected_periods)
    identities = set()
    codes_by_period = {period: set() for period in expected}
    metric_05_dimensions = {period: set() for period in expected}
    singleton_counts = {period: {} for period in expected}
    singleton_codes = {'METRIC-01', 'METRIC-02', 'METRIC-03', 'METRIC-04', 'METRIC-06'}

    for result in results:
        if not isinstance(result, MetricResult):
            raise MetricValidationError('aggregator returned a non-MetricResult value')
        if result.metric_code not in METRIC_CODES:
            raise MetricValidationError(f'unsupported metric code: {result.metric_code}')
        if result.period_type not in PERIOD_TYPES:
            raise MetricValidationError('invalid period type')
        period = (result.period_start, result.period_end)
        if period not in expected:
            raise MetricValidationError('result period differs from requested periods')
        if result.identity in identities:
            raise MetricValidationError('duplicate metric snapshot identity')
        identities.add(result.identity)
        codes_by_period[period].add(result.metric_code)
        if result.metric_code in singleton_codes:
            if (
                result.scope_type != 'ALL' or result.scope_key != 'ALL'
                or result.dimension_type != 'ALL' or result.dimension_key != 'ALL'
            ):
                raise MetricValidationError(
                    f'{result.metric_code} must use the singleton ALL scope and dimension'
                )
            singleton_counts[period][result.metric_code] = (
                singleton_counts[period].get(result.metric_code, 0) + 1
            )

        if result.temporal_type not in ('POINT', 'INTERVAL'):
            raise MetricValidationError('invalid temporal_type')
        if result.quality_status not in QUALITY_STATUSES:
            raise MetricValidationError('invalid quality_status')
        if result.quality_status != 'EXACT' and not result.quality_reason:
            raise MetricValidationError('non-EXACT result requires quality_reason')
        _validate_decimal(result.value_decimal, 'value_decimal', allow_none=True)
        if result.value_decimal is None and result.metric_code != 'METRIC-06':
            raise MetricValidationError('only unavailable METRIC-06 may have a null value')
        if result.coverage_ratio is not None:
            _validate_decimal(result.coverage_ratio, 'coverage_ratio')
            if result.coverage_ratio < 0 or result.coverage_ratio > 1:
                raise MetricValidationError('coverage_ratio must be between 0 and 1')

        if result.metric_code == 'METRIC-05':
            if result.dimension_type != 'BOOK' or not result.dimension_key:
                raise MetricValidationError('METRIC-05 requires BOOK dimension')
            if result.rank is None or result.rank < 1:
                raise MetricValidationError('METRIC-05 rank must be positive')
            if result.dimension_key in metric_05_dimensions[period]:
                raise MetricValidationError('duplicate METRIC-05 book dimension')
            metric_05_dimensions[period].add(result.dimension_key)
            required_payload = {'book_id', 'title', 'author', 'category_id', 'category_name'}
            if not result.dimension_payload or not required_payload.issubset(
                result.dimension_payload
            ):
                raise MetricValidationError('METRIC-05 payload is incomplete')
        elif result.rank is not None:
            raise MetricValidationError('rank is only valid for METRIC-05')

        if result.metric_code == 'METRIC-06' and result.value_decimal is not None:
            if result.value_decimal < 0 or result.value_decimal > 1:
                raise MetricValidationError('METRIC-06 ratio must be between 0 and 1')
        if result.metric_code == 'METRIC-06' and result.coverage_ratio is None:
            raise MetricValidationError('METRIC-06 requires coverage_ratio')
        if (
            result.metric_code == 'METRIC-06'
            and result.value_decimal is None
            and result.quality_status != 'UNAVAILABLE'
        ):
            raise MetricValidationError('null METRIC-06 must be UNAVAILABLE')

    required_singletons = {'METRIC-01', 'METRIC-02', 'METRIC-03', 'METRIC-04', 'METRIC-06'}
    for period, codes in codes_by_period.items():
        if not required_singletons.issubset(codes):
            raise MetricValidationError(f'period {period} is missing required metrics')
        for metric_code in required_singletons:
            if singleton_counts[period].get(metric_code) != 1:
                raise MetricValidationError(
                    f'period {period} must contain exactly one {metric_code}'
                )


def _snapshot_from_result(job_run_id, result, generated_time, calculation_version):
    return MetricSnapshot(
        job_run_id=job_run_id,
        metric_code=result.metric_code,
        period_type=result.period_type,
        period_start=result.period_start,
        period_end=result.period_end,
        temporal_type=result.temporal_type,
        as_of_time=result.as_of_time,
        scope_type=result.scope_type,
        scope_key=result.scope_key,
        dimension_type=result.dimension_type,
        dimension_key=result.dimension_key,
        metric_value=result.value_decimal,
        unit=result.unit,
        rank_value=result.rank,
        dimension_payload=(
            json.dumps(result.dimension_payload, ensure_ascii=False, sort_keys=True)
            if result.dimension_payload is not None else None
        ),
        quality_status=result.quality_status,
        quality_reason=result.quality_reason,
        coverage_ratio=result.coverage_ratio,
        calculation_version=calculation_version,
        generated_time=generated_time,
    )


def _build_idempotency_key(period_type, periods, request_identity, job_type, retry_of):
    period_text = ','.join(
        f'{start.isoformat()}/{end.isoformat()}' for start, end in periods
    )
    raw = '|'.join([
        JOB_NAME,
        period_type,
        period_text,
        request_identity,
        job_type,
        str(retry_of or ''),
        CALCULATION_VERSION,
    ])
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _outcome(job_run, reused=False):
    return MetricJobOutcome(
        job_run_id=job_run.id,
        run_key=job_run.run_key,
        status=job_run.status,
        snapshot_row_count=int(job_run.snapshot_row_count or 0),
        result_checksum=job_run.result_checksum or '',
        reused=reused,
    )


def _existing_request(idempotency_key):
    return MetricJobRun.query.filter_by(idempotency_key=idempotency_key).first()


def _reuse_or_raise(job_run):
    if job_run.status == 'SUCCESS':
        snapshots = MetricSnapshot.query.filter_by(
            job_run_id=job_run.id
        ).populate_existing().all()
        actual = len(snapshots)
        checksum_matches = (
            bool(job_run.result_checksum)
            and _checksum_for_snapshots(snapshots) == job_run.result_checksum
        )
        if actual == job_run.snapshot_row_count and actual > 0 and checksum_matches:
            return _outcome(job_run, reused=True)
    raise MetricJobRequestError(
        f'Existing metric request is {job_run.status} (job_run_id={job_run.id}); '
        'use a new request identity for rerun.'
    )


def _mark_failed(job_run_id, exc, now_provider):
    db.session.rollback()
    job_run = db.session.get(MetricJobRun, job_run_id)
    if job_run is None:
        return
    job_run.status = 'FAILED'
    job_run.finish_time = now_provider()
    job_run.snapshot_row_count = 0
    job_run.error_type = type(exc).__name__[:100]
    job_run.error_summary = str(exc).replace('\n', ' ')[:1000]
    db.session.commit()


def run_metric_job(
    *,
    period_type,
    periods,
    request_identity,
    allowed_databases,
    job_type='MANUAL',
    requested_by_user_id=None,
    retry_of_job_run_id=None,
    compute_func=compute_metrics,
    now_provider=datetime.now,
):
    """Compute all periods, validate all results, then publish exactly once."""
    normalized_type = (period_type or '').upper()
    normalized_job_type = (job_type or '').upper()
    if normalized_type not in PERIOD_TYPES:
        raise MetricJobRequestError('period_type must be DAY or MONTH')
    if normalized_job_type not in ('MANUAL', 'BACKFILL', 'RETRY'):
        raise MetricJobRequestError('job_type must be MANUAL, BACKFILL or RETRY')
    periods = tuple(sorted(periods))
    if not periods:
        raise MetricJobRequestError('at least one period is required')
    for start, end in periods:
        if start.tzinfo is not None or end.tzinfo is not None:
            raise MetricJobRequestError('period boundaries must be naive Shanghai datetimes')
        canonical_start, canonical_end = canonical_period(normalized_type, start)
        if (start, end) != (canonical_start, canonical_end):
            raise MetricJobRequestError('period boundaries are not canonical half-open periods')
    if not request_identity or not request_identity.strip():
        raise MetricJobRequestError('request identity is required')

    actual_database = db.engine.url.database
    if actual_database not in tuple(allowed_databases or ()):
        raise DatabaseWriteNotAllowed(
            f'Metric writes are not allowed for database {actual_database!r}'
        )

    idempotency_key = _build_idempotency_key(
        normalized_type,
        periods,
        request_identity.strip(),
        normalized_job_type,
        retry_of_job_run_id,
    )
    existing = _existing_request(idempotency_key)
    if existing is not None:
        return _reuse_or_raise(existing)

    now = now_provider()
    job_run = MetricJobRun(
        run_key=str(uuid4()),
        idempotency_key=idempotency_key,
        job_name=JOB_NAME,
        job_type=normalized_job_type,
        period_type=normalized_type,
        requested_start=min(start for start, _ in periods),
        requested_end=max(end for _, end in periods),
        engine=ENGINE,
        calculation_version=CALCULATION_VERSION,
        business_timezone=BUSINESS_TIMEZONE,
        status='PENDING',
        requested_by_user_id=requested_by_user_id,
        retry_of_job_run_id=retry_of_job_run_id,
        create_time=now,
        snapshot_row_count=0,
    )
    db.session.add(job_run)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        existing = _existing_request(idempotency_key)
        if existing is not None:
            return _reuse_or_raise(existing)
        raise

    job_run_id = job_run.id
    try:
        job_run.status = 'RUNNING'
        job_run.start_time = now_provider()
        db.session.commit()
    except Exception as exc:
        try:
            _mark_failed(job_run_id, exc, now_provider)
        except Exception:
            db.session.rollback()
        raise MetricJobExecutionError('Metric job could not start', job_run_id) from exc

    try:
        results = []
        for start, end in periods:
            period_results = compute_func(normalized_type, start, end)
            results.extend(period_results)
        validate_metric_results(results, periods, CALCULATION_VERSION)
        checksum = calculate_result_checksum(results)
        generated_time = now_provider()

        db.session.rollback()
        locked_job = MetricJobRun.query.filter_by(id=job_run_id).populate_existing().with_for_update().one()
        if locked_job.status != 'RUNNING':
            raise MetricJobExecutionError('Metric job is no longer RUNNING', job_run_id)
        snapshots = [
            _snapshot_from_result(job_run_id, result, generated_time, CALCULATION_VERSION)
            for result in results
        ]
        db.session.add_all(snapshots)
        locked_job.status = 'SUCCESS'
        locked_job.finish_time = generated_time
        locked_job.snapshot_row_count = len(snapshots)
        locked_job.result_checksum = checksum
        locked_job.error_type = None
        locked_job.error_summary = None
        db.session.commit()
        return _outcome(locked_job)
    except Exception as exc:
        try:
            _mark_failed(job_run_id, exc, now_provider)
        except Exception:
            db.session.rollback()
        if isinstance(exc, MetricJobExecutionError):
            raise
        raise MetricJobExecutionError('Metric job failed', job_run_id) from exc


def _complete_job(job_run):
    if job_run.status != 'SUCCESS' or not job_run.snapshot_row_count:
        return False
    snapshots = MetricSnapshot.query.filter_by(
        job_run_id=job_run.id
    ).populate_existing().all()
    return (
        len(snapshots) == job_run.snapshot_row_count
        and bool(job_run.result_checksum)
        and _checksum_for_snapshots(snapshots) == job_run.result_checksum
    )


def get_current_snapshot_set(
    period_type,
    period_start,
    period_end,
    calculation_version=CALCULATION_VERSION,
):
    candidates = db.session.query(MetricJobRun).join(
        MetricSnapshot, MetricSnapshot.job_run_id == MetricJobRun.id
    ).filter(
        MetricSnapshot.period_type == period_type,
        MetricSnapshot.period_start == period_start,
        MetricSnapshot.period_end == period_end,
        MetricSnapshot.calculation_version == calculation_version,
        MetricJobRun.status == 'SUCCESS',
        MetricJobRun.calculation_version == calculation_version,
    ).distinct().order_by(
        MetricJobRun.finish_time.desc(),
        MetricJobRun.id.desc(),
    ).all()
    for job_run in candidates:
        if not _complete_job(job_run):
            continue
        snapshots = MetricSnapshot.query.filter_by(
            job_run_id=job_run.id,
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            calculation_version=calculation_version,
        ).order_by(
            MetricSnapshot.metric_code,
            MetricSnapshot.rank_value,
            MetricSnapshot.dimension_key,
        ).all()
        if snapshots:
            return CurrentSnapshotSet(job_run=job_run, snapshots=tuple(snapshots))
    return None


def get_latest_snapshot_set(period_type, calculation_version=CALCULATION_VERSION):
    latest = db.session.query(
        MetricSnapshot.period_start,
        MetricSnapshot.period_end,
    ).join(
        MetricJobRun, MetricJobRun.id == MetricSnapshot.job_run_id
    ).filter(
        MetricSnapshot.period_type == period_type,
        MetricSnapshot.calculation_version == calculation_version,
        MetricJobRun.status == 'SUCCESS',
        MetricJobRun.calculation_version == calculation_version,
    ).order_by(
        MetricSnapshot.period_end.desc(),
        MetricJobRun.finish_time.desc(),
        MetricJobRun.id.desc(),
    ).first()
    if latest is None:
        return None
    return get_current_snapshot_set(
        period_type,
        latest.period_start,
        latest.period_end,
        calculation_version,
    )


def snapshot_payload(snapshot):
    return json.loads(snapshot.dimension_payload) if snapshot.dimension_payload else None
