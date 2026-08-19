# Legacy schema fingerprint

`schema_fingerprint.py` is the production V2 migration guard for the twelve
legacy business tables. It reads only SQLAlchemy Inspector metadata and never
reads business rows or executes DDL/DML.

The canonical payload includes table names; column name, type, nullable and
default; primary keys; foreign keys; indexes; and unique constraints. Tables,
metadata lists and JSON keys are deterministically sorted before UTF-8
SHA-256 hashing. It excludes data, row counts, auto-increment counters,
creation timestamps and MySQL runtime metadata.

Run it from `backend`:

```powershell
python tools/schema_fingerprint.py --database smart_library_phase13_test_20260819_1
python tools/schema_fingerprint.py --database smart_library
```

The historical value `e75546ceecfe370c8498aeec7d32d57168083318ae78914311b6bbc9df935499`
is retained as `HISTORICAL_REFERENCE_ONLY`: its original normalization rule was
not committed. The result produced by this tool after matching the Phase 1.3
test database and production database is the authoritative
`PRODUCTION_V2_LEGACY_SCHEMA_BASELINE` for the planned V2 migration.

Current signed baseline:

```text
fingerprint_version: legacy-schema-v1
PRODUCTION_V2_LEGACY_SCHEMA_BASELINE: bf8af85c77c622e57360bec1c4e28267e5639e941fc8b437041f36df013a12e7
```
