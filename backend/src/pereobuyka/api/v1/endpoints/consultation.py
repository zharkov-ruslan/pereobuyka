"""Заглушка LLM-консультации (до этапа с OpenRouter)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from pereobuyka.api.v1.endpoints.common import CurrentUser
from pereobuyka.api.v1.schemas import ConsultationRequest, ConsultationResponse
from pereobuyka.config import get_settings

router = APIRouter(tags=["Consultation"])


@router.post("/consultation/messages", response_model=ConsultationResponse)
async def consultation_message(
    body: ConsultationRequest, _user_id: CurrentUser
) -> ConsultationResponse:
    """Принять сообщение; без OPENROUTER_API_KEY — 503."""
    settings = get_settings()
    if not settings.openrouter_api_key.strip():
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "LLM-консультация будет доступна после настройки OPENROUTER_API_KEY",
                }
            },
        )
    raise HTTPException(
        status_code=503,
        detail={
            "error": {
                "code": "NOT_IMPLEMENTED",
                "message": "Интеграция LLM — в следующем этапе",
            }
        },
    )
