"""Add is_accepted to items.

Revision ID: 202512012237
Revises: 202511300300
Create Date: 2025-12-01 22:37:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202512012237'
down_revision = '202511300300'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('items', sa.Column('is_accepted', sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column('items', 'is_accepted')
