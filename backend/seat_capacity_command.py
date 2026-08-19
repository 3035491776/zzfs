# -*- coding: utf-8 -*-
"""Controlled Flask CLI entry point for daily seat-capacity capture."""

from datetime import datetime
import json
import re

import click
from sqlalchemy.engine import URL

from config import Config


DATABASE_NAME_PATTERN = re.compile(r'^[A-Za-z0-9_]+$')


def register_seat_capacity_command(app):
    """Register the Phase 1.4 manual capture command."""
    app.cli.add_command(capture_seat_capacity_command)


@click.command('capture-seat-capacity')
@click.option(
    '--date',
    'capacity_date',
    required=True,
    type=click.DateTime(formats=['%Y-%m-%d']),
    help='Business date in YYYY-MM-DD format.',
)
@click.option('--request-id', required=True, help='Stable external request identity.')
@click.option('--database', required=True, help='Explicit target database name.')
@click.option('--retry-of', type=click.IntRange(min=1), default=None)
def capture_seat_capacity_command(capacity_date, request_id, database, retry_of):
    """Capture one day of seat capacity into an explicitly allowed database."""
    if not DATABASE_NAME_PATTERN.fullmatch(database):
        raise click.ClickException('Invalid database name.')

    from app import create_app
    from services.seat_capacity_service import (
        SeatCapacityError,
        capture_seat_capacity,
    )

    selected_app = create_app(
        {'SQLALCHEMY_DATABASE_URI': _database_uri(database)}
    )
    with selected_app.app_context():
        try:
            outcome = capture_seat_capacity(
                target_date=capacity_date.date(),
                request_identity=request_id,
                allowed_databases=selected_app.config.get(
                    'CAPACITY_CAPTURE_ALLOWED_DATABASES', ()
                ),
                job_type='MANUAL',
                retry_of_job_run_id=retry_of,
            )
        except SeatCapacityError as exc:
            raise click.ClickException(str(exc)) from exc

    click.echo(json.dumps(outcome.to_dict(), ensure_ascii=True, sort_keys=True))


def _database_uri(database):
    return URL.create(
        drivername='mysql+pymysql',
        username=Config.DB_USER,
        password=Config.DB_PASS,
        host=Config.DB_HOST,
        port=int(Config.DB_PORT),
        database=database,
        query={'charset': 'utf8mb4'},
    )
