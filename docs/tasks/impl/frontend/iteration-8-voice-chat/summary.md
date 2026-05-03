# iter-fe-08 — Итог

## Сделано

- **Web:** кнопка микрофона (распознавание ru-RU, текст попадает в поле ввода), индикатор «Слушаю…», сообщения об отказе в доступе к микрофону и об отсутствии API; кнопка озвучивания последнего ответа ассистента (TTS).
- **Backend:** `POST /api/v1/consultation/transcribe` (multipart `file` → `{ "text" }`), вызов Whisper HTTP API; при пустом ключе — 503; аудио не логируется.
- **Bot:** в состоянии консультации обрабатывается `voice`: скачивание → transcribe → тот же поток, что и для текста.
- Контракты и интеграции обновлены; тесты `backend/tests/test_consultation_transcribe.py`.

## Ручная проверка

1. **Web:** авторизоваться, открыть чат, HTTPS (например localhost с доверенным сертификатом или dev-домен), нажать микрофон, убедиться что текст появляется в поле; отправить; при ответе ассистента — кнопка с иконкой динамика озвучивает текст.
2. **Bot:** в `.env` задать **`SPEECH_TO_TEXT_API_KEY`**, **`SPEECH_TO_TEXT_BASE_URL`** (как **`OPENROUTER_BASE_URL`** для OpenRouter STT), **`SPEECH_TO_TEXT_MODEL`** при необходимости; для чата — **`OPENROUTER_API_KEY`**. Режим `SPEECH_TO_TEXT_PROVIDER=openrouter` (по умолчанию). `/ask` → голосовое → ответ. Альтернатива: `openai_multipart`, база `https://api.openai.com/v1`, модель `whisper-1`.
