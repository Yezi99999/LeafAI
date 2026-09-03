"""add points_consumption_rate + points_transaction

Revision ID: 0005_points
Revises: 0004_feature_toggle
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa


revision = "0005_points"
down_revision = "0004_feature_toggle"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "points_consumption_rate" not in tables:
        op.create_table(
            "points_consumption_rate",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("service_code", sa.String(64), nullable=False),
            sa.Column("rate", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("rate_unit", sa.String(20), nullable=False, server_default="per_call"),
            sa.Column("model_id", sa.Integer(), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("create_time", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("update_time", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_points_consumption_rate_service_code", "points_consumption_rate", ["service_code"])

    if "points_transaction" not in tables:
        op.create_table(
            "points_transaction",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("tx_type", sa.String(20), nullable=False),
            sa.Column("points_delta", sa.Integer(), nullable=False),
            sa.Column("service_code", sa.String(64), nullable=True),
            sa.Column("task_id", sa.String(64), nullable=True),
            sa.Column("model_id", sa.Integer(), nullable=True),
            sa.Column("balance_after", sa.Integer(), nullable=False),
            sa.Column("remark", sa.String(256), nullable=True),
            sa.Column("create_time", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_points_transaction_user_id", "points_transaction", ["user_id"])
        op.create_index("ix_points_transaction_service_code", "points_transaction", ["service_code"])
        op.create_index("ix_points_transaction_create_time", "points_transaction", ["create_time"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()
    if "points_transaction" in tables:
        op.drop_index("ix_points_transaction_create_time", table_name="points_transaction")
        op.drop_index("ix_points_transaction_service_code", table_name="points_transaction")
        op.drop_index("ix_points_transaction_user_id", table_name="points_transaction")
        op.drop_table("points_transaction")
    if "points_consumption_rate" in tables:
        op.drop_index("ix_points_consumption_rate_service_code", table_name="points_consumption_rate")
        op.drop_table("points_consumption_rate")