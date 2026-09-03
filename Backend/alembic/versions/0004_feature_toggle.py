"""add feature_toggle

Revision ID: 0004_feature_toggle
Revises: 0003_user_free_quota
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa


revision = "0004_feature_toggle"
down_revision = "0003_user_free_quota"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "feature_toggle" not in inspector.get_table_names():
        op.create_table(
            "feature_toggle",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("code", sa.String(64), nullable=False),
            sa.Column("name", sa.String(128), nullable=False),
            sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("whitelist_user_ids", sa.JSON(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True, server_default=""),
            sa.Column("create_time", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
            sa.Column("update_time", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_feature_toggle_code", "feature_toggle", ["code"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "feature_toggle" in inspector.get_table_names():
        op.drop_index("ix_feature_toggle_code", table_name="feature_toggle")
        op.drop_table("feature_toggle")