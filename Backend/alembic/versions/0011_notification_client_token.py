"""0011 notification client_token

通知表增加 client_token：面向客户端的公开标识，避免暴露内部 id 与 user_id。

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0011"
down_revision = "0010"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns("user_notification")]
    if "client_token" not in cols:
        op.add_column(
            "user_notification",
            sa.Column("client_token", sa.String(36), nullable=False,
                      server_default=sa.text("gen_random_uuid()::text")),
        )
        op.create_index("ix_user_notification_client_token", "user_notification", ["client_token"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c["name"] for c in inspector.get_columns("user_notification")]
    if "client_token" in cols:
        op.drop_index("ix_user_notification_client_token", table_name="user_notification")
        op.drop_column("user_notification", "client_token")