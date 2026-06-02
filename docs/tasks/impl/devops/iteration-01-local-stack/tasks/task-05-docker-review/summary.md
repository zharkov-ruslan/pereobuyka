# task-05: ревью docker-expert

Проведено по [`.agents/skills/docker-expert/SKILL.md`](../../../../../.agents/skills/docker-expert/SKILL.md).

## Замечания и исправления

1. **Multi-stage** — builder + runtime для всех трёх сервисов; в production-образ не попадают dev-зависимости.
2. **Non-root** — `app` (uid 1001) для Python, `nextjs` для web.
3. **Healthchecks** — backend `/health`, postgres `pg_isready`, web HTTP на :3000.
4. **Секреты** — только `.env.docker` / env_file; `.env` в .dockerignore.
5. **Pin образов** — фиксированные major-теги базовых image.
6. **Entrypoint** — миграции до старта uvicorn; seed вынесен в `make compose-seed` (идемпотентность seed).

Итог: правки учтены в финальных Dockerfile и compose до merge итерации.
