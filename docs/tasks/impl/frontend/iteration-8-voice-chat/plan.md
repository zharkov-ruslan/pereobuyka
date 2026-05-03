# iter-fe-08 — Голосовой режим чата

## Решения

1. **Веб:** только **Web Speech API** (распознавание в браузере, без загрузки аудио на сервер). Озвучивание ответов — **Speech Synthesis** (кнопка «последний ответ ассистента»). Нужны **HTTPS** и поддерживающий браузер (Chrome/Edge и т.д.).
2. **Telegram:** голос в `/ask` → **POST `/api/v1/consultation/transcribe`** → текст → consultation API. STT по умолчанию **OpenRouter** (см. ADR-005): **`SPEECH_TO_TEXT_API_KEY`**, **`SPEECH_TO_TEXT_BASE_URL`** (как **`OPENROUTER_BASE_URL`**, иначе пусто → из **`OPENROUTER_BASE_URL`**), **`SPEECH_TO_TEXT_MODEL`**, `SPEECH_TO_TEXT_PROVIDER=openrouter`. Для чата LLM — **`OPENROUTER_API_KEY`**. Опционально `openai_multipart`. Без настроенного ключа STT — понятное сообщение; **сырой звук в логи не пишется**.

## Файлы

- `web/lib/web-speech.ts`, `web/components/chat-widget.tsx`
- `backend/src/pereobuyka/services/speech_to_text.py`, `docs/tech/adr/adr-005-speech-to-text.md`, правки `config.py`, `consultation.py`, `schemas.py`
- `bot/src/pereobuyka/client/backend.py`, `bot/src/pereobuyka/bot/handlers/ask.py`
- `docs/tech/api/openapi.yaml`, `api-contracts.md`, `integrations.md`, `backend/.env.example`
