"""HTTP-распознавание речи для голосовых вложений консультации.

См. docs/tech/adr/adr-005-speech-to-text.md.
"""

from __future__ import annotations

import base64
import logging
from typing import Literal

import httpx

logger = logging.getLogger(__name__)

SpeechToTextProviderKind = Literal["openrouter", "openai_multipart"]


class SpeechToTextNotConfiguredError(Exception):
    """Нет ключа или базового URL для выбранного провайдера STT."""


class SpeechToTextUpstreamError(Exception):
    """Ошибка или неожиданный ответ внешнего STT."""


def _normalize_audio_format(filename: str, content_type: str | None) -> str:
    lower = filename.lower()
    if lower.endswith((".ogg", ".oga", ".opus")):
        return "ogg"
    mapping = (
        (".mp3", "mp3"),
        (".wav", "wav"),
        (".webm", "webm"),
        (".flac", "flac"),
        (".m4a", "m4a"),
    )
    for ext, fmt in mapping:
        if lower.endswith(ext):
            return fmt
    ct = (content_type or "").lower()
    if "ogg" in ct or "opus" in ct:
        return "ogg"
    if "mpeg" in ct or "mp3" in ct:
        return "mp3"
    if "wav" in ct:
        return "wav"
    if "webm" in ct:
        return "webm"
    if "mp4" in ct or "m4a" in ct or "aac" in ct:
        return "m4a"
    return "ogg"


async def _transcribe_openrouter(
    *,
    audio: bytes,
    filename: str,
    content_type: str | None,
    api_key: str,
    api_base_url: str,
    model: str,
    timeout_seconds: float,
) -> str:
    key = api_key.strip()
    if not key:
        raise SpeechToTextNotConfiguredError
    url = api_base_url.strip().rstrip("/") + "/audio/transcriptions"
    fmt = _normalize_audio_format(filename, content_type)
    body: dict[str, object] = {
        "model": model.strip() or "openai/whisper-large-v3-turbo",
        "input_audio": {
            "data": base64.b64encode(audio).decode("ascii"),
            "format": fmt,
        },
        "language": "ru",
    }
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {key}"},
                json=body,
            )
    except httpx.TimeoutException as e:
        logger.warning("STT (OpenRouter) request timeout")
        raise SpeechToTextUpstreamError("Таймаут распознавания речи") from e
    except httpx.RequestError as e:
        logger.warning("STT (OpenRouter) request failed: %s", e)
        raise SpeechToTextUpstreamError("Сервис распознавания недоступен") from e

    if resp.status_code >= 400:
        logger.warning("STT (OpenRouter) upstream HTTP %s", resp.status_code)
        raise SpeechToTextUpstreamError("Не удалось распознать речь")

    try:
        payload = resp.json()
    except Exception:
        raise SpeechToTextUpstreamError("Некорректный ответ сервиса распознавания") from None
    text = (payload.get("text") or "").strip() if isinstance(payload, dict) else ""
    if not text:
        raise SpeechToTextUpstreamError("Пустая транскрипция")
    return text


async def _transcribe_openai_multipart(
    *,
    audio: bytes,
    filename: str,
    content_type: str | None,
    api_key: str,
    api_base_url: str,
    model: str,
    timeout_seconds: float,
) -> str:
    key = api_key.strip()
    if not key:
        raise SpeechToTextNotConfiguredError
    url = api_base_url.strip().rstrip("/") + "/audio/transcriptions"
    mime = content_type or "application/octet-stream"
    files = {"file": (filename or "audio.ogg", audio, mime)}
    data = {"model": model.strip() or "whisper-1", "language": "ru"}
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            resp = await client.post(
                url,
                headers={"Authorization": f"Bearer {key}"},
                files=files,
                data=data,
            )
    except httpx.TimeoutException as e:
        logger.warning("STT (OpenAI multipart) request timeout")
        raise SpeechToTextUpstreamError("Таймаут распознавания речи") from e
    except httpx.RequestError as e:
        logger.warning("STT (OpenAI multipart) request failed: %s", e)
        raise SpeechToTextUpstreamError("Сервис распознавания недоступен") from e

    if resp.status_code >= 400:
        logger.warning("STT (OpenAI multipart) upstream HTTP %s", resp.status_code)
        raise SpeechToTextUpstreamError("Не удалось распознать речь")

    try:
        payload = resp.json()
    except Exception:
        raise SpeechToTextUpstreamError("Некорректный ответ сервиса распознавания") from None
    text = (payload.get("text") or "").strip() if isinstance(payload, dict) else ""
    if not text:
        raise SpeechToTextUpstreamError("Пустая транскрипция")
    return text


async def transcribe_uploaded_audio(
    *,
    audio: bytes,
    filename: str,
    content_type: str | None,
    provider: SpeechToTextProviderKind,
    timeout_seconds: float = 90.0,
    speech_to_text_api_key: str = "",
    speech_to_text_base_url: str = "",
    speech_to_text_model: str = "",
) -> str:
    """Распознать загруженное аудио согласно ``provider`` (см. ADR-005)."""
    if provider == "openrouter":
        model = speech_to_text_model.strip() or "openai/whisper-large-v3-turbo"
        return await _transcribe_openrouter(
            audio=audio,
            filename=filename,
            content_type=content_type,
            api_key=speech_to_text_api_key,
            api_base_url=speech_to_text_base_url or "https://openrouter.ai/api/v1",
            model=model,
            timeout_seconds=timeout_seconds,
        )
    if provider == "openai_multipart":
        model = speech_to_text_model.strip() or "whisper-1"
        return await _transcribe_openai_multipart(
            audio=audio,
            filename=filename,
            content_type=content_type,
            api_key=speech_to_text_api_key,
            api_base_url=speech_to_text_base_url or "https://api.openai.com/v1",
            model=model,
            timeout_seconds=timeout_seconds,
        )
    raise SpeechToTextUpstreamError(f"Неизвестный провайдер STT: {provider}")
