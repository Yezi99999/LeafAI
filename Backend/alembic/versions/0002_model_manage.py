"""add model management fields to ai_model

Revision ID: 0002_model_manage
Revises: 0001_admin
Create Date: 2026-09-03
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_model_manage"
down_revision = "0001_admin"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("ai_model")}

    additions = {
        "version": sa.Column("version", sa.String(64), nullable=True, server_default=""),
        "deploy_env": sa.Column("deploy_env", sa.String(20), nullable=False, server_default="prod"),
        "deploy_status": sa.Column("deploy_status", sa.String(20), nullable=False, server_default="running"),
        "unit_points": sa.Column("unit_points", sa.Integer(), nullable=False, server_default="0"),
        "avg_latency_ms": sa.Column("avg_latency_ms", sa.Float(), nullable=True),
        "success_count": sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        "fail_count": sa.Column("fail_count", sa.Integer(), nullable=False, server_default="0"),
        "last_deploy_time": sa.Column("last_deploy_time", sa.DateTime(), nullable=True),
    }
    for name, col in additions.items():
        if name not in cols:
            op.add_column("ai_model", col)

    # 去掉 server_default，避免后续插入显式列冲突
    for name, col in additions.items():
        if name not in cols and col.server_default is not None:
            op.alter_column("ai_model", name, server_default=None)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("ai_model")}
    for name in ["version", "deploy_env", "deploy_status", "unit_points",
                 "avg_latency_ms", "success_count", "fail_count", "last_deploy_time"]:
        if name in cols:
            op.drop_column("ai_model", name)