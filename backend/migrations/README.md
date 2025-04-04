# Database Migrations

This directory contains database migration scripts managed by Alembic.

## Commands

1. Generate a new migration:
```bash
cd backend
alembic revision --autogenerate -m "description of changes"
```

2. Apply migrations:
```bash
cd backend
alembic upgrade head
```

3. Rollback one migration:
```bash
cd backend
alembic downgrade -1
```

4. Check current migration status:
```bash
cd backend
alembic current
```

5. Check migration history:
```bash
cd backend
alembic history
```

## Important Notes

- Always review autogenerated migrations before applying them
- Test migrations in development before applying to production
- Back up your database before applying migrations in production