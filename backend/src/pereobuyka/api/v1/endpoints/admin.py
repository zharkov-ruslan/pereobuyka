"""Административные эндпоинты: услуги, расписание, записи, визиты, бонусы."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Response
from sqlalchemy.exc import IntegrityError

from pereobuyka.api.v1.deps_extra import AdminActor, SessionPg
from pereobuyka.api.v1.schemas import (
    AdminAppointmentListResponse,
    AppointmentStatus,
    BonusAdjustRequest,
    BonusTransaction,
    ScheduleExceptionCreate,
    ScheduleExceptionListResponse,
    ScheduleExceptionPatch,
    ScheduleRuleCreate,
    ScheduleRuleListResponse,
    ScheduleRulePatch,
    ServiceCreate,
    ServiceItem,
    ServiceListResponse,
    ServiceOut,
    ServicePatch,
    VisitConfirmRequest,
)
from pereobuyka.api.v1.schemas import BonusAccount as BonusAccountOut
from pereobuyka.api.v1.schemas import ScheduleException as ScheduleExceptionOut
from pereobuyka.api.v1.schemas import ScheduleRule as ScheduleRuleOut
from pereobuyka.api.v1.schemas import Visit as VisitOut
from pereobuyka.db.models import User as UserRow
from pereobuyka.services.api_adapters import (
    schedule_exception_from_orm,
    schedule_rule_from_orm,
    service_from_orm,
)
from pereobuyka.services.visit_commands import (
    bonus_adjust_postgres,
    confirm_visit_postgres,
    fetch_bonus_account_client,
)
from pereobuyka.storage.repositories.postgres import (
    PostgresAppointmentRepository,
    PostgresScheduleRepository,
    PostgresServiceRepository,
)

router = APIRouter(tags=["Admin"])


@router.get("/admin/services", response_model=ServiceListResponse)
async def admin_list_services_ep(
    session: SessionPg,
    _admin: AdminActor,
    is_active: bool | None = Query(None),
) -> ServiceListResponse:
    """Список услуг (включая неактивные при фильтре)."""
    svc = PostgresServiceRepository(session)
    rows = await svc.list_all(is_active=is_active)
    items = [
        ServiceItem(
            id=s.id,
            name=s.name,
            description=s.description or "",
            duration_minutes=s.duration_minutes,
            price=s.price,
            is_active=s.is_active,
        )
        for s in rows
    ]
    return ServiceListResponse(items=items)


@router.post("/admin/services", response_model=ServiceOut, status_code=201)
async def admin_create_service_ep(
    session: SessionPg, _admin: AdminActor, body: ServiceCreate
) -> ServiceOut:
    """Создать услугу."""
    svc = PostgresServiceRepository(session)
    s = await svc.create(body)
    return service_from_orm(s)


@router.get("/admin/services/{service_id}", response_model=ServiceOut)
async def admin_get_service_ep(
    session: SessionPg, _admin: AdminActor, service_id: UUID
) -> ServiceOut:
    """Получить услугу по id."""
    svc = PostgresServiceRepository(session)
    s = await svc.get(service_id)
    if s is None:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Услуга не найдена"}}
        )
    return service_from_orm(s)


@router.patch("/admin/services/{service_id}", response_model=ServiceOut)
async def admin_patch_service_ep(
    session: SessionPg,
    _admin: AdminActor,
    service_id: UUID,
    body: ServicePatch,
) -> ServiceOut:
    """Обновить услугу."""
    svc = PostgresServiceRepository(session)
    s = await svc.patch(service_id, body)
    if s is None:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Услуга не найдена"}}
        )
    return service_from_orm(s)


@router.delete("/admin/services/{service_id}", status_code=204)
async def admin_delete_service_ep(
    session: SessionPg, _admin: AdminActor, service_id: UUID
) -> Response:
    """Удалить услугу."""
    svc = PostgresServiceRepository(session)
    s = await svc.get(service_id)
    if s is None:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Услуга не найдена"}}
        )
    try:
        await svc.delete(service_id)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "code": "DOMAIN_ERROR",
                    "message": "Услуга используется в записях или визитах",
                }
            },
        ) from None
    return Response(status_code=204)


@router.get("/admin/schedule/rules", response_model=ScheduleRuleListResponse)
async def admin_schedule_rules_list(
    session: SessionPg,
    _admin: AdminActor,
    date_from: date = Query(...),
    date_to: date = Query(...),
) -> ScheduleRuleListResponse:
    """Шаблон расписания по дням недели (даты в запросе для совместимости с OpenAPI)."""
    _ = (date_from, date_to)
    sched = PostgresScheduleRepository(session)
    rows = await sched.list_rules()
    return ScheduleRuleListResponse(items=[schedule_rule_from_orm(r) for r in rows])


@router.post("/admin/schedule/rules", response_model=ScheduleRuleOut, status_code=201)
async def admin_schedule_rules_create(
    session: SessionPg, _admin: AdminActor, body: ScheduleRuleCreate
) -> ScheduleRuleOut:
    """Добавить правило дня недели."""
    sched = PostgresScheduleRepository(session)
    try:
        r = await sched.create_rule(body)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "code": "DOMAIN_ERROR",
                    "message": "Правило для этого дня недели уже существует",
                }
            },
        ) from None
    return schedule_rule_from_orm(r)


@router.get("/admin/schedule/rules/{rule_id}", response_model=ScheduleRuleOut)
async def admin_schedule_rule_get(
    session: SessionPg, _admin: AdminActor, rule_id: UUID
) -> ScheduleRuleOut:
    """Одно правило расписания."""
    sched = PostgresScheduleRepository(session)
    r = await sched.get_rule(rule_id)
    if r is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Правило не найдено"}},
        )
    return schedule_rule_from_orm(r)


@router.patch("/admin/schedule/rules/{rule_id}", response_model=ScheduleRuleOut)
async def admin_schedule_rule_patch(
    session: SessionPg,
    _admin: AdminActor,
    rule_id: UUID,
    body: ScheduleRulePatch,
) -> ScheduleRuleOut:
    """Изменить правило."""
    sched = PostgresScheduleRepository(session)
    try:
        r = await sched.patch_rule(rule_id, body)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail={"error": {"code": "DOMAIN_ERROR", "message": "Конфликт дня недели"}},
        ) from None
    if r is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Правило не найдено"}},
        )
    return schedule_rule_from_orm(r)


@router.delete("/admin/schedule/rules/{rule_id}", status_code=204)
async def admin_schedule_rule_delete(
    session: SessionPg, _admin: AdminActor, rule_id: UUID
) -> Response:
    """Удалить правило."""
    sched = PostgresScheduleRepository(session)
    ok = await sched.delete_rule(rule_id)
    if not ok:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Правило не найдено"}},
        )
    return Response(status_code=204)


@router.get("/admin/schedule/exceptions", response_model=ScheduleExceptionListResponse)
async def admin_schedule_exceptions_list(
    session: SessionPg,
    _admin: AdminActor,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
) -> ScheduleExceptionListResponse:
    """Исключения расписания по датам."""
    sched = PostgresScheduleRepository(session)
    rows = await sched.list_exceptions(date_from=date_from, date_to=date_to)
    return ScheduleExceptionListResponse(items=[schedule_exception_from_orm(r) for r in rows])


@router.post("/admin/schedule/exceptions", response_model=ScheduleExceptionOut, status_code=201)
async def admin_schedule_exceptions_create(
    session: SessionPg, _admin: AdminActor, body: ScheduleExceptionCreate
) -> ScheduleExceptionOut:
    """Добавить исключение на дату."""
    sched = PostgresScheduleRepository(session)
    try:
        r = await sched.create_exception(body)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail={
                "error": {
                    "code": "DOMAIN_ERROR",
                    "message": "Исключение на эту дату уже существует",
                }
            },
        ) from None
    return schedule_exception_from_orm(r)


@router.get("/admin/schedule/exceptions/{exception_id}", response_model=ScheduleExceptionOut)
async def admin_schedule_exception_get(
    session: SessionPg, _admin: AdminActor, exception_id: UUID
) -> ScheduleExceptionOut:
    """Одно исключение расписания."""
    sched = PostgresScheduleRepository(session)
    r = await sched.get_exception(exception_id)
    if r is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Исключение не найдено"}},
        )
    return schedule_exception_from_orm(r)


@router.patch("/admin/schedule/exceptions/{exception_id}", response_model=ScheduleExceptionOut)
async def admin_schedule_exception_patch(
    session: SessionPg,
    _admin: AdminActor,
    exception_id: UUID,
    body: ScheduleExceptionPatch,
) -> ScheduleExceptionOut:
    """Изменить исключение."""
    sched = PostgresScheduleRepository(session)
    try:
        r = await sched.patch_exception(exception_id, body)
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail={"error": {"code": "DOMAIN_ERROR", "message": "Конфликт даты исключения"}},
        ) from None
    if r is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Исключение не найдено"}},
        )
    return schedule_exception_from_orm(r)


@router.delete("/admin/schedule/exceptions/{exception_id}", status_code=204)
async def admin_schedule_exception_delete(
    session: SessionPg, _admin: AdminActor, exception_id: UUID
) -> Response:
    """Удалить исключение."""
    sched = PostgresScheduleRepository(session)
    ok = await sched.delete_exception(exception_id)
    if not ok:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Исключение не найдено"}},
        )
    return Response(status_code=204)


@router.get("/admin/appointments", response_model=AdminAppointmentListResponse)
async def admin_appointments_list(
    session: SessionPg,
    _admin: AdminActor,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    status_filter: AppointmentStatus | None = Query(None, alias="status"),
    user_id: UUID | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> AdminAppointmentListResponse:
    """Журнал записей для администратора."""
    appt_repo = PostgresAppointmentRepository(session)
    pairs, total = await appt_repo.list_for_admin(
        date_from=date_from,
        date_to=date_to,
        status=status_filter,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    items = PostgresAppointmentRepository.build_admin_rows(pairs)
    return AdminAppointmentListResponse(items=items, total=total)


@router.post("/admin/visits", response_model=VisitOut, status_code=201)
async def admin_confirm_visit(
    session: SessionPg,
    admin_id: AdminActor,
    body: VisitConfirmRequest,
) -> VisitOut:
    """Подтвердить визит и провести бонусные операции."""
    return await confirm_visit_postgres(session, admin_id, body)


@router.get("/admin/users/{user_id}/bonus-account", response_model=BonusAccountOut)
async def admin_user_bonus_account(
    session: SessionPg, _admin: AdminActor, user_id: UUID
) -> BonusAccountOut:
    """Бонусный счёт указанного пользователя."""
    row = await session.get(UserRow, user_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Пользователь не найден"}},
        )
    return await fetch_bonus_account_client(session, user_id)


@router.post(
    "/admin/users/{user_id}/bonus-transactions",
    response_model=BonusTransaction,
    status_code=201,
)
async def admin_bonus_adjust(
    session: SessionPg,
    _admin: AdminActor,
    user_id: UUID,
    body: BonusAdjustRequest,
) -> BonusTransaction:
    """Ручная корректировка бонусов."""
    row = await session.get(UserRow, user_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": "Пользователь не найден"}},
        )
    return await bonus_adjust_postgres(session, user_id, body)
