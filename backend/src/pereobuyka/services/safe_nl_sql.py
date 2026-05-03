"""Ограниченное чтение БД для админского NL→SQL: только SELECT, белый список таблиц."""

from __future__ import annotations

import re

import sqlglot
from sqlglot import exp

ALLOWED_TABLES = frozenset(
    {
        "users",
        "services",
        "schedule_rules",
        "schedule_exceptions",
        "appointment_services",
        "appointments",
        "visits",
        "visit_lines",
        "bonus_accounts",
        "bonus_transactions",
        "loyalty_settings",
        "faq_entries",
        "consultation_messages",
    }
)

_FORBIDDEN_MODIFIERS = re.compile(
    r"\b(FOR\s+(UPDATE|NO\s+KEY\s+UPDATE|SHARE|KEY\s+SHARE))\b",
    re.IGNORECASE,
)

_DANGEROUS_FUNCTIONS = frozenset(
    {
        "pg_sleep",
        "pg_read_file",
        "pg_write_file",
        "pg_ls_dir",
        "dblink_connect",
        "dblink_exec",
        "dblink_open",
    }
)


class SafeNlSqlError(ValueError):
    """Запрос не прошёл проверку безопасности."""


def nl_sql_schema_doc() -> str:
    """Краткое описание схемы для промпта модели (public, операционные таблицы)."""
    return """Схема public (PostgreSQL), только для SELECT:
- users(id uuid PK, name text, phone text, role text, telegram_id bigint, telegram_username text,
  registered_at timestamptz, source text)
- services(id uuid PK, name text, description text, price numeric, duration_minutes int,
  is_active boolean)
- schedule_rules(id uuid PK, weekday smallint, start_time time, end_time time, is_day_off boolean)
- schedule_exceptions(id uuid PK, exception_date date, start_time time, end_time time,
  is_day_off boolean)
- appointments(id uuid PK, user_id uuid FK users, starts_at timestamptz, ends_at timestamptz,
  total_price numeric, status text, created_at timestamptz, source text, discount_percent smallint,
  created_by_user_id uuid FK users nullable)
- appointment_services(appointment_id uuid FK appointments, service_id uuid FK services,
  quantity int, составной PK)
- visits(id uuid PK, appointment_id uuid FK appointments unique, total_amount numeric,
  bonus_spent int, bonus_earned int, confirmed_at timestamptz, confirmed_by_user_id uuid FK users,
  client_rating_stars smallint, client_rating_comment text, service_rating_stars smallint,
  service_rating_comment text)
- visit_lines(visit_id uuid FK visits, service_id uuid FK services, quantity int, составной PK)
- bonus_accounts(id uuid PK, user_id uuid FK users unique, balance int)
- bonus_transactions(id uuid PK, account_id uuid FK bonus_accounts, type text, amount int,
  visit_id uuid FK visits nullable, created_at timestamptz, comment text)
- loyalty_settings(id smallint PK, max_bonus_spend_percent smallint,
  earn_percent_after_visit smallint)
- faq_entries(id uuid PK, question text, answer text, is_active boolean)
- consultation_messages(id uuid PK, user_id uuid FK users, role text, content text,
  created_at timestamptz, request_id uuid nullable)
"""


def _strip_single_statement(raw: str) -> str:
    s = raw.strip().rstrip(";")
    if _FORBIDDEN_MODIFIERS.search(s):
        raise SafeNlSqlError("Запрещён блокировочный режим FOR UPDATE / FOR SHARE")
    return s


def _assert_select_statement(expr: exp.Expression) -> None:
    if isinstance(expr, exp.Select):
        return
    if isinstance(expr, exp.Union):
        _assert_select_statement(expr.this)
        _assert_select_statement(expr.expression)
        return
    raise SafeNlSqlError("Разрешён только SELECT (включая UNION и WITH … SELECT)")


def _forbidden_dml_types() -> tuple[type[exp.Expression], ...]:
    types_: list[type[exp.Expression]] = []
    for name in (
        "Insert",
        "Update",
        "Delete",
        "Drop",
        "Create",
        "Alter",
        "Truncate",
        "Merge",
        "Copy",
        "Command",
    ):
        cls = getattr(exp, name, None)
        if cls is not None:
            types_.append(cls)
    return tuple(types_)


def _identifier_name(node: exp.Expression | None) -> str | None:
    if node is None:
        return None
    if isinstance(node, exp.Identifier):
        return str(node.this).lower()
    if isinstance(node, str):
        return node.lower()
    return str(node).lower()


def _check_allowed_tables(expr: exp.Expression) -> None:
    for table in expr.find_all(exp.Table):
        schema = _identifier_name(table.args.get("db"))
        if schema and schema not in ("public", ""):
            raise SafeNlSqlError(f"Недопустимая схема таблицы: {schema}")
        tname = _identifier_name(table.this)
        if not tname:
            raise SafeNlSqlError("Не удалось определить имя таблицы")
        if tname not in ALLOWED_TABLES:
            raise SafeNlSqlError(f"Таблица не в белом списке: {tname}")


def _check_dangerous_functions(expr: exp.Expression) -> None:
    for fn in expr.find_all(exp.Anonymous):
        name = str(fn.this).lower() if fn.this is not None else ""
        if name in _DANGEROUS_FUNCTIONS:
            raise SafeNlSqlError(f"Запрещённая функция: {name}")
    for fn in expr.find_all(exp.Func):
        raw = fn.sql_name()
        if raw and raw.lower() in _DANGEROUS_FUNCTIONS:
            raise SafeNlSqlError(f"Запрещённая функция: {raw.lower()}")


def validate_and_normalize_select(raw_sql: str) -> str:
    """Проверить AST и вернуть нормализованный SELECT одной инструкцией."""
    sql = _strip_single_statement(raw_sql)
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except sqlglot.errors.ParseError as e:
        raise SafeNlSqlError(f"Синтаксис SQL не распознан: {e!s}") from e
    if len(statements) != 1:
        raise SafeNlSqlError("Допускается ровно один SQL-запрос")
    stmt = statements[0]
    _assert_select_statement(stmt)
    for cls in _forbidden_dml_types():
        if stmt.find(cls):
            raise SafeNlSqlError("Обнаружены запрещённые операции (не SELECT)")
    _check_allowed_tables(stmt)
    _check_dangerous_functions(stmt)
    return stmt.sql(dialect="postgres")


def wrap_with_limit(inner_sql: str, *, limit: int) -> str:
    """Обёртка с верхней границей строк (limit уже проверен как положительное целое)."""
    cap = max(1, int(limit))
    return f"SELECT * FROM ({inner_sql}) AS _nlq_sub LIMIT {cap + 1}"
