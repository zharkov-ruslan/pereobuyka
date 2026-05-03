"""Эндпоинты клиента: профиль, записи, визиты, бонусы, правила лояльности."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from pereobuyka.api.v1.deps_extra import SessionPg
from pereobuyka.api.v1.endpoints.common import CurrentUser
from pereobuyka.api.v1.schemas import Appointment as AppointmentOut
from pereobuyka.api.v1.schemas import (
    AppointmentListResponse,
    AppointmentPatchRequest,
    AppointmentStatus,
    BonusTransactionListResponse,
    LoyaltyRules,
    ServiceRatingBody,
    User,
    VisitListResponse,
)
from pereobuyka.api.v1.schemas import BonusAccount as BonusAccountOut
from pereobuyka.api.v1.schemas import Visit as VisitOut
from pereobuyka.services.admin_mutations_pg import set_service_rating_client
from pereobuyka.services.api_adapters import appointment_from_orm, visit_from_orm
from pereobuyka.services.auth_user_pg import get_me_pg
from pereobuyka.services.visit_commands import (
    fetch_bonus_account_client,
    fetch_loyalty_rules_public,
    list_bonus_transactions_client,
)
from pereobuyka.storage.repositories.postgres import PostgresAppointmentRepository

router = APIRouter(tags=["Client", "Public"])


@router.get("/me", response_model=User)
async def me(session: SessionPg, user_id: CurrentUser) -> User:
    """Текущий пользователь по Bearer-токену."""
    return await get_me_pg(session, user_id)


@router.get("/loyalty/rules", response_model=LoyaltyRules)
async def loyalty_rules(session: SessionPg) -> LoyaltyRules:
    """Публичные правила программы лояльности."""
    return await fetch_loyalty_rules_public(session)


@router.get("/me/appointments", response_model=AppointmentListResponse)
async def my_appointments(
    session: SessionPg,
    user_id: CurrentUser,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    status_filter: AppointmentStatus | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> AppointmentListResponse:
    """Список записей клиента с фильтрами."""
    appt_repo = PostgresAppointmentRepository(session)
    rows, total = await appt_repo.list_for_user(
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    items = [appointment_from_orm(a) for a in rows]
    return AppointmentListResponse(items=items, total=total)


@router.patch("/me/appointments/{appointment_id}", response_model=AppointmentOut)
async def patch_my_appointment(
    appointment_id: UUID,
    session: SessionPg,
    user_id: CurrentUser,
    body: AppointmentPatchRequest,
) -> AppointmentOut:
    """Отмена записи клиентом (только scheduled → cancelled)."""
    if body.status != AppointmentStatus.cancelled:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Клиент может только отменить запись",
                },
            },
        )
    appt_repo = PostgresAppointmentRepository(session)
    ap = await appt_repo.get_for_user(user_id, appointment_id)
    if ap is None:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Запись не найдена"}}
        )
    if ap.status != "scheduled":
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "code": "APPOINTMENT_INVALID_STATE",
                    "message": "Отменить можно только запланированную запись",
                }
            },
        )
    ap.status = "cancelled"
    await session.flush()
    await session.refresh(ap, attribute_names=["lines"])
    return appointment_from_orm(ap)


@router.get("/me/visits", response_model=VisitListResponse)
async def my_visits(
    session: SessionPg,
    user_id: CurrentUser,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> VisitListResponse:
    """История подтверждённых визитов."""
    appt_repo = PostgresAppointmentRepository(session)
    rows, total = await appt_repo.list_visits_for_user(
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    items = [visit_from_orm(v) for v in rows]
    return VisitListResponse(items=items, total=total)


@router.get("/me/bonus-account", response_model=BonusAccountOut)
async def my_bonus_account(session: SessionPg, user_id: CurrentUser) -> BonusAccountOut:
    """Бонусный счёт клиента."""
    return await fetch_bonus_account_client(session, user_id)


@router.get("/me/bonus-transactions", response_model=BonusTransactionListResponse)
async def my_bonus_transactions(
    session: SessionPg,
    user_id: CurrentUser,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> BonusTransactionListResponse:
    """История бонусных операций."""
    return await list_bonus_transactions_client(session, user_id, limit=limit, offset=offset)


@router.post(
    "/me/visits/{visit_id}/service-rating",
    response_model=VisitOut,
    status_code=200,
)
async def rate_service_for_visit(
    session: SessionPg,
    user_id: CurrentUser,
    visit_id: UUID,
    body: ServiceRatingBody,
) -> VisitOut:
    return await set_service_rating_client(
        session,
        user_id=user_id,
        visit_id=visit_id,
        stars=body.stars,
        comment=body.comment,
    )
