"""seed automation rules

Revision ID: 3f_seed_automation_rules
Revises: 1a2b3c4d_add_artifact_metadata
Create Date: 2025-08-12
"""

from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3f_seed_automation_rules"
down_revision = "1a2b3c4d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tables if they do not exist
    op.create_table(
        "automation_rules",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=True, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("trigger_type", sa.String(), nullable=False),
        sa.Column("event_pattern", sa.String(), nullable=True),
        sa.Column("conditions", sa.JSON(), nullable=True),
        sa.Column("actions", sa.JSON(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_template", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("execution_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_executed", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "rule_executions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("rule_id", sa.String(), nullable=False, index=True),
        sa.Column("event_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("executed_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False, index=True),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
    )

    rules_table = sa.table(
        "automation_rules",
        sa.Column("id", sa.String()),
        sa.Column("user_id", sa.String()),
        sa.Column("name", sa.String()),
        sa.Column("description", sa.Text()),
        sa.Column("trigger_type", sa.String()),
        sa.Column("event_pattern", sa.String()),
        sa.Column("conditions", sa.JSON()),
        sa.Column("actions", sa.JSON()),
        sa.Column("enabled", sa.Boolean()),
        sa.Column("is_template", sa.Boolean()),
        sa.Column("created_at", sa.DateTime()),
    )
    op.bulk_insert(
        rules_table,
        [
            {
                "id": "builtin_meeting_prep",
                "user_id": "system",
                "name": "Meeting Preparation",
                "description": "Create prep task 15 minutes before meetings",
                "trigger_type": "event",
                "event_pattern": "calendar.event.created",
                "conditions": {
                    "any": [
                        {"title_contains": "meeting"},
                        {"title_contains": "call"},
                        {"title_contains": "1:1"},
                        {"title_contains": "sync"},
                    ]
                },
                "actions": [
                    {
                        "type": "create_task",
                        "params": {
                            "title_template": "Prep for: {title}",
                            "description": "Review agenda, prepare questions, gather materials",
                            "minutes_before": 15,
                            "priority": "high",
                        },
                    }
                ],
                "enabled": True,
                "is_template": True,
                "created_at": datetime.now(timezone.utc),
            },
            {
                "id": "builtin_daily_summary",
                "user_id": "system",
                "name": "Daily Summary",
                "description": "Send daily agenda at 8am",
                "trigger_type": "schedule",
                "event_pattern": "",
                "conditions": {},
                "actions": [
                    {
                        "type": "aggregate_and_notify",
                        "params": {
                            "sources": ["calendar", "tasks", "emails"],
                            "channel": "preferred",
                            "template": "daily_summary",
                        },
                    }
                ],
                "enabled": False,
                "is_template": True,
                "created_at": datetime.now(timezone.utc),
            },
            {
                "id": "builtin_email_to_task",
                "user_id": "system",
                "name": "Email to Task",
                "description": "Convert important emails to tasks",
                "trigger_type": "event",
                "event_pattern": "email.received",
                "conditions": {
                    "any": [
                        {"subject_contains": "ACTION"},
                        {"subject_contains": "TODO"},
                        {"body_contains": "by EOD"},
                        {"from_vip": True},
                    ]
                },
                "actions": [
                    {
                        "type": "create_task",
                        "params": {
                            "title_template": "Email: {subject}",
                            "description_template": "From: {from}\n\n{preview}",
                            "due_date": "smart_parse",
                            "priority": "medium",
                        },
                    }
                ],
                "enabled": False,
                "is_template": True,
                "created_at": datetime.now(timezone.utc),
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("rule_executions")
    op.drop_table("automation_rules")


