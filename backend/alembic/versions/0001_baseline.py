from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0001_baseline'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Baseline placeholder; real schema should be managed via subsequent revisions
    pass


def downgrade() -> None:
    pass



