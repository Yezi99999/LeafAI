"""0008 rate_to_multiplier

将 points_consumption_rate.rate 改名为 multiplier 且类型改为 Float：
新语义为「倍率」，实际消耗积分 = 模型 unit_points × multiplier。

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"]: c for c in
            inspector.get_columns("points_consumption_rate")}
    if "rate" in cols and "multiplier" not in cols:
        op.alter_column(
            "points_consumption_rate",
            "rate",
            new_column_name="multiplier",
            existing_type=sa.Integer(),
            type_=sa.Float(),
            existing_nullable=True,
        )
    elif "multiplier" in cols:
        op.alter_column(
            "points_consumption_rate",
            "multiplier",
            existing_type=sa.Integer(),
            type_=sa.Float(),
            existing_nullable=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in
            inspector.get_columns("points_consumption_rate")}
    if "multiplier" in cols and "rate" not in cols:
        op.alter_column(
            "points_consumption_rate",
            "multiplier",
            new_column_name="rate",
            existing_type=sa.Float(),
            type_=sa.Integer(),
            existing_nullable=True,
        )