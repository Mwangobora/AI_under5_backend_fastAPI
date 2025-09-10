"""Merge heads

Revision ID: cbe94b687f55
Revises: 0002_add_children_growth_tables, a4081f6cd81e
Create Date: 2025-09-10 15:12:30.048151

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cbe94b687f55'
down_revision = ('0002_add_children_growth_tables', 'a4081f6cd81e')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
