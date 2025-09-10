"""Add language column to users table"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_language_to_users'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('language', sa.String(length=10), nullable=False, server_default='english'))
    # Remove server_default after populate
    op.alter_column('users', 'language', server_default=None)


def downgrade() -> None:
    op.drop_column('users', 'language')
