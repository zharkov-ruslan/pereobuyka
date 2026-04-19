from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from pereobuyka.llm.system_prompt import DEFAULT_SYSTEM_PROMPT

# Каталог проекта бота (…/bot/), независимо от CWD — чтобы подхватывался bot/.env
_BOT_PROJECT_DIR = Path(__file__).resolve().parents[2]


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value.strip()


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def _system_prompt_from_env() -> str:
    raw = os.getenv("SYSTEM_PROMPT")
    if raw is None or not raw.strip():
        return DEFAULT_SYSTEM_PROMPT
    return raw.strip()


@dataclass(frozen=True, slots=True)
class AppConfig:
    telegram_bot_token: str

    openrouter_api_key: str
    openrouter_model: str
    openrouter_base_url: str

    system_prompt: str

    log_level: str

    # HTTP-клиент к backend
    backend_base_url: str
    bot_secret: str


def load_config() -> AppConfig:
    # Local development convenience: load variables from `.env` if present.
    # Secrets should NOT be committed; see `.env.example`.
    load_dotenv(_BOT_PROJECT_DIR / ".env", override=False)

    return AppConfig(
        telegram_bot_token=_require_env("TELEGRAM_BOT_TOKEN"),
        openrouter_api_key=_require_env("OPENROUTER_API_KEY"),
        openrouter_model=_require_env("OPENROUTER_MODEL"),
        openrouter_base_url=_env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        system_prompt=_system_prompt_from_env(),
        log_level=_env("LOG_LEVEL", "INFO").upper(),
        backend_base_url=_env("BACKEND_BASE_URL", "http://localhost:8000"),
        bot_secret=_env("BOT_SECRET", ""),
    )
