"""Helpers for running SQL with asyncpg (one statement per execute)."""

from __future__ import annotations

from alembic import op


def split_sql_statements(sql: str) -> list[str]:
    statements: list[str] = []
    buf: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        buf.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(buf))
            buf = []
    if buf:
        statements.append("\n".join(buf))
    return statements


def execute_sql(sql: str) -> None:
    for stmt in split_sql_statements(sql):
        op.execute(stmt)
