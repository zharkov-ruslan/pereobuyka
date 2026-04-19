"""Конфигурация приложения: загрузка переменных окружения через pydantic-settings."""

from functools import lru_cache

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

    # Секрет для авторизации бота (временная мера до реализации JWT auth)
    bot_secret: str = ""


@lru_cache
def get_settings() -> Settings:
    """Вернуть кешированный экземпляр настроек приложения."""
    return Settings()
