"""Общие утилиты пакета pereobuyka."""

from datetime import datetime


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    """Вернуть True, если интервалы [a_start, a_end) и [b_start, b_end) пересекаются."""
    return a_start < b_end and a_end > b_start
