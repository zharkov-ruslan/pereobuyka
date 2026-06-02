# iter-dev-01: локальный полный стек

## Цель

Поднять postgres + backend + bot + web одной командой `make compose-up`.

## Решения

- Layout `devops/<service>/` + build context = каталог сервиса
- Корневой `docker-compose.yml` заменяет compose «только БД»
- `db-up` / `db-down` — только postgres для гибридной разработки
- Env для compose — `.env.docker` (шаблон `.env.docker.example`)

## Задачи

1. devops-layout — структура каталогов
2. dockerfiles — multi-stage образы
3. compose — полный стек
4. makefile — compose-* цели
5. docker-review — ревью по skill docker-expert
6. compose-guide — docs/tech/docker-compose-local.md
7. docs-sync — README, onboarding, architecture, plan
