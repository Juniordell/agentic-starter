---
name: postgres
description: >
  SQL patterns, canonical queries, SQLAlchemy ORM, and connection management.
  Auto-activates when writing SQL queries, defining database models,
  or implementing data access layers.
---

# Postgres

## Core principle
Postgres stores facts. Use it for exact, structured queries —
counts, sums, averages, joins. Never use it for meaning-based search.

## SQLAlchemy connection
```python
from sqlalchemy import create_engine, text
from src.project_name.config import get_settings

engine = create_engine(get_settings().database_url)

def execute_query(sql: str) -> list[dict]:
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        return [dict(row._mapping) for row in result]
```

## Canonical query patterns
```python
# Always parameterize — never f-string SQL
result = conn.execute(
    text("SELECT SUM(amount) FROM orders WHERE date >= :start"),
    {"start": start_date}
)
```

## Routing rule
- Revenue, count, average → Postgres (SQL)
- Sentiment, text search → Qdrant

## Negative knowledge
- Do NOT use f-strings for SQL — always use parameterized queries
- Do NOT use ORM for complex analytics — write raw SQL
- Do NOT leave connections open — always use context managers
- Do NOT skip indexes on columns used in WHERE clauses
