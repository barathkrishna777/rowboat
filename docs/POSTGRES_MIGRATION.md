# Migrating from SQLite to PostgreSQL

## Why

SQLite works for single-process local dev, but breaks under concurrent writes
(e.g. Railway multi-worker or parallel swipe requests).  PostgreSQL is the
production target.

## Steps

### 1. Provision a Postgres instance

Railway: add a Postgres plugin. Locally: `docker run -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:16`.

### 2. Set `DATABASE_URL`

```env
# .env or Railway variables
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/rowboat
```

The app reads `DATABASE_URL` via `src/config.py` → SQLAlchemy uses it directly.

### 3. Generate the initial migration

```bash
# Creates alembic/versions/<hash>_initial.py from current models
alembic revision --autogenerate -m "initial"
```

Review the generated file, then apply:

```bash
alembic upgrade head
```

### 4. Ongoing schema changes

1. Edit models in `src/db/tables.py`.
2. `alembic revision --autogenerate -m "describe change"`
3. Review the migration, then `alembic upgrade head`.

### 5. Remove `create_all` in production

Once Alembic manages the schema, you can skip the `Base.metadata.create_all`
call in `src/db/database.py:init_db()` for production.  Keep it for tests
and local SQLite dev.

## Notes

- `asyncpg` is the async driver for Postgres (already in `requirements.txt`).
- `aiosqlite` remains for local dev / tests.
- The `alembic/env.py` reads `DATABASE_URL` from `src.config.settings` so
  credentials are never hard-coded in `alembic.ini`.
