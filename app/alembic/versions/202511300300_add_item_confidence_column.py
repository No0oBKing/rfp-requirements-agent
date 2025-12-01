"""Add confidence column to items.

Revision ID: 202511300300
Revises: 202511291700
Create Date: 2025-11-30 03:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "202511300300"
down_revision: Union[str, Sequence[str], None] = "202511291700"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add confidence column to items."""
    op.add_column("items", sa.Column("confidence", sa.Float(), nullable=True))


def downgrade() -> None:
    """Remove confidence column from items."""
    op.drop_column("items", "confidence")
