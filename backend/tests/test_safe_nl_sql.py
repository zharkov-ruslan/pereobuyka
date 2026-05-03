"""Тесты валидатора NL→SQL (без LLM и без БД)."""

from __future__ import annotations

import pytest

from pereobuyka.services.safe_nl_sql import (
    SafeNlSqlError,
    validate_and_normalize_select,
    wrap_with_limit,
)


def test_validate_select_simple() -> None:
    sql = validate_and_normalize_select("SELECT id FROM users LIMIT 5")
    assert "users" in sql.lower()


def test_validate_rejects_insert() -> None:
    with pytest.raises(SafeNlSqlError):
        validate_and_normalize_select(
            "INSERT INTO users (id, name) VALUES (gen_random_uuid(), 'x')"
        )


def test_validate_rejects_second_statement() -> None:
    with pytest.raises(SafeNlSqlError):
        validate_and_normalize_select("SELECT 1; SELECT 2")


def test_validate_rejects_unknown_table() -> None:
    with pytest.raises(SafeNlSqlError):
        validate_and_normalize_select("SELECT * FROM alembic_version")


def test_validate_rejects_non_public_schema() -> None:
    with pytest.raises(SafeNlSqlError):
        validate_and_normalize_select('SELECT * FROM "information_schema"."tables"')


def test_validate_rejects_for_update() -> None:
    with pytest.raises(SafeNlSqlError):
        validate_and_normalize_select("SELECT id FROM users FOR UPDATE")


def test_validate_rejects_pg_sleep() -> None:
    with pytest.raises(SafeNlSqlError):
        validate_and_normalize_select("SELECT pg_sleep(10)")


def test_wrap_with_limit() -> None:
    w = wrap_with_limit("SELECT 1 AS a", limit=10)
    assert "LIMIT 11" in w
    assert "_nlq_sub" in w
