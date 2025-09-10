"""Add children and growth records tables

Revision ID: 0002_add_children_growth_tables
Revises: 0001_add_language_to_users
Create Date: 2025-09-10 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0002_add_children_growth_tables'
down_revision = '0001_add_language_to_users'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sex enum
    sex_enum = postgresql.ENUM('Male', 'Female', name='sexenum')
    sex_enum.create(op.get_bind())
    
    # Create children table
    op.create_table('children',
        sa.Column('child_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sex', sex_enum, nullable=False),
        sa.Column('birth_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('child_id')
    )
    op.create_index(op.f('ix_children_parent_id'), 'children', ['parent_id'], unique=False)
    
    # Create growth_records table
    op.create_table('growth_records',
        sa.Column('record_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('age_months', sa.Integer(), nullable=False),
        sa.Column('weight_kg', sa.Float(), nullable=False),
        sa.Column('height_cm', sa.Float(), nullable=False),
        sa.Column('muac_cm', sa.Float(), nullable=True),
        sa.Column('bmi', sa.Float(), nullable=True),
        sa.Column('diet_diversity_score', sa.Integer(), nullable=False),
        sa.Column('recent_infection', sa.Boolean(), nullable=False),
        sa.Column('z_scores_percentiles', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('prediction_results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['child_id'], ['children.child_id'], ),
        sa.PrimaryKeyConstraint('record_id')
    )
    op.create_index(op.f('ix_growth_records_child_id'), 'growth_records', ['child_id'], unique=False)
    op.create_index('idx_growth_records_age', 'growth_records', ['age_months'], unique=False)
    op.create_index('idx_growth_records_child_recorded', 'growth_records', ['child_id', 'recorded_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_growth_records_child_recorded', 'growth_records')
    op.drop_index('idx_growth_records_age', 'growth_records')
    op.drop_index(op.f('ix_growth_records_child_id'), 'growth_records')
    op.drop_index(op.f('ix_children_parent_id'), 'children')
    
    # Drop tables
    op.drop_table('growth_records')
    op.drop_table('children')
    
    # Drop enum
    sex_enum = postgresql.ENUM('Male', 'Female', name='sexenum')
    sex_enum.drop(op.get_bind())
