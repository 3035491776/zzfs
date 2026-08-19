"""create phase1 metric tables

Revision ID: cb66160115ed
Revises: 013276c226a7
Create Date: 2026-08-19 14:05:59.772978

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cb66160115ed'
down_revision = '013276c226a7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'metric_job_run',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='任务运行ID'),
        sa.Column('run_key', sa.String(length=36), nullable=False, comment='对外任务标识'),
        sa.Column('idempotency_key', sa.String(length=64), nullable=False, comment='请求幂等键'),
        sa.Column('job_name', sa.String(length=64), nullable=False, comment='任务名称'),
        sa.Column('job_type', sa.String(length=20), nullable=False, comment='任务类型'),
        sa.Column('period_type', sa.String(length=16), nullable=False, comment='周期粒度'),
        sa.Column('requested_start', sa.DateTime(), nullable=False, comment='请求范围开始时间'),
        sa.Column('requested_end', sa.DateTime(), nullable=False, comment='请求范围结束时间'),
        sa.Column('engine', sa.String(length=16), nullable=False, comment='计算引擎'),
        sa.Column('calculation_version', sa.String(length=40), nullable=False, comment='计算版本'),
        sa.Column('business_timezone', sa.String(length=64), nullable=False, comment='业务时区'),
        sa.Column('status', sa.String(length=16), nullable=False, comment='任务状态'),
        sa.Column('requested_by_user_id', sa.Integer(), nullable=True, comment='手工任务发起用户ID'),
        sa.Column('retry_of_job_run_id', sa.Integer(), nullable=True, comment='被重试的任务运行ID'),
        sa.Column('create_time', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('start_time', sa.DateTime(), nullable=True, comment='开始时间'),
        sa.Column('finish_time', sa.DateTime(), nullable=True, comment='结束时间'),
        sa.Column('input_row_count', sa.BigInteger(), nullable=True, comment='参与计算的逻辑事实行数'),
        sa.Column('snapshot_row_count', sa.Integer(), nullable=True, comment='发布的快照行数'),
        sa.Column('result_checksum', sa.String(length=64), nullable=True, comment='规范化结果校验值'),
        sa.Column('error_type', sa.String(length=100), nullable=True, comment='错误类型'),
        sa.Column('error_summary', sa.String(length=1000), nullable=True, comment='脱敏错误摘要'),
        sa.ForeignKeyConstraint(
            ['requested_by_user_id'], ['user.id'], ondelete='SET NULL'
        ),
        sa.ForeignKeyConstraint(
            ['retry_of_job_run_id'], ['metric_job_run.id']
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key', name='uq_metric_job_run_idempotency_key'),
        sa.UniqueConstraint('run_key', name='uq_metric_job_run_run_key'),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index(
        'ix_metric_job_run_status_create_time',
        'metric_job_run',
        ['status', 'create_time'],
        unique=False,
    )
    op.create_index(
        'ix_metric_job_run_period_range_version_status',
        'metric_job_run',
        ['period_type', 'requested_start', 'requested_end', 'calculation_version', 'status'],
        unique=False,
    )
    op.create_index(
        'ix_metric_job_run_job_name_create_time',
        'metric_job_run',
        ['job_name', 'create_time'],
        unique=False,
    )

    op.create_table(
        'metric_snapshot',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='指标快照ID'),
        sa.Column('job_run_id', sa.Integer(), nullable=False, comment='任务运行ID'),
        sa.Column('metric_code', sa.String(length=64), nullable=False, comment='指标编码'),
        sa.Column('period_type', sa.String(length=16), nullable=False, comment='周期粒度'),
        sa.Column('period_start', sa.DateTime(), nullable=False, comment='周期开始时间'),
        sa.Column('period_end', sa.DateTime(), nullable=False, comment='周期结束时间'),
        sa.Column('temporal_type', sa.String(length=16), nullable=False, comment='POINT或INTERVAL'),
        sa.Column('as_of_time', sa.DateTime(), nullable=True, comment='时点指标统计时点'),
        sa.Column('scope_type', sa.String(length=32), nullable=False, comment='统计范围类型'),
        sa.Column('scope_key', sa.String(length=128), nullable=False, comment='统计范围标识'),
        sa.Column('dimension_type', sa.String(length=32), nullable=False, comment='维度类型'),
        sa.Column('dimension_key', sa.String(length=128), nullable=False, comment='维度标识'),
        sa.Column('metric_value', sa.Numeric(precision=20, scale=6), nullable=True, comment='指标原始值'),
        sa.Column('unit', sa.String(length=16), nullable=False, comment='指标单位'),
        sa.Column('rank_value', sa.Integer(), nullable=True, comment='DENSE_RANK排名'),
        sa.Column('dimension_payload', sa.Text(), nullable=True, comment='规范化展示元数据JSON'),
        sa.Column('quality_status', sa.String(length=20), nullable=False, comment='数据质量状态'),
        sa.Column('quality_reason', sa.String(length=255), nullable=True, comment='数据质量原因'),
        sa.Column('coverage_ratio', sa.Numeric(precision=7, scale=6), nullable=True, comment='数据覆盖率'),
        sa.Column('calculation_version', sa.String(length=40), nullable=False, comment='计算版本'),
        sa.Column('generated_time', sa.DateTime(), nullable=False, comment='结果生成时间'),
        sa.ForeignKeyConstraint(
            ['job_run_id'], ['metric_job_run.id'], ondelete='RESTRICT'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'job_run_id', 'metric_code', 'period_type', 'period_start', 'period_end',
            'scope_type', 'scope_key', 'dimension_type', 'dimension_key',
            name='uq_metric_snapshot_job_metric_period_scope_dimension',
        ),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index(
        'ix_metric_snapshot_period_version_job',
        'metric_snapshot',
        ['period_type', 'period_start', 'period_end', 'calculation_version', 'job_run_id'],
        unique=False,
    )
    op.create_index(
        'ix_metric_snapshot_metric_period_version',
        'metric_snapshot',
        ['metric_code', 'period_type', 'period_start', 'calculation_version'],
        unique=False,
    )
    op.create_index(
        'ix_metric_snapshot_job_metric_rank',
        'metric_snapshot',
        ['job_run_id', 'metric_code', 'rank_value'],
        unique=False,
    )

    op.create_table(
        'seat_capacity_snapshot',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='容量快照ID'),
        sa.Column('capacity_date', sa.Date(), nullable=False, comment='容量所属日期'),
        sa.Column('service_start', sa.Time(), nullable=False, comment='服务开始时间'),
        sa.Column('service_end', sa.Time(), nullable=False, comment='服务结束时间'),
        sa.Column('total_seat_count', sa.Integer(), nullable=False, comment='当日总座位数'),
        sa.Column('serviceable_seat_count', sa.Integer(), nullable=False, comment='当日可预约座位数'),
        sa.Column('capacity_minutes', sa.BigInteger(), nullable=False, comment='当日可预约容量分钟'),
        sa.Column('quality_status', sa.String(length=20), nullable=False, comment='数据质量状态'),
        sa.Column('quality_reason', sa.String(length=255), nullable=True, comment='数据质量原因'),
        sa.Column('job_run_id', sa.Integer(), nullable=False, comment='任务运行ID'),
        sa.Column('captured_time', sa.DateTime(), nullable=False, comment='容量捕获时间'),
        sa.ForeignKeyConstraint(
            ['job_run_id'], ['metric_job_run.id'], ondelete='RESTRICT'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'job_run_id', 'capacity_date', name='uq_seat_capacity_snapshot_job_date'
        ),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index(
        'ix_seat_capacity_snapshot_date_job',
        'seat_capacity_snapshot',
        ['capacity_date', 'job_run_id'],
        unique=False,
    )

    op.create_table(
        'borrow_due_change',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='到期时间变更ID'),
        sa.Column('borrow_id', sa.Integer(), nullable=False, comment='借阅记录ID'),
        sa.Column('change_sequence', sa.Integer(), nullable=False, comment='借阅内变更序号'),
        sa.Column('change_type', sa.String(length=20), nullable=False, comment='变更类型'),
        sa.Column('old_due_time', sa.DateTime(), nullable=False, comment='变更前到期时间'),
        sa.Column('new_due_time', sa.DateTime(), nullable=False, comment='变更后到期时间'),
        sa.Column('change_time', sa.DateTime(), nullable=False, comment='实际变更时间'),
        sa.Column('operator_user_id', sa.Integer(), nullable=True, comment='操作用户ID'),
        sa.ForeignKeyConstraint(
            ['borrow_id'], ['borrow.id'], ondelete='RESTRICT'
        ),
        sa.ForeignKeyConstraint(
            ['operator_user_id'], ['user.id'], ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'borrow_id', 'change_sequence', name='uq_borrow_due_change_borrow_sequence'
        ),
        mysql_engine='InnoDB',
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci',
    )
    op.create_index(
        'ix_borrow_due_change_borrow_time',
        'borrow_due_change',
        ['borrow_id', 'change_time'],
        unique=False,
    )


def downgrade():
    op.drop_table('borrow_due_change')
    op.drop_table('seat_capacity_snapshot')
    op.drop_table('metric_snapshot')
    op.drop_table('metric_job_run')
