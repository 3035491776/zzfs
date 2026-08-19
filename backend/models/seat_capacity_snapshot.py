# -*- coding: utf-8 -*-
"""每日座位可预约容量历史事实模型。"""

from datetime import datetime

from extensions import db


class SeatCapacitySnapshot(db.Model):
    """保存每日可预约容量的一个不可变版本。"""

    __tablename__ = 'seat_capacity_snapshot'
    __table_args__ = (
        db.UniqueConstraint(
            'job_run_id', 'capacity_date', name='uq_seat_capacity_snapshot_job_date'
        ),
        db.Index(
            'ix_seat_capacity_snapshot_date_job', 'capacity_date', 'job_run_id'
        ),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci',
        },
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='容量快照ID')
    capacity_date = db.Column(db.Date, nullable=False, comment='容量所属日期')
    service_start = db.Column(db.Time, nullable=False, comment='服务开始时间')
    service_end = db.Column(db.Time, nullable=False, comment='服务结束时间')
    total_seat_count = db.Column(db.Integer, nullable=False, comment='当日总座位数')
    serviceable_seat_count = db.Column(db.Integer, nullable=False, comment='当日可预约座位数')
    capacity_minutes = db.Column(db.BigInteger, nullable=False, comment='当日可预约容量分钟')
    quality_status = db.Column(
        db.String(20), nullable=False, default='EXACT', comment='数据质量状态'
    )
    quality_reason = db.Column(db.String(255), nullable=True, comment='数据质量原因')
    job_run_id = db.Column(
        db.Integer,
        db.ForeignKey('metric_job_run.id', ondelete='RESTRICT'),
        nullable=False,
        comment='任务运行ID',
    )
    captured_time = db.Column(
        db.DateTime, nullable=False, default=datetime.now, comment='容量捕获时间'
    )
