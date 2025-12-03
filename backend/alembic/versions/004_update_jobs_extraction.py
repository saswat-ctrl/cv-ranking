"""Add extraction and parsing fields to jobs table

Revision ID: 004_update_jobs_extraction
Revises: 003
Create Date: 2025-11-28

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Add extraction and parsing fields to ranking_jobs table
    op.add_column('ranking_jobs', sa.Column('extraction_status', sa.String(20), nullable=False, server_default='pending'))
    op.add_column('ranking_jobs', sa.Column('extracted_text', sa.Text(), nullable=True))
    op.add_column('ranking_jobs', sa.Column('extraction_error', sa.Text(), nullable=True))
    op.add_column('ranking_jobs', sa.Column('extraction_duration', sa.Float(), nullable=True))
    op.add_column('ranking_jobs', sa.Column('file_size', sa.Integer(), nullable=True))
    op.add_column('ranking_jobs', sa.Column('file_type', sa.String(100), nullable=True))


def downgrade():
    op.drop_column('ranking_jobs', 'file_type')
    op.drop_column('ranking_jobs', 'file_size')
    op.drop_column('ranking_jobs', 'extraction_duration')
    op.drop_column('ranking_jobs', 'extraction_error')
    op.drop_column('ranking_jobs', 'extracted_text')
    op.drop_column('ranking_jobs', 'extraction_status')
