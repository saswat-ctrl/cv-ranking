"""Add user_score to candidates

Revision ID: 007_add_user_score
Revises: 006_add_ranking_fields
Create Date: 2025-12-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_add_user_score'
down_revision = '006_add_ranking_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add user_score column to candidates table
    op.add_column('candidates', sa.Column('user_score', sa.Float(), nullable=True))


def downgrade():
    # Remove user_score column
    op.drop_column('candidates', 'user_score')
