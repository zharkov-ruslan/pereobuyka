"""Конфигурация приложения: загрузка переменных окружения через pydantic-settings."""

from functools import lru_cache
from uuid import UUID

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

    # LLM (OpenRouter) — необязательны на этапе каркаса
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    # Один «раунд» OpenRouter; медленные модели — увеличьте (см. таймаут бота CONSULTATION_REQUEST_TIMEOUT)
    consultation_llm_timeout_seconds: float = 90.0
    consultation_max_tool_rounds: int = 6
    consultation_system_prompt: str = ""
    # IANA, напр. Europe/Moscow: «сегодня» в consultation и отсечение прошедших слотов
    consultation_business_timezone: str = "Europe/Moscow"

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
