# -*- coding: utf-8 -*-
"""指标快照模型。"""

from datetime import datetime

from extensions import db
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.sql.dml import Delete, Update
from sqlalchemy.sql.elements import TextClause


class MetricSnapshot(db.Model):
    """保存一次任务发布的一条不可变指标结果。"""

    __tablename__ = 'metric_snapshot'
    __table_args__ = (
        db.UniqueConstraint(
            'job_run_id', 'metric_code', 'period_type', 'period_start', 'period_end',
            'scope_type', 'scope_key', 'dimension_type', 'dimension_key',
            name='uq_metric_snapshot_job_metric_period_scope_dimension',
        ),
        db.Index(
            'ix_metric_snapshot_period_version_job',
            'period_type', 'period_start', 'period_end', 'calculation_version', 'job_run_id',
        ),
        db.Index(
            'ix_metric_snapshot_metric_period_version',
            'metric_code', 'period_type', 'period_start', 'calculation_version',
        ),
        db.Index(
            'ix_metric_snapshot_job_metric_rank',
            'job_run_id', 'metric_code', 'rank_value',
        ),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci',
        },
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='指标快照ID')
    job_run_id = db.Column(
        db.Integer,
        db.ForeignKey('metric_job_run.id', ondelete='RESTRICT'),
        nullable=False,
        comment='任务运行ID',
    )
    metric_code = db.Column(db.String(64), nullable=False, comment='指标编码')
    period_type = db.Column(db.String(16), nullable=False, comment='周期粒度')
    period_start = db.Column(db.DateTime, nullable=False, comment='周期开始时间')
    period_end = db.Column(db.DateTime, nullable=False, comment='周期结束时间')
    temporal_type = db.Column(db.String(16), nullable=False, comment='POINT或INTERVAL')
    as_of_time = db.Column(db.DateTime, nullable=True, comment='时点指标统计时点')
    scope_type = db.Column(db.String(32), nullable=False, default='ALL', comment='统计范围类型')
    scope_key = db.Column(db.String(128), nullable=False, default='ALL', comment='统计范围标识')
    dimension_type = db.Column(db.String(32), nullable=False, default='ALL', comment='维度类型')
    dimension_key = db.Column(db.String(128), nullable=False, default='ALL', comment='维度标识')
    metric_value = db.Column(db.Numeric(20, 6), nullable=True, comment='指标原始值')
    unit = db.Column(db.String(16), nullable=False, comment='指标单位')
    rank_value = db.Column(db.Integer, nullable=True, comment='DENSE_RANK排名')
    dimension_payload = db.Column(db.Text, nullable=True, comment='规范化展示元数据JSON')
    quality_status = db.Column(
        db.String(20), nullable=False, default='EXACT', comment='数据质量状态'
    )
    quality_reason = db.Column(db.String(255), nullable=True, comment='数据质量原因')
    coverage_ratio = db.Column(db.Numeric(7, 6), nullable=True, comment='数据覆盖率')
    calculation_version = db.Column(db.String(40), nullable=False, comment='计算版本')
    generated_time = db.Column(
        db.DateTime, nullable=False, default=datetime.now, comment='结果生成时间'
    )


@event.listens_for(MetricSnapshot, 'before_update')
def _prevent_metric_snapshot_update(mapper, connection, target):
    del mapper, connection, target
    raise RuntimeError('Published MetricSnapshot rows are immutable')


@event.listens_for(MetricSnapshot, 'before_delete')
def _prevent_metric_snapshot_delete(mapper, connection, target):
    del mapper, connection, target
    raise RuntimeError('Published MetricSnapshot rows are immutable')


@event.listens_for(Engine, 'before_execute')
def _prevent_metric_snapshot_bulk_mutation(
    connection, clauseelement, multiparams, params, execution_options
):
    del connection, multiparams, params, execution_options
    if isinstance(clauseelement, (Update, Delete)):
        table = getattr(clauseelement, 'table', None)
        if table is not None and table.name == 'metric_snapshot':
            raise RuntimeError('Published MetricSnapshot rows are immutable')
    if isinstance(clauseelement, TextClause):
        normalized = ' '.join(clauseelement.text.lower().split())
        if (
            normalized.startswith('update metric_snapshot')
            or normalized.startswith('delete from metric_snapshot')
        ):
            raise RuntimeError('Published MetricSnapshot rows are immutable')
