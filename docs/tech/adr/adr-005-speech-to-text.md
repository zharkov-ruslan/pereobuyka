# ADR-005 — Реализация серверного STT для консультации (голос Telegram)

| | |
|---|---|
| **Статус** | Accepted |
| **Дата** | 2026-05-01 |
| **Обновление** | 2026-05-01 — единый набор STT: `SPEECH_TO_TEXT_API_KEY`, `SPEECH_TO_TEXT_BASE_URL`, `SPEECH_TO_TEXT_MODEL` |
| **Автор** | Команда проекта |

---

## Контекст

Канал Telegram присылает голосовые сообщения как бинарные файлы (обычно OGG/Opus). Веб-клиент может использовать **Web Speech API** в браузере без серверного STT. Для бота нужен **серверный** шаг: аудио → текст → тот же сценарий, что и для текстового вопроса в `POST /api/v1/consultation/messages`.

Требования:

- один выделенный backend-эндпоинт приёма файла (`POST /api/v1/consultation/transcribe`);
- не логировать сырой звук и не хранить его без отдельного решения;
- провайдер STT сменяется конфигурацией (`SPEECH_TO_TEXT_PROVIDER`);
- биллинг через **OpenRouter** без обязательного прямого платёжного аккаунта OpenAI; при этом **ключ API для консультации (LLM) и ключ для STT разделены** в конфигурации (раздельные лимиты, ротация, политика доступа).

---

## Рассмотренные варианты

### 1. Только локальная модель (Whisper / аналоги на CPU/GPU)

**Плюсы:** нет утечки аудио к третьей стороне при корректном деплое; предсказуемая стоимость при высокой нагрузке.  
**Минусы:** усложнение поставки (вес модели, GPU, latency); для MVP и небольшого трафика избыточно.

### 2. Облачный STT через **прямой OpenAI API** (`multipart` → `POST …/audio/transcriptions`)

**Плюсы:** стабильный контракт [OpenAI Speech to text](https://platform.openai.com/docs/guides/speech-to-text).  
**Минусы:** отдельный биллинг и ключ OpenAI; для проекта **не** основной путь.

### 3. **OpenRouter STT** (JSON, base64)

**Плюсы:** тот же класс сервисов, что и для LLM; API в [OpenRouter — Create transcription](https://openrouter.ai/docs/api/api-reference/stt/create-audio-transcriptions).  
**Минусы:** контракт отличается от OpenAI-multipart (тело `application/json`, `input_audio.data` / `format`, поле `model`).

### 4. Иные провайдеры (Google, Yandex SpeechKit, …)

**Плюсы:** локализация данных и регуляторика.  
**Минусы:** отдельные контракты; подключаются при явной потребности.

---

## Решение

1. **Провайдер по умолчанию — `openrouter`:** запрос на `POST {base}/audio/transcriptions` с телом в формате OpenRouter STT. Хост **`SPEECH_TO_TEXT_BASE_URL`**; если пусто — **`OPENROUTER_BASE_URL`** (тот же, что для LLM). Ключ **`SPEECH_TO_TEXT_API_KEY`**. Модель — **`SPEECH_TO_TEXT_MODEL`**; если пусто — `openai/whisper-large-v3-turbo`.

2. **Консультация (чат / LLM)** использует **`OPENROUTER_API_KEY`** (`openrouter_api_key`) — не смешивать с ключом STT в коде и в логах.

3. **Альтернатива — `openai_multipart`:** те же **`SPEECH_TO_TEXT_API_KEY`**, **`SPEECH_TO_TEXT_BASE_URL`** (часто `https://api.openai.com/v1`), **`SPEECH_TO_TEXT_MODEL`** (часто `whisper-1`). Если `SPEECH_TO_TEXT_MODEL` пусто — в коде подставляется `whisper-1`.

4. Реализация: **`speech_to_text.py`**, **`transcribe_uploaded_audio`**, ветка по **`speech_to_text_provider`**.

5. **Web Speech API** — только на клиенте веба.

---

## Последствия

- В `.env` нужно задать **оба** ключа, если используются и диалог, и голос в боте через OpenRouter STT: **`OPENROUTER_API_KEY`** и **`SPEECH_TO_TEXT_API_KEY`**. **`SPEECH_TO_TEXT_BASE_URL`** обычно совпадает с **`OPENROUTER_BASE_URL`**. Допустимо **продублировать одно и то же значение** ключа OpenRouter в обе переменные, если политика проекта это позволяет.
- Документация: `integrations.md`, `backend/.env.example`, контракты API.

---

## Ссылки

- OpenRouter STT: [create-audio-transcriptions](https://openrouter.ai/docs/api/api-reference/stt/create-audio-transcriptions)
- OpenAPI проекта: `docs/tech/api/openapi.yaml` — `POST /api/v1/consultation/transcribe`
- Интеграции: `docs/tech/integrations.md`
