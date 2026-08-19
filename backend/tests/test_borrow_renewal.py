# -*- coding: utf-8 -*-
"""MySQL integration tests for Phase 1.5 concurrent-safe renewal."""

from datetime import datetime, timedelta
import threading
import unittest
from uuid import uuid4
from unittest.mock import patch

from sqlalchemy import event, inspect, select, text
from sqlalchemy.engine import URL

from app import create_app
from config import Config
from extensions import db
from models import (
    Book,
    Borrow,
    BorrowDueChange,
    Category,
    Notification,
    User,
)
from utils.jwt_utils import create_token


TEST_DATABASE = 'smart_library_phase13_test_20260819_1'
FIXED_DUE_TIME = datetime(2026, 8, 25, 12, 0, 0)


class BorrowRenewalIntegrationTest(unittest.TestCase):
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
            }
        )
        cls.context = cls.app.app_context()
        cls.context.push()
        if db.engine.url.database != TEST_DATABASE:
            raise AssertionError('Test suite refused a non-test database connection.')
        required_tables = {'borrow', 'borrow_due_change', 'book', 'category', 'user'}
        missing_tables = required_tables.difference(inspect(db.engine).get_table_names())
        if missing_tables:
            raise AssertionError(
                f'Phase 1.5 test database is missing tables: {sorted(missing_tables)}'
            )

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        cls.context.pop()

    def setUp(self):
        self._cleanup_phase15_rows()
        self.prefix = f'P15TEST-{uuid4().hex[:10]}'
        self.category = Category(name=f'{self.prefix}-CATEGORY')
        self.owner = User(
            username=f'{self.prefix}-OWNER',
            password='phase15-test-password',
            real_name='Phase 1.5 Owner',
            role='student',
            status='active',
        )
        self.other_user = User(
            username=f'{self.prefix}-OTHER',
            password='phase15-test-password',
            real_name='Phase 1.5 Other',
            role='student',
            status='active',
        )
        db.session.add_all([self.category, self.owner, self.other_user])
        db.session.commit()

        self.book = Book(
            title='Phase 1.5 Test Book',
            author='Phase 1.5',
            isbn=f'{self.prefix}-ISBN',
            stock=4,
            category_id=self.category.id,
            is_deleted=False,
        )
        db.session.add(self.book)
        db.session.commit()

        self.owner_token = create_token(
            self.owner.id, self.owner.username, self.owner.role
        )
        self.other_token = create_token(
            self.other_user.id, self.other_user.username, self.other_user.role
        )

    def tearDown(self):
        db.session.rollback()
        self._cleanup_phase15_rows()

    def test_normal_overdue_renewal_records_fact_and_preserves_response(self):
        borrow = self._create_borrow(status='overdue')
        original_book_stock = self.book.stock
        notification_count = Notification.query.count()

        response = self._renew(borrow.id, self.owner_token)

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload['code'], 200)
        self.assertEqual(set(payload['data']), {'borrow', 'new_due_time'})
        self.assertEqual(payload['data']['borrow']['id'], borrow.id)
        self.assertEqual(payload['data']['borrow']['renew_count'], 1)
        self.assertEqual(payload['data']['borrow']['status'], 'borrowed')
        self.assertEqual(
            payload['data']['new_due_time'], payload['data']['borrow']['due_time']
        )
        self.assertIn('续借成功，新到期日：', payload['message'])

        db.session.expire_all()
        persisted = db.session.get(Borrow, borrow.id)
        change = BorrowDueChange.query.filter_by(borrow_id=borrow.id).one()
        self.assertEqual(persisted.renew_count, 1)
        self.assertEqual(persisted.status, 'borrowed')
        self.assertEqual(change.change_sequence, 1)
        self.assertEqual(change.change_type, 'RENEW')
        self.assertEqual(change.old_due_time, FIXED_DUE_TIME)
        self.assertEqual(change.new_due_time, persisted.due_time)
        self.assertEqual(change.operator_user_id, self.owner.id)
        self.assertEqual(db.session.get(Book, self.book.id).stock, original_book_stock)
        self.assertEqual(Notification.query.count(), notification_count)

    def test_renewal_limit_is_rechecked_without_writes(self):
        borrow = self._create_borrow(renew_count=Config.MAX_RENEW_COUNT)

        response = self._renew(borrow.id, self.owner_token)

        self.assertEqual(response.status_code, 400)
        self.assertIn('续借次数已达上限', response.get_json()['message'])
        self._assert_borrow_unchanged(borrow.id, Config.MAX_RENEW_COUNT)
        self.assertEqual(BorrowDueChange.query.filter_by(borrow_id=borrow.id).count(), 0)

    def test_illegal_statuses_are_rejected_without_writes(self):
        for status in ('pending', 'returned', 'rejected'):
            with self.subTest(status=status):
                borrow = self._create_borrow(status=status)
                response = self._renew(borrow.id, self.owner_token)
                self.assertEqual(response.status_code, 400)
                self.assertIn('只有处于在借/逾期', response.get_json()['message'])
                self._assert_borrow_unchanged(borrow.id, 0, status=status)
                self.assertEqual(
                    BorrowDueChange.query.filter_by(borrow_id=borrow.id).count(), 0
                )

    def test_non_owner_is_rejected_without_writes(self):
        borrow = self._create_borrow()

        response = self._renew(borrow.id, self.other_token)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json()['message'], '无权操作此记录')
        self._assert_borrow_unchanged(borrow.id, 0)
        self.assertEqual(BorrowDueChange.query.filter_by(borrow_id=borrow.id).count(), 0)

    def test_old_renewal_history_is_not_backfilled(self):
        borrow = self._create_borrow(renew_count=1)

        response = self._renew(borrow.id, self.owner_token)

        self.assertEqual(response.status_code, 200)
        changes = BorrowDueChange.query.filter_by(borrow_id=borrow.id).all()
        self.assertEqual([change.change_sequence for change in changes], [2])

    def test_two_connections_serialize_and_revalidate_at_limit(self):
        borrow = self._create_borrow(renew_count=1)
        borrow_id = borrow.id
        db.session.execute(
            select(Borrow).where(Borrow.id == borrow_id).with_for_update()
        ).scalar_one()

        workers_ready = threading.Barrier(3)
        both_lock_attempts = threading.Event()
        attempt_guard = threading.Lock()
        lock_attempt_count = 0
        connection_ids = []
        responses = []
        worker_errors = []

        def observe_lock_attempt(conn, cursor, statement, parameters, context, executemany):
            del conn, cursor, parameters, context, executemany
            nonlocal lock_attempt_count
            normalized = statement.upper()
            if 'FOR UPDATE' not in normalized or 'BORROW' not in normalized:
                return
            with attempt_guard:
                lock_attempt_count += 1
                if lock_attempt_count >= 2:
                    both_lock_attempts.set()

        def concurrent_request():
            with self.app.app_context():
                try:
                    connection_ids.append(
                        db.session.execute(text('SELECT CONNECTION_ID()')).scalar_one()
                    )
                    workers_ready.wait(timeout=5)
                    with self.app.test_client() as client:
                        response = client.put(
                            f'/api/borrows/{borrow_id}/renew',
                            headers=self._auth_header(self.owner_token),
                        )
                    responses.append((response.status_code, response.get_json()))
                except Exception as exc:  # pragma: no cover - asserted below
                    worker_errors.append(exc)
                finally:
                    db.session.remove()

        event.listen(db.engine, 'before_cursor_execute', observe_lock_attempt)
        workers = [threading.Thread(target=concurrent_request) for _ in range(2)]
        for worker in workers:
            worker.start()

        try:
            workers_ready.wait(timeout=5)
            self.assertTrue(
                both_lock_attempts.wait(timeout=5),
                'Both independent requests must reach SELECT ... FOR UPDATE.',
            )
        finally:
            db.session.rollback()
            event.remove(db.engine, 'before_cursor_execute', observe_lock_attempt)

        for worker in workers:
            worker.join(timeout=10)

        self.assertTrue(all(not worker.is_alive() for worker in workers))
        self.assertEqual(worker_errors, [])
        self.assertEqual(len(set(connection_ids)), 2)
        self.assertEqual(sorted(status for status, _ in responses), [200, 400])
        failed_payload = next(payload for status, payload in responses if status == 400)
        self.assertIn('续借次数已达上限', failed_payload['message'])

        db.session.expire_all()
        persisted = db.session.get(Borrow, borrow_id)
        changes = BorrowDueChange.query.filter_by(borrow_id=borrow_id).all()
        self.assertEqual(persisted.renew_count, 2)
        self.assertEqual([change.change_sequence for change in changes], [2])

    def test_due_change_insert_failure_rolls_back_borrow_update(self):
        borrow = self._create_borrow()
        db.session.add(
            BorrowDueChange(
                borrow_id=borrow.id,
                change_sequence=1,
                change_type='RENEW',
                old_due_time=FIXED_DUE_TIME - timedelta(days=1),
                new_due_time=FIXED_DUE_TIME,
                change_time=FIXED_DUE_TIME,
                operator_user_id=self.owner.id,
            )
        )
        db.session.commit()

        response = self._renew(borrow.id, self.owner_token)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.get_json()['message'], '续借失败，请稍后重试')
        self._assert_borrow_unchanged(borrow.id, 0)
        self.assertEqual(BorrowDueChange.query.filter_by(borrow_id=borrow.id).count(), 1)

    def test_borrow_update_failure_rolls_back_due_change(self):
        borrow = self._create_borrow()

        def fail_borrow_update(mapper, connection, target):
            del mapper, connection, target
            raise RuntimeError('simulated Borrow update failure')

        event.listen(Borrow, 'before_update', fail_borrow_update)
        try:
            response = self._renew(borrow.id, self.owner_token)
        finally:
            event.remove(Borrow, 'before_update', fail_borrow_update)

        self.assertEqual(response.status_code, 500)
        self._assert_borrow_unchanged(borrow.id, 0)
        self.assertEqual(BorrowDueChange.query.filter_by(borrow_id=borrow.id).count(), 0)

    def test_commit_failure_rolls_back_both_records(self):
        borrow = self._create_borrow()

        with patch.object(
            db.session, 'commit', side_effect=RuntimeError('simulated commit failure')
        ):
            response = self._renew(borrow.id, self.owner_token)

        self.assertEqual(response.status_code, 500)
        self._assert_borrow_unchanged(borrow.id, 0)
        self.assertEqual(BorrowDueChange.query.filter_by(borrow_id=borrow.id).count(), 0)

    def _create_borrow(self, status='borrowed', renew_count=0):
        borrow = Borrow(
            user_id=self.owner.id,
            book_id=self.book.id,
            status=status,
            borrow_time=FIXED_DUE_TIME - timedelta(days=20),
            due_time=FIXED_DUE_TIME,
            renew_count=renew_count,
        )
        db.session.add(borrow)
        db.session.commit()
        return borrow

    def _renew(self, borrow_id, token):
        with self.app.test_client() as client:
            return client.put(
                f'/api/borrows/{borrow_id}/renew',
                headers=self._auth_header(token),
            )

    @staticmethod
    def _auth_header(token):
        return {'Authorization': f'Bearer {token}'}

    def _assert_borrow_unchanged(self, borrow_id, renew_count, status='borrowed'):
        db.session.expire_all()
        persisted = db.session.get(Borrow, borrow_id)
        self.assertEqual(persisted.renew_count, renew_count)
        self.assertEqual(persisted.status, status)
        self.assertEqual(persisted.due_time, FIXED_DUE_TIME)

    def _cleanup_phase15_rows(self):
        db.session.rollback()
        user_ids = [
            user_id
            for (user_id,) in db.session.query(User.id)
            .filter(User.username.like('P15TEST-%'))
            .all()
        ]
        book_ids = [
            book_id
            for (book_id,) in db.session.query(Book.id)
            .filter(Book.isbn.like('P15TEST-%'))
            .all()
        ]
        borrow_query = db.session.query(Borrow.id)
        if user_ids and book_ids:
            borrow_query = borrow_query.filter(
                (Borrow.user_id.in_(user_ids)) | (Borrow.book_id.in_(book_ids))
            )
        elif user_ids:
            borrow_query = borrow_query.filter(Borrow.user_id.in_(user_ids))
        elif book_ids:
            borrow_query = borrow_query.filter(Borrow.book_id.in_(book_ids))
        else:
            borrow_query = borrow_query.filter(text('1 = 0'))
        borrow_ids = [borrow_id for (borrow_id,) in borrow_query.all()]

        if borrow_ids:
            BorrowDueChange.query.filter(
                BorrowDueChange.borrow_id.in_(borrow_ids)
            ).delete(synchronize_session=False)
            Borrow.query.filter(Borrow.id.in_(borrow_ids)).delete(
                synchronize_session=False
            )
        if user_ids:
            Notification.query.filter(Notification.user_id.in_(user_ids)).delete(
                synchronize_session=False
            )
        if book_ids:
            Book.query.filter(Book.id.in_(book_ids)).delete(synchronize_session=False)
        if user_ids:
            User.query.filter(User.id.in_(user_ids)).delete(synchronize_session=False)
        Category.query.filter(Category.name.like('P15TEST-%')).delete(
            synchronize_session=False
        )
        db.session.commit()


if __name__ == '__main__':
    unittest.main()
