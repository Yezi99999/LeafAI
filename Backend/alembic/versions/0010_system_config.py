"""0010 system_config

系统配置键值表：后台可编辑的站点配置（如 API 接入文档）。

Revision ID: 0010
Revises: 0008
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0008"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "system_config" not in inspector.get_table_names():
        op.create_table(
            "system_config",
            sa.Column("key", sa.String(64), primary_key=True),
            sa.Column("value", sa.JSON(), nullable=True),
            sa.Column("update_time", sa.DateTime(), nullable=True,
                      server_default=sa.text("now()")),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "system_config" in inspector.get_table_names():
        op.drop_table("system_config")