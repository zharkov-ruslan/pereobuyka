from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv

<<<<<<< HEAD
=======
from pereobuyka.llm.system_prompt import DEFAULT_SYSTEM_PROMPT

>>>>>>> 8714249 (Реализация Этапа 0)

def _require_env(name: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value.strip()


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


<<<<<<< HEAD
=======
def _system_prompt_from_env() -> str:
    raw = os.getenv("SYSTEM_PROMPT")
    if raw is None or not raw.strip():
        return DEFAULT_SYSTEM_PROMPT
    return raw.strip()


>>>>>>> 8714249 (Реализация Этапа 0)
@dataclass(frozen=True, slots=True)
class AppConfig:
    telegram_bot_token: str

    openrouter_api_key: str
    openrouter_model: str
    openrouter_base_url: str

<<<<<<< HEAD
=======
    system_prompt: str

>>>>>>> 8714249 (Реализация Этапа 0)
    log_level: str


def load_config() -> AppConfig:
    # Local development convenience: load variables from `.env` if present.
    # Secrets should NOT be committed; see `.env.example`.
    load_dotenv(override=False)

    return AppConfig(
        telegram_bot_token=_require_env("TELEGRAM_BOT_TOKEN"),
        openrouter_api_key=_require_env("OPENROUTER_API_KEY"),
        openrouter_model=_require_env("OPENROUTER_MODEL"),
        openrouter_base_url=_env("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
<<<<<<< HEAD
=======
        system_prompt=_system_prompt_from_env(),
>>>>>>> 8714249 (Реализация Этапа 0)
        log_level=_env("LOG_LEVEL", "INFO").upper(),
    )

