# Tasklist — Этап 3: LLM-консультант (backend + бот)

Статус этапа: **закрыт по текущему DoD** (см. `docs/plan.md`).

## Цель

Дать клиенту ответы на вопросы об услугах/слотах/бонусах **строго на основе данных backend**, и оформить запись через **function-calling** (без «выдуманных» цен/окон).

## Сделано

- **Backend**
  - Клиент OpenRouter (`OpenRouterChatClient`) на базе `openai` SDK (Chat Completions + tools).
  - Оркестратор `run_consultation`: системный промпт + фактический контекст + tool-calls.
  - Tools: `list_services`, `list_slots`, `create_appointment` (через существующие сервисы/репозитории).
  - Лимит раундов tool-calls: `CONSULTATION_MAX_TOOL_ROUNDS`.
  - Endpoint `POST /api/v1/consultation/messages`: `503 SERVICE_UNAVAILABLE` на недоступность LLM/ошибки оркестрации (без утечки внутренних деталей).
  - DI `get_consultation_runner` для детерминированных тестов.
- **Bot**
  - Команда `/ask <вопрос>` → `POST /api/v1/consultation/messages`.
  - Help в `/start`.
- **Тесты**
  - Backend: endpoint (ключ/валидация/ошибки) + оркестратор (create через tool).
  - Bot: unit-тесты разбора текста `/ask`.

## Переменные окружения

См. `backend/.env.example` (`OPENROUTER_*`, `CONSULTATION_*`).

## Команды проверки

```bash
make backend-test
make backend-lint
make bot-test
make bot-lint
```
