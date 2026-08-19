# -*- coding: utf-8 -*-
"""Repeatable MySQL integration tests for Phase 1.4 capacity capture."""

from datetime import date, datetime
import hashlib
import json
import threading
import time as time_module
import unittest
from unittest.mock import patch

from sqlalchemy.engine import URL
from sqlalchemy.exc import IntegrityError

from app import create_app
from config import Config
from extensions import db
from models import MetricJobRun, Reservation, Seat, SeatCapacitySnapshot
import services.seat_capacity_service as capacity_service
from services.seat_capacity_service import (
    CALCULATION_VERSION,
    CaptureExecutionError,
    CaptureRequestError,
    JOB_NAME,
    _build_idempotency_key,
    capture_seat_capacity,
)


TEST_DATABASE = 'smart_library_phase13_test_20260819_1'
FIXED_NOW = datetime(2026, 8, 19, 12, 0, 0)


class SeatCapacityIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        uri = URL.create(
            drivername='mysql+pymysql',
            username=Config.DB_USER,
            password=Config.DB_PASS,
            host=Config.DB_HOST,
            port=int(Config.DB_PORT),
            database=TEST_DATABASE,
            query={'charset': 'utf8mb4'},
        )
        cls.app = create_app(
            {
                'TESTING': True,
                'SQLALCHEMY_DATABASE_URI': uri,
                'CAPACITY_CAPTURE_ALLOWED_DATABASES': (TEST_DATABASE,),
            }
        )
        cls.context = cls.app.app_context()
        cls.context.push()
        if db.engine.url.database != TEST_DATABASE:
            raise AssertionError('Test suite refused a non-test database connection.')

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        cls.context.pop()

    def setUp(self):
        self._cleanup_phase14_rows()
        self.assertEqual(Seat.query.count(), 0)
        self.assertEqual(Reservation.query.count(), 0)

    def tearDown(self):
        db.session.rollback()
        self._cleanup_phase14_rows()

    def test_exact_capacity_and_business_tables_are_read_only(self):
        self._add_seats('available', 'occupied', 'maintenance')
        before = self._business_digest()

        outcome = self._capture(date(2026, 8, 19), 'exact-readonly')

        self.assertEqual(outcome.status, 'SUCCESS')
        self.assertEqual(outcome.total_seat_count, 3)
        self.assertEqual(outcome.serviceable_seat_count, 2)
        self.assertEqual(outcome.service_start, '08:00:00')
        self.assertEqual(outcome.service_end, '22:00:00')
        self.assertEqual(outcome.capacity_minutes, 1680)
        self.assertEqual(outcome.quality_status, 'EXACT')
        self.assertEqual(self._business_digest(), before)

    def test_before_tracking_start_is_unavailable(self):
        outcome = self._capture(date(2026, 8, 18), 'before-start')

        self.assertEqual(outcome.status, 'SUCCESS')
        self.assertEqual(outcome.quality_status, 'UNAVAILABLE')
        self.assertEqual(outcome.capacity_minutes, 0)
        self.assertIn('BEFORE_TRACKING_START', outcome.quality_reason)

    def test_missed_historical_capture_is_unavailable(self):
        outcome = self._capture(
            date(2026, 8, 19),
            'missed-day',
            captured_time=datetime(2026, 8, 20, 9, 0, 0),
        )

        self.assertEqual(outcome.quality_status, 'UNAVAILABLE')
        self.assertIn('HISTORICAL_EXACT_MISSING', outcome.quality_reason)

    def test_zero_seats_is_exact(self):
        outcome = self._capture(date(2026, 8, 19), 'zero-seat')

        self.assertEqual(outcome.total_seat_count, 0)
        self.assertEqual(outcome.serviceable_seat_count, 0)
        self.assertEqual(outcome.capacity_minutes, 0)
        self.assertEqual(outcome.quality_status, 'EXACT')

    def test_duplicate_request_reuses_job_run(self):
        first = self._capture(date(2026, 8, 19), 'same-request')
        second = self._capture(date(2026, 8, 19), 'same-request')

        self.assertEqual(second.job_run_id, first.job_run_id)
        self.assertTrue(second.reused)
        self.assertEqual(MetricJobRun.query.filter_by(job_name=JOB_NAME).count(), 1)

    def test_concurrent_duplicate_reports_running_without_second_job(self):
        started = threading.Event()
        release = threading.Event()
        thread_outcomes = []
        thread_errors = []
        original_collector = capacity_service.collect_capacity_fact

        def slow_collector(target_date, request_time, now_provider):
            started.set()
            release.wait(timeout=5)
            return original_collector(target_date, request_time, now_provider)

        def first_request():
            with self.app.app_context():
                try:
                    thread_outcomes.append(
                        self._capture(date(2026, 8, 19), 'concurrent-request')
                    )
                except Exception as exc:  # pragma: no cover - asserted below
                    thread_errors.append(exc)

        with patch.object(
            capacity_service, 'collect_capacity_fact', side_effect=slow_collector
        ):
            worker = threading.Thread(target=first_request)
            worker.start()
            self.assertTrue(started.wait(timeout=5))
            with self.assertRaises(CaptureRequestError) as raised:
                self._capture(date(2026, 8, 19), 'concurrent-request')
            self.assertIn('still RUNNING', str(raised.exception))
            release.set()
            worker.join(timeout=5)

        self.assertFalse(worker.is_alive())
        self.assertEqual(thread_errors, [])
        self.assertEqual(len(thread_outcomes), 1)
        self.assertEqual(thread_outcomes[0].status, 'SUCCESS')
        self.assertEqual(MetricJobRun.query.filter_by(job_name=JOB_NAME).count(), 1)

    def test_explicit_rerun_creates_new_version(self):
        first = self._capture(date(2026, 8, 19), 'rerun-original')
        second = self._capture(
            date(2026, 8, 19),
            'rerun-explicit',
            retry_of_job_run_id=first.job_run_id,
        )

        self.assertNotEqual(second.job_run_id, first.job_run_id)
        self.assertEqual(
            db.session.get(MetricJobRun, second.job_run_id).retry_of_job_run_id,
            first.job_run_id,
        )
        self.assertEqual(
            SeatCapacitySnapshot.query.filter_by(
                capacity_date=date(2026, 8, 19)
            ).count(),
            2,
        )

    def test_snapshot_unique_constraint(self):
        outcome = self._capture(date(2026, 8, 19), 'unique-original')
        duplicate = SeatCapacitySnapshot(
            capacity_date=date(2026, 8, 19),
            service_start=datetime.strptime('08:00', '%H:%M').time(),
            service_end=datetime.strptime('22:00', '%H:%M').time(),
            total_seat_count=0,
            serviceable_seat_count=0,
            capacity_minutes=0,
            quality_status='EXACT',
            job_run_id=outcome.job_run_id,
            captured_time=FIXED_NOW,
        )
        db.session.add(duplicate)

        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        self.assertEqual(
            SeatCapacitySnapshot.query.filter_by(
                job_run_id=outcome.job_run_id
            ).count(),
            1,
        )

    def test_publish_failure_rolls_back_snapshot_and_marks_job_failed(self):
        self._add_seats('available')
        original_commit = db.session.commit
        failed_once = False

        def fail_publish_commit():
            nonlocal failed_once
            has_capacity = any(
                isinstance(item, SeatCapacitySnapshot) for item in db.session.new
            )
            has_success = any(
                isinstance(item, MetricJobRun) and item.status == 'SUCCESS'
                for item in db.session.dirty
            )
            if not failed_once and (has_capacity or has_success):
                failed_once = True
                raise RuntimeError('simulated publish failure')
            return original_commit()

        with patch.object(db.session, 'commit', side_effect=fail_publish_commit):
            with self.assertRaises(CaptureExecutionError) as raised:
                self._capture(date(2026, 8, 19), 'publish-failure')

        job_run = db.session.get(MetricJobRun, raised.exception.job_run_id)
        self.assertEqual(job_run.status, 'FAILED')
        self.assertEqual(job_run.snapshot_row_count, 0)
        self.assertEqual(
            SeatCapacitySnapshot.query.filter_by(job_run_id=job_run.id).count(),
            0,
        )

    def test_failed_request_is_not_reused_as_success(self):
        self._add_seats('unsupported-status')
        with self.assertRaises(CaptureExecutionError) as first:
            self._capture(date(2026, 8, 19), 'failed-request')

        with self.assertRaises(CaptureRequestError) as repeated:
            self._capture(date(2026, 8, 19), 'failed-request')

        self.assertIn(str(first.exception.job_run_id), str(repeated.exception))
        self.assertEqual(MetricJobRun.query.filter_by(job_name=JOB_NAME).count(), 1)

        with patch.object(
            Config, 'CAPACITY_CAPTURE_ALLOWED_DATABASES', (TEST_DATABASE,)
        ):
            result = self.app.test_cli_runner().invoke(
                args=[
                    'capture-seat-capacity',
                    '--date',
                    '2026-08-19',
                    '--request-id',
                    'phase14-test-failed-request',
                    '--database',
                    TEST_DATABASE,
                ]
            )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('Existing request failed', result.output)

    def test_cross_midnight_refuses_exact(self):
        times = iter(
            [
                datetime(2026, 8, 19, 23, 59, 59),
                datetime(2026, 8, 20, 0, 0, 1),
            ]
        )

        with self.assertRaises(CaptureExecutionError) as raised:
            capture_seat_capacity(
                target_date=date(2026, 8, 19),
                request_identity='phase14-test-cross-midnight',
                allowed_databases=(TEST_DATABASE,),
                now_provider=lambda: next(times),
            )

        job_run = db.session.get(MetricJobRun, raised.exception.job_run_id)
        self.assertEqual(job_run.status, 'FAILED')
        self.assertEqual(
            SeatCapacitySnapshot.query.filter_by(job_run_id=job_run.id).count(),
            0,
        )

    def test_publish_recheck_prevents_exact_downgrade(self):
        exact = self._capture(date(2026, 8, 19), 'exact-before-race')
        self.assertEqual(exact.quality_status, 'EXACT')

        with patch.object(
            capacity_service, '_find_successful_exact', return_value=None
        ):
            with self.assertRaises(CaptureExecutionError) as raised:
                self._capture(
                    date(2026, 8, 19),
                    'unavailable-race',
                    captured_time=datetime(2026, 8, 20, 9, 0, 0),
                )

        failed_job = db.session.get(MetricJobRun, raised.exception.job_run_id)
        self.assertEqual(failed_job.status, 'FAILED')
        self.assertEqual(
            SeatCapacitySnapshot.query.filter_by(
                capacity_date=date(2026, 8, 19),
                quality_status='UNAVAILABLE',
            ).count(),
            0,
        )

    def test_stale_request_is_marked_failed(self):
        target_date = date(2026, 8, 19)
        request_identity = 'phase14-test-stale-request'
        job_run = MetricJobRun(
            run_key='phase14-stale-run-key',
            idempotency_key=_build_idempotency_key(
                target_date, request_identity, 'MANUAL', None
            ),
            job_name=JOB_NAME,
            job_type='MANUAL',
            period_type='DAY',
            requested_start=datetime(2026, 8, 19, 0, 0, 0),
            requested_end=datetime(2026, 8, 20, 0, 0, 0),
            engine='PYTHON',
            calculation_version=CALCULATION_VERSION,
            business_timezone='Asia/Shanghai',
            status='PENDING',
            create_time=datetime(2026, 8, 19, 11, 40, 0),
        )
        db.session.add(job_run)
        db.session.commit()

        with self.assertRaises(CaptureRequestError):
            capture_seat_capacity(
                target_date=target_date,
                request_identity=request_identity,
                allowed_databases=(TEST_DATABASE,),
                captured_time=FIXED_NOW,
            )

        db.session.refresh(job_run)
        self.assertEqual(job_run.status, 'FAILED')
        self.assertEqual(job_run.snapshot_row_count, 0)

    def test_stale_waiter_reuses_success_completed_while_waiting(self):
        target_date = date(2026, 8, 19)
        request_identity = 'phase14-test-stale-success-race'
        job_run = MetricJobRun(
            run_key='phase14-stale-success-key',
            idempotency_key=_build_idempotency_key(
                target_date, request_identity, 'MANUAL', None
            ),
            job_name=JOB_NAME,
            job_type='MANUAL',
            period_type='DAY',
            requested_start=datetime(2026, 8, 19, 0, 0, 0),
            requested_end=datetime(2026, 8, 20, 0, 0, 0),
            engine='PYTHON',
            calculation_version=CALCULATION_VERSION,
            business_timezone='Asia/Shanghai',
            status='RUNNING',
            create_time=datetime(2026, 8, 19, 11, 40, 0),
            start_time=datetime(2026, 8, 19, 11, 40, 0),
        )
        db.session.add(job_run)
        db.session.commit()
        job_run_id = job_run.id

        row_locked = threading.Event()
        allow_publish = threading.Event()
        waiter_started = threading.Event()
        publisher_errors = []
        waiter_errors = []
        waiter_outcomes = []

        def complete_original_job():
            with self.app.app_context():
                try:
                    locked = (
                        MetricJobRun.query.filter_by(id=job_run_id)
                        .populate_existing()
                        .with_for_update()
                        .one()
                    )
                    row_locked.set()
                    allow_publish.wait(timeout=5)
                    snapshot = SeatCapacitySnapshot(
                        capacity_date=target_date,
                        service_start=datetime.strptime('08:00', '%H:%M').time(),
                        service_end=datetime.strptime('22:00', '%H:%M').time(),
                        total_seat_count=0,
                        serviceable_seat_count=0,
                        capacity_minutes=0,
                        quality_status='EXACT',
                        quality_reason='stale race test',
                        job_run_id=locked.id,
                        captured_time=FIXED_NOW,
                    )
                    db.session.add(snapshot)
                    locked.status = 'SUCCESS'
                    locked.finish_time = FIXED_NOW
                    locked.input_row_count = 0
                    locked.snapshot_row_count = 1
                    db.session.commit()
                except Exception as exc:  # pragma: no cover - asserted below
                    publisher_errors.append(exc)

        def duplicate_request():
            with self.app.app_context():
                waiter_started.set()
                try:
                    waiter_outcomes.append(
                        capture_seat_capacity(
                            target_date=target_date,
                            request_identity=request_identity,
                            allowed_databases=(TEST_DATABASE,),
                            captured_time=FIXED_NOW,
                        )
                    )
                except Exception as exc:  # pragma: no cover - asserted below
                    waiter_errors.append(exc)

        publisher = threading.Thread(target=complete_original_job)
        publisher.start()
        self.assertTrue(row_locked.wait(timeout=5))

        waiter = threading.Thread(target=duplicate_request)
        waiter.start()
        self.assertTrue(waiter_started.wait(timeout=5))
        time_module.sleep(0.2)
        allow_publish.set()
        publisher.join(timeout=5)
        waiter.join(timeout=5)

        self.assertFalse(publisher.is_alive())
        self.assertFalse(waiter.is_alive())
        self.assertEqual(publisher_errors, [])
        self.assertEqual(waiter_errors, [])
        self.assertEqual(len(waiter_outcomes), 1)
        self.assertTrue(waiter_outcomes[0].reused)
        self.assertEqual(waiter_outcomes[0].status, 'SUCCESS')
        db.session.rollback()
        db.session.expire_all()
        persisted = db.session.get(MetricJobRun, job_run_id)
        self.assertEqual(persisted.status, 'SUCCESS')
        self.assertEqual(persisted.snapshot_row_count, 1)
        self.assertEqual(
            SeatCapacitySnapshot.query.filter_by(job_run_id=job_run_id).count(),
            1,
        )

    def test_database_allow_list_checks_actual_connection(self):
        with self.assertRaises(capacity_service.DatabaseWriteNotAllowed):
            capture_seat_capacity(
                target_date=date(2026, 8, 19),
                request_identity='phase14-test-wrong-allow-list',
                allowed_databases=('smart_library',),
                captured_time=FIXED_NOW,
            )
        self.assertEqual(MetricJobRun.query.filter_by(job_name=JOB_NAME).count(), 0)

    def test_future_date_is_rejected_before_job_creation(self):
        with self.assertRaises(CaptureRequestError):
            self._capture(date(2026, 8, 20), 'future-date')
        self.assertEqual(MetricJobRun.query.filter_by(job_name=JOB_NAME).count(), 0)

    def _capture(self, target_date, request_identity, **kwargs):
        return capture_seat_capacity(
            target_date=target_date,
            request_identity=f'phase14-test-{request_identity}',
            allowed_databases=(TEST_DATABASE,),
            captured_time=kwargs.pop('captured_time', FIXED_NOW),
            **kwargs,
        )

    def _add_seats(self, *statuses):
        for index, status in enumerate(statuses, start=1):
            db.session.add(
                Seat(
                    seat_number=f'P14TEST-{index}',
                    room_name='Phase 1.4 Test Room',
                    floor=1,
                    status=status,
                )
            )
        db.session.commit()

    def _cleanup_phase14_rows(self):
        job_ids = [
            value
            for (value,) in db.session.query(MetricJobRun.id)
            .filter(MetricJobRun.job_name == JOB_NAME)
            .all()
        ]
        if job_ids:
            SeatCapacitySnapshot.query.filter(
                SeatCapacitySnapshot.job_run_id.in_(job_ids)
            ).delete(synchronize_session=False)
            MetricJobRun.query.filter(
                MetricJobRun.id.in_(job_ids)
            ).update(
                {MetricJobRun.retry_of_job_run_id: None},
                synchronize_session=False,
            )
            MetricJobRun.query.filter(
                MetricJobRun.id.in_(job_ids)
            ).delete(synchronize_session=False)
        Seat.query.filter(Seat.seat_number.like('P14TEST-%')).delete(
            synchronize_session=False
        )
        db.session.commit()

    def _business_digest(self):
        seats = [
            tuple(row)
            for row in db.session.query(
                Seat.id,
                Seat.seat_number,
                Seat.room_name,
                Seat.floor,
                Seat.status,
                Seat.has_power,
                Seat.description,
            )
            .order_by(Seat.id)
            .all()
        ]
        reservations = [
            tuple(row)
            for row in db.session.query(
                Reservation.id,
                Reservation.user_id,
                Reservation.seat_id,
                Reservation.date,
                Reservation.start_time,
                Reservation.end_time,
                Reservation.status,
                Reservation.checkin_time,
                Reservation.create_time,
            )
            .order_by(Reservation.id)
            .all()
        ]
        payload = json.dumps(
            {'seat': seats, 'reservation': reservations},
            default=str,
            ensure_ascii=True,
            sort_keys=True,
        ).encode('utf-8')
        return hashlib.sha256(payload).hexdigest()


if __name__ == '__main__':
    unittest.main()
