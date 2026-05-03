"""Конфигурация приложения: загрузка переменных окружения через pydantic-settings."""

from functools import lru_cache
from typing import Literal
from uuid import UUID

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Конфигурация приложения, загружаемая из переменных окружения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # База данных — PostgreSQL в production; SQLite только для локальной разработки
    database_url: str = "sqlite+aiosqlite:///./dev.db"

    # Логирование
    log_level: str = "INFO"

    # CORS для локального web-клиента
    cors_allow_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # OpenRouter (только LLM-консультация); STT — префикс SPEECH_TO_TEXT_* (см. ADR-005)
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # Один «раунд» OpenRouter; медленные модели — увеличьте
    # (см. таймаут бота CONSULTATION_REQUEST_TIMEOUT)
    consultation_llm_timeout_seconds: float = 90.0
    consultation_max_tool_rounds: int = 6
    consultation_system_prompt: str = ""
    # IANA, напр. Europe/Moscow: «сегодня» в consultation и отсечение прошедших слотов
    consultation_business_timezone: str = "Europe/Moscow"

    # NL→SQL для админки (ADR-006): лимит строк и таймаут выполнения SELECT в БД
    admin_nl_sql_max_rows: int = 200
    admin_nl_sql_statement_timeout_ms: int = 15000

    # Speech-to-text (ADR-005): SPEECH_TO_TEXT_* — один набор для openrouter и openai_multipart
    speech_to_text_provider: Literal["openrouter", "openai_multipart"] = "openrouter"
    speech_to_text_api_key: str = ""
    # Пусто: при openrouter — как OPENROUTER_BASE_URL; при openai_multipart — https://api.openai.com/v1
    speech_to_text_base_url: str = ""
    # Пусто в коде: openrouter — openai/whisper-large-v3-turbo; openai_multipart — whisper-1
    speech_to_text_model: str = ""

    @field_validator("speech_to_text_provider", mode="before")
    @classmethod
    def _normalize_stt_provider(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    # Секрет для авторизации бота (временная мера до реализации JWT auth)
    bot_secret: str = ""

    # MVP: Bearer для /api/v1/admin/*; пусто — 403
    admin_api_token: str = ""
    # Пользователь-админ в БД (см. seed) — confirmed_by у визитов
    admin_actor_user_id: UUID = UUID("00000000-0000-0000-0000-0000000000aa")


@lru_cache
def get_settings() -> Settings:
    """Вернуть кешированный экземпляр настроек приложения."""
    return Settings()
