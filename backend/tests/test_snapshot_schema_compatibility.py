# -*- coding: utf-8 -*-
"""Regression tests for running Snapshot-backed APIs on the legacy schema."""

from datetime import date, datetime, time
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from sqlalchemy import inspect

from app import create_app
from extensions import db
from models import Book, Borrow, Category, Reservation, Seat, User
from utils.jwt_utils import create_token


LEGACY_TABLES = (
    'user', 'category', 'seat', 'sms_log', 'book', 'borrow', 'reservation',
    'notification', 'ai_conversation', 'access_log', 'book_request', 'seat_repair',
)


class SnapshotSchemaCompatibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = TemporaryDirectory()
        database_path = Path(cls.temp_dir.name) / 'legacy-smart-library.db'
        cls.app = create_app({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{database_path.as_posix()}',
        })
        cls.context = cls.app.app_context()
        cls.context.push()

        legacy_metadata = [db.metadata.tables[name] for name in LEGACY_TABLES]
        db.metadata.create_all(bind=db.engine, tables=legacy_metadata)
        cls.table_names = set(inspect(db.engine).get_table_names())
        if cls.table_names != set(LEGACY_TABLES):
            raise AssertionError('Compatibility test must use exactly the legacy 12-table schema.')

        admin = User(
            username='legacy-admin', password='unused', real_name='旧库管理员',
            role='admin', status='active',
        )
        category = Category(name='旧库分类', is_deleted=False)
        seat = Seat(
            seat_number='LEGACY-001', room_name='旧库阅览室', floor=1,
            status='available', has_power=True,
        )
        db.session.add_all([admin, category, seat])
        db.session.flush()
        book = Book(
            title='旧库图书', author='旧库作者', isbn='LEGACY-ISBN-001',
            stock=3, category_id=category.id, is_deleted=False,
        )
        db.session.add(book)
        db.session.flush()
        db.session.add_all([
            Borrow(
                user_id=admin.id, book_id=book.id, status='borrowed',
                borrow_time=datetime(2026, 8, 1, 9),
                due_time=datetime(2026, 9, 1, 9),
            ),
            Reservation(
                user_id=admin.id, seat_id=seat.id, date=date.today(),
                start_time=time(9), end_time=time(10), status='reserved',
            ),
        ])
        db.session.commit()
        cls.admin_token = create_token(admin.id, admin.username, admin.role)

    @classmethod
    def tearDownClass(cls):
        db.session.remove()
        db.engine.dispose()
        cls.context.pop()
        cls.temp_dir.cleanup()

    def test_legacy_schema_dashboard_uses_realtime_fallback(self):
        self.assertNotIn('metric_snapshot', self.table_names)
        self.assertNotIn('metric_job_run', self.table_names)
        headers = {'Authorization': f'Bearer {self.admin_token}'}

        with self.app.test_client() as client:
            response = client.get('/api/dashboard/stats', headers=headers)

        self.assertEqual(response.status_code, 200)
        data = response.get_json()['data']
        self.assertEqual(data['source'], 'realtime_fallback')
        self.assertEqual(data['total_stock'], 3)
        self.assertEqual(data['total_borrowed'], 1)

    def test_legacy_schema_monthly_and_ai_report_are_snapshot_unavailable(self):
        headers = {'Authorization': f'Bearer {self.admin_token}'}

        with patch('api.report_api.generate_monthly_report_analysis') as generate_analysis:
            with self.app.test_client() as client:
                monthly = client.get(
                    '/api/reports/monthly?month=2026-08', headers=headers
                )
                ai_report = client.post(
                    '/api/reports/monthly/ai-analysis',
                    json={'month': '2026-08'},
                    headers=headers,
                )

        for response in (monthly, ai_report):
            self.assertEqual(response.status_code, 404)
            self.assertEqual(
                response.get_json()['data']['source'], 'snapshot_unavailable'
            )
        generate_analysis.assert_not_called()


if __name__ == '__main__':
    unittest.main()
