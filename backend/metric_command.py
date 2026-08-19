# -*- coding: utf-8 -*-
"""Small Flask CLI for manual metric runs and backfill."""

from datetime import datetime

import click
from flask import current_app

from services.metric_contract import enumerate_periods
from services.metric_pipeline_service import (
    MetricJobExecutionError,
    MetricJobRequestError,
    run_metric_job,
)


def _parse_value(period_type, value):
    pattern = '%Y-%m-%d' if period_type == 'DAY' else '%Y-%m'
    try:
        return datetime.strptime(value, pattern).date()
    except ValueError as exc:
        raise click.BadParameter(f'expected {pattern}') from exc


def register_metric_command(app):
    @app.cli.command('run-metrics')
    @click.option(
        '--period',
        'period_type',
        type=click.Choice(['day', 'month'], case_sensitive=False),
        required=True,
    )
    @click.option('--start', required=True, help='First day (YYYY-MM-DD) or month (YYYY-MM).')
    @click.option('--end', required=True, help='Last inclusive day or month.')
    @click.option('--request-id', required=True)
    @click.option(
        '--job-type',
        type=click.Choice(['manual', 'backfill', 'retry'], case_sensitive=False),
        default='manual',
        show_default=True,
    )
    @click.option('--retry-of', type=int, default=None)
    def run_metrics(period_type, start, end, request_id, job_type, retry_of):
        normalized = period_type.upper()
        periods = enumerate_periods(
            normalized,
            _parse_value(normalized, start),
            _parse_value(normalized, end),
        )
        try:
            outcome = run_metric_job(
                period_type=normalized,
                periods=periods,
                request_identity=request_id,
                allowed_databases=current_app.config.get(
                    'METRIC_RUN_ALLOWED_DATABASES', ()
                ),
                job_type=job_type.upper(),
                retry_of_job_run_id=retry_of,
            )
        except (MetricJobRequestError, MetricJobExecutionError) as exc:
            raise click.ClickException(str(exc)) from exc

        click.echo(
            f'job_run_id={outcome.job_run_id} status={outcome.status} '
            f'snapshots={outcome.snapshot_row_count} checksum={outcome.result_checksum} '
            f'reused={str(outcome.reused).lower()}'
        )
