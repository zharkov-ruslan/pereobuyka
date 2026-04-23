"""HTTP-клиент к Переобуйка Backend API."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, NotRequired, TypedDict, cast
from uuid import UUID

import httpx

logger = logging.getLogger(__name__)


class ServiceItem(TypedDict):
    id: str
    name: str
    price: str
    duration_minutes: int


class SlotWindow(TypedDict):
    starts_at: str
    ends_at: str


class AppointmentItem(TypedDict):
    id: str
    starts_at: str
    ends_at: str
    status: str
    total_price: str


class BonusAccount(TypedDict):
    balance: int


class BonusTransaction(TypedDict):
    created_at: str
    type: str
    amount: int


class VisitItem(TypedDict):
    confirmed_at: str
    total_amount: str
    bonus_earned: int
    bonus_spent: int


class MeResponse(TypedDict):
    id: str
    name: str
    phone: NotRequired[str | None]
    telegram_id: NotRequired[int | None]


class TelegramAuthResponse(TypedDict):
    access_token: str
    token_type: str
    user: MeResponse


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

    async def get_services(self) -> list[ServiceItem]:
        """Получить каталог активных услуг."""
        result = await self._get("/api/v1/services", headers={})
        if not isinstance(result, dict):
            return []
        items = result.get("items")
        if not isinstance(items, list):
            return []
        return cast(list[ServiceItem], items)

    async def _get(self, path: str, headers: dict[str, str]) -> list[dict[str, Any]] | dict[str, Any]:
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
    ) -> list[SlotWindow]:
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
        if not isinstance(items, list):
            return []
        return cast(list[SlotWindow], items)

    async def create_appointment(
        self,
        starts_at: str,
        service_items: list[dict],
    ) -> AppointmentItem:
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
        return cast(AppointmentItem, self._ensure_object(raw))

    async def get_me(self) -> MeResponse:
        """Получить профиль текущего пользователя."""
        return cast(MeResponse, await self._get_object("/api/v1/me"))

    async def auth_telegram(self, *, telegram_id: int, name: str, phone: str | None = None) -> TelegramAuthResponse:
        """Создать/обновить пользователя через auth-эндпоинт Telegram."""
        payload: dict[str, str | int | None] = {"telegram_id": telegram_id, "name": name}
        if phone:
            payload["phone"] = phone
        try:
            response = await self._http.post(
                f"{self._base_url}/api/v1/auth/telegram",
                headers=self._headers,
                json=payload,
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning("Backend unavailable: %s", exc)
            raise BackendUnavailableError from exc
        raw = _parse_response(response)
        return cast(TelegramAuthResponse, self._ensure_object(raw))

    async def list_my_appointments(self, *, status: str | None = None, limit: int = 10) -> list[AppointmentItem]:
        """Получить список записей текущего клиента."""
        params: dict[str, str | int] = {"limit": limit, "offset": 0}
        if status is not None:
            params["status"] = status
        try:
            response = await self._http.get(
                f"{self._base_url}/api/v1/me/appointments",
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
        if not isinstance(items, list):
            return []
        return cast(list[AppointmentItem], items)

    async def cancel_appointment(self, appointment_id: str) -> AppointmentItem:
        """Отменить запись клиента."""
        try:
            response = await self._http.patch(
                f"{self._base_url}/api/v1/me/appointments/{appointment_id}",
                headers=self._headers,
                json={"status": "cancelled"},
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning("Backend unavailable: %s", exc)
            raise BackendUnavailableError from exc
        return cast(AppointmentItem, self._ensure_object(_parse_response(response)))

    async def get_bonus_account(self) -> BonusAccount:
        """Получить текущий баланс бонусов."""
        return cast(BonusAccount, await self._get_object("/api/v1/me/bonus-account"))

    async def list_bonus_transactions(self, *, limit: int = 5) -> list[BonusTransaction]:
        """Получить последние бонусные операции."""
        return cast(
            list[BonusTransaction],
            await self._get_items("/api/v1/me/bonus-transactions", {"limit": limit, "offset": 0}),
        )

    async def list_visits(self, *, limit: int = 5) -> list[VisitItem]:
        """Получить последние подтверждённые визиты."""
        return cast(
            list[VisitItem],
            await self._get_items("/api/v1/me/visits", {"limit": limit, "offset": 0}),
        )

    async def _get_items(self, path: str, params: dict[str, str | int]) -> list[dict[str, Any]]:
        try:
            response = await self._http.get(
                f"{self._base_url}{path}",
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
        if not isinstance(items, list):
            return []
        return cast(list[dict[str, Any]], items)

    async def _get_object(self, path: str) -> dict[str, Any]:
        try:
            response = await self._http.get(
                f"{self._base_url}{path}",
                headers=self._headers,
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.warning("Backend unavailable: %s", exc)
            raise BackendUnavailableError from exc
        return self._ensure_object(_parse_response(response))

    def _ensure_object(self, raw: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any]:
        if isinstance(raw, dict):
            return raw
        raise BackendError(
            status_code=500,
            code="INVALID_RESPONSE",
            message="Ожидался JSON-объект",
        )


def _parse_response(response: httpx.Response) -> dict[str, Any] | list[dict[str, Any]]:
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
