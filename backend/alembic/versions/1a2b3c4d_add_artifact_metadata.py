import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '1a2b3c4d'
down_revision = '043f676b4c56'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('artifacts', sa.Column('file_path', sa.String(length=512), nullable=True))
    op.add_column(
        'artifacts',
        sa.Column('status', sa.String(length=50), nullable=False, server_default='completed'),
    )


def downgrade() -> None:
    op.drop_column('artifacts', 'status')
    op.drop_column('artifacts', 'file_path')
