# Database Migrations (Alembic)

This directory contains database migration scripts managed by Alembic.

---

## Prerequisites

Before running migrations, make sure you have:
1. Copied `alembic.ini.example` to `alembic.ini` in the project root directory.
2. Updated the `sqlalchemy.url` connection string in `alembic.ini` with your database credentials:
   ```ini
   sqlalchemy.url = postgresql://username:password@localhost:5432/docsly
   ```

---

## Common Commands

Always run these commands from the **project root directory**.

### 1. Create a New Migration

Generate a new migration script automatically after you change your SQLAlchemy model classes:
```bash
# Windows
$env:PYTHONPATH="."; alembic revision --autogenerate -m "describe your changes"

# Linux / macOS
PYTHONPATH=. alembic revision --autogenerate -m "describe your changes"
```

### 2. Apply Migrations to Database

Upgrade the database schema to the latest version:
```bash
alembic upgrade head
```

### 3. Revert Last Migration

Roll back the database schema by one version:
```bash
alembic downgrade -1
```

### 4. Check Current Status

View the current migration version of the database:
```bash
alembic current
```
