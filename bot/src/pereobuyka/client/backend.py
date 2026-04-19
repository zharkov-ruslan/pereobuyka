"""HTTP-клиент к Переобуйка Backend API."""

from __future__ import annotations

import logging
from datetime import date
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)


class BackendError(Exception):
    """Ошибка, возвращённая backend API."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(f"[{status_code}] {code}: {message}")


class BackendUnavailableError(BackendError):
    """Backend недоступен (сетевая ошибка или таймаут)."""

    def __init__(self) -> None:
        super().__init__(0, "BACKEND_UNAVAILABLE", "Сервис временно недоступен")


class BackendClient:
    """Асинхронный клиент к backend API.

    Создаётся один раз при запуске бота, передаётся в handlers через DI aiogram.
    Используйте :meth:`for_user` для запросов, требующих авторизации.
    """

    def __init__(self, base_url: str, bot_secret: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._bot_secret = bot_secret
        self._http = httpx.AsyncClient(timeout=10.0)

    async def close(self) -> None:
        """Закрыть HTTP-сессию."""
        await self._http.aclose()

    def for_user(self, telegram_user_id: int) -> _UserClient:
        """Вернуть клиент с привязкой к конкретному пользователю Telegram."""
        return _UserClient(self._http, self._base_url, self._bot_secret, telegram_user_id)

    async def get_services(self) -> list[dict]:
        """Получить каталог активных услуг."""
        result = await self._get("/api/v1/services", headers={})
        if not isinstance(result, dict):
            return []
        items = result.get("items")
        return items if isinstance(items, list) else []

    async def _get(self, path: str, headers: dict[str, str]) -> list[dict] | dict:
        try:
            response = await self._http.get(
                f"{self._base_url}{path}",
                headers=headers,
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning("Backend unavailable: %s", exc)
            raise BackendUnavailableError from exc
        return _parse_response(response)


def _user_auth_headers(bot_secret: str, telegram_user_id: int) -> dict[str, str]:
    """Заголовки для backend: без пустого ``Bearer `` (httpx: illegal header value)."""
    secret = bot_secret.strip()
    if not secret:
        return {}
    return {
        "Authorization": f"Bearer {secret}",
        "X-Telegram-User-Id": str(telegram_user_id),
    }


class _UserClient:
    """Клиент для запросов, привязанных к конкретному пользователю."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        base_url: str,
        bot_secret: str,
        telegram_user_id: int,
    ) -> None:
        self._http = http
        self._base_url = base_url
        self._headers = _user_auth_headers(bot_secret, telegram_user_id)

    async def get_slots(
        self,
        date_from: date,
        date_to: date,
        service_ids: list[UUID],
    ) -> list[dict]:
        """Получить свободные временные окна."""
        # Тип значений в tuple совместим с ожиданием httpx.AsyncClient.get(params=...)
        params: list[tuple[str, str | int | float | bool | None]] = [
            ("date_from", str(date_from)),
            ("date_to", str(date_to)),
        ]
        for sid in service_ids:
            params.append(("service_ids", str(sid)))
        try:
            response = await self._http.get(
                f"{self._base_url}/api/v1/slots",
                headers=self._headers,
                params=params,
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning("Backend unavailable: %s", exc)
            raise BackendUnavailableError from exc
        result = _parse_response(response)
        if not isinstance(result, dict):
            return []
        items = result.get("items")
        return items if isinstance(items, list) else []

    async def create_appointment(
        self,
        starts_at: str,
        service_items: list[dict],
    ) -> dict:
        """Создать запись на обслуживание."""
        try:
            response = await self._http.post(
                f"{self._base_url}/api/v1/appointments",
                headers=self._headers,
                json={"starts_at": starts_at, "service_items": service_items},
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning("Backend unavailable: %s", exc)
            raise BackendUnavailableError from exc
        raw = _parse_response(response)
        if not isinstance(raw, dict):
            raise BackendError(
                status_code=500,
                code="INVALID_RESPONSE",
                message="Ожидался JSON-объект",
            )
        return raw


def _parse_response(response: httpx.Response) -> dict | list:
    if response.is_success:
        return response.json()  # type: ignore[no-any-return]
    try:
        detail = response.json()
    except Exception:
        detail = {}
    error = detail.get("error", {}) if isinstance(detail, dict) else {}
    raise BackendError(
        status_code=response.status_code,
        code=error.get("code", "UNKNOWN"),
        message=error.get("message", "Ошибка сервера"),
    )
