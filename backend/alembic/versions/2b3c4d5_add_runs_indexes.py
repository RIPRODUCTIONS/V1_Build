"""add indexes for agent_runs

Revision ID: 2b3c4d5
Revises: 1a2b3c4d_add_artifact_metadata
Create Date: 2025-08-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2b3c4d5"
down_revision = "1a2b3c4d_add_artifact_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_agent_runs_intent", "agent_runs", ["intent"], unique=False)
    op.create_index("ix_agent_runs_status", "agent_runs", ["status"], unique=False)
    op.create_index("ix_agent_runs_created_at", "agent_runs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_agent_runs_created_at", table_name="agent_runs")
    op.drop_index("ix_agent_runs_status", table_name="agent_runs")
    op.drop_index("ix_agent_runs_intent", table_name="agent_runs")


