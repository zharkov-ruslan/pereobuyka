"""Initial PostgreSQL schema (data-model.md).

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-20

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _uuid_pk(name: str = "id") -> sa.Column:
    return sa.Column(
        name,
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
    )


def upgrade() -> None:
    op.create_table(
        "users",
        _uuid_pk(),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "registered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("source", sa.Text(), nullable=False),
        sa.CheckConstraint("char_length(name) <= 200", name="ck_users_name_len"),
        sa.CheckConstraint("phone IS NULL OR char_length(phone) <= 32", name="ck_users_phone_len"),
        sa.CheckConstraint("role IN ('client', 'admin')", name="ck_users_role_values"),
        sa.CheckConstraint("char_length(role) <= 16", name="ck_users_role_len"),
        sa.CheckConstraint("source IN ('telegram', 'web')", name="ck_users_source_values"),
        sa.CheckConstraint("char_length(source) <= 16", name="ck_users_source_len"),
    )

    op.create_table(
        "services",
        _uuid_pk(),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.CheckConstraint("char_length(name) <= 255", name="ck_services_name_len"),
        sa.CheckConstraint("char_length(description) <= 4000", name="ck_services_description_len"),
        sa.CheckConstraint("price >= 0", name="ck_services_price_nonneg"),
        sa.CheckConstraint("duration_minutes > 0", name="ck_services_duration_pos"),
    )

    op.create_table(
        "schedule_rules",
        _uuid_pk(),
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_day_off", sa.Boolean(), nullable=False),
        sa.CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_schedule_rules_weekday"),
        sa.UniqueConstraint("weekday", name="uq_schedule_rules_weekday"),
    )

    op.create_table(
        "schedule_exceptions",
        _uuid_pk(),
        sa.Column("exception_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_day_off", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("exception_date", name="uq_schedule_exceptions_date"),
    )

    op.create_table(
        "appointments",
        _uuid_pk(),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('scheduled', 'completed', 'cancelled')",
            name="ck_appointments_status_values",
        ),
        sa.CheckConstraint("char_length(status) <= 32", name="ck_appointments_status_len"),
        sa.CheckConstraint("ends_at > starts_at", name="ck_appointments_time_order"),
    )
    op.create_index("ix_appointments_user_id", "appointments", ["user_id"])
    op.create_index("ix_appointments_starts_at", "appointments", ["starts_at"])

    op.create_table(
        "appointment_services",
        sa.Column("appointment_id", UUID(as_uuid=True), nullable=False),
        sa.Column("service_id", UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("appointment_id", "service_id"),
        sa.CheckConstraint("quantity >= 1", name="ck_appointment_services_qty"),
    )
    op.create_index("ix_appointment_services_service_id", "appointment_services", ["service_id"])

    op.create_table(
        "visits",
        _uuid_pk(),
        sa.Column("appointment_id", UUID(as_uuid=True), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("bonus_spent", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("bonus_earned", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_by_user_id", UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["confirmed_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("appointment_id", name="uq_visits_appointment_id"),
        sa.CheckConstraint("bonus_spent >= 0", name="ck_visits_bonus_spent_nonneg"),
        sa.CheckConstraint("bonus_earned >= 0", name="ck_visits_bonus_earned_nonneg"),
    )
    op.create_index("ix_visits_confirmed_by_user_id", "visits", ["confirmed_by_user_id"])

    op.create_table(
        "visit_lines",
        sa.Column("visit_id", UUID(as_uuid=True), nullable=False),
        sa.Column("service_id", UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("visit_id", "service_id"),
        sa.CheckConstraint("quantity >= 1", name="ck_visit_lines_qty"),
    )
    op.create_index("ix_visit_lines_service_id", "visit_lines", ["service_id"])

    op.create_table(
        "bonus_accounts",
        _uuid_pk(),
        sa.Column("user_id", UUID(as_uuid=True), nullable=False),
        sa.Column("balance", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("user_id", name="uq_bonus_accounts_user_id"),
    )

    op.create_table(
        "bonus_transactions",
        _uuid_pk(),
        sa.Column("account_id", UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("visit_id", UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["account_id"], ["bonus_accounts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], ondelete="SET NULL"),
        sa.CheckConstraint("type IN ('earn', 'spend', 'adjust')", name="ck_bonus_tx_type_values"),
        sa.CheckConstraint("char_length(type) <= 16", name="ck_bonus_tx_type_len"),
        sa.CheckConstraint(
            "comment IS NULL OR char_length(comment) <= 1000", name="ck_bonus_tx_comment_len"
        ),
    )
    op.create_index("ix_bonus_transactions_account_id", "bonus_transactions", ["account_id"])
    op.create_index("ix_bonus_transactions_visit_id", "bonus_transactions", ["visit_id"])

    op.create_table(
        "faq_entries",
        _uuid_pk(),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.CheckConstraint("char_length(question) <= 500", name="ck_faq_question_len"),
        sa.CheckConstraint("char_length(answer) <= 16000", name="ck_faq_answer_len"),
    )

    op.create_table(
        "loyalty_settings",
        sa.Column("id", sa.SmallInteger(), primary_key=True),
        sa.Column("max_bonus_spend_percent", sa.SmallInteger(), nullable=False),
        sa.Column("earn_percent_after_visit", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_loyalty_singleton"),
        sa.CheckConstraint(
            "max_bonus_spend_percent >= 0 AND max_bonus_spend_percent <= 100",
            name="ck_loyalty_max_spend",
        ),
        sa.CheckConstraint(
            "earn_percent_after_visit >= 0 AND earn_percent_after_visit <= 100",
            name="ck_loyalty_earn",
        ),
    )


def downgrade() -> None:
    op.drop_table("loyalty_settings")
    op.drop_table("faq_entries")
    op.drop_index("ix_bonus_transactions_visit_id", table_name="bonus_transactions")
    op.drop_index("ix_bonus_transactions_account_id", table_name="bonus_transactions")
    op.drop_table("bonus_transactions")
    op.drop_table("bonus_accounts")
    op.drop_index("ix_visit_lines_service_id", table_name="visit_lines")
    op.drop_table("visit_lines")
    op.drop_index("ix_visits_confirmed_by_user_id", table_name="visits")
    op.drop_table("visits")
    op.drop_index("ix_appointment_services_service_id", table_name="appointment_services")
    op.drop_table("appointment_services")
    op.drop_index("ix_appointments_starts_at", table_name="appointments")
    op.drop_index("ix_appointments_user_id", table_name="appointments")
    op.drop_table("appointments")
    op.drop_table("schedule_exceptions")
    op.drop_table("schedule_rules")
    op.drop_table("services")
    op.drop_table("users")
