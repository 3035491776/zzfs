# -*- coding: utf-8 -*-
"""Capture immutable daily seat-capacity facts."""

from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta
import hashlib
import json
import uuid
from zoneinfo import ZoneInfo

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import MetricJobRun, Seat, SeatCapacitySnapshot


BUSINESS_TIMEZONE = 'Asia/Shanghai'
CAPACITY_EXACT_START_DATE = date(2026, 8, 19)
SERVICE_START = time(8, 0)
SERVICE_END = time(22, 0)
SERVICE_MINUTES_PER_SEAT = 14 * 60
CALCULATION_VERSION = 'metrics-v1.0.0'
JOB_NAME = 'seat_capacity_capture'
ENGINE = 'PYTHON'
VALID_JOB_TYPES = frozenset({'MANUAL', 'SCHEDULED'})
VALID_SEAT_STATUSES = frozenset({'available', 'occupied', 'maintenance'})
SERVICEABLE_SEAT_STATUSES = frozenset({'available', 'occupied'})
STALE_JOB_MINUTES = 15


class SeatCapacityError(RuntimeError):
    """Base exception for controlled capacity-capture failures."""


class DatabaseWriteNotAllowed(SeatCapacityError):
    """Raised before writes when the actual database is not allow-listed."""


class CaptureRequestError(SeatCapacityError):
    """Raised when a capture request is invalid or unsafe."""


class CaptureExecutionError(SeatCapacityError):
    """Raised after a JobRun has been retained as FAILED."""

    def __init__(self, job_run_id, error_type):
        super().__init__(f'Capacity capture job {job_run_id} failed ({error_type}).')
        self.job_run_id = job_run_id
        self.error_type = error_type


@dataclass(frozen=True)
class CapacityFact:
    """Normalized payload published to seat_capacity_snapshot."""

    capacity_date: date
    service_start: time
    service_end: time
    total_seat_count: int
    serviceable_seat_count: int
    capacity_minutes: int
    quality_status: str
    quality_reason: str
    captured_time: datetime


@dataclass(frozen=True)
class CaptureOutcome:
    """Stable result returned by the service and CLI."""

    job_run_id: int
    run_key: str
    status: str
    reused: bool
    snapshot_id: int | None
    capacity_date: str | None
    total_seat_count: int | None
    serviceable_seat_count: int | None
    service_start: str | None
    service_end: str | None
    capacity_minutes: int | None
    quality_status: str | None
    quality_reason: str | None

    def to_dict(self):
        return asdict(self)


def business_now():
    """Return a naive datetime whose business interpretation is Asia/Shanghai."""
    return datetime.now(ZoneInfo(BUSINESS_TIMEZONE)).replace(tzinfo=None)


def assert_write_database_allowed(allowed_databases):
    """Verify the actual SQLAlchemy connection target before any write."""
    database_name = db.engine.url.database
    allowed = {name for name in (allowed_databases or ()) if name}
    if not database_name or database_name not in allowed:
        raise DatabaseWriteNotAllowed(
            'Seat capacity capture is disabled for the current database.'
        )
    return database_name


def collect_capacity_fact(target_date, request_time, now_provider=business_now):
    """Read current Seat facts or publish an explicit historical gap."""
    today = request_time.date()
    if target_date < CAPACITY_EXACT_START_DATE:
        return _unavailable_fact(
            target_date,
            now_provider(),
            'BEFORE_TRACKING_START: Capacity history was not tracked before '
            'Phase 1.4 activation.',
        )
    if target_date < today:
        return _unavailable_fact(
            target_date,
            now_provider(),
            'HISTORICAL_EXACT_MISSING: Same-day capacity was not captured for '
            'this date.',
        )

    read_started = now_provider()
    if read_started.date() != target_date:
        raise CaptureRequestError(
            'Business date changed before Seat facts were read; EXACT capture refused.'
        )
    status_counts = dict(
        db.session.query(Seat.status, func.count(Seat.id))
        .group_by(Seat.status)
        .all()
    )
    read_finished = now_provider()
    if read_finished.date() != target_date:
        raise CaptureRequestError(
            'Business date changed while Seat facts were read; EXACT capture refused.'
        )
    unknown_statuses = set(status_counts) - VALID_SEAT_STATUSES
    if unknown_statuses:
        raise CaptureRequestError(
            'Seat data contains unsupported status values; EXACT capture refused.'
        )

    total_count = sum(status_counts.values())
    serviceable_count = sum(
        status_counts.get(status, 0) for status in SERVICEABLE_SEAT_STATUSES
    )
    return CapacityFact(
        capacity_date=target_date,
        service_start=SERVICE_START,
        service_end=SERVICE_END,
        total_seat_count=total_count,
        serviceable_seat_count=serviceable_count,
        capacity_minutes=serviceable_count * SERVICE_MINUTES_PER_SEAT,
        quality_status='EXACT',
        quality_reason='CURRENT_DAY_SEAT_FACTS: Captured from current Seat records.',
        captured_time=read_finished,
    )


def capture_seat_capacity(
    target_date,
    request_identity,
    allowed_databases,
    *,
    job_type='MANUAL',
    retry_of_job_run_id=None,
    requested_by_user_id=None,
    captured_time=None,
    now_provider=None,
):
    """Create one idempotent JobRun and publish one daily capacity fact."""
    assert_write_database_allowed(allowed_databases)
    if captured_time is not None and now_provider is not None:
        raise CaptureRequestError('Use captured_time or now_provider, not both.')
    clock = now_provider or (
        (lambda: captured_time) if captured_time else business_now
    )
    request_time = clock()
    _validate_capture_request(target_date, request_identity, job_type, request_time)

    idempotency_key = _build_idempotency_key(
        target_date,
        request_identity,
        job_type,
        retry_of_job_run_id,
    )
    existing = MetricJobRun.query.filter_by(
        idempotency_key=idempotency_key
    ).first()
    if existing:
        return _reuse_existing(existing, request_time)

    prior_exact = _find_successful_exact(target_date)
    if target_date < request_time.date() and prior_exact:
        raise CaptureRequestError(
            'A historical EXACT snapshot already exists; a newer UNAVAILABLE '
            'version is not allowed.'
        )

    retry_of = _validate_retry_request(retry_of_job_run_id, target_date)
    if target_date == request_time.date() and prior_exact and retry_of is None:
        raise CaptureRequestError(
            f'Active rerun requires retry_of_job_run_id={prior_exact.id}.'
        )

    job_run, reused = _create_pending_job(
        target_date=target_date,
        idempotency_key=idempotency_key,
        job_type=job_type,
        retry_of_job_run_id=retry_of.id if retry_of else None,
        requested_by_user_id=requested_by_user_id,
        captured_time=request_time,
    )
    if reused:
        return _reuse_existing(job_run, request_time)

    try:
        job_run.status = 'RUNNING'
        job_run.start_time = request_time
        db.session.commit()

        fact = collect_capacity_fact(target_date, request_time, clock)
        return _publish_capacity(job_run.id, fact)
    except Exception as exc:
        db.session.rollback()
        _mark_failed(job_run.id, exc)
        raise CaptureExecutionError(job_run.id, type(exc).__name__) from exc


def _validate_capture_request(target_date, request_identity, job_type, captured_time):
    if not isinstance(target_date, date) or isinstance(target_date, datetime):
        raise CaptureRequestError('target_date must be a date.')
    if target_date > captured_time.date():
        raise CaptureRequestError('Future capacity dates cannot be captured.')
    if not request_identity or not request_identity.strip():
        raise CaptureRequestError('request_identity is required.')
    if job_type not in VALID_JOB_TYPES:
        raise CaptureRequestError('job_type must be MANUAL or SCHEDULED.')


def _validate_retry_request(retry_of_job_run_id, target_date):
    if retry_of_job_run_id is None:
        return None
    retry_of = db.session.get(MetricJobRun, retry_of_job_run_id)
    if retry_of is None:
        raise CaptureRequestError('retry_of_job_run_id does not exist.')
    if retry_of.job_name != JOB_NAME:
        raise CaptureRequestError('retry_of_job_run_id belongs to another job.')
    if retry_of.requested_start.date() != target_date:
        raise CaptureRequestError('A rerun must target the same capacity date.')
    if retry_of.status not in {'SUCCESS', 'FAILED'}:
        raise CaptureRequestError('Only a terminal JobRun can be rerun.')
    return retry_of


def _reuse_existing(job_run, request_time):
    if job_run.status == 'SUCCESS':
        return _build_outcome(job_run, reused=True)
    if job_run.status == 'FAILED':
        raise CaptureRequestError(
            f'Existing request failed in JobRun {job_run.id}; use a new request '
            'identity with retry_of_job_run_id.'
        )

    anchor_time = job_run.start_time or job_run.create_time
    if anchor_time and request_time - anchor_time >= timedelta(
        minutes=STALE_JOB_MINUTES
    ):
        locked = (
            MetricJobRun.query.filter_by(id=job_run.id)
            .populate_existing()
            .with_for_update()
            .one()
        )
        if locked.status == 'SUCCESS':
            locked_id = locked.id
            db.session.commit()
            return _build_outcome(
                db.session.get(MetricJobRun, locked_id), reused=True
            )
        if locked.status == 'FAILED':
            locked_id = locked.id
            db.session.rollback()
            raise CaptureRequestError(
                f'Existing request failed in JobRun {locked_id}; use a new '
                'request identity with retry_of_job_run_id.'
            )
        anchor_time = locked.start_time or locked.create_time
        if locked.status in {'PENDING', 'RUNNING'} and (
            anchor_time
            and request_time - anchor_time >= timedelta(minutes=STALE_JOB_MINUTES)
        ):
            locked.status = 'FAILED'
            locked.finish_time = request_time
            locked.snapshot_row_count = 0
            locked.error_type = 'StaleJobRun'
            locked.error_summary = (
                'Seat capacity capture exceeded the execution timeout without '
                'publishing a snapshot.'
            )
            db.session.commit()
            raise CaptureRequestError(
                f'Stale JobRun {locked.id} was marked FAILED; retry with a new '
                'request identity and retry_of_job_run_id.'
            )
        db.session.rollback()

    current_status = job_run.status
    db.session.rollback()
    raise CaptureRequestError(
        f'JobRun {job_run.id} is still {current_status}; no duplicate execution '
        'was started.'
    )


def _build_idempotency_key(
    target_date, request_identity, job_type, retry_of_job_run_id
):
    payload = {
        'job_name': JOB_NAME,
        'capacity_date': target_date.isoformat(),
        'calculation_version': CALCULATION_VERSION,
        'job_type': job_type,
        'request_identity': request_identity.strip(),
        'retry_of_job_run_id': retry_of_job_run_id,
    }
    encoded = json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def _create_pending_job(
    *,
    target_date,
    idempotency_key,
    job_type,
    retry_of_job_run_id,
    requested_by_user_id,
    captured_time,
):
    period_start = datetime.combine(target_date, time.min)
    job_run = MetricJobRun(
        run_key=str(uuid.uuid4()),
        idempotency_key=idempotency_key,
        job_name=JOB_NAME,
        job_type=job_type,
        period_type='DAY',
        requested_start=period_start,
        requested_end=period_start + timedelta(days=1),
        engine=ENGINE,
        calculation_version=CALCULATION_VERSION,
        business_timezone=BUSINESS_TIMEZONE,
        status='PENDING',
        requested_by_user_id=requested_by_user_id,
        retry_of_job_run_id=retry_of_job_run_id,
        create_time=captured_time,
    )
    db.session.add(job_run)
    try:
        db.session.commit()
        return job_run, False
    except IntegrityError:
        db.session.rollback()
        existing = MetricJobRun.query.filter_by(
            idempotency_key=idempotency_key
        ).first()
        if existing is None:
            raise
        return existing, True


def _publish_capacity(job_run_id, fact):
    job_run = (
        MetricJobRun.query.filter_by(id=job_run_id)
        .with_for_update()
        .one()
    )
    if job_run.status != 'RUNNING':
        raise CaptureRequestError('JobRun is not in RUNNING state.')

    # The indexed date range is locked so an EXACT fact cannot be followed by a
    # concurrently published UNAVAILABLE version for the same business date.
    published_snapshots = (
        SeatCapacitySnapshot.query.filter_by(capacity_date=fact.capacity_date)
        .with_for_update()
        .all()
    )
    if fact.quality_status == 'UNAVAILABLE':
        published_job_ids = [snapshot.job_run_id for snapshot in published_snapshots]
        has_successful_exact = False
        if published_job_ids:
            has_successful_exact = (
                db.session.query(SeatCapacitySnapshot.id)
                .join(
                    MetricJobRun,
                    MetricJobRun.id == SeatCapacitySnapshot.job_run_id,
                )
                .filter(
                    SeatCapacitySnapshot.id.in_(
                        [snapshot.id for snapshot in published_snapshots]
                    ),
                    SeatCapacitySnapshot.quality_status == 'EXACT',
                    MetricJobRun.status == 'SUCCESS',
                )
                .first()
                is not None
            )
        if has_successful_exact:
            raise CaptureRequestError(
                'A historical EXACT snapshot was published concurrently; '
                'UNAVAILABLE publication refused.'
            )

    snapshot = SeatCapacitySnapshot(
        capacity_date=fact.capacity_date,
        service_start=fact.service_start,
        service_end=fact.service_end,
        total_seat_count=fact.total_seat_count,
        serviceable_seat_count=fact.serviceable_seat_count,
        capacity_minutes=fact.capacity_minutes,
        quality_status=fact.quality_status,
        quality_reason=fact.quality_reason,
        job_run_id=job_run.id,
        captured_time=fact.captured_time,
    )
    db.session.add(snapshot)
    db.session.flush()

    job_run.status = 'SUCCESS'
    job_run.finish_time = fact.captured_time
    job_run.input_row_count = fact.total_seat_count
    job_run.snapshot_row_count = 1
    job_run.result_checksum = _result_checksum(fact)
    job_run.error_type = None
    job_run.error_summary = None
    outcome = CaptureOutcome(
        job_run_id=job_run.id,
        run_key=job_run.run_key,
        status='SUCCESS',
        reused=False,
        snapshot_id=snapshot.id,
        capacity_date=snapshot.capacity_date.isoformat(),
        total_seat_count=snapshot.total_seat_count,
        serviceable_seat_count=snapshot.serviceable_seat_count,
        service_start=snapshot.service_start.isoformat(),
        service_end=snapshot.service_end.isoformat(),
        capacity_minutes=snapshot.capacity_minutes,
        quality_status=snapshot.quality_status,
        quality_reason=snapshot.quality_reason,
    )
    db.session.commit()
    return outcome


def _mark_failed(job_run_id, exc):
    job_run = db.session.get(MetricJobRun, job_run_id)
    if job_run is None or job_run.status == 'SUCCESS':
        return
    job_run.status = 'FAILED'
    job_run.finish_time = business_now()
    job_run.input_row_count = None
    job_run.snapshot_row_count = 0
    job_run.result_checksum = None
    job_run.error_type = type(exc).__name__[:100]
    job_run.error_summary = (
        'Seat capacity capture failed without publishing a snapshot.'
    )
    db.session.commit()


def _find_successful_exact(target_date):
    return (
        MetricJobRun.query.join(
            SeatCapacitySnapshot,
            SeatCapacitySnapshot.job_run_id == MetricJobRun.id,
        )
        .filter(
            MetricJobRun.job_name == JOB_NAME,
            MetricJobRun.status == 'SUCCESS',
            SeatCapacitySnapshot.capacity_date == target_date,
            SeatCapacitySnapshot.quality_status == 'EXACT',
        )
        .order_by(MetricJobRun.id.desc())
        .first()
    )


def _unavailable_fact(target_date, captured_time, reason):
    return CapacityFact(
        capacity_date=target_date,
        service_start=SERVICE_START,
        service_end=SERVICE_END,
        total_seat_count=0,
        serviceable_seat_count=0,
        capacity_minutes=0,
        quality_status='UNAVAILABLE',
        quality_reason=reason,
        captured_time=captured_time,
    )


def _result_checksum(fact):
    payload = {
        'capacity_date': fact.capacity_date.isoformat(),
        'service_start': fact.service_start.isoformat(),
        'service_end': fact.service_end.isoformat(),
        'total_seat_count': fact.total_seat_count,
        'serviceable_seat_count': fact.serviceable_seat_count,
        'capacity_minutes': fact.capacity_minutes,
        'quality_status': fact.quality_status,
        'quality_reason': fact.quality_reason,
    }
    encoded = json.dumps(
        payload, ensure_ascii=True, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def _build_outcome(job_run, reused):
    snapshot = SeatCapacitySnapshot.query.filter_by(job_run_id=job_run.id).first()
    return CaptureOutcome(
        job_run_id=job_run.id,
        run_key=job_run.run_key,
        status=job_run.status,
        reused=reused,
        snapshot_id=snapshot.id if snapshot else None,
        capacity_date=snapshot.capacity_date.isoformat() if snapshot else None,
        total_seat_count=snapshot.total_seat_count if snapshot else None,
        serviceable_seat_count=(
            snapshot.serviceable_seat_count if snapshot else None
        ),
        service_start=snapshot.service_start.isoformat() if snapshot else None,
        service_end=snapshot.service_end.isoformat() if snapshot else None,
        capacity_minutes=snapshot.capacity_minutes if snapshot else None,
        quality_status=snapshot.quality_status if snapshot else None,
        quality_reason=snapshot.quality_reason if snapshot else None,
    )
