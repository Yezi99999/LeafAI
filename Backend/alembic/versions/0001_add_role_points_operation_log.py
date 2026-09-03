"""add role, points_balance to user; add operation_log

Revision ID: 0001_admin
Revises:
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_admin"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # user 表新增角色与积分字段（仅当不存在时添加）
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    user_cols = {c["name"] for c in inspector.get_columns("user")}

    if "role" not in user_cols:
        op.add_column("user", sa.Column("role", sa.String(32), nullable=False, server_default="user"))
    if "points_balance" not in user_cols:
        op.add_column("user", sa.Column("points_balance", sa.Integer(), nullable=False, server_default="0"))

    # 同步已有超管记录的角色
    op.execute("UPDATE \"user\" SET role = 'admin' WHERE is_superuser = TRUE")

    # 操作审计表
    if not inspector.has_table("operation_log"):
        op.create_table(
            "operation_log",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("admin_user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("module", sa.String(64), nullable=False),
            sa.Column("action", sa.String(64), nullable=False),
            sa.Column("target_id", sa.String(128), nullable=True),
            sa.Column("detail", sa.JSON(), nullable=True),
            sa.Column("ip", sa.String(64), nullable=True),
            sa.Column("user_agent", sa.String(256), nullable=True),
            sa.Column("create_time", sa.DateTime(), nullable=True),
        )
        op.create_index("ix_operation_log_admin_user_id", "operation_log", ["admin_user_id"])
        op.create_index("ix_operation_log_create_time", "operation_log", ["create_time"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("operation_log"):
        op.drop_index("ix_operation_log_admin_user_id", table_name="operation_log")
        op.drop_index("ix_operation_log_create_time", table_name="operation_log")
        op.drop_table("operation_log")

    user_cols = {c["name"] for c in inspector.get_columns("user")}
    if "points_balance" in user_cols:
        op.drop_column("user", "points_balance")
    if "role" in user_cols:
        op.drop_column("user", "role")