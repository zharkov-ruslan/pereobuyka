"""Краткая история /ask per-user для LLM (in-memory, сбрасывается на /start)."""

from __future__ import annotations

# пары user+assistant (role/content), максимум _MAX_REPLIES реплик
_MAX_REPLIES = 20
_history: dict[int, list[dict[str, str]]] = {}


def get_ask_history(user_id: int) -> list[dict[str, str]]:
    return list(_history.get(user_id, []))


def append_ask_turn(user_id: int, user_text: str, assistant_text: str) -> None:
    h = _history.setdefault(user_id, [])
    h.append({"role": "user", "content": user_text})
    h.append({"role": "assistant", "content": assistant_text})
    if len(h) > _MAX_REPLIES:
        del h[0 : len(h) - _MAX_REPLIES]


def clear_ask_history(user_id: int) -> None:
    _history.pop(user_id, None)
