#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compute a deterministic fingerprint for the twelve legacy MySQL tables.

This is deliberately a metadata-only read tool.  It neither reads business
rows nor issues DDL/DML, so it can be used before and after a V2 migration to
prove that the legacy schema did not change.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import make_url

from config import Config


LEGACY_TABLES = (
    'access_log',
    'ai_conversation',
    'book',
    'book_request',
    'borrow',
    'category',
    'notification',
    'reservation',
    'seat',
    'seat_repair',
    'sms_log',
    'user',
)


def _json_value(value: Any) -> Any:
    """Return a JSON-safe value without leaking database runtime metadata."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {
            str(key): _json_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    return str(value)


def _stable_sort(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        items,
        key=lambda item: json.dumps(
            item, ensure_ascii=False, sort_keys=True, separators=(',', ':')
        ),
    )


def legacy_schema_metadata(database: str) -> dict[str, Any]:
    """Read and normalize only the stable legacy schema metadata."""
    url = make_url(Config.SQLALCHEMY_DATABASE_URI).set(database=database)
    engine = create_engine(url, pool_pre_ping=True)

    try:
        inspector = inspect(engine)
        present_tables = set(inspector.get_table_names())
        missing_tables = sorted(set(LEGACY_TABLES) - present_tables)
        if missing_tables:
            raise RuntimeError(
                'Missing required legacy tables: ' + ', '.join(missing_tables)
            )

        tables: dict[str, Any] = {}
        for table_name in LEGACY_TABLES:
            columns = _stable_sort([
                {
                    'name': column['name'],
                    'type': str(column['type']),
                    'nullable': bool(column['nullable']),
                    'default': _json_value(column.get('default')),
                }
                for column in inspector.get_columns(table_name)
            ])
            primary_key = sorted(
                inspector.get_pk_constraint(table_name).get(
                    'constrained_columns'
                ) or []
            )
            foreign_keys = _stable_sort([
                {
                    'name': foreign_key.get('name'),
                    'columns': sorted(
                        foreign_key.get('constrained_columns') or []
                    ),
                    'referred_schema': foreign_key.get('referred_schema'),
                    'referred_table': foreign_key.get('referred_table'),
                    'referred_columns': sorted(
                        foreign_key.get('referred_columns') or []
                    ),
                    'options': _json_value(foreign_key.get('options') or {}),
                }
                for foreign_key in inspector.get_foreign_keys(table_name)
            ])
            indexes = _stable_sort([
                {
                    'name': index.get('name'),
                    'columns': sorted(index.get('column_names') or []),
                    'unique': bool(index.get('unique')),
                }
                for index in inspector.get_indexes(table_name)
            ])
            unique_constraints = _stable_sort([
                {
                    'name': constraint.get('name'),
                    'columns': sorted(constraint.get('column_names') or []),
                }
                for constraint in inspector.get_unique_constraints(table_name)
            ])
            tables[table_name] = {
                'columns': columns,
                'primary_key': primary_key,
                'foreign_keys': foreign_keys,
                'indexes': indexes,
                'unique_constraints': unique_constraints,
            }

        return {
            'fingerprint_version': 'legacy-schema-v1',
            'tables': tables,
        }
    finally:
        engine.dispose()


def fingerprint(metadata: dict[str, Any]) -> str:
    payload = json.dumps(
        metadata,
        ensure_ascii=False,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Compute a metadata-only legacy schema fingerprint.'
    )
    parser.add_argument(
        '--database', default=Config.DB_NAME,
        help='Database to inspect; defaults to the configured database.',
    )
    parser.add_argument(
        '--json', action='store_true',
        help='Emit normalized metadata JSON in addition to the hash.',
    )
    args = parser.parse_args()

    try:
        metadata = legacy_schema_metadata(args.database)
    except Exception as exc:  # pragma: no cover - CLI boundary
        print(f'ERROR={exc}', file=sys.stderr)
        return 2

    print(f'DATABASE={args.database}')
    print(f'LEGACY_TABLE_COUNT={len(LEGACY_TABLES)}')
    print(f'LEGACY_SCHEMA_HASH={fingerprint(metadata)}')
    if args.json:
        print(json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
