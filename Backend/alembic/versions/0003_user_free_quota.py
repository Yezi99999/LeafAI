"""add free_quota to user

Revision ID: 0003_user_free_quota
Revises: 0002_model_manage
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa


revision = "0003_user_free_quota"
down_revision = "0002_model_manage"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("user")}
    if "free_quota" not in cols:
        op.add_column(
            "user",
            sa.Column("free_quota", sa.JSON(), nullable=True, server_default=sa.text("'{}'::json")),
        )
        op.alter_column("user", "free_quota", server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("user")}
    if "free_quota" in cols:
        op.drop_column("user", "free_quota")