"""Web UI: telegram_username, appointment source/discount, visit ratings, consultation log.

Revision ID: 0002_web_ui
Revises: 0001_initial
Create Date: 2026-04-28

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0002_web_ui"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_username", sa.Text(), nullable=True))
    op.create_index(
        "ix_users_telegram_username_unique",
        "users",
        ["telegram_username"],
        unique=True,
        postgresql_where=sa.text("telegram_username IS NOT NULL"),
    )

    op.add_column(
        "appointments",
        sa.Column(
            "source",
            sa.Text(),
            server_default="web",
            nullable=False,
        ),
    )
    op.add_column(
        "appointments",
        sa.Column("discount_percent", sa.SmallInteger(), server_default="0", nullable=False),
    )
    op.add_column(
        "appointments",
        sa.Column(
            "created_by_user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_check_constraint(
        "ck_appointments_source_values",
        "appointments",
        "source IN ('llm','telegram_bot','web','admin')",
    )
    op.create_check_constraint(
        "ck_appointments_discount_percent",
        "appointments",
        "discount_percent >= 0 AND discount_percent <= 100",
    )

    op.add_column(
        "visits",
        sa.Column("client_rating_stars", sa.SmallInteger(), nullable=True),
    )
    op.add_column(
        "visits",
        sa.Column("client_rating_comment", sa.Text(), nullable=True),
    )
    op.add_column(
        "visits",
        sa.Column("service_rating_stars", sa.SmallInteger(), nullable=True),
    )
    op.add_column(
        "visits",
        sa.Column("service_rating_comment", sa.Text(), nullable=True),
    )
    op.create_check_constraint(
        "ck_visits_client_rating_stars",
        "visits",
        "client_rating_stars IS NULL OR (client_rating_stars >= 1 AND client_rating_stars <= 5)",
    )
    op.create_check_constraint(
        "ck_visits_service_rating_stars",
        "visits",
        "service_rating_stars IS NULL OR (service_rating_stars >= 1 AND service_rating_stars <= 5)",
    )

    op.create_table(
        "consultation_messages",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("request_id", UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint(
            "role IN ('user','assistant')",
            name="ck_consultation_messages_role",
        ),
        sa.CheckConstraint(
            "char_length(content) <= 16000",
            name="ck_consultation_messages_content_len",
        ),
    )
    op.create_index(
        "ix_consultation_messages_user_created",
        "consultation_messages",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_consultation_messages_user_created", table_name="consultation_messages")
    op.drop_table("consultation_messages")

    op.drop_constraint("ck_visits_service_rating_stars", "visits", type_="check")
    op.drop_constraint("ck_visits_client_rating_stars", "visits", type_="check")
    op.drop_column("visits", "service_rating_comment")
    op.drop_column("visits", "service_rating_stars")
    op.drop_column("visits", "client_rating_comment")
    op.drop_column("visits", "client_rating_stars")

    op.drop_constraint("ck_appointments_discount_percent", "appointments", type_="check")
    op.drop_constraint("ck_appointments_source_values", "appointments", type_="check")
    op.drop_column("appointments", "created_by_user_id")
    op.drop_column("appointments", "discount_percent")
    op.drop_column("appointments", "source")

    op.drop_index("ix_users_telegram_username_unique", table_name="users")
    op.drop_column("users", "telegram_username")
