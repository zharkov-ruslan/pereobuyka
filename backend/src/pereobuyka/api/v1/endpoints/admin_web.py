"""Админ-эндпоинты веб UI: дашборд, сетка, аналитика, клиенты, правки."""

from __future__ import annotations

from datetime import date as date_type
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_503_SERVICE_UNAVAILABLE

from pereobuyka.api.v1.deps_extra import AdminActor, SessionPg
from pereobuyka.api.v1.schemas import (
    AdminAppointmentCreateBody,
    AdminAppointmentListResponse,
    AdminAppointmentPatchBody,
    AdminClientListResponse,
    AdminClientQuickCreateBody,
    AdminClientRow,
    AdminDataInsightRequest,
    AdminDataInsightResponse,
    AdminVisitPatchBody,
    AnalyticsWeekResponse,
    DashboardTodayResponse,
    VisitListResponse,
    VisitRatingBody,
    WeekGridResponse,
)
from pereobuyka.api.v1.schemas import (
    Appointment as AppointmentOut,
)
from pereobuyka.api.v1.schemas import (
    Visit as VisitOut,
)
from pereobuyka.config import get_settings
from pereobuyka.db.models import User as UserRow
from pereobuyka.llm.errors import ConsultationOrchestrationError, ConsultationProviderError
from pereobuyka.services.admin_mutations_pg import (
    create_appointment_admin,
    create_client_quick_admin,
    patch_appointment_admin,
    patch_visit_admin,
    set_client_rating_admin,
)
from pereobuyka.services.admin_nl_sql_service import run_admin_data_insight
from pereobuyka.services.admin_web_dashboard import (
    admin_clients_list,
    analytics_week,
    dashboard_today,
    week_grid,
)
from pereobuyka.services.api_adapters import visit_from_orm
from pereobuyka.services.consultation_deps import build_default_openrouter_client
from pereobuyka.services.safe_nl_sql import SafeNlSqlError
from pereobuyka.storage.repositories.postgres import PostgresAppointmentRepository

router = APIRouter(tags=["Admin"])


@router.get("/admin/dashboard/today", response_model=DashboardTodayResponse)
async def admin_dashboard_today(
    session: SessionPg,
    _admin: AdminActor,
) -> DashboardTodayResponse:
    settings = get_settings()
    return await dashboard_today(session, business_tz=settings.consultation_business_timezone)


@router.get("/admin/dashboard/week-grid", response_model=WeekGridResponse)
async def admin_dashboard_week_grid(
    session: SessionPg,
    _admin: AdminActor,
    week_start: date_type = Query(..., description="Понедельник недели"),
) -> WeekGridResponse:
    settings = get_settings()
    return await week_grid(
        session, week_start=week_start, business_tz=settings.consultation_business_timezone
    )


@router.get("/admin/analytics/week", response_model=AnalyticsWeekResponse)
async def admin_analytics_week(
    session: SessionPg,
    _admin: AdminActor,
    week_start: date_type = Query(..., description="Понедельник недели"),
) -> AnalyticsWeekResponse:
    settings = get_settings()
    return await analytics_week(
        session, week_start=week_start, business_tz=settings.consultation_business_timezone
    )


@router.post("/admin/analytics/data-insight", response_model=AdminDataInsightResponse)
async def admin_analytics_data_insight(
    session: SessionPg,
    _admin: AdminActor,
    body: AdminDataInsightRequest,
) -> AdminDataInsightResponse:
    """Вопрос на естественном языке → безопасный SELECT → выборка и краткое резюме (только admin).

    См. ADR-006: валидация AST, белый список таблиц, лимит строк, аудит в логах.
    """
    settings = get_settings()
    if not settings.openrouter_api_key.strip():
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Запрос к модели недоступен (нет OPENROUTER_API_KEY).",
                },
            },
        )
    llm = build_default_openrouter_client(settings)
    try:
        return await run_admin_data_insight(
            settings=settings,
            session=session,
            admin_user_id=_admin,
            question=body.question.strip(),
            llm=llm,
        )
    except SafeNlSqlError as e:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "NL_SQL_REJECTED",
                    "message": str(e).strip() or "Запрос не прошёл проверку безопасности",
                },
            },
        ) from None
    except ConsultationOrchestrationError as e:
        msg = str(e).strip() or "Не удалось обработать ответ модели"
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": {"code": "SERVICE_UNAVAILABLE", "message": msg}},
        ) from None
    except ConsultationProviderError as e:
        msg = str(e).strip() or "Провайдер LLM недоступен"
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": {"code": "SERVICE_UNAVAILABLE", "message": msg}},
        ) from None


@router.get("/admin/clients", response_model=AdminClientListResponse)
async def admin_clients(
    session: SessionPg,
    _admin: AdminActor,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> AdminClientListResponse:
    return await admin_clients_list(session, limit=limit, offset=offset)


@router.post("/admin/clients", response_model=AdminClientRow, status_code=201)
async def admin_create_client_quick(
    session: SessionPg,
    _admin: AdminActor,
    body: AdminClientQuickCreateBody,
) -> AdminClientRow:
    return await create_client_quick_admin(session, name=body.name, phone=body.phone)


@router.post("/admin/appointments", response_model=AppointmentOut, status_code=201)
async def admin_create_appointment_ep(
    session: SessionPg,
    _admin: AdminActor,
    body: AdminAppointmentCreateBody,
) -> AppointmentOut:
    return await create_appointment_admin(
        session,
        admin_user_id=_admin,
        user_id=body.user_id,
        starts_at=body.starts_at,
        service_items=body.service_items,
        discount_percent=body.discount_percent,
    )


@router.get("/admin/clients/{user_id}", response_model=AdminClientRow)
async def admin_client_detail(
    session: SessionPg,
    _admin: AdminActor,
    user_id: UUID,
) -> AdminClientRow:
    lst = await admin_clients_list(session, limit=10_000, offset=0)
    for row in lst.items:
        if row.user_id == user_id:
            return row
    raise HTTPException(
        status_code=404,
        detail={"error": {"code": "NOT_FOUND", "message": "Клиент не найден"}},
    )


@router.get("/admin/users/{user_id}/appointments", response_model=AdminAppointmentListResponse)
async def admin_user_appointments(
    session: SessionPg,
    _admin: AdminActor,
    user_id: UUID,
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> AdminAppointmentListResponse:
    row = await session.get(UserRow, user_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Пользователь не найден"}},
        )
    appt_repo = PostgresAppointmentRepository(session)
    from pereobuyka.api.v1.schemas import AppointmentStatus

    st = AppointmentStatus(status_filter) if status_filter else None
    pairs, total = await appt_repo.list_for_admin(
        date_from=None,
        date_to=None,
        status=st,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    items = PostgresAppointmentRepository.build_admin_rows(pairs)
    return AdminAppointmentListResponse(items=items, total=total)


@router.get("/admin/users/{user_id}/visits", response_model=VisitListResponse)
async def admin_user_visits(
    session: SessionPg,
    _admin: AdminActor,
    user_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> VisitListResponse:
    row = await session.get(UserRow, user_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Пользователь не найден"}},
        )
    appt_repo = PostgresAppointmentRepository(session)
    rows, total = await appt_repo.list_visits_for_user(
        user_id=user_id,
        date_from=None,
        date_to=None,
        limit=limit,
        offset=offset,
    )
    return VisitListResponse(items=[visit_from_orm(row) for row in rows], total=total)


@router.patch("/admin/appointments/{appointment_id}", response_model=AppointmentOut)
async def admin_patch_appointment_ep(
    session: SessionPg,
    _admin: AdminActor,
    appointment_id: UUID,
    body: AdminAppointmentPatchBody,
) -> AppointmentOut:
    return await patch_appointment_admin(session, appointment_id=appointment_id, body=body)


@router.patch("/admin/visits/{visit_id}", response_model=VisitOut)
async def admin_patch_visit_ep(
    session: SessionPg,
    _admin: AdminActor,
    visit_id: UUID,
    body: AdminVisitPatchBody,
) -> VisitOut:
    return await patch_visit_admin(session, visit_id=visit_id, body=body)


@router.post("/admin/visits/{visit_id}/client-rating", response_model=VisitOut)
async def admin_visit_client_rating(
    session: SessionPg,
    _admin: AdminActor,
    visit_id: UUID,
    body: VisitRatingBody,
) -> VisitOut:
    return await set_client_rating_admin(
        session,
        visit_id=visit_id,
        stars=body.stars,
        comment=body.comment,
    )
