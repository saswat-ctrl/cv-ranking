"""add ranking fields

Revision ID: 006_add_ranking_fields
Revises: 005_update_candidates_extraction
Create Date: 2025-11-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_ranking_fields'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add ranking fields to jobs table
    op.add_column('ranking_jobs', sa.Column('embedding', postgresql.BYTEA(), nullable=True))
    op.add_column('ranking_jobs', sa.Column('embedding_model', sa.String(), nullable=True))
    op.add_column('ranking_jobs', sa.Column('ranking_version', sa.String(), nullable=True))

    # Add ranking fields to candidates table
    op.add_column('candidates', sa.Column('embedding', postgresql.BYTEA(), nullable=True))
    op.add_column('candidates', sa.Column('embedding_model', sa.String(), nullable=True))
    op.add_column('candidates', sa.Column('ranking_score', sa.Float(), nullable=True))
    op.add_column('candidates', sa.Column('semantic_score', sa.Float(), nullable=True))
    op.add_column('candidates', sa.Column('keyword_score', sa.Float(), nullable=True))
    op.add_column('candidates', sa.Column('ranking_reasoning', sa.Text(), nullable=True))
    op.add_column('candidates', sa.Column('ranked_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('candidates', sa.Column('is_readable', sa.Boolean(), server_default='true', nullable=True))

    # Create indexes
    op.create_index('idx_candidates_ranking_score', 'candidates', ['ranking_score'], unique=False)
    op.create_index('idx_candidates_readable', 'candidates', ['is_readable'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_candidates_readable', table_name='candidates')
    op.drop_index('idx_candidates_ranking_score', table_name='candidates')

    # Drop columns from candidates table
    op.drop_column('candidates', 'is_readable')
    op.drop_column('candidates', 'ranked_at')
    op.drop_column('candidates', 'ranking_reasoning')
    op.drop_column('candidates', 'keyword_score')
    op.drop_column('candidates', 'semantic_score')
    op.drop_column('candidates', 'ranking_score')
    op.drop_column('candidates', 'embedding_model')
    op.drop_column('candidates', 'embedding')

    # Drop columns from jobs table
    op.drop_column('ranking_jobs', 'ranking_version')
    op.drop_column('ranking_jobs', 'embedding_model')
    op.drop_column('ranking_jobs', 'embedding')
