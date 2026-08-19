# -*- coding: utf-8 -*-
"""Repeatable MySQL integration tests for the V2 metric data loop."""

from dataclasses import replace
from datetime import date, datetime, time, timedelta
from decimal import Decimal
import threading
import unittest
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import event, inspect
from sqlalchemy.engine import URL
from sqlalchemy.exc import IntegrityError

from app import create_app
from config import Config
from extensions import db
from models import (
    Book, BookRequest, Borrow, BorrowDueChange, Category, MetricJobRun,
    MetricSnapshot, Reservation, Seat, SeatCapacitySnapshot, User,
)
from services.metric_contract import CALCULATION_VERSION, MetricResult, canonical_period
from services.metric_pipeline_service import (
    DatabaseWriteNotAllowed, MetricJobExecutionError, MetricJobRequestError,
    MetricValidationError,
    calculate_result_checksum, get_current_snapshot_set, run_metric_job,
    validate_metric_results,
)
from services.metrics_aggregator import _due_time_at, compute_metrics
from utils.jwt_utils import create_token


TEST_DATABASE = 'smart_library_phase13_test_20260819_1'
MONTH_START = datetime(2026, 7, 1)
MONTH_END = datetime(2026, 8, 1)


class MetricsPipelineIntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        uri = URL.create(
            drivername='mysql+pymysql', username=Config.DB_USER, password=Config.DB_PASS,
            host=Config.DB_HOST, port=int(Config.DB_PORT), database=TEST_DATABASE,
            query={'charset': 'utf8mb4'},
        )
        cls.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': uri,
            'METRIC_RUN_ALLOWED_DATABASES': (TEST_DATABASE,),
        })
        cls.context = cls.app.app_context()
        cls.context.push()
        if db.engine.url.database != TEST_DATABASE:
            raise AssertionError('Metric tests refused a non-test database connection.')
        required = {'metric_job_run', 'metric_snapshot', 'seat_capacity_snapshot', 'borrow_due_change'}
        if not required.issubset(inspect(db.engine).get_table_names()):
            raise AssertionError('V2 tables are missing from the independent test database.')

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        cls.context.pop()

    def setUp(self):
        self._cleanup()
        self.prefix = f'P16T-{uuid4().hex[:8]}'
        self._seed_dataset()

    def tearDown(self):
        db.session.rollback()
        self._cleanup()

    def test_all_six_metrics_daily_monthly_and_boundaries(self):
        monthly = compute_metrics('MONTH', MONTH_START, MONTH_END)
        by_code = self._by_code(monthly)
        self.assertEqual(by_code['METRIC-01'][0].value_decimal, Decimal(5))
        self.assertEqual(by_code['METRIC-01'][0].quality_status, 'BEST_EFFORT')
        self.assertEqual(by_code['METRIC-02'][0].value_decimal, Decimal(13))
        self.assertEqual(by_code['METRIC-03'][0].value_decimal, Decimal(5))
        self.assertEqual(by_code['METRIC-03'][0].quality_status, 'BEST_EFFORT')
        self.assertEqual(by_code['METRIC-04'][0].value_decimal, Decimal(3))
        self.assertEqual(
            [(row.value_decimal, row.rank) for row in by_code['METRIC-05']],
            [(Decimal(5), 1), (Decimal(5), 1), (Decimal(3), 2)],
        )
        self.assertIn(str(self.book_c.id), [row.dimension_key for row in by_code['METRIC-05']])
        utilization = by_code['METRIC-06'][0]
        self.assertEqual(utilization.value_decimal, Decimal(1100) / Decimal(4000))
        self.assertEqual(utilization.quality_status, 'BEST_EFFORT')
        self.assertEqual(utilization.coverage_ratio, Decimal('0.064516'))

        day_start, day_end = canonical_period('DAY', date(2026, 7, 1))
        daily = self._by_code(compute_metrics('DAY', day_start, day_end))
        self.assertEqual(daily['METRIC-02'][0].value_decimal, Decimal(13))
        self.assertEqual(daily['METRIC-06'][0].value_decimal, Decimal('0.5'))
        self.assertEqual(daily['METRIC-06'][0].quality_status, 'EXACT')

    def test_metric_03_reconstructs_all_required_historical_cases(self):
        results = self._by_code(compute_metrics('MONTH', MONTH_START, MONTH_END))
        self.assertEqual(results['METRIC-03'][0].value_decimal, Decimal(5))
        before_change = self.history['change_before']
        after_change = self.history['change_after']
        self.assertGreaterEqual(
            _due_time_at(before_change, self.changes[before_change.id], MONTH_END), MONTH_END
        )
        self.assertLess(
            _due_time_at(after_change, self.changes[after_change.id], MONTH_END), MONTH_END
        )
        self.assertEqual(self.history['return_at_e'].return_time, MONTH_END)
        self.assertLess(self.history['return_before_e'].return_time, MONTH_END)
        self.assertEqual(self.history['legacy'].renew_count, 1)
        self.assertEqual(self.changes[self.history['legacy'].id], [])

    def test_metric_06_unavailable_day_is_not_silently_zero_capacity(self):
        start, end = canonical_period('DAY', date(2026, 7, 3))
        result = self._by_code(compute_metrics('DAY', start, end))['METRIC-06'][0]
        self.assertIsNone(result.value_decimal)
        self.assertEqual(result.quality_status, 'UNAVAILABLE')
        self.assertEqual(result.coverage_ratio, Decimal(0))

    def test_validation_and_checksum_are_stable(self):
        results = compute_metrics('MONTH', MONTH_START, MONTH_END)
        validate_metric_results(results, [(MONTH_START, MONTH_END)], CALCULATION_VERSION)
        self.assertEqual(
            calculate_result_checksum(results),
            calculate_result_checksum(list(reversed(results))),
        )
        with self.assertRaises(MetricValidationError):
            validate_metric_results(
                results + [results[0]], [(MONTH_START, MONTH_END)], CALCULATION_VERSION
            )
        with self.assertRaises(MetricValidationError):
            validate_metric_results(results, [(MONTH_START, MONTH_END)], 'metrics-wrong')
        with self.assertRaises(MetricValidationError):
            validate_metric_results(
                results + [replace(results[0], dimension_key='EXTRA')],
                [(MONTH_START, MONTH_END)],
                CALCULATION_VERSION,
            )

    def test_job_success_idempotency_and_business_tables_read_only(self):
        before = self._business_state()
        first = self._run('success-idempotent')
        second = self._run('success-idempotent')
        self.assertEqual(first.status, 'SUCCESS')
        self.assertGreater(first.snapshot_row_count, 6)
        self.assertEqual(second.job_run_id, first.job_run_id)
        self.assertTrue(second.reused)
        self.assertEqual(self._business_state(), before)
        job = db.session.get(MetricJobRun, first.job_run_id)
        self.assertEqual(job.snapshot_row_count, MetricSnapshot.query.filter_by(job_run_id=job.id).count())
        self.assertEqual(job.result_checksum, first.result_checksum)

    def test_compute_validation_and_multi_period_failures_publish_zero(self):
        failures = []

        def fail_compute(period_type, start, end):
            del period_type, start, end
            raise RuntimeError('simulated compute failure')

        failures.append(('compute-failure', [(MONTH_START, MONTH_END)], fail_compute))

        def invalid_compute(period_type, start, end):
            rows = compute_metrics(period_type, start, end)
            return rows + [rows[0]]

        failures.append(('validation-failure', [(MONTH_START, MONTH_END)], invalid_compute))

        first_day = canonical_period('DAY', date(2026, 7, 1))
        second_day = canonical_period('DAY', date(2026, 7, 2))

        def fail_second(period_type, start, end):
            if start == second_day[0]:
                raise RuntimeError('second period failed')
            return compute_metrics(period_type, start, end)

        failures.append(('multi-period-failure', [first_day, second_day], fail_second))

        for name, periods, compute_func in failures:
            with self.subTest(name=name):
                with self.assertRaises(MetricJobExecutionError) as raised:
                    self._run(name, periods=periods, compute_func=compute_func)
                job = db.session.get(MetricJobRun, raised.exception.job_run_id)
                self.assertEqual(job.status, 'FAILED')
                self.assertEqual(job.snapshot_row_count, 0)
                self.assertEqual(MetricSnapshot.query.filter_by(job_run_id=job.id).count(), 0)

    def test_publish_failure_rolls_back_all_snapshots(self):
        original_commit = db.session.commit
        failed = False

        def fail_publish():
            nonlocal failed
            publishing = any(isinstance(row, MetricSnapshot) for row in db.session.new)
            if publishing and not failed:
                failed = True
                raise RuntimeError('simulated publish failure')
            return original_commit()

        with patch.object(db.session, 'commit', side_effect=fail_publish):
            with self.assertRaises(MetricJobExecutionError) as raised:
                self._run('publish-failure')
        job = db.session.get(MetricJobRun, raised.exception.job_run_id)
        self.assertEqual(job.status, 'FAILED')
        self.assertEqual(MetricSnapshot.query.filter_by(job_run_id=job.id).count(), 0)

    def test_rerun_is_immutable_and_current_selects_latest_success(self):
        first = self._run('rerun-a')
        first_ids = [row.id for row in MetricSnapshot.query.filter_by(job_run_id=first.job_run_id).all()]
        second = self._run('rerun-b', job_type='RETRY', retry_of=first.job_run_id)
        current = get_current_snapshot_set('MONTH', MONTH_START, MONTH_END)
        self.assertEqual(current.job_run.id, second.job_run_id)
        self.assertEqual(
            [row.id for row in MetricSnapshot.query.filter_by(job_run_id=first.job_run_id).all()],
            first_ids,
        )
        self.assertGreater(MetricSnapshot.query.filter_by(job_run_id=second.job_run_id).count(), 0)

    def test_metric_snapshot_unique_identity_rejects_duplicate(self):
        outcome = self._run('snapshot-unique')
        original = MetricSnapshot.query.filter_by(job_run_id=outcome.job_run_id).first()
        duplicate = MetricSnapshot(
            job_run_id=original.job_run_id, metric_code=original.metric_code,
            period_type=original.period_type, period_start=original.period_start,
            period_end=original.period_end, temporal_type=original.temporal_type,
            as_of_time=original.as_of_time, scope_type=original.scope_type,
            scope_key=original.scope_key, dimension_type=original.dimension_type,
            dimension_key=original.dimension_key, metric_value=original.metric_value,
            unit=original.unit, rank_value=original.rank_value,
            dimension_payload=original.dimension_payload,
            quality_status=original.quality_status, quality_reason=original.quality_reason,
            coverage_ratio=original.coverage_ratio,
            calculation_version=original.calculation_version,
            generated_time=original.generated_time,
        )
        db.session.add(duplicate)
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()
        self.assertEqual(
            MetricSnapshot.query.filter_by(job_run_id=outcome.job_run_id).count(),
            outcome.snapshot_row_count,
        )

    def test_published_snapshot_is_orm_immutable_and_checksum_protects_reuse(self):
        request_id = 'immutable-checksum'
        outcome = self._run(request_id)
        snapshot = MetricSnapshot.query.filter_by(job_run_id=outcome.job_run_id).first()
        original_value = snapshot.metric_value
        snapshot.metric_value = original_value + Decimal(1)
        with self.assertRaises(RuntimeError):
            db.session.commit()
        db.session.rollback()
        self.assertEqual(db.session.get(MetricSnapshot, snapshot.id).metric_value, original_value)

        with self.assertRaises(RuntimeError):
            MetricSnapshot.query.filter_by(id=snapshot.id).update(
                {MetricSnapshot.metric_value: original_value + Decimal(1)},
                synchronize_session=False,
            )
        db.session.rollback()
        with self.assertRaises(RuntimeError):
            MetricSnapshot.query.filter_by(id=snapshot.id).delete(
                synchronize_session=False
            )
        db.session.rollback()

        connection = db.engine.raw_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    'UPDATE metric_snapshot SET metric_value = metric_value + 1 WHERE id = %s',
                    (snapshot.id,),
                )
            connection.commit()
        finally:
            connection.close()
        db.session.rollback()
        with self.assertRaises(MetricJobRequestError):
            self._run(request_id)

    def test_snapshot_unavailable_and_dashboard_fallback_are_explicit(self):
        headers = {'Authorization': f'Bearer {self.admin_token}'}
        with self.app.test_client() as client:
            monthly = client.get('/api/reports/monthly?month=2026-06', headers=headers)
            stats = client.get('/api/dashboard/stats', headers=headers)
        self.assertEqual(monthly.status_code, 404)
        self.assertEqual(monthly.get_json()['data']['source'], 'snapshot_unavailable')
        self.assertEqual(stats.status_code, 200)
        self.assertEqual(stats.get_json()['data']['source'], 'realtime_fallback')

    def test_backfill_cli_publishes_all_periods_once(self):
        result = self.app.test_cli_runner().invoke(args=[
            'run-metrics', '--period', 'day', '--start', '2026-07-01',
            '--end', '2026-07-02', '--request-id', f'{self.prefix}-backfill',
            '--job-type', 'backfill',
        ])
        self.assertEqual(result.exit_code, 0, result.output)
        job = MetricJobRun.query.filter_by(job_name='metric_aggregation', job_type='BACKFILL').one()
        self.assertEqual(job.status, 'SUCCESS')
        periods = db.session.query(MetricSnapshot.period_start).filter_by(job_run_id=job.id).distinct().count()
        self.assertEqual(periods, 2)

    def test_database_allow_list_blocks_formal_or_unlisted_database(self):
        with self.assertRaises(DatabaseWriteNotAllowed):
            self._run('wrong-allow-list', allowed_databases=('smart_library',))
        self.assertEqual(MetricJobRun.query.filter_by(job_name='metric_aggregation').count(), 0)

    def test_dashboard_and_monthly_report_read_latest_snapshot(self):
        first = self._run('api-a')
        second = self._run('api-b', job_type='RETRY', retry_of=first.job_run_id)
        self._run('api-day', periods=[canonical_period('DAY', date(2026, 7, 1))])
        failed_job = MetricJobRun(
            run_key=str(uuid4()), idempotency_key=uuid4().hex, job_name='metric_aggregation',
            job_type='RETRY', period_type='MONTH', requested_start=MONTH_START,
            requested_end=MONTH_END, engine='PYTHON', calculation_version=CALCULATION_VERSION,
            business_timezone='Asia/Shanghai', status='FAILED', create_time=datetime.now(),
            finish_time=datetime.now(), snapshot_row_count=0,
        )
        db.session.add(failed_job)
        db.session.commit()

        headers = {'Authorization': f'Bearer {self.admin_token}'}
        with self.app.test_client() as client:
            monthly = client.get('/api/reports/monthly?month=2026-07', headers=headers)
            stats = client.get('/api/dashboard/stats', headers=headers)
            popular = client.get('/api/dashboard/popular-books', headers=headers)
        self.assertEqual(monthly.status_code, 200)
        report = monthly.get_json()['data']
        self.assertEqual(report['source'], 'snapshot')
        self.assertEqual(report['job_run_id'], second.job_run_id)
        self.assertEqual(report['core_stats']['borrow_count'], 13)
        self.assertEqual(len(report['book_analysis']['popular_books']), 3)
        self.assertEqual(stats.get_json()['data']['source'], 'snapshot')
        self.assertEqual(popular.get_json()['data']['job_run_id'], second.job_run_id)

    def _run(self, request_id, periods=None, compute_func=compute_metrics,
             job_type='MANUAL', retry_of=None, allowed_databases=(TEST_DATABASE,)):
        return run_metric_job(
            period_type='MONTH' if periods is None else (
                'DAY' if periods[0][1] - periods[0][0] == timedelta(days=1) else 'MONTH'
            ),
            periods=periods or [(MONTH_START, MONTH_END)],
            request_identity=f'{self.prefix}-{request_id}',
            allowed_databases=allowed_databases,
            job_type=job_type,
            retry_of_job_run_id=retry_of,
            compute_func=compute_func,
        )

    @staticmethod
    def _by_code(results):
        grouped = {}
        for result in results:
            grouped.setdefault(result.metric_code, []).append(result)
        return grouped

    def _seed_dataset(self):
        category = Category(name=f'{self.prefix}-CATEGORY')
        users = [
            User(username=f'{self.prefix}-{role}-{index}', password='test', real_name=role,
                 role=role, status='active')
            for index, role in enumerate(('student', 'teacher', 'student', 'admin'), start=1)
        ]
        db.session.add_all([category, *users])
        db.session.commit()
        self.student, self.teacher, self.requester, self.admin = users
        self.admin_token = create_token(self.admin.id, self.admin.username, self.admin.role)
        books = [
            Book(title=f'Book {name}', author='Metric Test', isbn=f'{self.prefix}-{name}',
                 stock=stock, category_id=category.id, is_deleted=deleted)
            for name, stock, deleted in (('A', 2, False), ('B', 3, False), ('C', 7, True))
        ]
        seats = [
            Seat(seat_number=f'{self.prefix}-S1', room_name='Metric Room', floor=1,
                 status='available', has_power=True),
            Seat(seat_number=f'{self.prefix}-S2', room_name='Metric Room', floor=1,
                 status='maintenance', has_power=False),
        ]
        db.session.add_all([*books, *seats])
        db.session.commit()
        self.book_a, self.book_b, self.book_c = books

        for book, count in ((self.book_a, 5), (self.book_b, 5), (self.book_c, 3)):
            for index in range(count):
                db.session.add(Borrow(
                    user_id=self.student.id, book_id=book.id, status='returned',
                    borrow_time=MONTH_START + timedelta(hours=index),
                    due_time=MONTH_START + timedelta(days=20),
                    return_time=MONTH_START + timedelta(days=10), renew_count=0,
                ))
        db.session.add_all([
            Borrow(user_id=self.student.id, book_id=self.book_a.id, status='pending',
                   borrow_time=MONTH_START, due_time=None, renew_count=0),
            Borrow(user_id=self.student.id, book_id=self.book_a.id, status='rejected',
                   borrow_time=MONTH_START, due_time=None, renew_count=0),
            Borrow(user_id=self.student.id, book_id=self.book_a.id, status='returned',
                   borrow_time=MONTH_END, due_time=MONTH_END + timedelta(days=10),
                   return_time=MONTH_END + timedelta(days=2), renew_count=0),
        ])
        db.session.commit()

        history_specs = {
            'unreturned': (None, MONTH_END - timedelta(days=5), 0),
            'return_at_e': (MONTH_END, MONTH_END - timedelta(days=5), 0),
            'return_before_e': (MONTH_END - timedelta(seconds=1), MONTH_END - timedelta(days=5), 0),
            'returned_after_e': (MONTH_END + timedelta(days=1), MONTH_END - timedelta(days=5), 0),
            'change_before': (None, MONTH_END + timedelta(days=10), 1),
            'change_after': (None, MONTH_END + timedelta(days=10), 1),
            'legacy': (None, MONTH_END - timedelta(days=2), 1),
        }
        self.history = {}
        for name, (returned, due, renew_count) in history_specs.items():
            borrow = Borrow(
                user_id=self.student.id, book_id=self.book_a.id, status='returned',
                borrow_time=MONTH_START - timedelta(days=20), due_time=due,
                return_time=returned, renew_count=renew_count,
            )
            db.session.add(borrow)
            self.history[name] = borrow
        db.session.commit()

        before = BorrowDueChange(
            borrow_id=self.history['change_before'].id, change_sequence=1, change_type='RENEW',
            old_due_time=MONTH_END - timedelta(days=5), new_due_time=MONTH_END + timedelta(days=10),
            change_time=MONTH_END - timedelta(days=2), operator_user_id=self.student.id,
        )
        after = BorrowDueChange(
            borrow_id=self.history['change_after'].id, change_sequence=1, change_type='RENEW',
            old_due_time=MONTH_END - timedelta(days=5), new_due_time=MONTH_END + timedelta(days=10),
            change_time=MONTH_END + timedelta(days=1), operator_user_id=self.student.id,
        )
        db.session.add_all([before, after])
        db.session.add_all([
            Reservation(user_id=self.teacher.id, seat_id=seats[0].id, date=date(2026, 7, 1),
                        start_time=time(8, 0), end_time=time(16, 20), status='completed'),
            Reservation(user_id=self.teacher.id, seat_id=seats[0].id, date=date(2026, 7, 2),
                        start_time=time(8, 0), end_time=time(18, 0), status='no_show'),
            Reservation(user_id=self.teacher.id, seat_id=seats[0].id, date=date(2026, 8, 1),
                        start_time=time(8, 0), end_time=time(9, 0), status='completed'),
            BookRequest(user_id=self.requester.id, title='Requested', status='pending',
                        create_time=MONTH_START + timedelta(days=3)),
            BookRequest(user_id=self.admin.id, title='Admin Requested', status='pending',
                        create_time=MONTH_START + timedelta(days=3)),
        ])
        db.session.commit()
        self.changes = {borrow.id: [] for borrow in self.history.values()}
        self.changes[self.history['change_before'].id] = [before]
        self.changes[self.history['change_after'].id] = [after]
        self._add_capacity(date(2026, 7, 1), 1000, 'EXACT')
        self._add_capacity(date(2026, 7, 2), 3000, 'EXACT')
        self._add_capacity(date(2026, 7, 3), 0, 'UNAVAILABLE')

    def _add_capacity(self, capacity_date, minutes, quality):
        job = MetricJobRun(
            run_key=str(uuid4()), idempotency_key=uuid4().hex, job_name='seat_capacity_capture',
            job_type='MANUAL', period_type='DAY',
            requested_start=datetime.combine(capacity_date, time.min),
            requested_end=datetime.combine(capacity_date + timedelta(days=1), time.min),
            engine='PYTHON', calculation_version=CALCULATION_VERSION,
            business_timezone='Asia/Shanghai', status='SUCCESS', create_time=datetime.now(),
            start_time=datetime.now(), finish_time=datetime.now(), snapshot_row_count=1,
        )
        db.session.add(job)
        db.session.flush()
        db.session.add(SeatCapacitySnapshot(
            capacity_date=capacity_date, service_start=time(8), service_end=time(22),
            total_seat_count=2, serviceable_seat_count=1, capacity_minutes=minutes,
            quality_status=quality,
            quality_reason=None if quality == 'EXACT' else 'HISTORICAL_EXACT_MISSING',
            job_run_id=job.id, captured_time=datetime.now(),
        ))
        db.session.commit()

    def _business_state(self):
        return (
            tuple(db.session.query(Book.id, Book.stock, Book.is_deleted).order_by(Book.id).all()),
            tuple(db.session.query(Borrow.id, Borrow.status, Borrow.due_time, Borrow.renew_count).order_by(Borrow.id).all()),
            tuple(db.session.query(Reservation.id, Reservation.status).order_by(Reservation.id).all()),
        )

    def _cleanup(self):
        db.session.rollback()
        user_ids = [row[0] for row in db.session.query(User.id).filter(User.username.like('P16T-%')).all()]
        book_ids = [row[0] for row in db.session.query(Book.id).filter(Book.isbn.like('P16T-%')).all()]
        seat_ids = [row[0] for row in db.session.query(Seat.id).filter(Seat.seat_number.like('P16T-%')).all()]
        job_ids = [row[0] for row in db.session.query(MetricJobRun.id).filter(
            (MetricJobRun.idempotency_key.like('P16T-%')) |
            (MetricJobRun.job_name == 'metric_aggregation')
        ).all()]
        if job_ids:
            db.session.rollback()
            connection = db.engine.raw_connection()
            try:
                placeholders = ','.join(['%s'] * len(job_ids))
                with connection.cursor() as cursor:
                    cursor.execute(
                        f'DELETE FROM metric_snapshot WHERE job_run_id IN ({placeholders})',
                        tuple(job_ids),
                    )
                connection.commit()
            finally:
                connection.close()
            db.session.expire_all()
        capacity_job_ids = [row[0] for row in db.session.query(MetricJobRun.id).join(
            SeatCapacitySnapshot, SeatCapacitySnapshot.job_run_id == MetricJobRun.id
        ).filter(SeatCapacitySnapshot.capacity_date.between(date(2026, 7, 1), date(2026, 7, 3))).all()]
        if capacity_job_ids:
            SeatCapacitySnapshot.query.filter(SeatCapacitySnapshot.job_run_id.in_(capacity_job_ids)).delete(synchronize_session=False)
        all_job_ids = set(job_ids + capacity_job_ids)
        if all_job_ids:
            MetricJobRun.query.filter(MetricJobRun.id.in_(all_job_ids)).update(
                {MetricJobRun.retry_of_job_run_id: None}, synchronize_session=False
            )
            MetricJobRun.query.filter(MetricJobRun.id.in_(all_job_ids)).delete(synchronize_session=False)
        if book_ids:
            borrow_ids = [row[0] for row in db.session.query(Borrow.id).filter(Borrow.book_id.in_(book_ids)).all()]
            if borrow_ids:
                BorrowDueChange.query.filter(BorrowDueChange.borrow_id.in_(borrow_ids)).delete(synchronize_session=False)
                Borrow.query.filter(Borrow.id.in_(borrow_ids)).delete(synchronize_session=False)
            Book.query.filter(Book.id.in_(book_ids)).delete(synchronize_session=False)
        if seat_ids:
            Reservation.query.filter(Reservation.seat_id.in_(seat_ids)).delete(synchronize_session=False)
            Seat.query.filter(Seat.id.in_(seat_ids)).delete(synchronize_session=False)
        if user_ids:
            BookRequest.query.filter(BookRequest.user_id.in_(user_ids)).delete(synchronize_session=False)
            User.query.filter(User.id.in_(user_ids)).delete(synchronize_session=False)
        Category.query.filter(Category.name.like('P16T-%')).delete(synchronize_session=False)
        db.session.commit()


if __name__ == '__main__':
    unittest.main()
