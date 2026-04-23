from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Каталог проекта бота (…/bot/) при запуске из исходников.
_BOT_PROJECT_DIR = Path(__file__).resolve().parents[2]


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value.strip()


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class AppConfig:
    telegram_bot_token: str

    log_level: str

    # HTTP-клиент к backend
    backend_base_url: str
    bot_secret: str
    # POST /consultation: несколько раундов tool-calls на бэке; 60s часто мало
    consultation_request_timeout: float


def load_config() -> AppConfig:
    # Local development convenience: load variables from `.env` if present.
    # При запуске как установленного пакета __file__ может указывать в uv-cache,
    # поэтому сначала пробуем cwd/.env, затем путь проекта из исходников.
    # Secrets should NOT be committed; see `.env.example`.
    load_dotenv(Path.cwd() / ".env", override=False)
    load_dotenv(_BOT_PROJECT_DIR / ".env", override=False)

    return AppConfig(
        telegram_bot_token=_require_env("TELEGRAM_BOT_TOKEN"),
        log_level=_env("LOG_LEVEL", "INFO").upper(),
        backend_base_url=_env("BACKEND_BASE_URL", "http://localhost:8000"),
        bot_secret=_env("BOT_SECRET", ""),
        consultation_request_timeout=_env_float("CONSULTATION_REQUEST_TIMEOUT", 300.0),
    )
