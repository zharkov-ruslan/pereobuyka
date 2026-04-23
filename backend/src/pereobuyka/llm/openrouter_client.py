"""Клиент чат-комплишенов OpenRouter (совместим с OpenAI Chat Completions API)."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any

logger = logging.getLogger(__name__)

from openai import (
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
)

from pereobuyka.llm.errors import ConsultationProviderError

# В Telegram уходят только нейтральные формулировки; детали — в логи сервера.
_MSG_RATE = (
    "Сейчас консультант не может ответить из-за высокой нагрузки. "
    "Попробуйте через несколько минут."
)
_MSG_403 = "Консультант временно недоступен. Попробуйте позже."
_MSG_GENERIC = "Консультант временно недоступен. Попробуйте позже."
_MSG_TIMEOUT = "Ответ консультанта занял слишком много времени. Попробуйте ещё раз."
_MSG_UNREACHABLE = "Консультант сейчас не на связи. Попробуйте позже."


def _provider_error_from_api_status(e: APIStatusError) -> ConsultationProviderError:
    """Ошибка HTTP API: пишем деталь в лог, клиенту — общий текст."""
    m = (e.message or str(e) or "").strip()
    logger.warning("OpenRouter HTTP %s: %s", e.status_code, m or "(без текста)")
    return ConsultationProviderError(_MSG_GENERIC)


class OpenRouterChatClient:
    """Тонкая обёртка над ``AsyncOpenAI`` для вызовов OpenRouter."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        model: str,
        timeout_seconds: float,
    ) -> None:
        self._model = model
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url.rstrip("/"),
            timeout=timeout_seconds,
        )

    async def create_chat_completion(
        self,
        *,
        messages: Sequence[Mapping[str, Any]],
        tools: Sequence[Mapping[str, Any]] | None = None,
    ) -> Any:
        """Вызвать chat completions; вернуть сырой объект ответа SDK."""
        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": list(messages),
        }
        if tools:
            kwargs["tools"] = list(tools)
            kwargs["tool_choice"] = "auto"
        try:
            return await self._client.chat.completions.create(**kwargs)
        except APITimeoutError as e:
            logger.warning("LLM request timeout: %s", e)
            raise ConsultationProviderError(_MSG_TIMEOUT) from e
        except APIConnectionError as e:
            logger.warning("LLM connection error: %s", e)
            raise ConsultationProviderError(_MSG_UNREACHABLE) from e
        except RateLimitError as e:
            logger.warning("LLM rate limit: %s", e)
            raise ConsultationProviderError(_MSG_RATE) from e
        except AuthenticationError as e:
            logger.error("LLM auth failed (проверьте OPENROUTER_API_KEY): %s", e)
            raise ConsultationProviderError(_MSG_GENERIC) from e
        except PermissionDeniedError as e:
            logger.warning("LLM 403: %s", (e.message or e))
            raise ConsultationProviderError(_MSG_403) from e
        except BadRequestError as e:
            raise _provider_error_from_api_status(e) from e
        except InternalServerError as e:
            logger.warning("LLM 5xx: %s", e)
            raise ConsultationProviderError(_MSG_GENERIC) from e
        except APIStatusError as e:
            raise _provider_error_from_api_status(e) from e
        except OpenAIError as e:
            logger.warning("LLM OpenAIError: %s", e)
            raise ConsultationProviderError(_MSG_GENERIC) from e
