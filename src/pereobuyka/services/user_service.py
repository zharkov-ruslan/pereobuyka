from __future__ import annotations

from datetime import datetime, timezone

from pereobuyka.models.user import User


class UserService:
    def __init__(self) -> None:
        self._users_by_telegram_id: dict[int, User] = {}

    def get_or_create(self, telegram_user_id: int) -> User:
        existing = self._users_by_telegram_id.get(telegram_user_id)
        if existing is not None:
            return existing

        user = User(
            telegram_user_id=telegram_user_id,
            created_at=datetime.now(tz=timezone.utc),
        )
        self._users_by_telegram_id[telegram_user_id] = user
        return user

