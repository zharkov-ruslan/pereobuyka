"""FastAPI-приложение: точка входа, lifespan, обработчики ошибок."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from pereobuyka.api.v1.router import router as api_v1_router
from pereobuyka.config import get_settings
from pereobuyka.db.session import dispose_db_engine, init_db_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Инициализация и завершение приложения (настройка логирования)."""
    settings = get_settings()
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    await init_db_engine(settings.database_url)
    logger.info("Переобуйка backend starting")
    yield
    await dispose_db_engine()
    logger.info("Переобуйка backend stopping")


app = FastAPI(
    title="Переобуйка API",
    description="Backend API системы шиномонтажного сервиса «Переобуйка».",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_v1_router, prefix="/api/v1")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Приводит HTTPException к формату контракта: {"error": {"code": ..., "message": ...}}."""
    if isinstance(exc.detail, dict):
        content = exc.detail
    else:
        content = {"error": {"code": "HTTP_ERROR", "message": str(exc.detail)}}
    return JSONResponse(status_code=exc.status_code, content=content, headers=exc.headers)


@app.get("/health", tags=["infrastructure"], summary="Проверка доступности сервиса")
async def health() -> dict[str, str]:
    """Вернуть статус доступности сервиса."""
    return {"status": "ok"}
