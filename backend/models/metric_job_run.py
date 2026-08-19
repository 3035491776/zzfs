# -*- coding: utf-8 -*-
"""指标任务运行记录模型。"""

from datetime import datetime

from extensions import db


class MetricJobRun(db.Model):
    """记录一次实际指标计算运行。"""

    __tablename__ = 'metric_job_run'
    __table_args__ = (
        db.UniqueConstraint('run_key', name='uq_metric_job_run_run_key'),
        db.UniqueConstraint('idempotency_key', name='uq_metric_job_run_idempotency_key'),
        db.Index('ix_metric_job_run_status_create_time', 'status', 'create_time'),
        db.Index(
            'ix_metric_job_run_period_range_version_status',
            'period_type', 'requested_start', 'requested_end',
            'calculation_version', 'status',
        ),
        db.Index('ix_metric_job_run_job_name_create_time', 'job_name', 'create_time'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci',
        },
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='任务运行ID')
    run_key = db.Column(db.String(36), nullable=False, comment='对外任务标识')
    idempotency_key = db.Column(db.String(64), nullable=False, comment='请求幂等键')
    job_name = db.Column(db.String(64), nullable=False, comment='任务名称')
    job_type = db.Column(db.String(20), nullable=False, comment='任务类型')
    period_type = db.Column(db.String(16), nullable=False, comment='周期粒度')
    requested_start = db.Column(db.DateTime, nullable=False, comment='请求范围开始时间')
    requested_end = db.Column(db.DateTime, nullable=False, comment='请求范围结束时间')
    engine = db.Column(db.String(16), nullable=False, default='PYTHON', comment='计算引擎')
    calculation_version = db.Column(db.String(40), nullable=False, comment='计算版本')
    business_timezone = db.Column(
        db.String(64), nullable=False, default='Asia/Shanghai', comment='业务时区'
    )
    status = db.Column(db.String(16), nullable=False, default='PENDING', comment='任务状态')
    requested_by_user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id', ondelete='SET NULL'),
        nullable=True,
        comment='手工任务发起用户ID',
    )
    retry_of_job_run_id = db.Column(
        db.Integer,
        db.ForeignKey('metric_job_run.id'),
        nullable=True,
        comment='被重试的任务运行ID',
    )
    create_time = db.Column(db.DateTime, nullable=False, default=datetime.now, comment='创建时间')
    start_time = db.Column(db.DateTime, nullable=True, comment='开始时间')
    finish_time = db.Column(db.DateTime, nullable=True, comment='结束时间')
    input_row_count = db.Column(db.BigInteger, nullable=True, comment='参与计算的逻辑事实行数')
    snapshot_row_count = db.Column(db.Integer, nullable=True, comment='发布的快照行数')
    result_checksum = db.Column(db.String(64), nullable=True, comment='规范化结果校验值')
    error_type = db.Column(db.String(100), nullable=True, comment='错误类型')
    error_summary = db.Column(db.String(1000), nullable=True, comment='脱敏错误摘要')
