"""LLM-консультация: OpenRouter + function-calling (факты и запись через сервисы)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_422_UNPROCESSABLE_CONTENT, HTTP_503_SERVICE_UNAVAILABLE

from pereobuyka.api.v1.deps_extra import SessionPg
from pereobuyka.api.v1.endpoints.common import ConsultationAppointmentSource, CurrentUser
from pereobuyka.api.v1.schemas import (
    ConsultationMessageListResponse,
    ConsultationMessageOut,
    ConsultationRequest,
    ConsultationResponse,
    ConsultationTranscribeResponse,
)
from pereobuyka.config import get_settings
from pereobuyka.db.models import ConsultationMessage as ConsultationMessageRow
from pereobuyka.db.session import get_db_session
from pereobuyka.llm.errors import ConsultationOrchestrationError, ConsultationProviderError
from pereobuyka.services.consultation_deps import (
    ConsultationRunner,
    build_default_openrouter_client,
    get_consultation_runner,
)
from pereobuyka.services.speech_to_text import (
    SpeechToTextNotConfiguredError,
    SpeechToTextUpstreamError,
    transcribe_uploaded_audio,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Consultation"])

SessionDep = Annotated[AsyncSession | None, Depends(get_db_session)]
RunnerDep = Annotated[ConsultationRunner, Depends(get_consultation_runner)]

_MAX_MESSAGE_LEN = 4000
_MAX_VOICE_BYTES = 25 * 1024 * 1024


@router.post("/consultation/messages", response_model=ConsultationResponse)
async def consultation_message(
    body: ConsultationRequest,
    user_id: CurrentUser,
    appointment_source: ConsultationAppointmentSource,
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
        logger.warning("Consultation: OPENROUTER_API_KEY (LLM) пуст, консультация недоступна")
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
            appointment_source=appointment_source,
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

    rid = result.request_id or request_id

    if session is not None:
        now = datetime.now(UTC)
        session.add(
            ConsultationMessageRow(
                id=uuid4(),
                user_id=user_id,
                role="user",
                content=msg,
                created_at=now,
                request_id=rid,
            )
        )
        session.add(
            ConsultationMessageRow(
                id=uuid4(),
                user_id=user_id,
                role="assistant",
                content=result.reply,
                created_at=datetime.now(UTC),
                request_id=rid,
            )
        )
        await session.flush()

    return ConsultationResponse(reply=result.reply, request_id=rid)


@router.post("/consultation/transcribe", response_model=ConsultationTranscribeResponse)
async def consultation_transcribe(
    user_id: CurrentUser,
    file: UploadFile = File(...),
) -> ConsultationTranscribeResponse:
    """Распознать короткое аудио (голос Telegram) в текст для POST /consultation/messages."""
    _ = user_id
    raw = await file.read()
    if not raw:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"error": {"code": "VALIDATION_ERROR", "message": "Пустой файл"}},
        )
    if len(raw) > _MAX_VOICE_BYTES:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
            detail={"error": {"code": "VALIDATION_ERROR", "message": "Файл слишком большой"}},
        )

    settings = get_settings()
    name = (file.filename or "voice.ogg").strip() or "voice.ogg"
    ctype = file.content_type
    timeout_s = min(120.0, max(30.0, settings.consultation_llm_timeout_seconds + 30.0))
    stt_base = settings.speech_to_text_base_url.strip()
    if settings.speech_to_text_provider == "openrouter":
        resolved_stt_base = stt_base or settings.openrouter_base_url
    else:
        resolved_stt_base = stt_base or "https://api.openai.com/v1"

    try:
        text = await transcribe_uploaded_audio(
            audio=raw,
            filename=name,
            content_type=ctype,
            provider=settings.speech_to_text_provider,
            timeout_seconds=timeout_s,
            speech_to_text_api_key=settings.speech_to_text_api_key,
            speech_to_text_base_url=resolved_stt_base,
            speech_to_text_model=settings.speech_to_text_model,
        )
    except SpeechToTextNotConfiguredError:
        logger.warning(
            "Consultation transcribe: STT not configured (provider=%s)",
            settings.speech_to_text_provider,
        )
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Распознавание голоса на сервере не настроено.",
                }
            },
        ) from None
    except SpeechToTextUpstreamError as e:
        msg = str(e).strip() or "Не удалось распознать речь"
        logger.warning("Consultation transcribe failed: %s", msg)
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": {"code": "SERVICE_UNAVAILABLE", "message": msg}},
        ) from None

    return ConsultationTranscribeResponse(text=text)


@router.get("/consultation/messages", response_model=ConsultationMessageListResponse)
async def consultation_messages_history(
    session: SessionPg,
    user_id: CurrentUser,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> ConsultationMessageListResponse:
    """История сообщений консультации для виджета чата."""
    filt = ConsultationMessageRow.user_id == user_id
    total = int(
        (await session.scalar(select(func.count()).select_from(ConsultationMessageRow).where(filt)))
        or 0
    )
    stmt = (
        select(ConsultationMessageRow)
        .where(filt)
        .order_by(ConsultationMessageRow.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    rows = list((await session.scalars(stmt)).all())
    items = [
        ConsultationMessageOut(
            id=r.id,
            role=r.role,  # type: ignore[arg-type]
            content=r.content,
            created_at=r.created_at.replace(tzinfo=None) if r.created_at.tzinfo else r.created_at,
            request_id=r.request_id,
        )
        for r in rows
    ]
    return ConsultationMessageListResponse(items=items, total=total)
