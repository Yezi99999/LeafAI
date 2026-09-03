"""add user_notification

Revision ID: 0006_user_notification
Revises: 0005_points
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa


revision = "0006_user_notification"
down_revision = "0005_points"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "user_notification" not in inspector.get_table_names():
        op.create_table(
            "user_notification",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("type", sa.String(20), nullable=False, server_default="system"),
            sa.Column("title", sa.String(128), nullable=False),
            sa.Column("content", sa.Text(), nullable=True, server_default=""),
            sa.Column("extra_data", sa.JSON(), nullable=True),
            sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("read_time", sa.DateTime(), nullable=True),
            sa.Column("create_time", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_user_notification_user_id", "user_notification", ["user_id"])
        op.create_index("ix_user_notification_type", "user_notification", ["type"])
        op.create_index("ix_user_notification_is_read", "user_notification", ["is_read"])
        op.create_index("ix_user_notification_create_time", "user_notification", ["create_time"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "user_notification" in inspector.get_table_names():
        op.drop_index("ix_user_notification_create_time", table_name="user_notification")
        op.drop_index("ix_user_notification_is_read", table_name="user_notification")
        op.drop_index("ix_user_notification_type", table_name="user_notification")
        op.drop_index("ix_user_notification_user_id", table_name="user_notification")
        op.drop_table("user_notification")