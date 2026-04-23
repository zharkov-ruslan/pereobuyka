"""LLM-консультация: OpenRouter + function-calling (факты и запись через сервисы)."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_422_UNPROCESSABLE_CONTENT, HTTP_503_SERVICE_UNAVAILABLE

from pereobuyka.api.v1.endpoints.common import CurrentUser
from pereobuyka.api.v1.schemas import ConsultationRequest, ConsultationResponse
from pereobuyka.config import get_settings
from pereobuyka.db.session import get_db_session
from pereobuyka.llm.errors import ConsultationOrchestrationError, ConsultationProviderError
from pereobuyka.services.consultation_deps import (
    ConsultationRunner,
    build_default_openrouter_client,
    get_consultation_runner,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Consultation"])

SessionDep = Annotated[AsyncSession | None, Depends(get_db_session)]
RunnerDep = Annotated[ConsultationRunner, Depends(get_consultation_runner)]

_MAX_MESSAGE_LEN = 4000


@router.post("/consultation/messages", response_model=ConsultationResponse)
async def consultation_message(
    body: ConsultationRequest,
    user_id: CurrentUser,
    session: SessionDep,
    run: RunnerDep,
) -> ConsultationResponse:
    """Принять сообщение клиента и вернуть ответ консультанта."""
    msg = body.message.strip()
    if not msg:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": {"code": "VALIDATION_ERROR", "message": "Сообщение не должно быть пустым"}
            },
        )
    if len(msg) > _MAX_MESSAGE_LEN:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": f"Слишком длинное сообщение (максимум {_MAX_MESSAGE_LEN} символов)",
                }
            },
        )

    history_payload: list[dict[str, str]] = [
        {"role": h.role, "content": c}
        for h in body.history
        if (c := h.content.strip())  # пустые реплики не передаём в LLM
    ]

    settings = get_settings()
    if not settings.openrouter_api_key.strip():
        logger.warning("Consultation: OPENROUTER_API_KEY пуст, консультация недоступна")
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Консультант временно недоступен. Попробуйте позже.",
                }
            },
        )

    request_id = uuid4()
    llm = build_default_openrouter_client(settings)
    try:
        result = await run(
            settings=settings,
            session=session,
            user_id=user_id,
            message=msg,
            request_id=request_id,
            llm_client=llm,
            history=history_payload or None,
        )
    except ConsultationProviderError as e:
        err_text = str(e).strip() or "Провайдер LLM недоступен"
        logger.warning("Consultation provider error: %s", err_text)
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": err_text,
                }
            },
        ) from None
    except ConsultationOrchestrationError as e:
        err_text = str(e).strip() or "Ошибка оркестрации консультации"
        logger.warning("Consultation orchestration failed: %s", err_text)
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": f"Не удалось сформировать ответ: {err_text}",
                }
            },
        ) from None

    return ConsultationResponse(reply=result.reply, request_id=result.request_id)
