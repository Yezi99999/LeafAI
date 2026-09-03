"""0007 business_daily_stats

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006_user_notification"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "business_daily_stats" not in inspector.get_table_names():
        op.create_table(
            "business_daily_stats",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("stat_date", sa.Date(), nullable=False),
            sa.Column("metric", sa.String(64), nullable=False),
            sa.Column("value", sa.Float(), nullable=False, server_default="0"),
            sa.Column("create_time", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.UniqueConstraint("stat_date", "metric", name="uq_business_daily_stats_date_metric"),
        )
        op.create_index("ix_business_daily_stats_stat_date", "business_daily_stats", ["stat_date"])


def downgrade() -> None:
    op.drop_index("ix_business_daily_stats_stat_date", table_name="business_daily_stats")
    op.drop_table("business_daily_stats")