# -*- coding: utf-8 -*-
"""Borrow renewal transaction with due-time history and row locking."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select

from extensions import db
from models.borrow import Borrow
from models.borrow_due_change import BorrowDueChange


class RenewalRuleError(Exception):
    """A renewal request that violates the existing API business rules."""

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


class RenewalPersistenceError(Exception):
    """A renewal that could not be atomically persisted."""


@dataclass(frozen=True)
class RenewalResult:
    borrow: Borrow
    due_change: BorrowDueChange


def renew_borrow_record(
    borrow_id,
    operator_user_id,
    *,
    max_renew_count,
    borrow_days,
    now_provider=datetime.now,
):
    """Lock, revalidate, record and update one renewal in a single transaction."""
    try:
        borrow = db.session.execute(
            select(Borrow)
            .where(Borrow.id == borrow_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        ).scalar_one_or_none()

        if borrow is None:
            raise RenewalRuleError('借阅记录不存在', status_code=404)
        if borrow.user_id != operator_user_id:
            raise RenewalRuleError('无权操作此记录', status_code=403)
        if borrow.status not in ('borrowed', 'overdue'):
            raise RenewalRuleError('只有处于在借/逾期的图书可续借')

        renew_count_before = borrow.renew_count or 0
        if renew_count_before >= max_renew_count:
            raise RenewalRuleError(f'续借次数已达上限（{max_renew_count}次）')
        if borrow.due_time is None:
            raise RenewalPersistenceError('借阅记录缺少原到期时间')

        change_time = now_provider()
        renew_count_after = renew_count_before + 1
        new_due_time = change_time + timedelta(days=borrow_days)
        due_change = BorrowDueChange(
            borrow_id=borrow.id,
            change_sequence=renew_count_after,
            change_type='RENEW',
            old_due_time=borrow.due_time,
            new_due_time=new_due_time,
            change_time=change_time,
            operator_user_id=operator_user_id,
        )

        db.session.add(due_change)
        borrow.due_time = new_due_time
        borrow.renew_count = renew_count_after
        borrow.status = 'borrowed'
        db.session.commit()

        return RenewalResult(borrow=borrow, due_change=due_change)
    except RenewalRuleError:
        db.session.rollback()
        raise
    except RenewalPersistenceError:
        db.session.rollback()
        raise
    except Exception as exc:
        db.session.rollback()
        raise RenewalPersistenceError('续借事务提交失败') from exc
