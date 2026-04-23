"""Подтверждение визита администратором и начисление бонусов."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import ROUND_DOWN, Decimal
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.status import HTTP_409_CONFLICT

from pereobuyka.api.v1.schemas import (
    BonusAdjustRequest,
    BonusTransactionType,
    Visit,
    VisitConfirmRequest,
)
from pereobuyka.db.models import (
    Appointment,
    BonusAccount,
    LoyaltySettings,
    VisitLine,
)
from pereobuyka.db.models import (
    BonusTransaction as BonusTxRow,
)
from pereobuyka.db.models import (
    Visit as VisitRow,
)
from pereobuyka.storage.postgres_repos import _as_utc_naive, ensure_user_exists


async def _get_loyalty(session: AsyncSession) -> LoyaltySettings:
    row = await session.get(LoyaltySettings, 1)
    if row is None:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail={
                "error": {"code": "LOYALTY_NOT_CONFIGURED", "message": "Нет настроек лояльности"}
            },
        )
    return row


async def _get_or_create_bonus_account(session: AsyncSession, user_id: UUID) -> BonusAccount:
    await ensure_user_exists(session, user_id)
    res = await session.scalars(select(BonusAccount).where(BonusAccount.user_id == user_id))
    acc = res.first()
    if acc:
        return acc
    acc = BonusAccount(id=uuid4(), user_id=user_id, balance=0)
    session.add(acc)
    await session.flush()
    return acc


async def confirm_visit_postgres(
    session: AsyncSession,
    admin_user_id: UUID,
    body: VisitConfirmRequest,
) -> Visit:
    """Создать визит, закрыть запись, провести бонусные транзакции."""
    appt = await session.get(Appointment, body.appointment_id)
    if appt is None:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Запись не найдена"}}
        )
    if appt.status != "scheduled":
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail={
                "error": {"code": "VISIT_INVALID_STATE", "message": "Запись не в статусе scheduled"}
            },
        )

    existing = await session.scalars(select(VisitRow).where(VisitRow.appointment_id == appt.id))
    if existing.first():
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail={
                "error": {"code": "VISIT_EXISTS", "message": "Визит для этой записи уже создан"}
            },
        )

    loyalty = await _get_loyalty(session)
    total_amount = Decimal(body.total_amount).quantize(Decimal("0.01"))
    max_bonus_money = (
        total_amount * Decimal(loyalty.max_bonus_spend_percent) / Decimal(100)
    ).quantize(
        Decimal("0.01"),
        ROUND_DOWN,
    )
    max_bonus_pts = int(max_bonus_money)

    bonus_spent_req = body.bonus_spent
    if bonus_spent_req < 0:
        raise HTTPException(
            status_code=422, detail={"error": {"code": "VALIDATION", "message": "bonus_spent < 0"}}
        )

    account = await _get_or_create_bonus_account(session, appt.user_id)
    bonus_spent = min(bonus_spent_req, max_bonus_pts, account.balance)

    bonus_earned = int(
        (total_amount * Decimal(loyalty.earn_percent_after_visit) / Decimal(100)).to_integral_value(
            ROUND_DOWN,
        )
    )

    await ensure_user_exists(session, admin_user_id)

    confirmed_at = datetime.now(UTC)
    visit_id = uuid4()

    vr = VisitRow(
        id=visit_id,
        appointment_id=appt.id,
        total_amount=total_amount,
        bonus_spent=bonus_spent,
        bonus_earned=bonus_earned,
        confirmed_at=confirmed_at,
        confirmed_by_user_id=admin_user_id,
    )
    session.add(vr)
    await session.flush()

    for line in body.lines:
        session.add(
            VisitLine(
                visit_id=visit_id,
                service_id=line.service_id,
                quantity=line.quantity,
            )
        )

    appt.status = "completed"

    new_balance = account.balance - bonus_spent + bonus_earned
    if new_balance < 0:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail={"error": {"code": "INSUFFICIENT_BONUS", "message": "Недостаточно бонусов"}},
        )
    account.balance = new_balance

    if bonus_spent > 0:
        session.add(
            BonusTxRow(
                id=uuid4(),
                account_id=account.id,
                type="spend",
                amount=-bonus_spent,
                visit_id=visit_id,
                created_at=confirmed_at,
                comment=None,
            )
        )
    if bonus_earned > 0:
        session.add(
            BonusTxRow(
                id=uuid4(),
                account_id=account.id,
                type="earn",
                amount=bonus_earned,
                visit_id=visit_id,
                created_at=confirmed_at,
                comment=None,
            )
        )

    return Visit(
        id=visit_id,
        appointment_id=appt.id,
        total_amount=f"{total_amount:.2f}",
        bonus_spent=bonus_spent,
        bonus_earned=bonus_earned,
        confirmed_at=_as_utc_naive(confirmed_at),
        confirmed_by_user_id=admin_user_id,
        lines=body.lines,
    )


async def fetch_loyalty_rules_public(session: AsyncSession):
    from pereobuyka.api.v1.schemas import LoyaltyRules

    row = await session.get(LoyaltySettings, 1)
    if row is None:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Нет правил"}}
        )
    return LoyaltyRules(
        max_bonus_spend_percent=int(row.max_bonus_spend_percent),
        earn_percent_after_visit=int(row.earn_percent_after_visit),
    )


async def fetch_bonus_account_client(session: AsyncSession, user_id: UUID):
    from pereobuyka.api.v1.schemas import BonusAccount

    account = await _get_or_create_bonus_account(session, user_id)
    return BonusAccount(id=account.id, user_id=account.user_id, balance=account.balance)


async def list_bonus_transactions_client(
    session: AsyncSession, user_id: UUID, limit: int, offset: int
):
    from pereobuyka.api.v1.schemas import BonusTransaction as BonusTxOut
    from pereobuyka.api.v1.schemas import BonusTransactionListResponse

    account = await _get_or_create_bonus_account(session, user_id)
    stmt = (
        select(BonusTxRow)
        .where(BonusTxRow.account_id == account.id)
        .order_by(BonusTxRow.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.scalars(stmt)).all()
    cnt_stmt = (
        select(func.count()).select_from(BonusTxRow).where(BonusTxRow.account_id == account.id)
    )
    total = int((await session.scalar(cnt_stmt)) or 0)

    items = [
        BonusTxOut(
            id=r.id,
            type=BonusTransactionType(r.type),
            amount=r.amount,
            visit_id=r.visit_id,
            created_at=_as_utc_naive(r.created_at),
            comment=r.comment,
        )
        for r in rows
    ]
    return BonusTransactionListResponse(items=items, total=total)


async def bonus_adjust_postgres(
    session: AsyncSession,
    target_user_id: UUID,
    body: BonusAdjustRequest,
):
    from pereobuyka.api.v1.schemas import BonusTransaction as BonusTxOut

    account = await _get_or_create_bonus_account(session, target_user_id)
    new_balance = account.balance + body.amount
    if new_balance < 0:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail={
                "error": {
                    "code": "INSUFFICIENT_BONUS",
                    "message": "Баланс не может стать отрицательным",
                }
            },
        )
    account.balance = new_balance
    confirmed_at = datetime.now(UTC)
    tx_row = BonusTxRow(
        id=uuid4(),
        account_id=account.id,
        type="adjust",
        amount=body.amount,
        visit_id=None,
        created_at=confirmed_at,
        comment=body.comment,
    )
    session.add(tx_row)
    await session.flush()
    return BonusTxOut(
        id=tx_row.id,
        type=BonusTransactionType.adjust,
        amount=body.amount,
        visit_id=None,
        created_at=_as_utc_naive(confirmed_at),
        comment=body.comment,
    )
